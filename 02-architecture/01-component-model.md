



# 01 Component model

## 1. Purpose and scope

This document defines the backend component model of the 2WAY system as implemented in the proof of concept (PoC). It specifies component categories, responsibilities, invariants, allowed and forbidden interactions, trust boundaries, and failure behavior.

This document is normative for backend structure and behavior. It does not define APIs, wire formats, schemas, storage layout, or runtime topology except where required to establish component correctness and boundaries. Frontend components are out of scope except as external callers.

## 2. Component model overview

The 2WAY backend is composed of managers and services running within a single long-lived backend process.

Managers form the protocol kernel. They implement all protocol-enforced behavior and invariants.

Services implement domain logic on top of managers. Services never define protocol rules and never bypass managers.

The component model enforces the following system-wide rules:

- All persistent state mutation flows through managers.
- All protocol invariants are enforced by managers, not services.
- Services may coordinate behavior but cannot weaken or override manager guarantees.
- No component accesses another component’s internal state directly.

## 3. Component categories

### 3.1 Managers

Managers are singleton backend components. Each manager owns exactly one conceptual domain and is authoritative for that domain.

Managers are stable, long-lived, and loaded at process startup.

### 3.2 Services

Services are backend components that implement domain-specific workflows.

Two service classes exist:

- System services.
- App extension services.

Both classes use managers exclusively to interact with system state.

## 4. Manager responsibilities and boundaries

### 4.1 Global manager invariants

All managers collectively enforce the following invariants:

- Graph Manager is the only component allowed to mutate graph state.
- Storage Manager is the only component allowed to execute raw database operations.
- Schema Manager is the only component allowed to interpret type and schema definitions.
- ACL Manager is the only component allowed to make authorization decisions.
- Key Manager is the only component allowed to access private key material.
- State Manager is the only component allowed to manage sync state and reconciliation.
- Network Manager is the only component allowed to perform peer communication and transport.
- Event Manager is the only component allowed to publish backend events.
- App Manager is the only component allowed to register, load, and bind apps.
- Auth Manager is the only component allowed to resolve frontend identity and session context.
- Log Manager is the only component allowed to emit structured logs.
- Health Manager is the only component allowed to report system health.
- DoS Guard Manager is the only component allowed to enforce rate limiting and abuse controls.

These invariants are mandatory. Violations invalidate correctness and security guarantees.

### 4.2 Individual manager responsibility domains

Each manager owns a single responsibility domain:

- Config Manager owns runtime configuration loading and access.
- Storage Manager owns SQLite access, transactions, and persistence boundaries.
- Key Manager owns node, user, and app key lifecycle, PEM file storage, signing, and decryption.
- Auth Manager owns frontend authentication, session validation, and identity resolution.
- Schema Manager owns schema objects, type resolution, and schema validation.
- ACL Manager owns authorization evaluation using OperationContext and graph data.
- Graph Manager owns all graph mutations, validation ordering, and global sequence assignment.
- App Manager owns app identity registration, lifecycle, and backend extension loading.
- State Manager owns sync domains, sequence tracking, reconciliation, and conflict handling.
- Network Manager owns transport setup, message exchange, signing verification, and encryption.
- Event Manager owns event publication and subscription.
- Log Manager owns audit, diagnostic, and operational logging.
- Health Manager owns liveness checks and health state reporting.
- DoS Guard Manager owns request throttling and abuse mitigation.

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

Services must supply complete OperationContext to all manager calls.

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

System services are backend services that exist independently of installed apps.

System services:

- Are loaded automatically.
- Define shared social or structural primitives.
- Own their own schema within their app domain.
- May expose stable backend APIs.

System services depend on managers but are not depended on by managers.

### 5.4 App extension services

App extension services are optional backend services tied to a single app identity.

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
- External input enters the system only through Auth Manager, Network Manager, or service interfaces.
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

Each component defines a strict trust boundary:

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
