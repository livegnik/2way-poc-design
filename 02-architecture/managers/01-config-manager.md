



# 01 Config Manager

Defines configuration ingestion, validation, snapshot publication, and mutation control for node-local settings. Specifies configuration sources, precedence, schema registration, and change propagation semantics. Defines APIs, security posture, and failure handling for configuration management.

For the meta specifications, see [01-config-manager meta](../../10-appendix/meta/02-architecture/managers/01-config-manager-meta.md).

## 1. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* All configuration access is mediated by [Config Manager](01-config-manager.md) APIs, no other component reads `.env` or `settings` directly.
* No configuration value becomes visible to consumers unless it has passed schema-based validation and policy checks.
* Precedence is deterministic, stable across restarts, and identical for all consumers within a process.
* Published snapshots are immutable, per-namespace, and cannot be mutated by consumers.
* Bootstrap critical `node.*` values sourced from `.env` are immutable for the life of the process.
* Unknown keys are rejected unless registered in the schema registry before load or reload.
* Reload is serialized, two-phase, and either fully commits or has no effect. Partial application is forbidden.
* Veto by an owning manager during prepare prevents commit and preserves the prior snapshot.
* `node.protocol.version` is resolved once from `.env`, cannot be overridden, and is the sole local source of truth for protocol negotiation per [01-protocol/11-versioning-and-compatibility.md](../../01-protocol/11-versioning-and-compatibility.md).
* Configuration is node local and is not stored in, derived from, or replicated via the graph, preserving the authority boundaries defined in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).

These guarantees must hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 2. Configuration model and storage

The configuration layer exists to keep node-local operational state self describing, auditable, and accessible through one interface.

Configuration follows a strict split:

* Values required before the backend can reliably open SQLite or locate key material live in `.env`.
* All other configuration lives in SQLite in the `settings` table and is accessed only through [Config Manager](01-config-manager.md).

### 2.1 Boot critical configuration in `.env`

`.env` holds only values needed to reach a minimally functioning backend process, open SQLite, locate keys, configure Tor wiring, and expose the HTTP entrypoint.

Boot-critical keys:

| Key | Required | Default | Notes |
| --- | --- | --- | --- |
| `BACKEND_DB_PATH` | Yes | `backend/instance/backend.db` | SQLite database path. |
| `BACKEND_HOST` | Yes | `127.0.0.1` | Local HTTP bind host. |
| `BACKEND_PORT` | Yes | `8000` | Local HTTP bind port. |
| `KEYS_DIR` | Yes | `backend/keys` | Key storage directory. |
| `TOR_CONTROL_PORT` | No | `9051` | Used only when Tor transport is enabled. |
| `TOR_SOCKS_PORT` | No | `9050` | Used only when Tor transport is enabled. |
| `PROTOCOL_VERSION` | Yes | `1.0.0` | Published as `node.protocol.version`. |

Rules:

* `.env` is parsed exactly once during startup.
* After parsing, [Config Manager](01-config-manager.md) keeps values in memory and no other component reads `.env` directly.
* `.env` does not contain graph identifiers, graph state, or mutable feature flags.
* `.env` is immutable after startup. Any change requires process restart.
* `PROTOCOL_VERSION` is validated and published as `node.protocol.version`.
* Required keys must be present and non-empty.
* `TOR_CONTROL_PORT` and `TOR_SOCKS_PORT` must be provided together or omitted together.

### 2.2 SQLite backed settings table

All non boot configuration is stored in SQLite in a single key-value table.

```sql

CREATE TABLE IF NOT EXISTS settings (

    key   TEXT PRIMARY KEY,

    value TEXT NOT NULL

);

```

Rules:

* Values are stored as raw text.
* [Config Manager](01-config-manager.md) performs type conversion and validation before publishing values.
* [Config Manager](01-config-manager.md) is the sole reader and writer of this table. [Storage Manager](02-storage-manager.md) provides the transaction and query primitives, but does not interpret keys.
* Updates are atomic and recorded as a new committed snapshot with a new `cfg_seq`.

### 2.3 Namespaces and separation of concerns

[Config Manager](01-config-manager.md) partitions configuration keys into namespaces. Namespaces determine ownership, access rules, and reload contracts.

Canonical namespaces:

* `node.*` boot and identity of the local runtime environment, sourced from `.env` plus defaults.
* `storage.*` storage tuning and operational settings, owned by [Storage Manager](02-storage-manager.md).
* `graph.*` graph engine operational settings, owned by [Graph Manager](07-graph-manager.md), excluding graph state.
* `schema.*` schema compilation and resolution settings, owned by [Schema Manager](05-schema-manager.md).
* `auth.*` local authentication operational settings, owned by [Auth Manager](04-auth-manager.md).
* `key.*` local key custody operational settings, owned by [Key Manager](03-key-manager.md).
* `network.*` network operational settings, owned by [Network Manager](10-network-manager.md), excluding keys and secrets.
* `acl.*` access control operational settings, owned by [ACL Manager](06-acl-manager.md), excluding graph ACL objects.
* `debug.*` debug logger toggles, owned by the debug logger utility.
* `log.*` logging thresholds and routing settings, owned by [Log Manager](12-log-manager.md).
* `dos.*` DoS containment thresholds, puzzle policy, and telemetry directives mandated by [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md), owned by [DoS Guard Manager](14-dos-guard-manager.md).
* `event.*` event routing and WebSocket related operational settings, owned by [Event Manager](11-event-manager.md).
* `health.*` health reporting and thresholds, owned by [Health Manager](13-health-manager.md).
* `state.*` sync and consistency operational settings, owned by [State Manager](09-state-manager.md).
* `service.<service_name>.*` system service settings owned by the service implementation.
* `app.<slug>.*` app scoped settings owned by the app backend extension or [App Manager](08-app-manager.md).

Rules:

* Each namespace has a single owning manager or owning app backend.
* A namespace may be reserved even if it defines zero keys.
* A manager may only request its own namespace snapshot, unless an explicit export contract exists.
* Frontend code never reads configuration directly. Frontend visible settings are obtained via services which call [Config Manager](01-config-manager.md) export APIs under [OperationContext](../services-and-apps/05-operation-context.md) and [ACL Manager](06-acl-manager.md) filtering.

Reserved namespaces are allowed even when no concrete keys are defined.

### 2.4 Configuration is not stored in the graph

[Config Manager](01-config-manager.md) must not store node local operational configuration in the graph.

Reasons:

* Configuration must be readable before [OperationContext](../services-and-apps/05-operation-context.md) and graph initialization, otherwise bootstrap can deadlock.
* Graph data replicates and is subject to ACL semantics intended for protocol objects, not node local state.
* Syncing node local host parameters or operational secrets to peers is a confidentiality and integrity violation.
* Keeping configuration out of the graph preserves protocol authority boundaries and prevents circular dependencies.

### 2.5 Protocol version tuple

[Config Manager](01-config-manager.md) is the sole owner of the locally configured protocol version required by [01-protocol/11-versioning-and-compatibility.md](../../01-protocol/11-versioning-and-compatibility.md).

Rules:

* The version originates from `.env` and is published as `node.protocol.version`.
* The version is exposed as both `(major, minor, patch)` integers and a normalized string `major.minor.patch`.
* The version cannot be overridden by SQLite settings, environment overrides, or runtime update APIs.
* Startup fails if the version is missing, malformed, or advertises a version newer than the running build supports.

## 3. Configuration sources and precedence

[Config Manager](01-config-manager.md) enforces a deterministic precedence stack:

1. Built-in defaults compiled with the backend.
2. `.env` boot configuration, limited to the keys described in section 2.1.
3. SQLite `settings` table for all mutable namespaces.
4. Environment overrides prefixed with `TWOWAY_` intended for CI and developer usage, applied for the life of the process.
5. Ephemeral overrides provided programmatically by CLI flags, test harnesses, or diagnostics, applied for the life of the process.

Rules:

* Later sources override earlier sources for the same key.
* Unknown keys cause validation failure unless registered in the schema registry before load or reload.
* `PROTOCOL_VERSION` and `node.protocol.version` are exempt from all overrides. Only `.env` may set them.

## 4. Internal engines and lifecycle

[Config Manager](01-config-manager.md) is implemented as a set of internal engines with strict sequencing.

### 4.1 Internal engines

* Schema Registry Engine
  * Accepts key registrations from managers and app backends.
  * Stores type, constraints, default, reloadability, secrecy classification, and export policy for each key.
  * Freezes registrations after startup publication, except for explicit app registration windows controlled by [App Manager](08-app-manager.md) during app load.
* Load Engine
  * Loads defaults, parses `.env`, queries SQLite settings, then applies override layers.
  * Produces a fully merged candidate configuration tree plus provenance metadata per key.
* Validation Engine
  * Validates the candidate tree against the schema registry.
  * Enforces type conversion, constraint checks, required keys, directory existence rules, and policy rules such as forbidden keys in `.env`.
  * Rejects unknown keys unless explicitly allowed by registration.
* Snapshot Engine
  * Produces immutable per namespace snapshots and a global immutable snapshot.
  * Assigns `cfg_seq`, timestamp, and provenance metadata to the snapshot.
  * Stores the committed snapshot in memory as the current authoritative view.
* Change Coordination Engine
  * Computes diffs between the current snapshot and a candidate snapshot.
  * Executes two phase notification, prepare then commit, to owning managers for affected namespaces.
  * Applies veto logic and ensures all or nothing commit.
* Export Filter Engine
  * Produces filtered views for services and frontend exposure based on [OperationContext](../services-and-apps/05-operation-context.md) and [ACL Manager](06-acl-manager.md) decisions.
  * Applies key level export policies declared in the schema registry.

### 4.2 Startup sequencing

Startup is fail closed and must be deterministic.

1. Schema Registry Engine registers all built in keys and defaults.
2. Load Engine reads `.env`. Structural errors halt startup before any other manager initializes.
3. [Storage Manager](02-storage-manager.md) is invoked to open SQLite. [Config Manager](01-config-manager.md) ensures the `settings` table exists, then reads all keys.
4. Load Engine merges defaults, `.env`, SQLite, then overrides per precedence.
5. Validation Engine validates the merged tree, including `node.protocol.version` validation and build compatibility checks.
6. Snapshot Engine creates the initial snapshot and assigns `cfg_seq`.
7. [Config Manager](01-config-manager.md) publishes namespace snapshots to managers during their initialization hooks. The `dos.*` namespace must reach [DoS Guard Manager](14-dos-guard-manager.md) as a single validated snapshot that satisfies the policy contract in [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md); if publication fails, [DoS Guard Manager](14-dos-guard-manager.md) must remain in fail-closed mode with no admissions.
8. Each manager must acknowledge acceptance. Failure to acknowledge halts startup. Partial initialization is forbidden.
9. [Health Manager](13-health-manager.md) is notified that [Config Manager](01-config-manager.md) is ready only after publication acknowledgements succeed.

### 4.3 Shutdown behavior

[Config Manager](01-config-manager.md) shutdown is passive and must not mutate state.

Rules:

* [Config Manager](01-config-manager.md) does not flush configuration to disk on shutdown, except for in flight updates that have already been committed to SQLite.
* [Config Manager](01-config-manager.md) stops accepting update requests once shutdown begins.
* [Config Manager](01-config-manager.md) stops delivering change notifications once shutdown begins.
* The last committed snapshot remains available for in process reads until process termination, unless the process is already in teardown.

### 4.4 Readiness and liveness

[Config Manager](01-config-manager.md) exposes readiness and liveness signals consumed by [Health Manager](13-health-manager.md).

Readiness:

* Ready only after the initial snapshot is validated, published to all managers, and all required acknowledgements have been received.

Liveness:

* Live while the [Config Manager](01-config-manager.md) event loop can service read requests and can serialize update or reload requests.
* Repeated reload failures do not make [Config Manager](01-config-manager.md) non live, but they mark it degraded.

## 5. Schema registration contract

[Config Manager](01-config-manager.md) requires explicit registration for all keys that may appear in SQLite, overrides, or exports.

### 5.1 Registration fields

A registration for a key includes:

* Key name, fully qualified, including namespace.
* Owning manager or owning app id.
* Type descriptor, including parse rules from text.
* Default value or default factory.
* Required flag.
* Constraint set, such as ranges, enum membership, path policy, and format policy.
* Reloadability flag, with optional reload scope.
* Secrecy classification, such as public, local sensitive, secret reference.
* Export policy, including whether the key may be exported and under what selector.
* Optional validation hook to be invoked during Validation Engine execution.
* Optional prepare and commit hooks for the owning manager.

### 5.2 Registration timing rules

* Built in manager registrations occur before `.env` parsing and before reading SQLite.
* App registrations occur only during app load, coordinated by [App Manager](08-app-manager.md), and must complete before app configuration can be read or exported.
* After initial publication, new registrations are rejected unless they are part of an explicit app load window.

### 5.3 Ownership rules

* Only the owning manager may register keys in its namespace.
* Only the owning manager may mark a key reloadable.
* Only the owning manager may receive prepare and commit notifications for changes in its namespace.

## 6. Runtime APIs and consumption model

[Config Manager](01-config-manager.md) exposes a strict API surface. All call paths that can mutate state require an [OperationContext](../services-and-apps/05-operation-context.md).

Read APIs:

* `getNodeConfig()`
  * Returns the immutable `node.*` snapshot.
  * Only callable by managers and core services.
* `getManagerConfig(manager_id)`
  * Returns the immutable snapshot for the caller namespace.
  * Rejected if the caller is not the owning manager or not explicitly whitelisted by an export contract.
* `getAppConfig(app_id)`
  * Returns the immutable snapshot for an app namespace.
  * Only callable by the owning app backend or [App Manager](08-app-manager.md) under an app scoped [OperationContext](../services-and-apps/05-operation-context.md).
* `getSetting(key, default=None, type_hint=None)`
  * Returns a typed value derived from the current snapshot.
  * Rejects access if key visibility is not permitted for the caller context.
* `listSettings(selector=None)`
  * Returns a filtered view of keys and values intended for diagnostics and administrative tooling.
  * Must apply ACL filtering and secrecy rules.

Export APIs:

* `exportConfig(operation_context, selector)`
  * Returns a filtered and policy safe configuration view for service layer and frontend usage.
  * [ACL Manager](06-acl-manager.md) must authorize export, and the export filter must enforce key level export policies.
  * `operation_context` is an [OperationContext](../services-and-apps/05-operation-context.md).

Mutation APIs:

* `updateSettings(operation_context, updates)`
  * Performs an atomic update of one or more SQLite backed keys.
  * Validates the resulting candidate snapshot before commit.
  * Emits audit log entries and a configuration update event through [Event Manager](11-event-manager.md) on success.
  * `operation_context` is an [OperationContext](../services-and-apps/05-operation-context.md).

Reload APIs:

* `reload(operation_context, reason=None)`
  * Re-runs the full load and validation pipeline against current sources.
  * Only affects namespaces that are not immutable.
  * Must serialize with any concurrent updates.
  * `operation_context` is an [OperationContext](../services-and-apps/05-operation-context.md).

Version API:

* `getProtocolVersion()`
  * Returns the locally declared `(major, minor, patch)` tuple and normalized string.
  * Returns only the immutable `.env` derived value.

API rules:

* Returned structures are immutable to prevent caller mutation.
* Read APIs must never perform database reads on the hot path once the snapshot is in memory, except for diagnostics explicitly documented as database backed.
* Mutation APIs must never allow writing `.env` sourced keys.

## 7. Change handling and immutability rules

### 7.1 Immutability

* `node.*` is immutable after startup.
* `node.protocol.version` is immutable and cannot be reloaded or overridden.
* Keys not marked reloadable may be updated in SQLite, but the update must not take effect until restart if the owning manager declares that behavior. In that case, [Config Manager](01-config-manager.md) must record the value but must not publish it as active.

### 7.2 Two phase change propagation

[Config Manager](01-config-manager.md) delivers change notifications in two phases:

* Prepare phase
  * [Config Manager](01-config-manager.md) sends the diff for affected keys to the owning managers.
  * Owning managers may veto the change with a structured rejection reason.
* Commit phase
  * If no veto occurs, [Config Manager](01-config-manager.md) commits the new snapshot, increments `cfg_seq`, and publishes the new namespace snapshots.
  * Managers receive a commit notification after the snapshot becomes authoritative.

Rules:

* Veto cancels the entire update or reload attempt.
* On veto, [Config Manager](01-config-manager.md) must preserve the prior snapshot and must not partially apply any changes.
* Change notifications must be delivered in deterministic order, based on a fixed manager ordering, and must be consistent across runs.
* `dos.*` policy updates must be committed atomically so that [DoS Guard Manager](14-dos-guard-manager.md) never observes partial policies, satisfying the policy update rule in [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).

### 7.3 Serialization

* Concurrent updates and reloads are serialized.
* A second request is queued behind the active request.
* The queue is bounded. On overflow, [Config Manager](01-config-manager.md) rejects requests with a fail closed error.

### 7.4 Installation and bootstrap mode

Some configuration must be set during initial node setup before normal administrative identity and permissions exist.

[Config Manager](01-config-manager.md) supports a limited bootstrap mode:

* Bootstrap writes are permitted only under an [OperationContext](../services-and-apps/05-operation-context.md) that carries an explicit bootstrap capability issued and validated by the installation flow.
* Bootstrap writes are limited to an allowlist of keys required to complete initial setup, such as network and privacy operational settings and initial app enablement flags.
* Bootstrap writes are still validated via the schema registry.
* Bootstrap mode ends when the installation flow marks the node as installed via an installation owned flag. After this, bootstrap capabilities are rejected.
* Rejected bootstrap writes after installation MUST return `ErrorDetail.code=acl_denied`.

[Config Manager](01-config-manager.md) does not create admin identities and does not own the installation state machine. It only enforces the capability and key allowlist rules for configuration writes.

## 8. Security, secrecy, and trust boundaries

* `.env`, environment overrides, and SQLite contents are untrusted until validated.
* [Config Manager](01-config-manager.md) must treat all loaded text as hostile input, including values sourced locally.
* Secrets are not stored directly in SQLite settings. [Config Manager](01-config-manager.md) stores only secret references, such as file paths or handle ids, and enforces secrecy classification to prevent export.
* Export must be deny-by-default. Only keys explicitly marked exportable may be returned by `exportConfig`.
* Access control for mutation and export flows through [OperationContext](../services-and-apps/05-operation-context.md) and [ACL Manager](06-acl-manager.md) authorization checks.
* Managers and services cannot escalate by editing files. Direct file edits are outside protocol guarantees and must not be relied upon for authorized change paths.
* [Config Manager](01-config-manager.md) must log configuration source usage per load and reload attempt, enabling audit and drift detection.

## 9. Failure posture and observability

Failure posture is fail closed.

Startup failures:

* Any load or validation failure halts startup before other managers initialize.
* Missing `.env`, malformed `.env`, invalid `node.protocol.version`, unknown keys, or failing constraints are fatal.

Runtime failures:

* Reload failure preserves the prior snapshot and emits structured error logs.
* Update failure does not partially write to SQLite. The update must be atomic, either fully persisted and committed, or fully rejected.
* Repeated failures mark the configuration subsystem degraded via [Health Manager](13-health-manager.md).

Error mapping for external surfaces:

* Validation failures, unknown keys, vetoes, or queue overflow -> `config_invalid`.
* Unauthorized export or update -> `acl_denied`.
* Persistence failures -> `storage_error`.
* Unexpected internal failures -> `internal_error`.

Observability:

* [Config Manager](01-config-manager.md) exposes metrics for [Health Manager](13-health-manager.md) consumption:
  * current `cfg_seq`
  * last reload timestamp and duration
  * count of registered keys and namespaces
  * count of reload attempts, successes, failures
  * veto counts by namespace
  * export requests count and denials count
* Audit logs capture:
  * who initiated an update or reload via [OperationContext](../services-and-apps/05-operation-context.md)
  * which keys changed
  * which sources contributed to the new snapshot
  * whether a veto occurred and by whom

## 10. Allowed and forbidden behaviors

### 10.1 Allowed

* Reading configuration exclusively through [Config Manager](01-config-manager.md) APIs.
* Registering keys and schemas during the permitted registration windows.
* Performing hot reload only for keys marked reloadable by the owning manager.
* Updating SQLite backed settings only through authorized backend APIs that invoke [Config Manager](01-config-manager.md).
* Exporting configuration only through `exportConfig` with explicit export policies and ACL authorization.
* Using bootstrap mode only for the limited installation allowlist and only before installation completes.

### 10.2 Forbidden

* Any component reading `.env` directly.
* Any component reading or writing the `settings` table directly.
* Publishing partially validated configuration or allowing consumers to observe intermediate state.
* Treating config callbacks as a general purpose event bus.
* Storing node local operational configuration in the graph or syncing it to peers.
* Allowing overrides to mutate `node.protocol.version` or any `.env` sourced key.
* Allowing a manager to read another manager namespace without an explicit export contract.
