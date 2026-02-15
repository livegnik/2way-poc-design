



# 01 Component model

Defines backend component categories, responsibilities, and interaction rules. Specifies manager/service boundaries, allowed interactions, and trust posture. Defines failure handling and guarantees for component behavior.

For the meta specifications, see [01-component-model meta](../10-appendix/meta/02-architecture/01-component-model-meta.md).

## 1. Component model overview

The 2WAY backend is composed of managers and services running within a single long-lived backend process as described in [00-architecture-overview.md](00-architecture-overview.md).

Managers form the protocol kernel. They implement all protocol-enforced behavior and invariants defined in [01-protocol/**](../01-protocol/).

Services implement domain logic on top of managers. Services never define protocol rules and never bypass managers, consistent with [02-architecture/04-data-flow-overview.md](04-data-flow-overview.md).

The component model enforces the following system-wide rules:

- All persistent state mutation flows through managers.
- All protocol invariants are enforced by managers, not services.
- Services may coordinate behavior but cannot weaken or override manager guarantees.
- No component accesses another component's internal state directly.
- [OperationContext](services-and-apps/05-operation-context.md) is mandatory and immutable for all request-scoped manager calls; local contexts are bound by [Auth Manager](managers/04-auth-manager.md), remote contexts by [State Manager](managers/09-state-manager.md), and automation contexts follow the same rules.
- Runtime configuration and policy inputs flow only through [Config Manager](managers/01-config-manager.md); no component reads `.env` or the `settings` table directly.
- Logs, events, and health signals flow only through [Log Manager](managers/12-log-manager.md), [Event Manager](managers/11-event-manager.md), and [Health Manager](managers/13-health-manager.md).
- Derived data and caches are non-authoritative, rebuildable, and never synced.

## 2. Component categories

### 2.1 Managers

Managers are singleton backend components. Each manager owns exactly one conceptual domain and is authoritative for that domain.

Managers are stable, long-lived, and loaded at process startup. They consume configuration snapshots from [Config Manager](managers/01-config-manager.md) and publish readiness through [Health Manager](managers/13-health-manager.md).

### 2.2 Services

Services are backend components that implement domain-specific workflows.

Two service classes exist:

- [System services](services-and-apps/02-system-services.md).
- [App services](services-and-apps/03-app-services.md).

Both classes use managers exclusively to interact with system state. The taxonomy is defined in [02-architecture/services-and-apps/01-services-vs-apps.md](services-and-apps/01-services-vs-apps.md).

Services load after required managers are ready, register readiness with [Health Manager](managers/13-health-manager.md), and read configuration exclusively through [Config Manager](managers/01-config-manager.md). Services may maintain derived caches only through [Storage Manager](managers/02-storage-manager.md) APIs and must treat them as non-authoritative.

## 3. Manager responsibilities and boundaries

### 3.1 Global manager invariants

All managers collectively enforce the following invariants:

| Manager | Invariant | Notes |
| --- | --- | --- |
| <span style="white-space:nowrap;">[Graph Manager](managers/07-graph-manager.md)</span> | Only component allowed to mutate graph state. | Serializes writes and assigns `global_seq`. |
| <span style="white-space:nowrap;">[Storage Manager](managers/02-storage-manager.md)</span> | Only component allowed to execute raw database operations. | Owns SQLite connections and transactions. |
| <span style="white-space:nowrap;">[Config Manager](managers/01-config-manager.md)</span> | Only component allowed to load, validate, and publish runtime configuration snapshots. | All components consume snapshots only. |
| <span style="white-space:nowrap;">[Schema Manager](managers/05-schema-manager.md)</span> | Only component allowed to interpret type and schema definitions. | Validation happens before ACL. |
| <span style="white-space:nowrap;">[ACL Manager](managers/06-acl-manager.md)</span> | Only component allowed to make authorization decisions. | Applies capability and ownership rules. |
| <span style="white-space:nowrap;">[Key Manager](managers/03-key-manager.md)</span> | Only component allowed to access private key material. | Signs and decrypts on behalf of authorized callers. |
| <span style="white-space:nowrap;">[State Manager](managers/09-state-manager.md)</span> | Only component allowed to manage sync state and reconciliation. | Orchestrates ingress/egress, never mutates graph directly. |
| <span style="white-space:nowrap;">[Network Manager](managers/10-network-manager.md)</span> | Only component allowed to perform peer communication and transport, after admission decisions from [DoS Guard Manager](managers/14-dos-guard-manager.md) and readiness gating by [Health Manager](managers/13-health-manager.md). | Treats transport as hostile; best-effort delivery only. |
| <span style="white-space:nowrap;">[Event Manager](managers/11-event-manager.md)</span> | Only component allowed to publish backend events. | Emits post-commit descriptors only. |
| <span style="white-space:nowrap;">[App Manager](managers/08-app-manager.md)</span> | Only component allowed to register, load, and bind apps. | Assigns `app_id`, wires app services. |
| <span style="white-space:nowrap;">[Auth Manager](managers/04-auth-manager.md)</span> | Only component allowed to resolve frontend identity and session context. | Binds local identities for OperationContext. |
| <span style="white-space:nowrap;">[Log Manager](managers/12-log-manager.md)</span> | Only component allowed to emit structured logs. | Mandatory audit and diagnostics path. |
| <span style="white-space:nowrap;">[Health Manager](managers/13-health-manager.md)</span> | Only component allowed to report system health. | Gates readiness for admission. |
| <span style="white-space:nowrap;">[DoS Guard Manager](managers/14-dos-guard-manager.md)</span> | Only component allowed to enforce rate limiting and abuse controls. | Issues challenges and admission decisions. |

These invariants are mandatory. Violations invalidate correctness and security guarantees.

### 3.2 Individual manager responsibility domains

Each manager owns a single responsibility domain:

| Manager | Responsibility domain | Notes |
| --- | --- | --- |
| <span style="white-space:nowrap;">[Config Manager](managers/01-config-manager.md)</span> | Runtime configuration loading, validation, namespace snapshots, and reload handshakes. | Only source of config truth. |
| <span style="white-space:nowrap;">[Storage Manager](managers/02-storage-manager.md)</span> | SQLite access, transactions, and persistence boundaries. | Owns schema materialization and sequence helpers. |
| <span style="white-space:nowrap;">[Key Manager](managers/03-key-manager.md)</span> | Node, user, and app key lifecycle, PEM file storage, signing, and decryption aligned to [01-protocol/05-keys-and-identity.md](../01-protocol/05-keys-and-identity.md) and [01-protocol/04-cryptography.md](../01-protocol/04-cryptography.md). | Private keys never leave this manager. |
| <span style="white-space:nowrap;">[Auth Manager](managers/04-auth-manager.md)</span> | Frontend authentication, session validation, and identity resolution. | Produces local identity bindings for OperationContext. |
| <span style="white-space:nowrap;">[Schema Manager](managers/05-schema-manager.md)</span> | Schema objects, type resolution, and schema validation. | Canonical schema authority. |
| <span style="white-space:nowrap;">[ACL Manager](managers/06-acl-manager.md)</span> | Authorization evaluation using [OperationContext](services-and-apps/05-operation-context.md) and graph data aligned to [01-protocol/06-access-control-model.md](../01-protocol/06-access-control-model.md). | Deterministic allow/deny with explicit precedence. |
| <span style="white-space:nowrap;">[Graph Manager](managers/07-graph-manager.md)</span> | All graph mutations, validation ordering, and global sequence assignment. | Single write path, atomic envelopes. |
| <span style="white-space:nowrap;">[App Manager](managers/08-app-manager.md)</span> | App identity registration, lifecycle, and app service loading. | Binds slugs to `app_id`, wires app services. |
| <span style="white-space:nowrap;">[State Manager](managers/09-state-manager.md)</span> | Sync domains, sequence tracking, reconciliation, and conflict handling aligned to [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md). | Applies ordering rules and constructs remote OperationContext. |
| <span style="white-space:nowrap;">[Network Manager](managers/10-network-manager.md)</span> | Transport setup, message exchange, signing verification, and encryption consistent with [01-protocol/08-network-transport-requirements.md](../01-protocol/08-network-transport-requirements.md). | Enforces admission + verification before State Manager. |
| <span style="white-space:nowrap;">[Event Manager](managers/11-event-manager.md)</span> | Event publication and subscription. | Best-effort delivery; no state mutation. |
| <span style="white-space:nowrap;">[Log Manager](managers/12-log-manager.md)</span> | Audit, diagnostic, and operational logging. | Mandatory logging surface. |
| <span style="white-space:nowrap;">[Health Manager](managers/13-health-manager.md)</span> | Liveness checks and health state reporting. | Aggregates readiness across managers. |
| <span style="white-space:nowrap;">[DoS Guard Manager](managers/14-dos-guard-manager.md)</span> | Request throttling and abuse mitigation aligned to [01-protocol/09-dos-guard-and-client-puzzles.md](../01-protocol/09-dos-guard-and-client-puzzles.md). | Admission control and puzzle issuance. |

Managers may call other managers only through explicit, validated inputs. Circular dependencies are forbidden.

### 3.3 Manager non-responsibilities

Managers explicitly do not perform the following:

- User interface logic.
- Application-specific business logic.
- Direct frontend rendering.
- Cross-domain policy decisions not encoded in schema or ACL rules.
- Implicit retries or compensating actions outside their domain.

## 4. Service responsibilities and boundaries

### 4.1 Service responsibilities

Services implement domain workflows using managers. Services are not authoritative.

Services may perform the following:

- Translate high-level actions into graph operations.
- Perform domain-specific validation prior to manager invocation.
- Aggregate read operations across managers.
- Emit domain events through Event Manager.
- Expose backend endpoints through defined interfaces.
- Consume configuration snapshots via [Config Manager](managers/01-config-manager.md) and declare required keys.
- Maintain derived caches and indices that are non-authoritative and rebuildable via [Storage Manager](managers/02-storage-manager.md).
- Register readiness and liveness signals through [Health Manager](managers/13-health-manager.md).
- Schedule automation jobs that construct fresh [OperationContext](services-and-apps/05-operation-context.md) instances with `actor_type=automation`.

Services must supply complete [OperationContext](services-and-apps/05-operation-context.md) to all request-scoped manager calls.
Remote envelopes are accepted only through the [Network Manager](managers/10-network-manager.md) to [State Manager](managers/09-state-manager.md) pipeline; services must not inject remote data directly into managers.

### 4.2 Service non-responsibilities

Services must not perform the following:

- Modify protocol invariants.
- Bypass Graph Manager for writes.
- Bypass Storage Manager for access to SQLite directly.
- Bypass ACL Manager for authorization.
- Access private keys directly.
- Perform network transport.
- Persist authoritative state outside the graph.
- Load or mutate runtime configuration outside [Config Manager](managers/01-config-manager.md).
- Emit logs, events, or health signals outside [Log Manager](managers/12-log-manager.md), [Event Manager](managers/11-event-manager.md), or [Health Manager](managers/13-health-manager.md).
- Treat derived caches as authoritative or sync them to peers.
- Mutate [OperationContext](services-and-apps/05-operation-context.md) after construction.

### 4.3 System services

System services are backend services that exist independently of installed apps, as defined in [02-architecture/services-and-apps/02-system-services.md](services-and-apps/02-system-services.md).

System services:

- Are loaded automatically.
- Define shared social or structural primitives.
- Own their own schema within their app domain.
- May expose stable backend APIs.

System services depend on managers but are not depended on by managers.

PoC-required system services are defined in [02-system-services.md](services-and-apps/02-system-services.md):

- System Bootstrap and Provisioning Service (Setup Service).
- Identity Service.
- Sync Service.
- Admin Service.

### 4.4 App services

App services are optional backend services tied to a single app identity, as defined in [02-architecture/services-and-apps/03-app-services.md](services-and-apps/03-app-services.md).

Additional constraints apply:

- They may act only within their app domain.
- They may not modify system services.
- They may not define or alter protocol behavior.
- They must remain removable without affecting system correctness.

App services interact with managers only through allowed manager APIs.

## 5. Allowed interactions

### 5.1 Manager to manager interactions

Allowed interactions are limited to:

- Explicit method calls using validated inputs.
- Read-only access to outputs exposed by another manager.
- Dependency ordering defined by initialization sequence.

Managers must not mutate state owned by another manager.

### 5.2 Service to manager interactions

Services may interact with managers as follows:

- Invoke [Graph Manager](managers/07-graph-manager.md) for all graph mutations and authoritative graph reads.
- Invoke [Schema Manager](managers/05-schema-manager.md) for schema validation and schema snapshots.
- Invoke [ACL Manager](managers/06-acl-manager.md) for permission checks.
- Invoke [Storage Manager](managers/02-storage-manager.md) only for derived cache tables or other non-graph storage helpers explicitly exposed by Storage Manager.
- Invoke [Config Manager](managers/01-config-manager.md) for configuration snapshots.
- Invoke [Event Manager](managers/11-event-manager.md) for event publication.
- Invoke [Log Manager](managers/12-log-manager.md) for logging.
- Invoke [Health Manager](managers/13-health-manager.md) for readiness/liveness reporting.
- Invoke [State Manager](managers/09-state-manager.md) only for sync orchestration, never for direct graph mutation.

All request-scoped interactions require a valid OperationContext.

### 5.3 External interactions

Frontend clients and remote peers are external to the component model:

- All external input is treated as untrusted.
- External input enters the system only through [interface layer entrypoints](../04-interfaces/) that bind [OperationContext](services-and-apps/05-operation-context.md) via [Auth Manager](managers/04-auth-manager.md) (local) or [Network Manager](managers/10-network-manager.md) + [State Manager](managers/09-state-manager.md) (remote).
- No external actor interacts directly with managers.
- Sync packages enter manager processing only through Network Manager and State Manager after DoS Guard admission and cryptographic verification.

## 6. Forbidden interactions

The following interactions are explicitly forbidden:

- Direct database access outside Storage Manager.
- Graph mutation outside Graph Manager.
- Authorization decisions outside ACL Manager.
- Private key access outside Key Manager.
- Network I/O outside Network Manager.
- Sync state mutation outside State Manager.
- Configuration read or write outside Config Manager.
- Log, event, or health emission outside Log Manager, Event Manager, or Health Manager.
- Managers depending on services.
- Services calling other services without explicit interfaces, OperationContext, and manager mediation.
- Cross-app data mutation without explicit ACL allowance.
- Treating derived caches as authoritative or syncing them.
- Mutation of OperationContext after construction.

## 7. Trust boundaries

Each component defines a strict trust boundary as detailed in [02-architecture/03-trust-boundaries.md](03-trust-boundaries.md):

- Managers trust only validated inputs from other managers.
- Services trust managers but not external inputs.
- App services are untrusted relative to core managers.
- Network Manager treats all inbound peer data as untrusted.
- Auth Manager treats frontend auth tokens and registration signatures as untrusted until verified.

Trust does not propagate implicitly across components.

## 8. Failure and rejection behavior

### 8.1 Invalid input

If a component receives invalid input:

- The input is rejected.
- No partial state mutation occurs.
- The failure is logged by the Log Manager.
- An error is returned to the caller.
- No implicit retries are performed.
- Missing or malformed OperationContext is rejected before schema or ACL evaluation.

### 8.2 Authorization failure

If authorization fails:

- The operation is rejected by ACL Manager.
- No graph mutation occurs.
- The failure is logged by the Log Manager.
- A permission error is returned.

### 8.3 Storage failure

If a storage operation fails:

- The entire operation is aborted.
- The transaction is rolled back.
- No partial writes occur.
- The failure is logged by the Log Manager.
- The error is surfaced to the caller.

### 8.4 Network failure

If a network operation fails:

- The failure is isolated to Network Manager.
- Local state remains unchanged.
- Sync state is preserved.
- Retry behavior is explicit and bounded.
- The failure is logged by the Log Manager.

### 8.5 Component crash

If a component crashes:

- No other component assumes recovery.
- Persistent state remains authoritative.
- Recovery occurs through process restart.
- In-memory state is discarded.
- The crash is logged by the Log Manager if able.

## 9. Guarantees

This component model guarantees the following:

* Single, deterministic write path for all persistent graph mutations.
* Atomic graph mutations with all-or-nothing commit semantics.
* Centralized enforcement of schema and authorization rules.
* Non-bypassable ownership of database access, configuration, keys, transport, sync, events, logs, and health reporting.
* Strict separation between protocol kernel and domain logic.
* Fixed validation order before mutation and sequencing.
* Monotonic global sequencing of accepted mutations.
* Side effects occur only after successful state mutation.
* One-way dependency flow, managers do not depend on services.
* App services are sandboxed to their app domain and manager APIs.
* Apps and app services can be removed without corrupting system state.
* Explicit and bounded trust relationships between components.
* All external input is treated as untrusted by default.
* No hidden persistence or authority paths.
* Persistent state is sufficient for deterministic recovery.
* OperationContext is immutable and required for all request-scoped manager calls.
* Derived data is non-authoritative, rebuildable, and never part of sync state.

No other guarantees are implied.


