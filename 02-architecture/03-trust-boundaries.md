



# 03 Trust boundaries

Defines architectural trust boundaries and enforcement requirements for 2WAY. Specifies allowed/forbidden interactions across boundaries and failure handling. Defines boundary invariants that protect validation, authorization, and persistence.

For the meta specifications, see [03-trust-boundaries meta](../10-appendix/meta/02-architecture/03-trust-boundaries-meta.md).

## 1. Trust model and baseline assumptions

The PoC assumes a hostile environment by default.

No component, input source, or peer is trusted unless trust is explicitly established through validated identity, enforced invariants, and ordered execution.

Baseline assumptions:

* All external input is untrusted.
* All internal components interact only through explicit interfaces.
* Trust is never transitive across boundaries.
* Validation, authorization, and sequencing are mandatory before persistence.

## 2. Invariants and guarantees

Across all trust boundaries, the following invariants and guarantees hold:

* All graph mutations pass through [Graph Manager](managers/07-graph-manager.md).
* All authorization decisions pass through [ACL Manager](managers/06-acl-manager.md).
* All schema validation passes through [Schema Manager](managers/05-schema-manager.md).
* All persistence passes through [Storage Manager](managers/02-storage-manager.md).
* All sync behavior passes through [State Manager](managers/09-state-manager.md) per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).
* All network I.O. passes through [Network Manager](managers/10-network-manager.md) per [01-protocol/08-network-transport-requirements.md](../01-protocol/08-network-transport-requirements.md).
* All private key usage is mediated by [Key Manager](managers/03-key-manager.md) per [01-protocol/05-keys-and-identity.md](../01-protocol/05-keys-and-identity.md).
* All write operations are serialized and assigned a monotonic global sequence.

These guarantees must hold regardless of caller identity, app context, service implementation, or remote peer behavior.

## 3. Frontend to backend trust boundary

### 3.1 Trust assumptions

The backend does not trust the frontend.

All frontend-originated input is untrusted, including:

* HTTP requests.
* WebSocket connections.
* App-generated payloads.
* Session tokens and identifiers.

### 3.2 Allowed behaviors

The frontend may:

* Authenticate via [Auth Manager](managers/04-auth-manager.md) mediated APIs.
* Invoke backend APIs exposed by services or managers through [04-interfaces/**](../04-interfaces/).
* Submit envelopes for validation and potential application per [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md).
* Receive events via [Event Manager](managers/11-event-manager.md) over WebSocket ([04-interfaces/02-websocket-events.md](../04-interfaces/02-websocket-events.md)).

### 3.3 Forbidden behaviors

The frontend must not:

* Access backend storage directly.
* Access private key material.
* Call managers directly.
* Bypass schema, ACL, or graph validation enforced by [Schema Manager](managers/05-schema-manager.md), [ACL Manager](managers/06-acl-manager.md), and [Graph Manager](managers/07-graph-manager.md).
* Mutate backend state outside documented APIs.

### 3.4 Failure and rejection behavior

On invalid, malformed, or unauthorized input:

* The request is rejected before any state mutation.
* No partial writes occur.
* No side effects are emitted.

## 4. App to backend trust boundary

### 4.1 Trust assumptions

Apps are not trusted by the backend.

This applies equally to frontend-only apps and apps with app services.

### 4.2 Allowed behaviors

Apps may:

* Declare schemas through the graph.
* Request graph reads and writes through services defined in [02-architecture/services-and-apps/**](services-and-apps/).
* Participate in sync domains as defined by schema and [State Manager](managers/09-state-manager.md).
* Emit app-scoped events via [Event Manager](managers/11-event-manager.md).

### 4.3 Forbidden behaviors

Apps must not:

* Modify protocol behavior.
* Access managers directly.
* Bypass ACL evaluation by [ACL Manager](managers/06-acl-manager.md).
* Bypass schema validation by [Schema Manager](managers/05-schema-manager.md).
* Access raw database connections.
* Access private key material.
* Influence global sequencing or sync ordering.

### 4.4 Failure and rejection behavior

If an app violates backend expectations:

* The operation is rejected.
* No protocol state is modified.
* The violation is contained to the app context.

## 5. Service to manager trust boundary

### 5.1 Trust assumptions

Managers do not trust services.

Services are constrained callers operating above the protocol kernel.

### 5.2 Allowed behaviors

Services may:

* Invoke manager APIs using a valid [OperationContext](services-and-apps/05-operation-context.md).
* Request reads and writes through [Graph Manager](managers/07-graph-manager.md).
* Request authorization decisions through [ACL Manager](managers/06-acl-manager.md).
* Emit events through [Event Manager](managers/11-event-manager.md).
* Log through [Log Manager](managers/12-log-manager.md).

### 5.3 Forbidden behaviors

Services must not:

* Access storage directly.
* Perform cryptographic operations directly.
* Modify manager internal state.
* Circumvent manager ordering or validation guarantees.

### 5.4 Failure and rejection behavior

Managers enforce invariants unconditionally.

If a service violates expectations:

* The request is rejected.
* No state is mutated.
* No partial persistence occurs.

## 6. Manager to storage trust boundary

### 6.1 Trust assumptions

Persistent storage is not trusted to enforce correctness or authorization.

All correctness guarantees are enforced above the storage layer.

### 6.2 Allowed behaviors

Managers may:

* Read and write only via [Storage Manager](managers/02-storage-manager.md).
* Rely on transactional atomicity provided by the storage engine.

### 6.3 Forbidden behaviors

Managers must not:

* Assume storage enforces ACLs, schemas, or ordering.
* Permit any component to access storage directly.

### 6.4 Failure and rejection behavior

On storage failure:

* Transactions are rolled back.
* The operation is considered failed.
* The system remains in a consistent state.

## 7. Local node to remote node trust boundary

### 7.1 Trust assumptions

Remote nodes are untrusted.

No assumptions are made about remote correctness, honesty, availability, or intent.

### 7.2 Allowed behaviors

Remote nodes may:

* Exchange signed and encrypted protocol messages defined in [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md) and [01-protocol/04-cryptography.md](../01-protocol/04-cryptography.md).
* Participate in sync within allowed domains per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).
* Present graph objects and identities for validation.

### 7.3 Forbidden behaviors

Remote nodes must not:

* Bypass local validation.
* Mutate local state without authorization.
* Introduce objects outside allowed domains.
* Rewrite or reorder local history.

### 7.4 Failure and rejection behavior

Inbound remote data is treated as hostile.

On validation or authorization failure:

* Packages are rejected.
* Sync state is not advanced.
* No partial application occurs.

## 8. Network transport trust boundary

### 8.1 Trust assumptions

The transport layer is not trusted.

Confidentiality, integrity, and authenticity are enforced at the protocol layer.

### 8.2 Allowed behaviors

Network Manager may:

* Transmit and receive encrypted payloads.
* Perform peer-level throttling and rate limiting enforced by [DoS Guard Manager](managers/14-dos-guard-manager.md).
* Reject malformed or abusive traffic per [01-protocol/10-errors-and-failure-modes.md](../01-protocol/10-errors-and-failure-modes.md).
* Apply client puzzles under load as defined by [DoS Guard Manager](managers/14-dos-guard-manager.md) and [01-protocol/09-dos-guard-and-client-puzzles.md](../01-protocol/09-dos-guard-and-client-puzzles.md).

### 8.3 Forbidden behaviors

Transport must not:

* Influence protocol semantics.
* Modify envelopes.
* Inject state changes.
* Affect sequencing or authorization decisions.

### 8.4 Failure and rejection behavior

On transport failure:

* Connections may be dropped.
* Backoff or retry may occur.
* Protocol state remains unaffected.

## 9. Rejection, failure, and containment rules

Across all trust boundaries:

* Invalid input is rejected as early as possible.
* Authorization failures do not leak sensitive information.
* No component attempts recovery by bypassing validation.
* Failures are local and contained.

The system fails closed. When a boundary cannot be enforced, the operation is rejected.

## 10. Summary of enforced trust boundaries

The PoC enforces strict trust separation:

* All untrusted input is validated before use.
* No component can escalate privileges across boundaries.
* All state mutation is centralized, ordered, and authorized.
* Sync and network interactions cannot corrupt local state.

These properties are mandatory for correctness and security and must be preserved by any compliant implementation.
