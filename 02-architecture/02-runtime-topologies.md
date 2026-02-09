



# 02 Runtime topologies

Defines permitted runtime arrangements for 2WAY nodes and their trust boundaries. Specifies component placement, allowed interactions, and failure behavior per topology. Defines invariants that must hold across all runtime configurations.

For the meta specifications, see [02-runtime-topologies meta](../10-appendix/meta/02-architecture/02-runtime-topologies-meta.md).

## 1. Invariants and guarantees

Across all runtime topologies, the following invariants and guarantees hold:

- Exactly one backend instance owns the authoritative Graph Manager for a node.
- All graph writes occur exclusively via the [Graph Manager](managers/07-graph-manager.md).
- All ACL decisions are enforced exclusively by the [ACL Manager](managers/06-acl-manager.md).
- All schema validation is enforced by the [Schema Manager](managers/05-schema-manager.md).
- All persistent state is written only through the [Storage Manager](managers/02-storage-manager.md).
- All private keys remain local to the backend and are owned by the [Key Manager](managers/03-key-manager.md).
- All network ingress and egress occurs through the [Network Manager](managers/10-network-manager.md).
- Frontend apps never execute backend logic directly.
- Backend services and extensions never bypass managers.
- Local state correctness is independent of network availability.

These guarantees must hold regardless of process layout, frontend presence, or network conditions.

## 2. Runtime topology model

A runtime topology is defined by:

- Backend process composition.
- Frontend attachment model.
- Storage and key locality.
- Network participation state.

All conforming implementations must match one of the defined topologies or be a strict specialization that preserves all invariants.

## 3. Integrated single-process topology

### 3.1 Description

The backend runs as a single long-lived process hosting all managers and services. Frontend apps execute locally and communicate with the backend over local HTTP ([04-interfaces/01-local-http-api.md](../04-interfaces/01-local-http-api.md)) and WebSocket ([04-interfaces/02-websocket-events.md](../04-interfaces/02-websocket-events.md)) interfaces.

### 3.2 Component placement

- Backend managers. Single process.
- System services. Same process as managers.
- App extension services. Same process as managers.
- Storage. Local SQLite database owned by [Storage Manager](managers/02-storage-manager.md).
- Key material. Local filesystem owned by [Key Manager](managers/03-key-manager.md).
- Frontend apps. Local browser or UI process.

### 3.3 Trust boundaries

- Strong trust boundary between frontend environment and backend process.
- No trust is placed in frontend input beyond authenticated identity and app context.
- No trust is placed in remote peers.

### 3.4 Allowed interactions

- Frontend apps invoke backend APIs through the local HTTP interface.
- Backend emits events to frontend clients through WebSocket.
- Backend initiates outbound network communication via [Network Manager](managers/10-network-manager.md).
- Backend performs autonomous sync and maintenance tasks.

### 3.5 Forbidden interactions

- Frontend apps accessing backend storage or keys directly.
- Frontend apps invoking managers or services without API mediation.
- App extension services accessing SQLite or key files directly.
- Any component bypassing Graph Manager for graph mutation.

### 3.6 Failure behavior

- Backend process failure halts all backend functionality.
- Frontend failure does not corrupt backend state.
- Network failure does not affect local graph correctness or availability.

## 4. Split frontend-backend topology

### 4.1 Description

The backend runs as a standalone local service. Frontend apps run in a separate process or device and communicate with the backend over authenticated local HTTP ([04-interfaces/01-local-http-api.md](../04-interfaces/01-local-http-api.md)) and WebSocket ([04-interfaces/02-websocket-events.md](../04-interfaces/02-websocket-events.md)) interfaces.

### 4.2 Component placement

- Backend managers and services. Dedicated backend process.
- Storage and keys. Backend host only.
- Frontend apps. Separate process or device.

### 4.3 Trust boundaries

- Strong trust boundary between frontend environment and backend host.
- Backend treats frontend as an untrusted client.
- Backend remains the sole authority for identity, state, and permissions.

### 4.4 Allowed interactions

- Frontend invokes backend APIs with authenticated sessions.
- Backend emits events to connected frontend clients.
- Backend participates in peer sync independently of frontend presence.

### 4.5 Forbidden interactions

- Frontend modifying backend configuration or state outside defined APIs.
- Frontend injecting executable logic into backend runtime.
- Backend delegating ACL, schema, or validation decisions to frontend handled by [ACL Manager](managers/06-acl-manager.md) and [Schema Manager](managers/05-schema-manager.md).

### 4.6 Failure behavior

- Frontend disconnection does not affect backend state.
- Backend restart invalidates frontend sessions.
- Network partitions do not affect local state integrity.

## 5. Headless backend topology

### 5.1 Description

The backend runs without any attached frontend clients. It maintains local state, performs sync, and enforces policy autonomously as described in [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).

### 5.2 Component placement

- Backend managers and services. Single process.
- No frontend apps attached.
- [Network Manager](managers/10-network-manager.md) active.

### 5.3 Trust boundaries

- All inbound data originates from untrusted remote peers.
- No user interaction is assumed.

### 5.4 Allowed interactions

- Peer-to-peer sync via [Network Manager](managers/10-network-manager.md).
- Administrative access through authenticated backend interfaces.

### 5.5 Forbidden interactions

- Assumption of interactive workflows.
- Frontend-specific session state.

### 5.6 Failure behavior

- Peer failure is isolated by sync state and rate limits.
- Backend failure halts sync but preserves durable state.

## 6. Multi-device topology

### 6.1 Description

Multiple backend nodes represent the same user identity on different devices. Each node maintains its own local graph and syncs with peers according to [State Manager](managers/09-state-manager.md) rules and [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).

### 6.2 Component placement

- One backend per device.
- Each backend holds independent storage and keys.
- Frontend apps attach locally to each backend.

### 6.3 Trust boundaries

- No implicit trust between devices.
- All trust is expressed through graph structure, keys, and ACLs.

### 6.4 Allowed interactions

- Device-to-device sync via [Network Manager](managers/10-network-manager.md).
- Independent local operation when offline.

### 6.5 Forbidden interactions

- Direct sharing of databases or key material between devices.
- State convergence outside defined sync protocols.

### 6.6 Failure behavior

- Loss or compromise of one device does not affect others.
- Conflicts are resolved through defined conflict resolution flows.

## 7. Remote peer topology

### 7.1 Description

Nodes communicate with untrusted remote peers for domain-scoped synchronization of graph state as defined in [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).

### 7.2 Component placement

- Each peer runs an independent backend instance.
- No shared execution context or storage.

### 7.3 Trust boundaries

- Strong cryptographic boundary between nodes as defined in [01-protocol/04-cryptography.md](../01-protocol/04-cryptography.md).
- No assumption of peer honesty, availability, or correctness.

### 7.4 Allowed interactions

- Signed and optionally encrypted envelope exchange as defined in [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md) and [01-protocol/04-cryptography.md](../01-protocol/04-cryptography.md).
- Capability negotiation and domain-scoped sync as defined in [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).

### 7.5 Forbidden interactions

- Remote execution of local code.
- Remote mutation of local state outside accepted envelopes.
- Implicit trust based on network reachability.

### 7.6 Failure behavior

- Invalid, replayed, or unauthorized envelopes are rejected as defined in [01-protocol/10-errors-and-failure-modes.md](../01-protocol/10-errors-and-failure-modes.md).
- Peer misbehavior does not corrupt local state.

## 8. Cross-topology constraints

Across all runtime topologies:

- [Graph Manager](managers/07-graph-manager.md) remains the single write authority.
- [Storage Manager](managers/02-storage-manager.md) remains the sole database access path.
- [Key Manager](managers/03-key-manager.md) remains the sole owner of private keys.
- [Network Manager](managers/10-network-manager.md) remains the sole network interface.
- Managers enforce identical semantics regardless of topology.

Any runtime arrangement that violates these constraints is non-conforming.

## 9. Rejection and invalid input handling

- Requests crossing an invalid trust boundary are rejected per [02-architecture/03-trust-boundaries.md](03-trust-boundaries.md).
- Requests violating topology constraints are rejected before state mutation.
- Rejections do not modify persistent state.
- Rejected inputs may be logged but must not trigger side effects.
