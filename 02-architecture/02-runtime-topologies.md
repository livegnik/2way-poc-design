



# 02 Runtime topologies

## 1. Purpose and scope

This document defines the valid runtime topologies for a 2WAY node as specified by the PoC build guide. It describes how backend managers, services, frontend apps, storage, keys, and network components are arranged and interact at runtime. It specifies trust boundaries, allowed and forbidden interactions, and required failure behavior. It does not define deployment tooling, packaging, orchestration, scaling, or operational automation.

This overview references:

* [01-protocol/**](../01-protocol/)
* [02-architecture/00-architecture-overview.md](00-architecture-overview.md)
* [02-architecture/01-component-model.md](01-component-model.md)
* [02-architecture/03-trust-boundaries.md](03-trust-boundaries.md)
* [02-architecture/04-data-flow-overview.md](04-data-flow-overview.md)
* [02-architecture/managers/**](managers/)
* [02-architecture/services-and-apps/**](services-and-apps/)
* [04-interfaces/**](../04-interfaces/)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

- Permitted runtime arrangements of backend managers, system services, app extension services, frontend apps, and network components defined in [01-component-model.md](01-component-model.md) and [02-architecture/services-and-apps/**](services-and-apps/).
- Trust boundaries between backend, frontend, local storage, and remote peers as defined in [02-architecture/03-trust-boundaries.md](03-trust-boundaries.md).
- Mandatory interaction paths between runtime components aligned to [02-architecture/04-data-flow-overview.md](04-data-flow-overview.md).
- Runtime behavior under failure, rejection, or partial availability.

This specification does not cover the following:

- Container boundaries or operating system isolation.
- High availability, clustering, or replication strategies.
- Load balancing or horizontal scaling.
- User interface composition or frontend framework choices.
- Transport implementation details beyond manager responsibilities.

## 3. Invariants and guarantees

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

## 4. Runtime topology model

A runtime topology is defined by:

- Backend process composition.
- Frontend attachment model.
- Storage and key locality.
- Network participation state.

All conforming implementations must match one of the defined topologies or be a strict specialization that preserves all invariants.

## 5. Integrated single-process topology

### 5.1 Description

The backend runs as a single long-lived process hosting all managers and services. Frontend apps execute locally and communicate with the backend over local HTTP ([04-interfaces/01-local-http-api.md](../04-interfaces/01-local-http-api.md)) and WebSocket ([04-interfaces/02-websocket-events.md](../04-interfaces/02-websocket-events.md)) interfaces.

### 5.2 Component placement

- Backend managers. Single process.
- System services. Same process as managers.
- App extension services. Same process as managers.
- Storage. Local SQLite database owned by [Storage Manager](managers/02-storage-manager.md).
- Key material. Local filesystem owned by [Key Manager](managers/03-key-manager.md).
- Frontend apps. Local browser or UI process.

### 5.3 Trust boundaries

- Strong trust boundary between frontend environment and backend process.
- No trust is placed in frontend input beyond authenticated identity and app context.
- No trust is placed in remote peers.

### 5.4 Allowed interactions

- Frontend apps invoke backend APIs through the local HTTP interface.
- Backend emits events to frontend clients through WebSocket.
- Backend initiates outbound network communication via [Network Manager](managers/10-network-manager.md).
- Backend performs autonomous sync and maintenance tasks.

### 5.5 Forbidden interactions

- Frontend apps accessing backend storage or keys directly.
- Frontend apps invoking managers or services without API mediation.
- App extension services accessing SQLite or key files directly.
- Any component bypassing Graph Manager for graph mutation.

### 5.6 Failure behavior

- Backend process failure halts all backend functionality.
- Frontend failure does not corrupt backend state.
- Network failure does not affect local graph correctness or availability.

## 6. Split frontend-backend topology

### 6.1 Description

The backend runs as a standalone local service. Frontend apps run in a separate process or device and communicate with the backend over authenticated local HTTP ([04-interfaces/01-local-http-api.md](../04-interfaces/01-local-http-api.md)) and WebSocket ([04-interfaces/02-websocket-events.md](../04-interfaces/02-websocket-events.md)) interfaces.

### 6.2 Component placement

- Backend managers and services. Dedicated backend process.
- Storage and keys. Backend host only.
- Frontend apps. Separate process or device.

### 6.3 Trust boundaries

- Strong trust boundary between frontend environment and backend host.
- Backend treats frontend as an untrusted client.
- Backend remains the sole authority for identity, state, and permissions.

### 6.4 Allowed interactions

- Frontend invokes backend APIs with authenticated sessions.
- Backend emits events to connected frontend clients.
- Backend participates in peer sync independently of frontend presence.

### 6.5 Forbidden interactions

- Frontend modifying backend configuration or state outside defined APIs.
- Frontend injecting executable logic into backend runtime.
- Backend delegating ACL, schema, or validation decisions to frontend handled by [ACL Manager](managers/06-acl-manager.md) and [Schema Manager](managers/05-schema-manager.md).

### 6.6 Failure behavior

- Frontend disconnection does not affect backend state.
- Backend restart invalidates frontend sessions.
- Network partitions do not affect local state integrity.

## 7. Headless backend topology

### 7.1 Description

The backend runs without any attached frontend clients. It maintains local state, performs sync, and enforces policy autonomously as described in [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).

### 7.2 Component placement

- Backend managers and services. Single process.
- No frontend apps attached.
- [Network Manager](managers/10-network-manager.md) active.

### 7.3 Trust boundaries

- All inbound data originates from untrusted remote peers.
- No user interaction is assumed.

### 7.4 Allowed interactions

- Peer-to-peer sync via [Network Manager](managers/10-network-manager.md).
- Administrative access through authenticated backend interfaces.

### 7.5 Forbidden interactions

- Assumption of interactive workflows.
- Frontend-specific session state.

### 7.6 Failure behavior

- Peer failure is isolated by sync state and rate limits.
- Backend failure halts sync but preserves durable state.

## 8. Multi-device topology

### 8.1 Description

Multiple backend nodes represent the same user identity on different devices. Each node maintains its own local graph and syncs with peers according to [State Manager](managers/09-state-manager.md) rules and [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).

### 8.2 Component placement

- One backend per device.
- Each backend holds independent storage and keys.
- Frontend apps attach locally to each backend.

### 8.3 Trust boundaries

- No implicit trust between devices.
- All trust is expressed through graph structure, keys, and ACLs.

### 8.4 Allowed interactions

- Device-to-device sync via [Network Manager](managers/10-network-manager.md).
- Independent local operation when offline.

### 8.5 Forbidden interactions

- Direct sharing of databases or key material between devices.
- State convergence outside defined sync protocols.

### 8.6 Failure behavior

- Loss or compromise of one device does not affect others.
- Conflicts are resolved through defined conflict resolution flows.

## 9. Remote peer topology

### 9.1 Description

Nodes communicate with untrusted remote peers for domain-scoped synchronization of graph state as defined in [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).

### 9.2 Component placement

- Each peer runs an independent backend instance.
- No shared execution context or storage.

### 9.3 Trust boundaries

- Strong cryptographic boundary between nodes as defined in [01-protocol/04-cryptography.md](../01-protocol/04-cryptography.md).
- No assumption of peer honesty, availability, or correctness.

### 9.4 Allowed interactions

- Signed and optionally encrypted envelope exchange as defined in [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md) and [01-protocol/04-cryptography.md](../01-protocol/04-cryptography.md).
- Capability negotiation and domain-scoped sync as defined in [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).

### 9.5 Forbidden interactions

- Remote execution of local code.
- Remote mutation of local state outside accepted envelopes.
- Implicit trust based on network reachability.

### 9.6 Failure behavior

- Invalid, replayed, or unauthorized envelopes are rejected as defined in [01-protocol/09-errors-and-failure-modes.md](../01-protocol/09-errors-and-failure-modes.md).
- Peer misbehavior does not corrupt local state.

## 10. Cross-topology constraints

Across all runtime topologies:

- [Graph Manager](managers/07-graph-manager.md) remains the single write authority.
- [Storage Manager](managers/02-storage-manager.md) remains the sole database access path.
- [Key Manager](managers/03-key-manager.md) remains the sole owner of private keys.
- [Network Manager](managers/10-network-manager.md) remains the sole network interface.
- Managers enforce identical semantics regardless of topology.

Any runtime arrangement that violates these constraints is non-conforming.

## 11. Rejection and invalid input handling

- Requests crossing an invalid trust boundary are rejected per [02-architecture/03-trust-boundaries.md](03-trust-boundaries.md).
- Requests violating topology constraints are rejected before state mutation.
- Rejections do not modify persistent state.
- Rejected inputs may be logged but must not trigger side effects.
