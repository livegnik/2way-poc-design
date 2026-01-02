# 00 Managers Overview

## 1. Purpose and scope

This document provides an implementation-ready overview of every backend manager in 2WAY and explains how the manager fabric fits together across responsibilities, invariants, lifecycle dependencies, and shared execution flows. It complements the detailed component specifications and the rest of the architecture corpus by aggregating the big-picture guidance needed before diving into the per-manager files. It does not redefine the individual contracts; instead it stitches them together so engineers and reviewers can see the system-wide shape and enforce the same fail-closed posture everywhere.

This specification consumes the protocol contracts defined in:
* `01-protocol/00-protocol-overview.md`
* `01-protocol/01-identifiers-and-namespaces.md`
* `01-protocol/02-object-model.md`
* `01-protocol/03-serialization-and-envelopes.md`
* `01-protocol/04-cryptography.md`
* `01-protocol/05-keys-and-identity.md`
* `01-protocol/06-access-control-model.md`
* `01-protocol/07-sync-and-consistency.md`
* `01-protocol/08-network-transport-requirements.md`
* `01-protocol/09-errors-and-failure-modes.md`
* `01-protocol/10-versioning-and-compatibility.md`
* `01-protocol/11-dos-guard-and-client-puzzles.md`

Those files remain normative for all behaviors described here.

If you are building or auditing the backend, start here to understand the manager fabric before diving into the dedicated specifications:

| Section | Description |
| --- | --- |
| Section 2 | Cross-cutting invariants that every manager must uphold. |
| Section 3 | Manager catalog, lifecycle stages, and dependency graph. |
| Section 4 | Critical execution flows (write path, read path, sync path, configuration reload, observability). |
| Section 5 | Detailed per-manager summaries (Config through DoS Guard). |
| Section 6 | Startup and shutdown ordering. |
| Section 7 | OperationContext and trust-boundary enforcement across managers. |
| Section 8 | Observability, readiness, and failure-handling posture. |
| Section 9 | Implementation checklist for engineers wiring the managers together. |

## 2. System-wide invariants owned collectively by the managers

All managers share a single fail-closed posture. Regardless of caller, transport, or execution context, these invariants hold:

1. **Single-write path**: Only Graph Manager mutates canonical graph state, Storage Manager persists it, and State Manager orders it. Other managers (Config, Schema, ACL, Event, Log, etc.) must never write graph rows or bypass the envelope sequencing described in `01-protocol/03-serialization-and-envelopes.md`.
2. **OperationContext discipline**: Auth Manager binds local requests to identities, App Manager binds them to apps, State Manager constructs the remote variant, and every manager consumes the immutable OperationContext before acting.
3. **Protocol precedence**: Structural validation -> Schema validation -> ACL evaluation -> Persistence (`01-protocol/00-protocol-overview.md`). Config, Schema, ACL, and Graph Managers enforce that ordering; no step may be skipped.
4. **Namespace isolation**: App IDs, domains, and sync domains never bleed across managers. App Manager registers identities, Schema Manager validates objects per app, ACL Manager enforces cross-app prohibitions, and Graph Manager refuses envelopes with mixed contexts (`01-protocol/01-identifiers-and-namespaces.md`).
5. **Separation of configuration vs. data**: Configuration lives in `.env` + SQLite `settings` and belongs to Config Manager; graph state never stores node-local configuration, mirroring the bootstrap/data split in `01-protocol/00-protocol-overview.md` and the authority boundaries in `01-protocol/02-object-model.md`.
6. **Cryptographic boundaries**: Only Key Manager accesses private keys. Network Manager, State Manager, and Graph Manager rely on it but never read raw key material (`01-protocol/04-cryptography.md`).
7. **Admission and DoS**: DoS Guard Manager controls every inbound/outbound connection via Network Manager's Bastion Engine; when DoS Guard is unavailable, admissions fail closed per `01-protocol/08-network-transport-requirements.md` and `01-protocol/11-dos-guard-and-client-puzzles.md`.
8. **Observability unity**: Log Manager is the only structured logging surface, Event Manager the only event surface, and Health Manager the only readiness/liveness authority. Managers emit telemetry exclusively through them, preserving the fail-closed reporting model in `01-protocol/09-errors-and-failure-modes.md`.

## 3. Manager catalog and dependency graph

The table below summarizes the 14 managers and their primary dependencies. Every dependency arrow must be honored during implementation and startup sequencing.

| ID | Manager | Core responsibilities | Depends on | Consumed by |
| --- | --- | --- | --- | --- |
| 01 | Config | Configuration ingestion, schema registry for settings, namespace snapshots, reloads. | Storage (settings table), ACL (export filtering), DoS Guard (policy snapshots). | All managers/services needing configuration. |
| 02 | Storage | SQLite lifecycle, schema materialization, transactional persistence, sequence helpers. | Config (db path). | Graph, State, Config, Schema, Log, Event, App. |
| 03 | Key | Key generation, storage, signing, ECIES crypto. | Config (key paths). | Network, State, Graph (via callers), App. |
| 04 | Auth | Local HTTP/WebSocket authentication -> OperationContext inputs. | Config (routes), Storage/front-end session store. | HTTP layer, all managers via OperationContext. |
| 05 | Schema | Loads/validates graph schemas, resolves type ids, compiles sync domains. | Graph (read access), Storage (type tables). | Graph, ACL, State, App, services. |
| 06 | ACL | Authorization for all graph reads/writes. | Schema (defaults), Graph (state), Config (policy). | Graph, Event (capsules), services. |
| 07 | Graph | Single write path, canonical read surface, traversal helpers. | Schema, ACL, Storage, Event, Log, State, Config, App. | State, Event (post-commit), services. |
| 08 | App | Registers apps, app identities, backend extensions. | Storage, Key, Config. | HTTP router, Schema (per app), Graph, ACL. |
| 09 | State | Sync metadata, inbound envelope coordination, outbound package construction. | Graph, Storage, Network, Config, Schema. | Network (packages), Health, services. |
| 10 | Network | Transport surfaces, bastion admission, crypto verification, peer discovery. | DoS Guard, Key, Config, State, Health, Event. | State (verified envelopes), Health. |
| 11 | Event | Sole event publication surface (internal bus + WebSocket). | ACL (audience capsules), Graph, App, Config, Auth. | Frontend clients, managers needing notifications. |
| 12 | Log | Structured logging, audit/security sinks, query APIs. | Config (log.*), Storage (filesystem). | Event (bridged alerts), operators, Health. |
| 13 | Health | Aggregates readiness/liveness across managers. | All managers (signals), Config. | DoS Guard (admission multiplier), operators, Event. |
| 14 | DoS Guard | Admission decisions, puzzles, telemetry to Network Manager. | Config (dos.*), Key (seeds), Health. | Network (bastion), Event, Log. |

### 3.1 Dependency constraints

* All managers run in the same process and communicate via in-process APIs or bounded channels; no network calls exist between managers.
* Dependency cycles are not allowed except the intentional telemetry loop (Health <- managers; Health -> DoS Guard). Implementations must prevent deadlocks by keeping interactions asynchronous where necessary (for example, Event Manager ingestion vs. ACL capsules).

## 4. Critical execution flows

### 4.1 Local write pipeline (HTTP request -> graph commit)

1. **HTTP interface** receives a request, authenticates it via Auth Manager, and constructs an OperationContext using App Manager resolution.
2. **Client/service** calls Graph Manager with an envelope.
3. Graph Manager sequences validation: structural checks -> Schema Manager validation -> ACL Manager authorization -> Storage Manager transaction (with Config-provided limits) -> commit, preserving the order mandated by `01-protocol/00-protocol-overview.md` and `01-protocol/03-serialization-and-envelopes.md`.
4. Graph Manager notifies State Manager (commit event) and Event Manager (post-commit descriptor). Log Manager receives audit/security logs from Graph + ACL.
5. Health Manager monitors Graph/Storage success metrics; DoS Guard may adjust admission if Graph emits sustained failures.

### 4.2 Controlled read pipeline

1. Caller obtains OperationContext (Auth/App).
2. Graph Manager enforces schema-aware filters, calls ACL Manager for read authorization (per `01-protocol/06-access-control-model.md`), queries Storage Manager via typed helpers, applies default visibility filtering, and returns immutable results.
3. Event Manager may deliver notifications summarizing the same objects but never bypasses ACL decisions; subscribers use reads for recovery.

### 4.3 Remote sync pipeline

1. Network Manager admits a peer via DoS Guard (`01-protocol/08-network-transport-requirements.md`, `01-protocol/11-dos-guard-and-client-puzzles.md`), verifies signatures/decrypts envelopes via Key Manager (`01-protocol/04-cryptography.md`, `01-protocol/05-keys-and-identity.md`), and forwards plaintext packages plus transport metadata to State Manager.
2. State Manager enforces ordering (global/domain sequences from Storage Manager) per `01-protocol/07-sync-and-consistency.md`, constructs a remote OperationContext, and invokes Graph Manager.
3. Graph Manager executes the same pipeline as local writes. After commit, State Manager updates sync metadata and may schedule outbound packages. Event Manager receives descriptors; Log Manager records sync outcomes.

### 4.4 Configuration reload pipeline

1. Admin (via CLI/HTTP) calls Config Manager `updateSettings` or `reload`.
2. Config Manager merges sources, validates via the settings schema registry, and diffs namespace snapshots, preserving compatibility expectations in `01-protocol/10-versioning-and-compatibility.md`.
3. Affected managers enter prepare/commit handshake, and each can veto. Managers apply new snapshots (for example, Network updates limits, DoS Guard updates difficulty, Event updates queue sizes). Health Manager goes `not_ready` if any veto or failure occurs.
4. Successful commit increments `cfg_seq`; Config Manager publishes audit logs/events; dependent managers report readiness once applied.

### 4.5 Observability and incident response

* **Log Manager** records every critical action (auth failure, ACL denial, config reload, network admission decision) so error families remain observable per `01-protocol/09-errors-and-failure-modes.md`.
* **Event Manager** broadcasts state changes to authorized subscribers (graph domain events, security alerts, network telemetry, health transitions) while honoring audience constraints derived from `01-protocol/06-access-control-model.md`.
* **Health Manager** exposes readiness/liveness snapshots; when `ready=false`, DoS Guard raises puzzle difficulty and Network Manager stops new admissions, delivering the shutdown posture described in `01-protocol/08-network-transport-requirements.md`. Event Manager and Log Manager record the transition.

## 5. Manager-by-manager summary

### 5.1 Config Manager (01)

* **Scope**: Central authority for configuration sources: built-in defaults, `.env`, SQLite `settings`, environment overrides, and ephemeral overrides.
* **Key services**:
  * Schema registry for configuration keys (namespaces `node.*`, `storage.*`, `graph.*`, etc.).
  * Immutable namespace snapshots distributed at startup/reload.
  * Two-phase change propagation with veto support and `cfg_seq` monotonic IDs.
* **Dependencies**: Storage Manager (settings table), ACL Manager (export filtering), Graph Manager (change notifications), DoS Guard (dos.* policies), Health Manager (readiness).
* **Critical invariants**:
  * No component reads `.env` or `settings` directly; Config Manager mediates all access.
  * Boot-critical `node.*` values are immutable after startup.
  * Unknown keys fail validation unless registered before load.
  * DoS Guard policies (`dos.*`) and the protocol version tuple are atomic snapshots.
* **Interfaces**: Read APIs (`getNodeConfig`, `getManagerConfig`, `exportConfig`), mutation/reload APIs, version introspection.


### 5.2 Storage Manager (02)

* **Scope**: Single owner of the SQLite database, WAL lifecycle, schema provisioning, and transactional primitives.
* **Key services**:
  * Global table creation (`identities`, `apps`, `global_seq`, etc.) and per-app table families (`app_N_*`).
  * Sequence Engine that persists `global_seq`, `domain_seq`, `sync_state` (`01-protocol/07-sync-and-consistency.md`).
  * Transaction helpers (read-only, write, savepoints) with envelope-level atomicity.
* **Dependencies**: Config Manager (database path), Graph Manager (write path), App Manager (per-app provisioning), Schema Manager (type tables).
* **Critical invariants**:
  * Exactly one writable connection per process; WAL mode enforced.
  * Graph rows append-only; metadata fields (`app_id`, `type_id`, `owner_identity`, `global_seq`) are immutable.
  * Failed writes never advance sequences; corruption or migration failure halts startup.


### 5.3 Key Manager (03)

* **Scope**: Generates, stores, loads, and uses secp256k1 key pairs for node, identity, and app scopes; performs signing and ECIES encryption/decryption.
* **Key services**:
  * Key Storage Engine with deterministic filesystem layout.
  * Cryptographic operation APIs that require explicit scope + key identifier parameters (no implicit selection).
  * Public-key derivation for graph binding (Graph Manager persists, Key Manager never writes graph data).
* **Dependencies**: Config Manager (key directory path). Consumers: Network Manager, State Manager, Graph Manager (via dependencies), App Manager.
* **Critical invariants**:
  * Private keys never leave disk/memory and are never exported/logged.
  * Node key must exist before startup completes; failure aborts the process.
  * Key rotation retains old keys but forbids ambiguity.


### 5.4 Auth Manager (04)

* **Scope**: Local authentication authority for HTTP/WebSocket entrypoints; resolves session tokens into backend identities and admin eligibility.
* **Key services**:
  * Token validation pipeline (presence, format, existence, expiry, identity mapping).
  * Admin gating evaluation for protected routes.
  * Construction inputs for OperationContext (requester identity, app context, admin flag).
* **Dependencies**: Storage/front-end session store, Config Manager (route settings), App Manager (app context), Health Manager (signals). Consumers: HTTP layer, Event/Log (audit), ACL/Graph (via OperationContext).
* **Critical invariants**:
  * Authentication is strictly separated from authorization.
  * OperationContext.requester_identity_id originates only here (for local traffic).
  * Missing or malformed tokens fail closed with explicit error categories.


### 5.5 Schema Manager (05)

* **Scope**: Loads schema definitions from app_0, validates structure, compiles type registries and sync domain metadata, and exposes read-only schema APIs.
* **Key services**:
  * Schema Loading/Validation Engines that enforce exactly one schema per app.
  * Type Registry Engine mapping `type_key` <-> `type_id` with immutability.
  * Sync Domain Compilation consumed by State Manager.
* **Dependencies**: Graph Manager (reads app_0), Storage Manager (type tables), Config (limits). Consumers: Graph, ACL, State, services.
* **Critical invariants**:
  * Compiled schemas are immutable until explicit reload; reload is atomic.
  * Cross-app schema references forbidden.
  * Schema validation failures halt startup and mark health degraded.


### 5.6 ACL Manager (06)

* **Scope**: Sole authorization engine for graph reads/writes, enforcing schema defaults, ownership rules, object-level ACLs, and remote execution constraints.
* **Key services**:
  * Deterministic evaluation pipeline (ownership -> schema defaults -> app/domain limits -> object ACLs -> graph constraints -> remote constraints).
  * ACL capsules for Event Manager subscribers.
  * Traversal support via Graph Manager (bounded).
* **Dependencies**: Schema Manager, Graph Manager (state queries), Config (policy toggles). Consumers: Graph, Event, services.
* **Critical invariants**:
  * No other component can authorize graph access.
  * Explicit deny overrides allow; schema prohibitions override ACLs.
  * Remote envelopes obey extra constraints (no local history rewrites).


### 5.7 Graph Manager (07)

* **Scope**: Only path for persisted graph mutations and authoritative read surface; coordinates schema validation, ACL enforcement, sequencing, and event emission.
* **Key services**:
  * Graph Write Engine (serialized writes, sequencing, Storage Manager commits).
  * Graph Read Engine (authorization-aware reads).
  * RAM Graph + Traversal Engines supporting ACL decisions.
  * Sequencing Engine guaranteeing monotonic `global_seq`.
* **Dependencies**: Schema, ACL, Storage, Config, App, Event, Log, State. Consumers: State, Event, services.
* **Critical invariants**:
  * Envelopes must pass structural -> schema -> ACL order before commit.
  * Writes and reads are scoped to a single app/domain per envelope.
  * Events never emit until commit succeeds; reads never leak unauthorized state.


### 5.8 App Manager (08)

* **Scope**: Declares and registers applications, assigns `app_id` values, binds app identities to keys, initializes per-app storage, and wires optional backend extensions.
* **Key services**:
  * Persistent registry (slug <-> `app_id`).
  * Application identity Parents in app_0, generated via Key Manager.
  * Extension service wiring with enforced manager boundaries.
* **Dependencies**: Storage, Key, Config. Consumers: Auth (routing), Schema (per-app schema), Graph (app_id enforcement), ACL.
* **Critical invariants**:
  * App IDs are declared before use, unique, and never reused.
  * Cross-app access is forbidden unless ACL explicitly allows.
  * Extension services cannot bypass managers or access raw storage/key/network.


### 5.9 State Manager (09)

* **Scope**: Maintains sync metadata, orchestrates inbound remote envelopes, constructs outbound packages, and coordinates deterministic ordering with Graph/Storage.
* **Key services**:
  * State Engine (commit observation, metadata updates).
  * Sync Engine (peer/domain progression, package construction).
  * Recovery Engine (startup reconstruction, fail-fast on inconsistency).
  * Read Surface Engine (read-only metadata views).
* **Dependencies**: Graph, Storage, Network, Config, Schema. Consumers: Network, Health, services (observability).
* **Critical invariants**:
  * Graph mutations never occur here; State Manager only coordinates.
  * Sync progression never regresses; ordering enforced per `global_seq`.
  * Failures default to rejection; no speculative or partial state is exposed.


### 5.10 Network Manager (10)

* **Scope**: Owns transport surfaces, bastion admission, cryptographic binding at the edge, peer discovery, outbound scheduling, and integration with DoS Guard.
* **Key services**:
  * Network Startup Engine (ordered initialization, readiness gating).
  * Bastion Engine (DoS Guard admission, challenge transport).
  * Incoming Engine (verified inbound envelopes).
  * Outgoing Engine (signed/encrypted outbound packages).
  * Peer discovery and reachability tracking loops.
* **Dependencies**: DoS Guard, Key, State, Config, Health, Event, Log. Consumers: State (verified packages), Health (signals).
* **Critical invariants**:
  * No payload crosses into State Manager without DoS admission and crypto verification.
  * Transport-level IDs are never treated as authenticated identity.
  * Best-effort transport only; retries/persistence belong to State Manager.


### 5.11 Event Manager (11)

* **Scope**: Exclusive event publication surface (internal manager bus + WebSocket to frontend); normalizes descriptors, enforces ACL-based audiences, and manages delivery.
* **Key services**:
  * Source Intake -> Normalization -> Audience -> Delivery engines with bounded queues.
  * Subscription Registry (immutable filters, resume tokens, heartbeat/backpressure).
  * Telemetry Engine for queue depth/failures.
* **Dependencies**: Graph, App, Config, ACL (audience capsules), Auth (OperationContext for sockets), DoS Guard (subscription throttling). Consumers: frontend clients, managers needing notifications.
* **Critical invariants**:
  * Events never contain mutable graph data or secrets; they reference committed objects only.
  * Authorization is enforced via cached ACL capsules per envelope.
  * Delivery is best-effort; clients must use read APIs for recovery.


### 5.12 Log Manager (12)

* **Scope**: Central structured logging authority; enforces record schema, routes to sinks (stdout, rolling files, Event bridge), and exposes read-only query APIs.
* **Key services**:
  * Submission -> Validation -> Normalization -> Routing -> Sink pipeline.
  * Integrity hashing for audit/security files; retention management.
  * Optional Event Manager bridge for high-severity alerts.
* **Dependencies**: Config (log.*), filesystem. Consumers: Event (alerts), Health (sinks), operators.
* **Critical invariants**:
  * No component writes logs directly to sinks; everything flows through Log Manager.
  * OperationContext metadata is mandatory when available.
  * Mandatory sinks failing forces readiness false and may cause request rejection.


### 5.13 Health Manager (13)

* **Scope**: Aggregates readiness/liveness across managers, publishes snapshots, and enforces fail-closed gating.
* **Key services**:
  * Signal Intake -> Validation -> Evaluation -> Publication pipeline.
  * Readiness evaluation requiring all critical managers to report `healthy`.
  * HTTP/admin APIs and Event/Log notifications for state transitions.
* **Dependencies**: All managers (signals), Config (thresholds). Consumers: DoS Guard (admission throttle), Event (notifications), operators.
* **Critical invariants**:
  * Readiness false until every critical manager reports `healthy`.
  * Snapshots are immutable, versioned via `health_seq`.
  * Health data exposed only to admin identities; aggregate states available broadly.


### 5.14 DoS Guard Manager (14)

* **Scope**: Admission control authority; issues/verifies puzzles, tracks abuse telemetry, and instructs Network Manager's Bastion Engine.
* **Key services**:
  * Telemetry Intake Engine (resource usage, per-identity stats).
  * Policy Engine (allow/deny/challenge decisions).
  * Puzzle Engine (generation/verification using Key Manager seeds).
  * Publication Engine (decisions to Network, telemetry to Log/Event).
* **Dependencies**: Network (telemetry), Key (puzzle seeds), Config (dos.*), Health (readiness multipliers). Consumers: Network, Event, Log.
* **Critical invariants**:
  * Decisions default to deny on failure; puzzles are opaque to other managers.
  * Admission cannot proceed when DoS Guard is unavailable.
  * Difficulty adjusts deterministically based on telemetry + health state.


## 6. Startup and shutdown choreography

### 6.1 Startup order (high-level)

1. **Config Manager** parses `.env`, loads settings, publishes snapshots.
2. **Storage Manager** opens SQLite, materializes schemas.
3. **Key Manager** loads the node key (plus app keys as needed).
4. **App Manager** registers apps and identities (needs Storage + Key).
5. **Schema Manager** loads/validates schemas (depends on Graph read access and the App registry).
6. **ACL Manager** initializes with schema metadata.
7. **Graph Manager** boots once Schema, ACL, Storage, Config, and App are ready.
8. **State Manager** reconstructs metadata once Graph/Storage ready.
9. **Log Manager** initializes sinks (so remaining managers can log).
10. **Event Manager** starts intake/delivery.
11. **Network Manager** starts bastion/admitted surfaces after DoS Guard is live.
12. **DoS Guard Manager** starts before Network admissions.
13. **Auth Manager** comes online once Config/App are ready.
14. **Health Manager** begins sampling once all managers report initial state.

Health Manager reports readiness only after every critical manager signals `healthy`. Any failure at any stage keeps readiness false and halts startup (Section 13).

### 6.2 Shutdown order

1. Health Manager marks readiness false.
2. Network + DoS Guard stop new admissions and drain sessions.
3. Event and Log managers flush buffers.
4. State Manager halts sync ingestion/export.
5. Graph stops accepting writes, completes in-flight transactions.
6. Remaining managers release resources (ACL, Schema, App, Auth, Config).
7. Storage closes connection; Key caches cleared in memory.

Partial shutdown is forbidden; each manager must ensure no new requests are accepted after its shutdown begins.

## 7. OperationContext and trust boundaries

* **Construction**:
  * Local: HTTP/WebSocket route -> Auth Manager -> App Manager binding -> OperationContext.
  * Remote: Network Manager verifies envelope -> State Manager constructs remote OperationContext (includes peer identity, sync domain, remote flag).
* **Consumption**: Every manager receiving an OperationContext must treat it as immutable. Graph uses it for app/domain scoping, ACL for identity + execution mode, Event for audience filtering, Log for audit metadata, Health for admin ACL gating.
* **Trusted vs. untrusted inputs**:
  * Transport data remains untrusted until Network + DoS Guard + Key Manager verify it.
  * Config data is untrusted until Config Manager validates it.
  * Graph data is untrusted until Graph Manager + Schema + ACL accept it.
  * Health and Event surfaces expose data only after ACL/admin checks.

## 8. Observability, readiness, and failure posture

1. **Logging**: All components push structured records into Log Manager. Mandatory sinks failing results in readiness false and may force request rejection (for example, audit-required flows).
2. **Events**: Graph, Config, Network, DoS Guard, Health, App, and Log publish descriptors to Event Manager only after commit or state transition. Event Manager enforces best-effort delivery with ACK/backpressure semantics.
3. **Health**: Every manager must emit health signals (heartbeat, state). Missing or invalid signals degrade readiness. Health Manager alerts Event/Log and DoS Guard when states change.
4. **Fail-closed principle**: If any manager cannot guarantee invariants (DoS Guard unreachable, Config reload invalid, Schema mismatch, Storage corruption), it must reject requests and mark health degraded. Recovery requires operator intervention (no silent repair).

## 9. Implementation checklist example

A short example checklist for wiring the managers together or reviewing an implementation:

1. **Configuration**: Are all managers reading configuration exclusively via Config Manager snapshots? Are settings keys registered with reload policies and owner namespaces?
2. **Start order**: Does the runtime enforce the startup sequence from Section 6? Are dependencies checked before readiness?
3. **OperationContext usage**: Does every entrypoint authenticate via Auth Manager (local) or the Network + State pipeline (remote) before invoking Graph/ACL?
4. **Graph write path**: Does every mutation route through Graph Manager and maintain the structural -> schema -> ACL -> persistence order?
5. **Sync**: Are inbound envelopes admitted only after DoS Guard + Network + Key verification, and is State Manager coordinating ordering before Graph?
6. **Logging/events**: Are logs routed only through Log Manager, and are event descriptors emitted only post-commit? Are Event Manager queues bounded with enforceable limits?
7. **Security**: Are keys confined to Key Manager? Are DoS puzzles opaque to other managers? Are ACL decisions centralized?
8. **Observability**: Are Config reloads, health transitions, network admissions, ACL denials, and schema reloads emitting logs/events per spec?
9. **Failure handling**: Does every manager fail closed on dependency loss (for example, DoS Guard forcing `deny`, Health forcing readiness false, Config veto halting reload)?
10. **Testing hooks**: Are bootstrap/diagnostic modes limited and still enforced via OperationContext + ACL, with no shortcuts that bypass these managers?

Satisfying this overview ensures that the detailed specifications (`01`-`14`) can be implemented consistently and that the entire manager fabric behaves deterministically under both normal and failure conditions.
