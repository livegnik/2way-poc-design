# 00 Managers Overview

## 1. Purpose and scope

This document provides an implementation-ready overview of every backend manager in 2WAY and explains how the manager fabric fits together across responsibilities, invariants, lifecycle dependencies, and shared execution flows. It complements the detailed component specifications and the rest of the architecture corpus by aggregating the big-picture guidance needed before diving into the per-manager files. It does not redefine the individual contracts; instead it stitches them together so engineers and reviewers can see the system-wide shape and enforce the same fail-closed posture everywhere.

This overview references:

* [01-protocol/**](../../01-protocol/)
* [02-architecture/00-architecture-overview.md](../00-architecture-overview.md)
* [02-architecture/01-component-model.md](../01-component-model.md)
* [02-architecture/02-runtime-topologies.md](../02-runtime-topologies.md)
* [02-architecture/03-trust-boundaries.md](../03-trust-boundaries.md)
* [02-architecture/04-data-flow-overview.md](../04-data-flow-overview.md)
* [02-architecture/managers/**](../managers/)
* [02-architecture/services-and-apps/**](../services-and-apps/)
* [04-interfaces/**](../../04-interfaces/)

This specification consumes the protocol contracts defined in:

* [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md)
* [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md)
* [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md)
* [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md)
* [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md)
* [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md)
* [01-protocol/10-versioning-and-compatibility.md](../../01-protocol/10-versioning-and-compatibility.md)
* [01-protocol/11-dos-guard-and-client-puzzles.md](../../01-protocol/11-dos-guard-and-client-puzzles.md)

Those files remain normative for all behaviors described here.

If you are building or auditing the backend, start here to understand the manager fabric before diving into the dedicated specifications:

| Section | Description |
| --- | --- |
| Section 2 | Cross-cutting invariants that every manager must uphold. |
| Section 3 | Manager catalog, lifecycle stages, and dependency graph. |
| Section 4 | Critical execution flows (write path, read path, sync path, configuration reload, observability). |
| Section 5 | Detailed per-manager summaries ([Config Manager](01-config-manager.md) through [DoS Guard Manager](14-dos-guard-manager.md)). |
| Section 6 | Startup and shutdown ordering. |
| Section 7 | [OperationContext](../services-and-apps/05-operation-context.md) and trust-boundary enforcement across managers. |
| Section 8 | Observability, readiness, and failure-handling posture. |
| Section 9 | Implementation checklist for engineers wiring the managers together. |

## 2. System-wide invariants owned collectively by the managers

All managers share a single fail-closed posture. Regardless of caller, transport, or execution context, these invariants hold:

1. **Single-write path**: Only [Graph Manager](07-graph-manager.md) mutates canonical graph state, [Storage Manager](02-storage-manager.md) persists it, and [State Manager](09-state-manager.md) orders it. Other managers ([Config Manager](01-config-manager.md), [Schema Manager](05-schema-manager.md), [ACL Manager](06-acl-manager.md), [Event Manager](11-event-manager.md), [Log Manager](12-log-manager.md), etc.) must never write graph rows or bypass the envelope sequencing described in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
2. **[OperationContext](../services-and-apps/05-operation-context.md) discipline**: [Auth Manager](04-auth-manager.md) binds local requests to identities, [App Manager](08-app-manager.md) binds them to apps, [State Manager](09-state-manager.md) constructs the remote variant, and every manager consumes the immutable [OperationContext](../services-and-apps/05-operation-context.md) before acting.
3. **Protocol precedence**: Structural validation -> [Schema Manager](05-schema-manager.md) validation -> [ACL Manager](06-acl-manager.md) evaluation -> Persistence ([01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md)). [Config Manager](01-config-manager.md), [Schema Manager](05-schema-manager.md), [ACL Manager](06-acl-manager.md), and [Graph Manager](07-graph-manager.md) enforce that ordering; no step may be skipped.
4. **Namespace isolation**: [App Manager](08-app-manager.md) IDs, domains, and sync domains never bleed across managers. [App Manager](08-app-manager.md) registers identities, [Schema Manager](05-schema-manager.md) validates objects per app, [ACL Manager](06-acl-manager.md) enforces cross-app prohibitions, and [Graph Manager](07-graph-manager.md) refuses envelopes with mixed contexts ([01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md)).
5. **Separation of configuration vs. data**: Configuration lives in `.env` + SQLite `settings` and belongs to [Config Manager](01-config-manager.md); graph state never stores node-local configuration, mirroring the bootstrap/data split in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) and the authority boundaries in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
6. **Cryptographic boundaries**: Only [Key Manager](03-key-manager.md) accesses private keys. [Network Manager](10-network-manager.md), [State Manager](09-state-manager.md), and [Graph Manager](07-graph-manager.md) rely on it but never read raw key material ([01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md)).
7. **Admission and DoS**: [DoS Guard Manager](14-dos-guard-manager.md) controls every inbound/outbound connection via [Network Manager](10-network-manager.md)'s Bastion Engine; when [DoS Guard Manager](14-dos-guard-manager.md) is unavailable, admissions fail closed per [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md) and [01-protocol/11-dos-guard-and-client-puzzles.md](../../01-protocol/11-dos-guard-and-client-puzzles.md).
8. **Observability unity**: [Log Manager](12-log-manager.md) is the only structured logging surface, [Event Manager](11-event-manager.md) the only event surface, and [Health Manager](13-health-manager.md) the only readiness/liveness authority. Managers emit telemetry exclusively through them, preserving the fail-closed reporting model in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

## 3. Manager catalog and dependency graph

The table below summarizes the 14 managers and their primary dependencies. Every dependency arrow must be honored during implementation and startup sequencing.

| ID | Manager | Core responsibilities | Depends on | Consumed by |
| --- | --- | --- | --- | --- |
| 01 | [Config](01-config-manager.md) | Configuration ingestion, schema registry for settings, namespace snapshots, reloads. | [Storage Manager](02-storage-manager.md) (settings table), [ACL Manager](06-acl-manager.md) (export filtering). | All managers/services needing configuration. |
| 02 | [Storage](02-storage-manager.md) | SQLite lifecycle, schema materialization, transactional persistence, sequence helpers. | [Config Manager](01-config-manager.md) (db path). | [Graph Manager](07-graph-manager.md), [State Manager](09-state-manager.md), [Config Manager](01-config-manager.md), [Schema Manager](05-schema-manager.md), [Log Manager](12-log-manager.md), [Event Manager](11-event-manager.md), [App Manager](08-app-manager.md). |
| 03 | [Key](03-key-manager.md) | Key generation, storage, signing, ECIES crypto. | [Config Manager](01-config-manager.md) (key paths). | [Network Manager](10-network-manager.md), [State Manager](09-state-manager.md), [App Manager](08-app-manager.md), [DoS Guard Manager](14-dos-guard-manager.md). |
| 04 | [Auth](04-auth-manager.md) | Local HTTP/WebSocket authentication -> [OperationContext](../services-and-apps/05-operation-context.md) inputs. | [Config Manager](01-config-manager.md) (routes), [App Manager](08-app-manager.md) (routing metadata), frontend session store. | HTTP layer, all managers via [OperationContext](../services-and-apps/05-operation-context.md). |
| 05 | [Schema](05-schema-manager.md) | Loads/validates graph schemas, resolves type ids, compiles sync domains. | [Graph Manager](07-graph-manager.md) (read access), [Storage Manager](02-storage-manager.md) (type tables), [Config Manager](01-config-manager.md) (limits). | [Graph Manager](07-graph-manager.md), [ACL Manager](06-acl-manager.md), [State Manager](09-state-manager.md), [App Manager](08-app-manager.md), services. |
| 06 | [ACL](06-acl-manager.md) | Authorization for all graph reads/writes. | [Schema Manager](05-schema-manager.md) (defaults), [Graph Manager](07-graph-manager.md) (state), [Config Manager](01-config-manager.md) (policy). | [Graph Manager](07-graph-manager.md), [Event Manager](11-event-manager.md) (capsules), services. |
| 07 | [Graph](07-graph-manager.md) | Single write path, canonical read surface, traversal helpers. | [Schema Manager](05-schema-manager.md), [ACL Manager](06-acl-manager.md), [Storage Manager](02-storage-manager.md), [Event Manager](11-event-manager.md), [Log Manager](12-log-manager.md), [State Manager](09-state-manager.md), [Config Manager](01-config-manager.md), [App Manager](08-app-manager.md). | [State Manager](09-state-manager.md), [Event Manager](11-event-manager.md) (post-commit), services. |
| 08 | [App](08-app-manager.md) | Registers apps, app identities, backend extensions. | [Storage Manager](02-storage-manager.md), [Key Manager](03-key-manager.md), [Config Manager](01-config-manager.md). | HTTP router, [Schema Manager](05-schema-manager.md) (per app), [Graph Manager](07-graph-manager.md), [ACL Manager](06-acl-manager.md). |
| 09 | [State](09-state-manager.md) | Sync metadata, inbound envelope coordination, outbound package construction. | [Graph Manager](07-graph-manager.md), [Storage Manager](02-storage-manager.md), [Network Manager](10-network-manager.md), [Config Manager](01-config-manager.md), [Schema Manager](05-schema-manager.md). | [Network Manager](10-network-manager.md) (packages), [Health Manager](13-health-manager.md), services. |
| 10 | [Network](10-network-manager.md) | Transport surfaces, bastion admission, crypto verification, peer discovery. | [DoS Guard Manager](14-dos-guard-manager.md), [Key Manager](03-key-manager.md), [State Manager](09-state-manager.md), [Config Manager](01-config-manager.md), [Health Manager](13-health-manager.md), [Event Manager](11-event-manager.md), [Log Manager](12-log-manager.md). | [State Manager](09-state-manager.md) (verified envelopes), [Health Manager](13-health-manager.md). |
| 11 | [Event](11-event-manager.md) | Sole event publication surface (internal bus + WebSocket). | [ACL Manager](06-acl-manager.md) (audience capsules), [Graph Manager](07-graph-manager.md), [App Manager](08-app-manager.md), [Config Manager](01-config-manager.md), [Auth Manager](04-auth-manager.md), [DoS Guard Manager](14-dos-guard-manager.md). | Frontend clients, managers needing notifications. |
| 12 | [Log](12-log-manager.md) | Structured logging, audit/security sinks, query APIs. | [Config Manager](01-config-manager.md) (log.*), filesystem. | [Event Manager](11-event-manager.md) (bridged alerts), [DoS Guard Manager](14-dos-guard-manager.md) (abuse signals), operators, [Health Manager](13-health-manager.md). |
| 13 | [Health](13-health-manager.md) | Aggregates readiness/liveness across managers. | All managers (signals), [Config Manager](01-config-manager.md). | [DoS Guard Manager](14-dos-guard-manager.md) (admission multiplier), operators, [Event Manager](11-event-manager.md). |
| 14 | [DoS Guard](14-dos-guard-manager.md) | Admission decisions, puzzles, telemetry to [Network Manager](10-network-manager.md). | [Network Manager](10-network-manager.md) (telemetry), [Config Manager](01-config-manager.md) (dos.*), [Key Manager](03-key-manager.md) (seeds), [Health Manager](13-health-manager.md). | [Network Manager](10-network-manager.md) (bastion), [Event Manager](11-event-manager.md), [Log Manager](12-log-manager.md). |

### 3.1 Dependency constraints

* All managers run in the same process and communicate via in-process APIs or bounded channels; no network calls exist between managers.
* Dependency cycles are not allowed except the intentional telemetry loop ([Health Manager](13-health-manager.md) <- managers; [Health Manager](13-health-manager.md) -> [DoS Guard Manager](14-dos-guard-manager.md)). Implementations must prevent deadlocks by keeping interactions asynchronous where necessary (for example, [Event Manager](11-event-manager.md) ingestion vs. ACL capsules).

## 4. Critical execution flows

### 4.1 Local write pipeline (HTTP request -> graph commit)

1. **HTTP interface** ([04-interfaces/01-local-http-api.md](../../04-interfaces/01-local-http-api.md)) receives a request, authenticates it via [Auth Manager](04-auth-manager.md), and constructs an [OperationContext](../services-and-apps/05-operation-context.md) using [App Manager](08-app-manager.md) resolution.
2. **Client/service** calls [Graph Manager](07-graph-manager.md) with an envelope defined in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
3. [Graph Manager](07-graph-manager.md) sequences validation: structural checks -> [Schema Manager](05-schema-manager.md) validation -> [ACL Manager](06-acl-manager.md) authorization -> [Storage Manager](02-storage-manager.md) transaction (with Config-provided limits) -> commit, preserving the order mandated by [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) and [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
4. [Graph Manager](07-graph-manager.md) notifies [State Manager](09-state-manager.md) (commit event) and [Event Manager](11-event-manager.md) (post-commit descriptor). [Log Manager](12-log-manager.md) receives audit/security logs from [Graph Manager](07-graph-manager.md) + [ACL Manager](06-acl-manager.md).
5. [Health Manager](13-health-manager.md) monitors [Graph Manager](07-graph-manager.md)/[Storage Manager](02-storage-manager.md) success metrics; [DoS Guard Manager](14-dos-guard-manager.md) may adjust admission if [Graph Manager](07-graph-manager.md) emits sustained failures.

### 4.2 Controlled read pipeline

1. Caller obtains [OperationContext](../services-and-apps/05-operation-context.md) ([Auth Manager](04-auth-manager.md)/[App Manager](08-app-manager.md)).
2. [Graph Manager](07-graph-manager.md) enforces schema-aware filters, calls [ACL Manager](06-acl-manager.md) for read authorization (per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md)), queries [Storage Manager](02-storage-manager.md) via typed helpers, applies default visibility filtering, and returns immutable results.
3. [Event Manager](11-event-manager.md) may deliver notifications summarizing the same objects but never bypasses [ACL Manager](06-acl-manager.md) decisions; subscribers use reads for recovery.

### 4.3 Remote sync pipeline

1. [Network Manager](10-network-manager.md) admits a peer via [DoS Guard Manager](14-dos-guard-manager.md) ([01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md), [01-protocol/11-dos-guard-and-client-puzzles.md](../../01-protocol/11-dos-guard-and-client-puzzles.md)), verifies signatures/decrypts envelopes via [Key Manager](03-key-manager.md) ([01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md), [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md), [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md)), and forwards plaintext packages plus transport metadata to [State Manager](09-state-manager.md).
2. [State Manager](09-state-manager.md) enforces ordering (global/domain sequences from [Storage Manager](02-storage-manager.md)) per [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md), constructs a remote [OperationContext](../services-and-apps/05-operation-context.md), and invokes [Graph Manager](07-graph-manager.md).
3. [Graph Manager](07-graph-manager.md) executes the same pipeline as local writes. After commit, [State Manager](09-state-manager.md) updates sync metadata and may schedule outbound packages. [Event Manager](11-event-manager.md) receives descriptors; [Log Manager](12-log-manager.md) records sync outcomes.

### 4.4 Configuration reload pipeline

1. Admin (via CLI/HTTP) calls [Config Manager](01-config-manager.md) `updateSettings` or `reload`.
2. [Config Manager](01-config-manager.md) merges sources, validates via the settings schema registry, and diffs namespace snapshots, preserving compatibility expectations in [01-protocol/10-versioning-and-compatibility.md](../../01-protocol/10-versioning-and-compatibility.md).
3. Affected managers enter prepare/commit handshake, and each can veto. Managers apply new snapshots (for example, [Network Manager](10-network-manager.md) updates limits, [DoS Guard Manager](14-dos-guard-manager.md) updates difficulty, [Event Manager](11-event-manager.md) updates queue sizes). [Health Manager](13-health-manager.md) goes `not_ready` if any veto or failure occurs.
4. Successful commit increments `cfg_seq`; [Config Manager](01-config-manager.md) publishes audit logs/events; dependent managers report readiness once applied.

### 4.5 Observability and incident response

* **[Log Manager](12-log-manager.md)** records every critical action (auth failure, [ACL Manager](06-acl-manager.md) denial, config reload, network admission decision) so error families remain observable per [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).
* **[Event Manager](11-event-manager.md)** broadcasts state changes to authorized subscribers (graph domain events, security alerts, network telemetry, health transitions) while honoring audience constraints derived from [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* **[Health Manager](13-health-manager.md)** exposes readiness/liveness snapshots; when `ready=false`, [DoS Guard Manager](14-dos-guard-manager.md) raises puzzle difficulty and [Network Manager](10-network-manager.md) stops new admissions, delivering the shutdown posture described in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md). [Event Manager](11-event-manager.md) and [Log Manager](12-log-manager.md) record the transition.

## 5. Manager-by-manager summary

### 5.1 [Config Manager](01-config-manager.md) (01)

* **Scope**: Central authority for configuration sources: built-in defaults, `.env`, SQLite `settings`, environment overrides, and ephemeral overrides.
* **Key services**:
  * Schema registry for configuration keys (namespaces `node.*`, `storage.*`, `graph.*`, etc.).
  * Immutable namespace snapshots distributed at startup/reload.
  * Two-phase change propagation with veto support and `cfg_seq` monotonic IDs.
* **Dependencies**: [Storage Manager](02-storage-manager.md) (settings table), [ACL Manager](06-acl-manager.md) (export filtering).
* **Critical invariants**:
  * No component reads `.env` or `settings` directly; [Config Manager](01-config-manager.md) mediates all access.
  * Boot-critical `node.*` values are immutable after startup.
  * Unknown keys fail validation unless registered before load.
  * [DoS Guard Manager](14-dos-guard-manager.md) policies (`dos.*`) and the protocol version tuple are atomic snapshots.
* **Interfaces**: Read APIs (`getNodeConfig`, `getManagerConfig`, `exportConfig`), mutation/reload APIs, version introspection.


### 5.2 [Storage Manager](02-storage-manager.md) (02)

* **Scope**: Single owner of the SQLite database, WAL lifecycle, schema provisioning, and transactional primitives.
* **Key services**:
  * Global table creation (`identities`, `apps`, `global_seq`, etc.) and per-app table families (`app_N_*`).
  * Sequence Engine that persists `global_seq`, `domain_seq`, `sync_state` ([01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)).
  * Transaction helpers (read-only, write, savepoints) with envelope-level atomicity.
* **Dependencies**: [Config Manager](01-config-manager.md) (database path).
* **Critical invariants**:
  * Exactly one writable connection per process; WAL mode enforced.
  * [Graph Manager](07-graph-manager.md) rows append-only; metadata fields (`app_id`, `type_id`, `owner_identity`, `global_seq`) are immutable.
  * Failed writes never advance sequences; corruption or migration failure halts startup.


### 5.3 [Key Manager](03-key-manager.md) (03)

* **Scope**: Generates, stores, loads, and uses secp256k1 key pairs for node, identity, and app scopes; performs signing and ECIES encryption/decryption.
* **Key services**:
  * Key Storage Engine with deterministic filesystem layout.
  * Cryptographic operation APIs that require explicit scope + key identifier parameters (no implicit selection).
  * Public-key derivation for graph binding ([Graph Manager](07-graph-manager.md) persists, [Key Manager](03-key-manager.md) never writes graph data).
* **Dependencies**: [Config Manager](01-config-manager.md) (key directory path). Consumers: [Network Manager](10-network-manager.md), [State Manager](09-state-manager.md), [App Manager](08-app-manager.md), [DoS Guard Manager](14-dos-guard-manager.md).
* **Critical invariants**:
  * Private keys never leave disk/memory and are never exported/logged.
  * Node key must exist before startup completes; failure aborts the process.
  * Key rotation retains old keys but forbids ambiguity.


### 5.4 [Auth Manager](04-auth-manager.md) (04)

* **Scope**: Local authentication authority for HTTP ([04-interfaces/01-local-http-api.md](../../04-interfaces/01-local-http-api.md)) and WebSocket ([04-interfaces/02-websocket-events.md](../../04-interfaces/02-websocket-events.md)) entrypoints; resolves session tokens into backend identities and admin eligibility.
* **Key services**:
  * Token validation pipeline (presence, format, existence, expiry, identity mapping).
  * Admin gating evaluation for protected routes.
  * Construction inputs for [OperationContext](../services-and-apps/05-operation-context.md) (requester identity, app context, admin flag).
* **Dependencies**: [Config Manager](01-config-manager.md) (route settings), [App Manager](08-app-manager.md) (routing metadata), frontend session store. Consumers: HTTP layer, [Event Manager](11-event-manager.md)/[Log Manager](12-log-manager.md) (audit), [ACL Manager](06-acl-manager.md)/[Graph Manager](07-graph-manager.md) (via [OperationContext](../services-and-apps/05-operation-context.md)).
* **Critical invariants**:
  * Authentication is strictly separated from authorization.
  * [OperationContext](../services-and-apps/05-operation-context.md).requester_identity_id originates only here (for local traffic).
  * Missing or malformed tokens fail closed with explicit error categories.


### 5.5 [Schema Manager](05-schema-manager.md) (05)

* **Scope**: Loads schema definitions from app_0, validates structure, compiles type registries and sync domain metadata, and exposes read-only schema APIs.
* **Key services**:
  * Schema Loading/Validation Engines that enforce exactly one schema per app.
  * Type Registry Engine mapping `type_key` <-> `type_id` with immutability.
  * Sync Domain Compilation consumed by [State Manager](09-state-manager.md).
* **Dependencies**: [Graph Manager](07-graph-manager.md) (reads app_0), [Storage Manager](02-storage-manager.md) (type tables), [Config Manager](01-config-manager.md) (limits). Consumers: [Graph Manager](07-graph-manager.md), [ACL Manager](06-acl-manager.md), [State Manager](09-state-manager.md), services.
* **Critical invariants**:
  * Compiled schemas are immutable until explicit reload; reload is atomic.
  * Cross-app schema references forbidden.
  * Schema validation failures halt startup and mark health degraded.


### 5.6 [ACL Manager](06-acl-manager.md) (06)

* **Scope**: Sole authorization engine for graph reads/writes, enforcing schema defaults, ownership rules, object-level ACLs, and remote execution constraints.
* **Key services**:
  * Deterministic evaluation pipeline (ownership -> schema defaults -> app/domain limits -> object ACLs -> graph constraints -> remote constraints).
  * ACL capsules for [Event Manager](11-event-manager.md) subscribers.
  * Traversal support via [Graph Manager](07-graph-manager.md) (bounded).
* **Dependencies**: [Schema Manager](05-schema-manager.md), [Graph Manager](07-graph-manager.md) (state queries), [Config Manager](01-config-manager.md) (policy toggles). Consumers: [Graph Manager](07-graph-manager.md), [Event Manager](11-event-manager.md), services.
* **Critical invariants**:
  * No other component can authorize graph access.
  * Explicit deny overrides allow; schema prohibitions override ACLs.
  * Remote envelopes obey extra constraints (no local history rewrites).


### 5.7 [Graph Manager](07-graph-manager.md) (07)

* **Scope**: Only path for persisted graph mutations and authoritative read surface; coordinates schema validation, [ACL Manager](06-acl-manager.md) enforcement, sequencing, and event emission.
* **Key services**:
  * Graph Write Engine (serialized writes, sequencing, [Storage Manager](02-storage-manager.md) commits).
  * Graph Read Engine (authorization-aware reads).
  * RAM Graph + Traversal Engines supporting [ACL Manager](06-acl-manager.md) decisions.
  * Sequencing Engine guaranteeing monotonic `global_seq`.
* **Dependencies**: [Schema Manager](05-schema-manager.md), [ACL Manager](06-acl-manager.md), [Storage Manager](02-storage-manager.md), [Config Manager](01-config-manager.md), [App Manager](08-app-manager.md), [Event Manager](11-event-manager.md), [Log Manager](12-log-manager.md), [State Manager](09-state-manager.md). Consumers: [State Manager](09-state-manager.md), [Event Manager](11-event-manager.md), services.
* **Critical invariants**:
  * Envelopes must pass structural -> schema -> [ACL Manager](06-acl-manager.md) order before commit.
  * Writes and reads are scoped to a single app/domain per envelope.
  * Events never emit until commit succeeds; reads never leak unauthorized state.


### 5.8 [App Manager](08-app-manager.md) (08)

* **Scope**: Declares and registers applications, assigns `app_id` values, binds app identities to keys, initializes per-app storage, and wires optional backend extensions.
* **Key services**:
  * Persistent registry (slug <-> `app_id`).
  * Application identity Parents in app_0, generated via [Key Manager](03-key-manager.md).
  * Extension service wiring with enforced manager boundaries.
* **Dependencies**: [Storage Manager](02-storage-manager.md), [Key Manager](03-key-manager.md), [Config Manager](01-config-manager.md). Consumers: [Auth Manager](04-auth-manager.md) (routing), [Schema Manager](05-schema-manager.md) (per-app schema), [Graph Manager](07-graph-manager.md) (app_id enforcement), [ACL Manager](06-acl-manager.md).
* **Critical invariants**:
  * [App Manager](08-app-manager.md) IDs are declared before use, unique, and never reused.
  * Cross-app access is forbidden unless [ACL Manager](06-acl-manager.md) explicitly allows.
  * Extension services cannot bypass managers or access raw storage/key/network.


### 5.9 [State Manager](09-state-manager.md) (09)

* **Scope**: Maintains sync metadata, orchestrates inbound remote envelopes, constructs outbound packages, and coordinates deterministic ordering with [Graph Manager](07-graph-manager.md)/[Storage Manager](02-storage-manager.md).
* **Key services**:
  * [State Manager](09-state-manager.md) Engine (commit observation, metadata updates).
  * Sync Engine (peer/domain progression, package construction).
  * Recovery Engine (startup reconstruction, fail-fast on inconsistency).
  * Read Surface Engine (read-only metadata views).
* **Dependencies**: [Graph Manager](07-graph-manager.md), [Storage Manager](02-storage-manager.md), [Network Manager](10-network-manager.md), [Config Manager](01-config-manager.md), [Schema Manager](05-schema-manager.md). Consumers: [Network Manager](10-network-manager.md), [Health Manager](13-health-manager.md), services (observability).
* **Critical invariants**:
  * [Graph Manager](07-graph-manager.md) mutations never occur here; [State Manager](09-state-manager.md) only coordinates.
  * Sync progression never regresses; ordering enforced per `global_seq`.
  * Failures default to rejection; no speculative or partial state is exposed.


### 5.10 [Network Manager](10-network-manager.md) (10)

* **Scope**: Owns transport surfaces, bastion admission, cryptographic binding at the edge, peer discovery, outbound scheduling, and integration with [DoS Guard Manager](14-dos-guard-manager.md).
* **Key services**:
  * [Network Manager](10-network-manager.md) Startup Engine (ordered initialization, readiness gating).
  * Bastion Engine ([DoS Guard Manager](14-dos-guard-manager.md) admission, challenge transport).
  * Incoming Engine (verified inbound envelopes).
  * Outgoing Engine (signed/encrypted outbound packages).
  * Peer discovery and reachability tracking loops.
* **Dependencies**: [DoS Guard Manager](14-dos-guard-manager.md), [Key Manager](03-key-manager.md), [State Manager](09-state-manager.md), [Config Manager](01-config-manager.md), [Health Manager](13-health-manager.md), [Event Manager](11-event-manager.md), [Log Manager](12-log-manager.md). Consumers: [State Manager](09-state-manager.md) (verified packages), [Health Manager](13-health-manager.md) (signals).
* **Critical invariants**:
  * No payload crosses into [State Manager](09-state-manager.md) without DoS admission and crypto verification.
  * Transport-level IDs are never treated as authenticated identity.
  * Best-effort transport only; retries/persistence belong to [State Manager](09-state-manager.md).


### 5.11 [Event Manager](11-event-manager.md) (11)

* **Scope**: Exclusive event publication surface (internal manager bus + WebSocket ([04-interfaces/02-websocket-events.md](../../04-interfaces/02-websocket-events.md)) to frontend); normalizes descriptors, enforces ACL-based audiences, and manages delivery.
* **Key services**:
  * Source Intake -> Normalization -> Audience -> Delivery engines with bounded queues.
  * Subscription Registry (immutable filters, resume tokens, heartbeat/backpressure).
  * Telemetry Engine for queue depth/failures.
* **Dependencies**: [Graph Manager](07-graph-manager.md), [App Manager](08-app-manager.md), [Config Manager](01-config-manager.md), [ACL Manager](06-acl-manager.md) (audience capsules), [Auth Manager](04-auth-manager.md) ([OperationContext](../services-and-apps/05-operation-context.md) for sockets), [DoS Guard Manager](14-dos-guard-manager.md) (subscription throttling). Consumers: frontend clients, managers needing notifications.
* **Critical invariants**:
  * Events never contain mutable graph data or secrets; they reference committed objects only.
  * Authorization is enforced via cached ACL capsules per envelope.
  * Delivery is best-effort; clients must use read APIs for recovery.


### 5.12 [Log Manager](12-log-manager.md) (12)

* **Scope**: Central structured logging authority; enforces record schema, routes to sinks (stdout, rolling files, [Event Manager](11-event-manager.md) bridge), and exposes read-only query APIs.
* **Key services**:
  * Submission -> Validation -> Normalization -> Routing -> Sink pipeline.
  * Integrity hashing for audit/security files; retention management.
  * Optional [Event Manager](11-event-manager.md) bridge for high-severity alerts.
* **Dependencies**: [Config Manager](01-config-manager.md) (log.*), filesystem. Consumers: [Event Manager](11-event-manager.md) (alerts), [DoS Guard Manager](14-dos-guard-manager.md) (security feeds), [Health Manager](13-health-manager.md) (sinks), operators.
* **Critical invariants**:
  * No component writes logs directly to sinks; everything flows through [Log Manager](12-log-manager.md).
  * [OperationContext](../services-and-apps/05-operation-context.md) metadata is mandatory when available.
  * Mandatory sinks failing forces readiness false and may cause request rejection.


### 5.13 [Health Manager](13-health-manager.md) (13)

* **Scope**: Aggregates readiness/liveness across managers, publishes snapshots, and enforces fail-closed gating.
* **Key services**:
  * Signal Intake -> Validation -> Evaluation -> Publication pipeline.
  * Readiness evaluation requiring all critical managers to report `healthy`.
  * HTTP/admin APIs ([04-interfaces/**](../../04-interfaces/)) and [Event Manager](11-event-manager.md)/[Log Manager](12-log-manager.md) notifications for state transitions.
* **Dependencies**: All managers (signals), [Config Manager](01-config-manager.md) (thresholds). Consumers: [DoS Guard Manager](14-dos-guard-manager.md) (admission throttle), [Event Manager](11-event-manager.md) (notifications), operators.
* **Critical invariants**:
  * Readiness false until every critical manager reports `healthy`.
  * Snapshots are immutable, versioned via `health_seq`.
  * [Health Manager](13-health-manager.md) data exposed only to admin identities; aggregate states available broadly.


### 5.14 [DoS Guard Manager](14-dos-guard-manager.md) (14)

* **Scope**: Admission control authority; issues/verifies puzzles, tracks abuse telemetry, and instructs [Network Manager](10-network-manager.md)'s Bastion Engine.
* **Key services**:
  * Telemetry Intake Engine (resource usage, per-identity stats).
  * Policy Engine (allow/deny/challenge decisions).
  * Puzzle Engine (generation/verification using [Key Manager](03-key-manager.md) seeds).
  * Publication Engine (decisions to [Network Manager](10-network-manager.md), telemetry to [Log Manager](12-log-manager.md)/[Event Manager](11-event-manager.md)).
* **Dependencies**: [Network Manager](10-network-manager.md) (telemetry), [Key Manager](03-key-manager.md) (puzzle seeds), [Config Manager](01-config-manager.md) (dos.*), [Health Manager](13-health-manager.md) (readiness multipliers). Consumers: [Network Manager](10-network-manager.md), [Event Manager](11-event-manager.md), [Log Manager](12-log-manager.md).
* **Critical invariants**:
  * Decisions default to deny on failure; puzzles are opaque to other managers.
  * Admission cannot proceed when [DoS Guard Manager](14-dos-guard-manager.md) is unavailable.
  * Difficulty adjusts deterministically based on telemetry + health state.


## 6. Startup and shutdown choreography

### 6.1 Startup order (high-level)

1. **[Config Manager](01-config-manager.md)** parses `.env`, loads settings, publishes snapshots.
2. **[Storage Manager](02-storage-manager.md)** opens SQLite, materializes schemas.
3. **[Key Manager](03-key-manager.md)** loads the node key (plus app keys as needed).
4. **[App Manager](08-app-manager.md)** registers apps and identities (needs [Storage Manager](02-storage-manager.md) + [Key Manager](03-key-manager.md)).
5. **[Schema Manager](05-schema-manager.md)** loads/validates schemas (depends on [Graph Manager](07-graph-manager.md) read access and the [App Manager](08-app-manager.md) registry).
6. **[ACL Manager](06-acl-manager.md)** initializes with schema metadata.
7. **[Graph Manager](07-graph-manager.md)** boots once [Schema Manager](05-schema-manager.md), [ACL Manager](06-acl-manager.md), [Storage Manager](02-storage-manager.md), [Config Manager](01-config-manager.md), and [App Manager](08-app-manager.md) are ready.
8. **[State Manager](09-state-manager.md)** reconstructs metadata once [Graph Manager](07-graph-manager.md)/[Storage Manager](02-storage-manager.md) ready.
9. **[Log Manager](12-log-manager.md)** initializes sinks (so remaining managers can log).
10. **[Event Manager](11-event-manager.md)** starts intake/delivery.
11. **[DoS Guard Manager](14-dos-guard-manager.md)** loads `dos.*`, registers its Bastion interface with [Network Manager](10-network-manager.md), and defaults to deny until [Health Manager](13-health-manager.md) signals are available.
12. **[Network Manager](10-network-manager.md)** brings up bastion/admitted surfaces only after [DoS Guard Manager](14-dos-guard-manager.md) registration succeeds.
13. **[Auth Manager](04-auth-manager.md)** comes online once [Config Manager](01-config-manager.md)/[App Manager](08-app-manager.md) are ready.
14. **[Health Manager](13-health-manager.md)** begins sampling once all managers report initial state.

[Health Manager](13-health-manager.md) reports readiness only after every critical manager signals `healthy`. Any failure at any stage keeps readiness false and halts startup (Section 13).

### 6.2 Shutdown order

1. [Health Manager](13-health-manager.md) marks readiness false.
2. [Network Manager](10-network-manager.md) + [DoS Guard Manager](14-dos-guard-manager.md) stop new admissions and drain sessions.
3. [Event Manager](11-event-manager.md) and [Log Manager](12-log-manager.md) managers flush buffers.
4. [State Manager](09-state-manager.md) halts sync ingestion/export.
5. [Graph Manager](07-graph-manager.md) stops accepting writes, completes in-flight transactions.
6. Remaining managers release resources ([ACL Manager](06-acl-manager.md), [Schema Manager](05-schema-manager.md), [App Manager](08-app-manager.md), [Auth Manager](04-auth-manager.md), [Config Manager](01-config-manager.md)).
7. [Storage Manager](02-storage-manager.md) closes connection; [Key Manager](03-key-manager.md) caches cleared in memory.

Partial shutdown is forbidden; each manager must ensure no new requests are accepted after its shutdown begins.

## 7. [OperationContext](../services-and-apps/05-operation-context.md) and trust boundaries

[OperationContext](../services-and-apps/05-operation-context.md) defines the execution context shared by managers, while [02-architecture/03-trust-boundaries.md](../03-trust-boundaries.md) defines the enforcement posture across boundaries.

* **Construction**:
  * Local: HTTP/WebSocket route -> [Auth Manager](04-auth-manager.md) -> [App Manager](08-app-manager.md) binding -> [OperationContext](../services-and-apps/05-operation-context.md).
  * Remote: [Network Manager](10-network-manager.md) verifies envelope -> [State Manager](09-state-manager.md) constructs remote [OperationContext](../services-and-apps/05-operation-context.md) (includes peer identity, sync domain, remote flag).
* **Consumption**: Every manager receiving an [OperationContext](../services-and-apps/05-operation-context.md) must treat it as immutable. [Graph Manager](07-graph-manager.md) uses it for app/domain scoping, [ACL Manager](06-acl-manager.md) for identity + execution mode, [Event Manager](11-event-manager.md) for audience filtering, [Log Manager](12-log-manager.md) for audit metadata, [Health Manager](13-health-manager.md) for admin [ACL Manager](06-acl-manager.md) gating.
* **Trusted vs. untrusted inputs**:
  * Transport data remains untrusted until [Network Manager](10-network-manager.md) + [DoS Guard Manager](14-dos-guard-manager.md) + [Key Manager](03-key-manager.md) verify it.
  * [Config Manager](01-config-manager.md) data is untrusted until [Config Manager](01-config-manager.md) validates it.
  * [Graph Manager](07-graph-manager.md) data is untrusted until [Graph Manager](07-graph-manager.md) + [Schema Manager](05-schema-manager.md) + [ACL Manager](06-acl-manager.md) accept it.
  * [Health Manager](13-health-manager.md) and [Event Manager](11-event-manager.md) surfaces expose data only after [ACL Manager](06-acl-manager.md)/admin checks.

## 8. Observability, readiness, and failure posture

1. **Logging**: All components push structured records into [Log Manager](12-log-manager.md). Mandatory sinks failing results in readiness false and may force request rejection (for example, audit-required flows).
2. **Events**: [Graph Manager](07-graph-manager.md), [Config Manager](01-config-manager.md), [Network Manager](10-network-manager.md), [DoS Guard Manager](14-dos-guard-manager.md), [Health Manager](13-health-manager.md), [App Manager](08-app-manager.md), and [Log Manager](12-log-manager.md) publish descriptors to [Event Manager](11-event-manager.md) only after commit or state transition. [Event Manager](11-event-manager.md) enforces best-effort delivery with ACK/backpressure semantics.
3. **[Health Manager](13-health-manager.md)**: Every manager must emit health signals (heartbeat, state). Missing or invalid signals degrade readiness. [Health Manager](13-health-manager.md) alerts [Event Manager](11-event-manager.md)/[Log Manager](12-log-manager.md) and [DoS Guard Manager](14-dos-guard-manager.md) when states change.
4. **Fail-closed principle**: If any manager cannot guarantee invariants ([DoS Guard Manager](14-dos-guard-manager.md) unreachable, [Config Manager](01-config-manager.md) reload invalid, [Schema Manager](05-schema-manager.md) mismatch, [Storage Manager](02-storage-manager.md) corruption), it must reject requests and mark health degraded. Recovery requires operator intervention (no silent repair).

## 9. Implementation checklist example

A short example checklist for wiring the managers together or reviewing an implementation:

1. **Configuration**: Are all managers reading configuration exclusively via [Config Manager](01-config-manager.md) snapshots? Are settings keys registered with reload policies and owner namespaces?
2. **Start order**: Does the runtime enforce the startup sequence from Section 6? Are dependencies checked before readiness?
3. **[OperationContext](../services-and-apps/05-operation-context.md) usage**: Does every entrypoint authenticate via [Auth Manager](04-auth-manager.md) (local) or the [Network Manager](10-network-manager.md) + [State Manager](09-state-manager.md) pipeline (remote) before invoking [Graph Manager](07-graph-manager.md)/[ACL Manager](06-acl-manager.md)?
4. **[Graph Manager](07-graph-manager.md) write path**: Does every mutation route through [Graph Manager](07-graph-manager.md) and maintain the structural -> schema -> [ACL Manager](06-acl-manager.md) -> persistence order?
5. **Sync**: Are inbound envelopes admitted only after [DoS Guard Manager](14-dos-guard-manager.md) + [Network Manager](10-network-manager.md) + [Key Manager](03-key-manager.md) verification, and is [State Manager](09-state-manager.md) coordinating ordering before [Graph Manager](07-graph-manager.md)?
6. **Logging/events**: Are logs routed only through [Log Manager](12-log-manager.md), and are event descriptors emitted only post-commit? Are [Event Manager](11-event-manager.md) queues bounded with enforceable limits?
7. **Security**: Are keys confined to [Key Manager](03-key-manager.md)? Are DoS puzzles opaque to other managers? Are [ACL Manager](06-acl-manager.md) decisions centralized?
8. **Observability**: Are [Config Manager](01-config-manager.md) reloads, health transitions, network admissions, [ACL Manager](06-acl-manager.md) denials, and schema reloads emitting logs/events per spec?
9. **Failure handling**: Does every manager fail closed on dependency loss (for example, [DoS Guard Manager](14-dos-guard-manager.md) forcing `deny`, [Health Manager](13-health-manager.md) forcing readiness false, [Config Manager](01-config-manager.md) veto halting reload)?
10. **Testing hooks**: Are bootstrap/diagnostic modes limited and still enforced via [OperationContext](../services-and-apps/05-operation-context.md) + [ACL Manager](06-acl-manager.md), with no shortcuts that bypass these managers?

Satisfying this overview ensures that the detailed specifications (`01`-`14`) can be implemented consistently and that the entire manager fabric behaves deterministically under both normal and failure conditions.
