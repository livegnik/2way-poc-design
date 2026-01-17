



# 01 Component model

## 1. Purpose and scope

This document defines the backend component model of the 2WAY system as implemented in the proof of concept (PoC). It specifies component categories, responsibilities, invariants, allowed and forbidden interactions, trust boundaries, and failure behavior.

This document is normative for backend structure and behavior. It does not define APIs, wire formats, schemas, storage layout, or runtime topology except where required to establish component correctness and boundaries. Frontend components are out of scope except as external callers.

This component model references:

* [01-protocol/**](../01-protocol/)
* [02-architecture/00-architecture-overview.md](00-architecture-overview.md)
* [02-architecture/02-runtime-topologies.md](02-runtime-topologies.md)
* [02-architecture/03-trust-boundaries.md](03-trust-boundaries.md)
* [02-architecture/04-data-flow-overview.md](04-data-flow-overview.md)
* [02-architecture/managers/**](managers/)
* [02-architecture/services-and-apps/**](services-and-apps/)
* [04-interfaces/**](../04-interfaces/)

## 2. Component model overview

The 2WAY backend is composed of managers and services running within a single long-lived backend process as described in [00-architecture-overview.md](00-architecture-overview.md).

Managers form the protocol kernel. They implement all protocol-enforced behavior and invariants defined in [01-protocol/**](../01-protocol/).

Services implement domain logic on top of managers. Services never define protocol rules and never bypass managers, consistent with [02-architecture/04-data-flow-overview.md](04-data-flow-overview.md).

The component model enforces the following system-wide rules:

- All persistent state mutation flows through managers.
- All protocol invariants are enforced by managers, not services.
- Services may coordinate behavior but cannot weaken or override manager guarantees.
- No component accesses another component's internal state directly.

## 3. Component categories

### 3.1 Managers

Managers are singleton backend components. Each manager owns exactly one conceptual domain and is authoritative for that domain.

Managers are stable, long-lived, and loaded at process startup.

### 3.2 Services

Services are backend components that implement domain-specific workflows.

Two service classes exist:

- [System services](services-and-apps/02-system-services.md).
- [App extension services](services-and-apps/03-app-backend-extensions.md).

Both classes use managers exclusively to interact with system state. The taxonomy is defined in [02-architecture/services-and-apps/01-services-vs-apps.md](services-and-apps/01-services-vs-apps.md).

## 4. Manager responsibilities and boundaries

### 4.1 Global manager invariants

All managers collectively enforce the following invariants:

- [Graph Manager](managers/07-graph-manager.md) is the only component allowed to mutate graph state.
- [Storage Manager](managers/02-storage-manager.md) is the only component allowed to execute raw database operations.
- [Schema Manager](managers/05-schema-manager.md) is the only component allowed to interpret type and schema definitions.
- [ACL Manager](managers/06-acl-manager.md) is the only component allowed to make authorization decisions.
- [Key Manager](managers/03-key-manager.md) is the only component allowed to access private key material.
- [State Manager](managers/09-state-manager.md) is the only component allowed to manage sync state and reconciliation.
- [Network Manager](managers/10-network-manager.md) is the only component allowed to perform peer communication and transport.
- [Event Manager](managers/11-event-manager.md) is the only component allowed to publish backend events.
- [App Manager](managers/08-app-manager.md) is the only component allowed to register, load, and bind apps.
- [Auth Manager](managers/04-auth-manager.md) is the only component allowed to resolve frontend identity and session context.
- [Log Manager](managers/12-log-manager.md) is the only component allowed to emit structured logs.
- [Health Manager](managers/13-health-manager.md) is the only component allowed to report system health.
- [DoS Guard Manager](managers/14-dos-guard-manager.md) is the only component allowed to enforce rate limiting and abuse controls.

These invariants are mandatory. Violations invalidate correctness and security guarantees.

### 4.2 Individual manager responsibility domains

Each manager owns a single responsibility domain:

- [Config Manager](managers/01-config-manager.md) owns runtime configuration loading and access.
- [Storage Manager](managers/02-storage-manager.md) owns SQLite access, transactions, and persistence boundaries.
- [Key Manager](managers/03-key-manager.md) owns node, user, and app key lifecycle, PEM file storage, signing, and decryption aligned to [01-protocol/05-keys-and-identity.md](../01-protocol/05-keys-and-identity.md) and [01-protocol/04-cryptography.md](../01-protocol/04-cryptography.md).
- [Auth Manager](managers/04-auth-manager.md) owns frontend authentication, session validation, and identity resolution.
- [Schema Manager](managers/05-schema-manager.md) owns schema objects, type resolution, and schema validation.
- [ACL Manager](managers/06-acl-manager.md) owns authorization evaluation using [OperationContext](services-and-apps/05-operation-context.md) and graph data aligned to [01-protocol/06-access-control-model.md](../01-protocol/06-access-control-model.md).
- [Graph Manager](managers/07-graph-manager.md) owns all graph mutations, validation ordering, and global sequence assignment.
- [App Manager](managers/08-app-manager.md) owns app identity registration, lifecycle, and backend extension loading.
- [State Manager](managers/09-state-manager.md) owns sync domains, sequence tracking, reconciliation, and conflict handling aligned to [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).
- [Network Manager](managers/10-network-manager.md) owns transport setup, message exchange, signing verification, and encryption consistent with [01-protocol/08-network-transport-requirements.md](../01-protocol/08-network-transport-requirements.md).
- [Event Manager](managers/11-event-manager.md) owns event publication and subscription.
- [Log Manager](managers/12-log-manager.md) owns audit, diagnostic, and operational logging.
- [Health Manager](managers/13-health-manager.md) owns liveness checks and health state reporting.
- [DoS Guard Manager](managers/14-dos-guard-manager.md) owns request throttling and abuse mitigation aligned to [01-protocol/11-dos-guard-and-client-puzzles.md](../01-protocol/11-dos-guard-and-client-puzzles.md).

Managers may call other managers only through explicit, validated inputs. Circular dependencies are forbidden.

### 4.3 Manager non-responsibilities

Managers explicitly do not perform the following:

- User interface logic.
- Application-specific business logic.
- Direct frontend rendering.
- Cross-domain policy decisions not encoded in schema or ACL rules.
- Implicit retries or compensating actions outside their domain.

## 5. Service responsibilities and boundaries

### 5.1 Service responsibilities

Services implement domain workflows using managers. Services are not authoritative.

Services may perform the following:

- Translate high-level actions into graph operations.
- Perform domain-specific validation prior to manager invocation.
- Aggregate read operations across managers.
- Emit domain events through Event Manager.
- Expose backend endpoints through defined interfaces.

Services must supply complete [OperationContext](services-and-apps/05-operation-context.md) to all manager calls.

### 5.2 Service non-responsibilities

Services must not perform the following:

- Modify protocol invariants.
- Bypass Graph Manager for writes.
- Bypass Storage Manager for access to SQLite directly.
- Bypass ACL Manager for authorization.
- Access private keys directly.
- Perform network transport.
- Persist state outside the graph.

### 5.3 System services

System services are backend services that exist independently of installed apps, as defined in [02-architecture/services-and-apps/02-system-services.md](services-and-apps/02-system-services.md).

System services:

- Are loaded automatically.
- Define shared social or structural primitives.
- Own their own schema within their app domain.
- May expose stable backend APIs.

System services depend on managers but are not depended on by managers.

### 5.4 App extension services

App extension services are optional backend services tied to a single app identity, as defined in [02-architecture/services-and-apps/03-app-backend-extensions.md](services-and-apps/03-app-backend-extensions.md).

Additional constraints apply:

- They may act only within their app domain.
- They may not modify system services.
- They may not define or alter protocol behavior.
- They must remain removable without affecting system correctness.

App extension services interact with managers only through allowed manager APIs.

## 6. Allowed interactions

### 6.1 Manager to manager interactions

Allowed interactions are limited to:

- Explicit method calls using validated inputs.
- Read-only access to outputs exposed by another manager.
- Dependency ordering defined by initialization sequence.

Managers must not mutate state owned by another manager.

### 6.2 Service to manager interactions

Services may interact with managers as follows:

- Invoke Graph Manager for all graph mutations.
- Invoke Schema Manager for schema validation.
- Invoke ACL Manager for permission checks.
- Invoke Storage Manager for read-only queries where permitted.
- Invoke Event Manager for event publication.
- Invoke Log Manager for logging.

All interactions require a valid OperationContext.

### 6.3 External interactions

Frontend clients and remote peers are external to the component model:

- All external input is treated as untrusted.
- External input enters the system only through Auth Manager, Network Manager, or [service interfaces](../04-interfaces/).
- No external actor interacts directly with managers.

## 7. Forbidden interactions

The following interactions are explicitly forbidden:

- Direct database access outside Storage Manager.
- Graph mutation outside Graph Manager.
- Authorization decisions outside ACL Manager.
- Private key access outside Key Manager.
- Network I O outside Network Manager.
- Sync state mutation outside State Manager.
- Managers depending on services.
- Services calling other services without manager mediation.
- Cross-app data mutation without explicit ACL allowance.

## 8. Trust boundaries

Each component defines a strict trust boundary as detailed in [02-architecture/03-trust-boundaries.md](03-trust-boundaries.md):

- Managers trust only validated inputs from other managers.
- Services trust managers but not external inputs.
- App extension services are untrusted relative to core managers.
- Network Manager treats all inbound peer data as untrusted.
- Auth Manager treats frontend credentials as untrusted until verified.

Trust does not propagate implicitly across components.

## 9. Failure and rejection behavior

### 9.1 Invalid input

If a component receives invalid input:

- The input is rejected.
- No partial state mutation occurs.
- The failure is logged by the Log Manager.
- An error is returned to the caller.
- No implicit retries are performed.

### 9.2 Authorization failure

If authorization fails:

- The operation is rejected by ACL Manager.
- No graph mutation occurs.
- The failure is logged by the Log Manager.
- A permission error is returned.

### 9.3 Storage failure

If a storage operation fails:

- The entire operation is aborted.
- The transaction is rolled back.
- No partial writes occur.
- The failure is logged by the Log Manager.
- The error is surfaced to the caller.

### 9.4 Network failure

If a network operation fails:

- The failure is isolated to Network Manager.
- Local state remains unchanged.
- Sync state is preserved.
- Retry behavior is explicit and bounded.
- The failure is logged by the Log Manager.

### 9.5 Component crash

If a component crashes:

- No other component assumes recovery.
- Persistent state remains authoritative.
- Recovery occurs through process restart.
- In-memory state is discarded.
- The crash is logged by the Log Manager if able.

## 10. Guarantees

This component model guarantees the following:

* Single, deterministic write path for all persistent graph mutations.
* Atomic graph mutations with all-or-nothing commit semantics.
* Centralized enforcement of schema and authorization rules.
* Non-bypassable ownership of database access, keys, transport, sync, events, and logs.
* Strict separation between protocol kernel and domain logic.
* Fixed validation order before mutation and sequencing.
* Monotonic global sequencing of accepted mutations.
* Side effects occur only after successful state mutation.
* One-way dependency flow, managers do not depend on services.
* App extensions are sandboxed to their app domain and manager APIs.
* Apps and extensions can be removed without corrupting system state.
* Explicit and bounded trust relationships between components.
* All external input is treated as untrusted by default.
* No hidden persistence or authority paths.
* Persistent state is sufficient for deterministic recovery.

No other guarantees are implied.
