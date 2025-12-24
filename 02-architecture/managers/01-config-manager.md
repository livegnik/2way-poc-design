



# 01 Config Manager

## 1. Purpose and scope

This specification defines the authoritative responsibilities, invariants, and interfaces of the Config Manager within the 2WAY backend. Config Manager owns configuration ingestion, validation, layering, publication, change propagation, and failure posture for runtime configuration that influences all other managers and services. The document covers configuration sources, precedence rules, consumer APIs, trust boundaries, and rejection behavior. It does not re-specify schema definitions, ACL rules, transport formats, or key custody beyond the references required to describe configuration handling.

## 2. Responsibilities and boundaries

Config Manager is responsible for:

* Loading `.env` boot-critical values plus settings persisted in SQLite.
* Validating configuration structure, types, and constraints before any value becomes visible to consumers.
* Publishing immutable configuration snapshots to other managers during initialization and on approved reloads.
* Managing per-manager configuration namespaces plus shared node-level settings sourced from a single key-value table.
* Detecting configuration drift (settings mutation, env refresh, remote pull) and coordinating controlled reloads where allowed.
* Exposing read-only subscription APIs that notify managers and services when eligible settings change.
* Providing typed getters and update methods that persist values, emit audit trails, and enforce policy.
* Supplying the canonical protocol version tuple declared in `01-protocol/10-versioning-and-compatibility.md` so compatibility logic reads a single source of truth.

Config Manager explicitly does not:

* Generate or store cryptographic secrets (Key Manager provides only references if needed).
* Bypass authorization, schema, or ACL enforcement when exposing configuration via APIs.
* Allow services, apps, or extensions to read `.env` or the `settings` table directly; all access flows through Config Manager.
* Allow partially validated configuration to leak to consumers or mutate runtime state owned by other managers.

## 3. Configuration model and storage

The configuration layer is responsible for boot-critical values, persistent server settings, and dynamic runtime adjustments that must survive restarts. It follows a simple rule: values required before the backend database or key store exists live in the `.env` file, and everything else resides in the backend database where it is versioned, queryable, and exposed through standard APIs. This keeps configuration self-describing and avoids scattering state across files.

### 3.1 Boot-critical configuration in `.env`

`.env` holds the minimal data required to bring the backend up far enough to open SQLite, locate keys, and configure transports. Example keys:

```
BACKEND_DB_PATH=backend/instance/backend.db
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
KEYS_DIR=backend/keys
TOR_CONTROL_PORT=9051
TOR_SOCKS_PORT=9050
PROTOCOL_VERSION=1.0.0
```

* `.env` is parsed exactly once at startup. After parsing, Config Manager keeps these values in memory, assigns them to the `node.*` namespace, and no other component reads the file directly.
* The file never contains graph identifiers or mutable feature flags. It describes the node host itself (paths, bind addresses, Tor wiring, declared protocol version) and determines how the backend reaches persistent resources.
* `.env` values are immutable after startup. Updating them requires a restart so that every manager observes the same boot posture.
* `PROTOCOL_VERSION` encodes the `(major.minor.patch)` tuple that the backend advertises to peers. Config Manager validates the tuple, ensures it matches the supported build version, and publishes it under `node.protocol.version` so handshake components reuse an identical value.

### 3.2 Settings stored in the backend database

All other configuration lives in SQLite inside a simple key-value table named `settings`. The table lives under Storage Manager custody, but only Config Manager reads or writes it.

```sql
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

* Every value is stored as raw text. Config Manager performs type conversion (bool, int, duration, JSON) and enforces constraints before publishing the data.
* The table holds operational preferences, feature flags, domain policies, caching preferences, logging thresholds, and any other mutable setting.
* Config Manager initializes the table on first run, applies defaults for missing keys, and exposes CRUD-style methods that wrap Storage Manager transactions.
* Updates to the table are versioned by Config Manager (`cfg_seq`), logged for audit, and propagated via events.

### 3.3 Namespaces and separation of concerns

* Config Manager partitions the aggregate configuration tree by namespace (`node.*`, `storage.*`, `graph.*`, `network.*`, `app.<id>.*`). Each manager owns its subtree and cannot peek into another subtree unless explicitly exported as a shared primitive.
* The `.env` file anchors the immutable `node.*` namespace. The `settings` table backs the rest of the namespaces, including app-scoped entries registered by App Manager or system services.
* Frontend and backend services never touch `.env` or `settings` directly. They call backend APIs that DAO into Config Manager, which enforces ACLs and OperationContext filters before returning values.
* The graph contains no server configuration. Schemas and ACL rules live in the graph because they describe protocol state, but environment and operational settings remain outside to avoid circular dependencies during bootstrap and to keep configuration unsynced between peers.

### 3.4 Why configuration is not stored in the graph

* Configuration must be readable before the graph or OperationContext exists, otherwise bootstrap would deadlock.
* Graph data replicates and carries ACL semantics that do not apply to local node-only configuration; syncing secrets or host parameters would leak state to peers.
* Keeping configuration outside the graph keeps the graph authoritative for domain objects only, while configuration remains lightweight, fast, and host-local.

### 3.5 Protocol version tuple

* Config Manager is the sole owner of the locally configured protocol version required by `01-protocol/10-versioning-and-compatibility.md`.
* The tuple originates from `.env`, cannot be overridden by SQLite settings or environment overrides, and is immutable for the life of the process. Bumping the tuple requires editing `.env` and restarting so every manager observes the same value.
* The tuple is published both as `(major, minor, patch)` integers and as a normalized string (e.g., `1.0.0`) so downstream components can follow the protocol document's lexicographic comparison rules without reparsing text.
* Startup fails if the tuple is missing, malformed, or advertises a version newer than the running build supports. This prevents Network Manager or handshake code from promising behavior it cannot provide.

## 4. Configuration sources and precedence

Config Manager enforces a deterministic precedence stack:

1. **Built-in defaults** compiled with the backend. Defaults guarantee safe operation even on first run.
2. **`.env` boot configuration** containing only the values described in section 3.1.
3. **SQLite `settings` table** providing all manager, service, and app namespaces.
4. **Environment overrides** prefixed with `TWOWAY_` for CI or developer usage. These override both `.env` and database-backed entries for the process lifetime.
5. **Ephemeral/test overrides** provided programmatically (CLI flags, integration tests). These exist only for the current process and are intended for tests or diagnostics.

Later sources override earlier ones for the same key. Unknown keys cause validation failure unless a manager or app registers the key and schema metadata ahead of the reload.

`PROTOCOL_VERSION` (and thus `node.protocol.version`) is exempt from overrides; it may only be set via `.env` to keep protocol negotiation deterministic.

## 5. Initialization, validation, and publication flow

### 5.1 Inputs

* Process arguments (config directory, ephemeral overrides).
* `.env` file contents.
* SQLite `settings` table plus built-in defaults.
* Optional runtime overrides (environment variables or test harness).

### 5.2 Flow

1. Config Manager loads built-in defaults into an in-memory tree.
2. `.env` is parsed. Structural errors abort startup before any other manager initializes.
3. SQLite is opened through Storage Manager. Config Manager ensures the `settings` table exists, reads all keys, and merges them onto the tree.
4. Environment overrides and ephemeral overrides are resolved, coerced into native types, and merged per precedence rules.
5. Config Manager resolves the `node.protocol.version` tuple, validates it against the supported build tuple, and publishes it for the compatibility workflow defined in `01-protocol/10-versioning-and-compatibility.md`.
6. Composite configuration is validated against registered schema definitions (built-in plus app/service contributions). Validation includes type checks, port range checks, Tor safety rules, and references to existing directories.
7. Config Manager emits a monotonic configuration version identifier (`cfg_seq`), stores the full snapshot, and exposes derived views to managers.
8. Managers receive their namespace snapshot during initialization hooks and must acknowledge acceptance. Failure to acknowledge halts startup.

### 5.3 Outputs

* Immutable snapshot objects keyed by namespace.
* Configuration version metadata (sequence, timestamp, provenance, source stack).
* Canonical protocol version tuple (major, minor, patch) used by Network Manager and State Manager during compatibility checks.
* Audit log entries capturing inputs, success/failure, and applied overrides.

## 6. Runtime APIs and consumption model

Config Manager exposes read-only and mutation-safe APIs:

* `getNodeConfig()` - returns node-level settings snapshot sourced from `.env` plus defaults.
* `getManagerConfig(managerId)` - returns the namespace snapshot for the caller. Only callable by the owning manager; requests from other managers are rejected unless explicitly whitelisted.
* `getAppConfig(appId)` - returns an app namespace snapshot scoped to the calling service/app backend extension.
* `getSetting(key, default=None, *, type_hint)` - typed accessor that converts to bool/int/duration/etc and enforces constraints.
* `updateSettings(OperationContext, updates)` - atomic update that writes to SQLite, validates changes, emits audit logs, and notifies Event Manager.
* `listSettings()` - returns the current key-value map for debugging or export, subject to ACL filtering.
* `subscribe(keys, callback)` - registers for change notifications on specific keys. Callbacks execute synchronously before the new configuration becomes visible elsewhere, enabling managers to veto invalid runtime changes.
* `exportConfig(OperationContext, selector)` - service-layer API that returns filtered configuration allowed for the caller's app/domain (used for surfacing safe settings to frontend clients). ACL Manager enforces visibility before Config Manager returns any values to this API.
* `getProtocolVersion()` - returns the `(major, minor, patch)` tuple (plus normalized string) for the locally configured protocol version defined in `01-protocol/10-versioning-and-compatibility.md`, enabling compatibility logic to declare and validate versions without fetching unrelated configuration.

All APIs return immutable structures (frozen dicts/tuples) to prevent mutation. Frontend apps interact through HTTP endpoints implemented by services, which in turn invoke Config Manager using OperationContext so ACL Manager can enforce administrative permissions.

## 7. Change handling and immutability rules

* Node runtime configuration (`node.*`) is static after startup. Changes require process restart.
* `node.protocol.version` cannot be reloaded or overridden. Administrators must edit `.env` and restart so every compatibility check observes the new tuple before the node advertises it to peers.
* Select manager namespaces may opt-in to hot reload (e.g., Log Manager verbosity, DoS thresholds). Hot reload requires schema metadata declaring the key as `reloadable` plus a validation hook in the owning manager.
* Config Manager monitors the `settings` table (triggered by its own updates) and exposes a manual `reload()` API for controlled refresh (used in tests or administrative commands). `.env` reloads require explicit restart.
* On reload, Config Manager repeats the full load/validate process. If validation fails, the previous snapshot remains authoritative, and failure details are logged.
* Change notifications are delivered in two phases: `prepare` (managers can veto) and `commit` (changes become visible). Veto triggers rejection and reverts to the prior snapshot, preventing partial updates.
* Config Manager serializes reload attempts; concurrent reload requests are queued to maintain deterministic sequencing.
* Runtime updates that succeed emit a configuration update event through Event Manager so subscribers (log tailers, cache subsystems) can react immediately. Subsystems that cannot support live updates (e.g., Tor ports) reject the change and instruct the caller to restart.

## 8. Security, secrecy, and trust boundaries

* `.env`, environment overrides, and SQLite contents are treated as untrusted until validated. Config Manager never trusts raw file contents, even if sourced locally.
* Secrets (API tokens, passwords) are not stored directly. Config Manager only stores references (paths, handle IDs). Key Manager or a dedicated secret vault retrieves actual secret material, ensuring Config Manager cannot exfiltrate private keys or credentials.
* Access control is enforced via ACL Manager for any configuration exposed beyond managers. OperationContext drives filtering, auditing, and rate limiting.
* Apps cannot escalate privileges by editing files. Configuration edits must go through backend APIs that invoke Config Manager; those APIs validate OperationContext and write to the `settings` table only when ACL Manager authorizes the caller.
* Config Manager logs all configuration sources used per reload, enabling Log Manager audits to detect unauthorized changes.

## 9. Failure posture and observability

* Any load or validation failure during startup halts the process before other managers initialize. Partial initialization is forbidden.
* Runtime reload failures leave the previous snapshot active and emit a structured error via Log Manager plus a degradation signal via Health Manager.
* Unknown keys, type mismatches, invalid ports, Tor misconfiguration, or forbidden overrides cause immediate rejection with actionable error messages. Health Manager marks the configuration subsystem as degraded when repeated failures occur.
* Config Manager surfaces metrics: last reload timestamp, duration, version, number of registered consumers, veto counts, and update event counts. Health Manager uses these metrics to report readiness.
* Audit logs capture who initiated a reload (OperationContext), which sources changed, and which keys were modified.

## 10. Allowed and forbidden behaviors

### 10.1 Allowed

* Reading configuration exclusively through Config Manager APIs.
* Appending new configuration namespaces by registering schemas during initialization.
* Performing hot reloads on keys explicitly marked as reloadable and only after successful validation.
* Exporting a filtered subset of configuration to frontend callers when ACL Manager authorizes it.
* Updating settings via backend APIs that invoke Config Manager, which then writes to SQLite and emits events.

### 10.2 Forbidden

* Managers reading each other's configuration without explicit export contracts.
* Services or apps editing `.env`, SQLite files, or other configuration artifacts directly.
* Using configuration data to bypass trust boundaries (e.g., injecting SQL snippets, file paths that access prohibited directories).
* Treating configuration watchers or callbacks as a general event bus; they exist solely for configuration changes.
* Storing protocol-level configuration inside the graph or syncing node-local settings to peers.

Config Manager enforces these constraints to ensure deterministic, auditable configuration state across all runtime topologies and to preserve the architectural invariants guaranteed by the component model.
