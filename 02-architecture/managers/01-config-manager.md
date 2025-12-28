



# 01 Config Manager

## 1. Purpose and scope

This specification defines the authoritative responsibilities, invariants, and interfaces of the Config Manager within the 2WAY backend.

Config Manager owns configuration ingestion, layering, validation, publication, controlled mutation, and change propagation for all runtime configuration that affects manager and service behavior.

This specification covers configuration sources, precedence rules, storage model, consumer APIs, trust boundaries, startup and shutdown behavior, reload semantics, and fail closed behavior.

This specification does not redefine protocol objects, graph schemas, ACL rules, transport encodings, or key custody beyond what is required to define configuration handling boundaries.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Load boot critical configuration from `.env` into an immutable in memory snapshot for the life of the process.
* Load persistent configuration from SQLite `settings` and merge it with defaults and `.env` according to deterministic precedence rules.
* Provide a single typed read interface for managers, services, and app backends to consume configuration.
* Provide a single controlled mutation interface for authorized callers to update SQLite backed configuration.
* Validate configuration values and structure before they become visible to any consumer.
* Maintain a schema registry for known keys, including types, constraints, defaults, reloadability, and export rules.
* Publish per namespace immutable snapshots to managers during startup and during approved reloads.
* Coordinate safe change propagation via a two phase prepare and commit sequence with veto support by owning managers.
* Emit a monotonic configuration version identifier (`cfg_seq`) and associated provenance metadata for every committed snapshot.
* Supply DoS Guard policy snapshots (rate limits, burst windows, difficulty caps, abuse thresholds, telemetry verbosity) exactly as defined in `01-protocol/11-dos-guard-and-client-puzzles.md`, ensuring atomic visibility to DoS Guard Manager.
* Supply the canonical locally declared protocol version tuple required by `01-protocol/10-versioning-and-compatibility.md`.

This specification does not cover the following:

* Creating the database file, database migrations, or general storage lifecycle, these are owned by Storage Manager.
* Creating, storing, or exporting cryptographic secret material, these are owned by Key Manager or a dedicated secret store.
* Defining graph schemas or ACL policies for protocol objects, these are owned by Graph Manager and ACL Manager.
* Network transport behavior, onion service lifecycle, peer discovery, or message routing, these are owned by Network Manager.
* Installation flows, admin account creation, or plugin installation, these are owned by Installation and App related components. Config Manager only provides a controlled settings interface used by those components.

## 3. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* All configuration access is mediated by Config Manager APIs, no other component reads `.env` or `settings` directly.
* No configuration value becomes visible to consumers unless it has passed schema based validation and policy checks.
* Precedence is deterministic, stable across restarts, and identical for all consumers within a process.
* Published snapshots are immutable, per namespace, and cannot be mutated by consumers.
* Bootstrap critical `node.*` values sourced from `.env` are immutable for the life of the process.
* Unknown keys are rejected unless registered in the schema registry before load or reload.
* Reload is serialized, two phase, and either fully commits or has no effect. Partial application is forbidden.
* Veto by an owning manager during prepare prevents commit and preserves the prior snapshot.
* `node.protocol.version` is resolved once from `.env`, cannot be overridden, and is the sole local source of truth for protocol negotiation.
* Configuration is node local and is not stored in, derived from, or replicated via the graph.

These guarantees must hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 4. Configuration model and storage

The configuration layer exists to keep node local operational state self describing, auditable, and accessible through one interface.

Configuration follows a strict split:

* Values required before the backend can reliably open SQLite or locate key material live in `.env`.
* All other configuration lives in SQLite in the `settings` table and is accessed only through Config Manager.

### 4.1 Boot critical configuration in `.env`

`.env` holds only values needed to reach a minimally functioning backend process, open SQLite, locate keys, configure Tor wiring, and expose the HTTP entrypoint.

Example keys:

```
BACKEND_DB_PATH=backend/instance/backend.db
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
KEYS_DIR=backend/keys
TOR_CONTROL_PORT=9051
TOR_SOCKS_PORT=9050
PROTOCOL_VERSION=1.0.0
```

Rules:

* `.env` is parsed exactly once during startup.
* After parsing, Config Manager keeps values in memory and no other component reads `.env` directly.
* `.env` does not contain graph identifiers, graph state, or mutable feature flags.
* `.env` is immutable after startup. Any change requires process restart.
* `PROTOCOL_VERSION` is validated and published as `node.protocol.version`.

### 4.2 SQLite backed settings table

All non boot configuration is stored in SQLite in a single key value table.

```sql
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

Rules:

* Values are stored as raw text.
* Config Manager performs type conversion and validation before publishing values.
* Config Manager is the sole reader and writer of this table. Storage Manager provides the transaction and query primitives, but does not interpret keys.
* Updates are atomic and recorded as a new committed snapshot with a new `cfg_seq`.

### 4.3 Namespaces and separation of concerns

Config Manager partitions configuration keys into namespaces. Namespaces determine ownership, access rules, and reload contracts.

Canonical namespaces:

* `node.*` boot and identity of the local runtime environment, sourced from `.env` plus defaults.
* `storage.*` storage tuning and operational settings, owned by Storage Manager.
* `graph.*` graph engine operational settings, owned by Graph Manager, excluding graph state.
* `network.*` network operational settings, owned by Network Manager, excluding keys and secrets.
* `acl.*` access control operational settings, owned by ACL Manager, excluding graph ACL objects.
* `log.*` logging thresholds and routing settings, owned by Log Manager.
* `dos.*` DoS containment thresholds, puzzle policy, and telemetry directives mandated by `01-protocol/11-dos-guard-and-client-puzzles.md`, owned by DoS Guard Manager.
* `event.*` event routing and websocket related operational settings, owned by Event Manager.
* `health.*` health reporting and thresholds, owned by Health Manager.
* `app.<app_id>.*` app scoped settings owned by the app backend extension or App Manager.

Rules:

* Each namespace has a single owning manager or owning app backend.
* A manager may only request its own namespace snapshot, unless an explicit export contract exists.
* Frontend code never reads configuration directly. Frontend visible settings are obtained via services which call Config Manager export APIs under OperationContext and ACL filtering.

### 4.4 Configuration is not stored in the graph

Config Manager must not store node local operational configuration in the graph.

Reasons:

* Configuration must be readable before OperationContext and graph initialization, otherwise bootstrap can deadlock.
* Graph data replicates and is subject to ACL semantics intended for protocol objects, not node local state.
* Syncing node local host parameters or operational secrets to peers is a confidentiality and integrity violation.
* Keeping configuration out of the graph preserves protocol authority boundaries and prevents circular dependencies.

### 4.5 Protocol version tuple

Config Manager is the sole owner of the locally configured protocol version required by `01-protocol/10-versioning-and-compatibility.md`.

Rules:

* The version originates from `.env` and is published as `node.protocol.version`.
* The version is exposed as both `(major, minor, patch)` integers and a normalized string `major.minor.patch`.
* The version cannot be overridden by SQLite settings, environment overrides, or runtime update APIs.
* Startup fails if the version is missing, malformed, or advertises a version newer than the running build supports.

## 5. Configuration sources and precedence

Config Manager enforces a deterministic precedence stack:

1. Built in defaults compiled with the backend.
2. `.env` boot configuration, limited to the keys described in section 4.1.
3. SQLite `settings` table for all mutable namespaces.
4. Environment overrides prefixed with `TWOWAY_` intended for CI and developer usage, applied for the life of the process.
5. Ephemeral overrides provided programmatically by CLI flags, test harnesses, or diagnostics, applied for the life of the process.

Rules:

* Later sources override earlier sources for the same key.
* Unknown keys cause validation failure unless registered in the schema registry before load or reload.
* `PROTOCOL_VERSION` and `node.protocol.version` are exempt from all overrides. Only `.env` may set them.

## 6. Internal engines and lifecycle

Config Manager is implemented as a set of internal engines with strict sequencing.

### 6.1 Internal engines

* Schema Registry Engine
  * Accepts key registrations from managers and app backends.
  * Stores type, constraints, default, reloadability, secrecy classification, and export policy for each key.
  * Freezes registrations after startup publication, except for explicit app registration windows controlled by App Manager during app load.
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
  * Produces filtered views for services and frontend exposure based on OperationContext and ACL Manager decisions.
  * Applies key level export policies declared in the schema registry.

### 6.2 Startup sequencing

Startup is fail closed and must be deterministic.

1. Schema Registry Engine registers all built in keys and defaults.
2. Load Engine reads `.env`. Structural errors halt startup before any other manager initializes.
3. Storage Manager is invoked to open SQLite. Config Manager ensures the `settings` table exists, then reads all keys.
4. Load Engine merges defaults, `.env`, SQLite, then overrides per precedence.
5. Validation Engine validates the merged tree, including `node.protocol.version` validation and build compatibility checks.
6. Snapshot Engine creates the initial snapshot and assigns `cfg_seq`.
7. Config Manager publishes namespace snapshots to managers during their initialization hooks. The `dos.*` namespace must reach DoS Guard Manager as a single validated snapshot that satisfies the policy contract in `01-protocol/11-dos-guard-and-client-puzzles.md`; if publication fails, DoS Guard Manager must remain in fail-closed mode with no admissions.
8. Each manager must acknowledge acceptance. Failure to acknowledge halts startup. Partial initialization is forbidden.
9. Health Manager is notified that Config Manager is ready only after publication acknowledgements succeed.

### 6.3 Shutdown behavior

Config Manager shutdown is passive and must not mutate state.

Rules:

* Config Manager does not flush configuration to disk on shutdown, except for in flight updates that have already been committed to SQLite.
* Config Manager stops accepting update requests once shutdown begins.
* Config Manager stops delivering change notifications once shutdown begins.
* The last committed snapshot remains available for in process reads until process termination, unless the process is already in teardown.

### 6.4 Readiness and liveness

Config Manager exposes readiness and liveness signals consumed by Health Manager.

Readiness:

* Ready only after the initial snapshot is validated, published to all managers, and all required acknowledgements have been received.

Liveness:

* Live while the Config Manager event loop can service read requests and can serialize update or reload requests.
* Repeated reload failures do not make Config Manager non live, but they mark it degraded.

## 7. Schema registration contract

Config Manager requires explicit registration for all keys that may appear in SQLite, overrides, or exports.

### 7.1 Registration fields

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

### 7.2 Registration timing rules

* Built in manager registrations occur before `.env` parsing and before reading SQLite.
* App registrations occur only during app load, coordinated by App Manager, and must complete before app configuration can be read or exported.
* After initial publication, new registrations are rejected unless they are part of an explicit app load window.

### 7.3 Ownership rules

* Only the owning manager may register keys in its namespace.
* Only the owning manager may mark a key reloadable.
* Only the owning manager may receive prepare and commit notifications for changes in its namespace.

## 8. Runtime APIs and consumption model

Config Manager exposes a strict API surface. All call paths that can mutate state require an OperationContext.

Read APIs:

* `getNodeConfig()`
  * Returns the immutable `node.*` snapshot.
  * Only callable by managers and core services.
* `getManagerConfig(manager_id)`
  * Returns the immutable snapshot for the caller namespace.
  * Rejected if the caller is not the owning manager or not explicitly whitelisted by an export contract.
* `getAppConfig(app_id)`
  * Returns the immutable snapshot for an app namespace.
  * Only callable by the owning app backend or App Manager under an app scoped OperationContext.
* `getSetting(key, default=None, type_hint=None)`
  * Returns a typed value derived from the current snapshot.
  * Rejects access if key visibility is not permitted for the caller context.
* `listSettings(selector=None)`
  * Returns a filtered view of keys and values intended for diagnostics and administrative tooling.
  * Must apply ACL filtering and secrecy rules.

Export APIs:

* `exportConfig(OperationContext, selector)`
  * Returns a filtered and policy safe configuration view for service layer and frontend usage.
  * ACL Manager must authorize export, and the export filter must enforce key level export policies.

Mutation APIs:

* `updateSettings(OperationContext, updates)`
  * Performs an atomic update of one or more SQLite backed keys.
  * Validates the resulting candidate snapshot before commit.
  * Emits audit log entries and a configuration update event through Event Manager on success.

Reload APIs:

* `reload(OperationContext, reason=None)`
  * Re runs the full load and validation pipeline against current sources.
  * Only affects namespaces that are not immutable.
  * Must serialize with any concurrent updates.

Version API:

* `getProtocolVersion()`
  * Returns the locally declared `(major, minor, patch)` tuple and normalized string.
  * Returns only the immutable `.env` derived value.

API rules:

* Returned structures are immutable to prevent caller mutation.
* Read APIs must never perform database reads on the hot path once the snapshot is in memory, except for diagnostics explicitly documented as database backed.
* Mutation APIs must never allow writing `.env` sourced keys.

## 9. Change handling and immutability rules

### 9.1 Immutability

* `node.*` is immutable after startup.
* `node.protocol.version` is immutable and cannot be reloaded or overridden.
* Keys not marked reloadable may be updated in SQLite, but the update must not take effect until restart if the owning manager declares that behavior. In that case, Config Manager must record the value but must not publish it as active.

### 9.2 Two phase change propagation

Config Manager delivers change notifications in two phases:

* Prepare phase
  * Config Manager sends the diff for affected keys to the owning managers.
  * Owning managers may veto the change with a structured rejection reason.

* Commit phase
  * If no veto occurs, Config Manager commits the new snapshot, increments `cfg_seq`, and publishes the new namespace snapshots.
  * Managers receive a commit notification after the snapshot becomes authoritative.

Rules:

* Veto cancels the entire update or reload attempt.
* On veto, Config Manager must preserve the prior snapshot and must not partially apply any changes.
* Change notifications must be delivered in deterministic order, based on a fixed manager ordering, and must be consistent across runs.
* `dos.*` policy updates must be committed atomically so that DoS Guard Manager never observes partial policies, satisfying the policy update rule in `01-protocol/11-dos-guard-and-client-puzzles.md`.

### 9.3 Serialization

* Concurrent updates and reloads are serialized.
* A second request is queued behind the active request.
* The queue is bounded. On overflow, Config Manager rejects requests with a fail closed error.

### 9.4 Installation and bootstrap mode

Some configuration must be set during initial node setup before normal administrative identity and permissions exist.

Config Manager supports a limited bootstrap mode:

* Bootstrap writes are permitted only under an OperationContext that carries an explicit bootstrap capability issued and validated by the installation flow.
* Bootstrap writes are limited to an allowlist of keys required to complete initial setup, such as network and privacy operational settings and initial plugin enablement flags.
* Bootstrap writes are still validated via the schema registry.
* Bootstrap mode ends when the installation flow marks the node as installed via an installation owned flag. After this, bootstrap capabilities are rejected.

Config Manager does not create admin identities and does not own the installation state machine. It only enforces the capability and key allowlist rules for configuration writes.

## 10. Security, secrecy, and trust boundaries

* `.env`, environment overrides, and SQLite contents are untrusted until validated.
* Config Manager must treat all loaded text as hostile input, including values sourced locally.
* Secrets are not stored directly in SQLite settings. Config Manager stores only secret references, such as file paths or handle ids, and enforces secrecy classification to prevent export.
* Export must be deny by default. Only keys explicitly marked exportable may be returned by `exportConfig`.
* Access control for mutation and export flows through OperationContext and ACL Manager authorization checks.
* Managers and services cannot escalate by editing files. Direct file edits are outside protocol guarantees and must not be relied upon for authorized change paths.
* Config Manager must log configuration source usage per load and reload attempt, enabling audit and drift detection.

## 11. Failure posture and observability

Failure posture is fail closed.

Startup failures:

* Any load or validation failure halts startup before other managers initialize.
* Missing `.env`, malformed `.env`, invalid `node.protocol.version`, unknown keys, or failing constraints are fatal.

Runtime failures:

* Reload failure preserves the prior snapshot and emits structured error logs.
* Update failure does not partially write to SQLite. The update must be atomic, either fully persisted and committed, or fully rejected.
* Repeated failures mark the configuration subsystem degraded via Health Manager.

Observability:

* Config Manager exposes metrics for Health Manager consumption:
  * current `cfg_seq`
  * last reload timestamp and duration
  * count of registered keys and namespaces
  * count of reload attempts, successes, failures
  * veto counts by namespace
  * export requests count and denials count
* Audit logs capture:
  * who initiated an update or reload via OperationContext
  * which keys changed
  * which sources contributed to the new snapshot
  * whether a veto occurred and by whom

## 12. Allowed and forbidden behaviors

### 12.1 Allowed

* Reading configuration exclusively through Config Manager APIs.
* Registering keys and schemas during the permitted registration windows.
* Performing hot reload only for keys marked reloadable by the owning manager.
* Updating SQLite backed settings only through authorized backend APIs that invoke Config Manager.
* Exporting configuration only through `exportConfig` with explicit export policies and ACL authorization.
* Using bootstrap mode only for the limited installation allowlist and only before installation completes.

### 12.2 Forbidden

* Any component reading `.env` directly.
* Any component reading or writing the `settings` table directly.
* Publishing partially validated configuration or allowing consumers to observe intermediate state.
* Treating config callbacks as a general purpose event bus.
* Storing node local operational configuration in the graph or syncing it to peers.
* Allowing overrides to mutate `node.protocol.version` or any `.env` sourced key.
* Allowing a manager to read another manager namespace without an explicit export contract.
