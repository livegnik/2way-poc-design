



# 07 Sync and consistency

## 1. Purpose and scope

This document defines the protocol-level synchronization and consistency rules for 2WAY. It specifies how [graph state](../02-architecture/managers/07-graph-manager.md) is exchanged between peers, how ordering and integrity are enforced, and which guarantees are provided. It is limited to protocol semantics. It does not define transport mechanisms, cryptographic primitives, [access control](06-access-control-model.md) rules, or [storage internals](../03-data/01-sqlite-layout.md) beyond what is required for correctness of sync.

This specification references:

- [01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)
- [02-object-model.md](02-object-model.md)
- [03-serialization-and-envelopes.md](03-serialization-and-envelopes.md)
- [04-cryptography.md](04-cryptography.md)
- [05-keys-and-identity.md](05-keys-and-identity.md)
- [06-access-control-model.md](06-access-control-model.md)
- [10-errors-and-failure-modes.md](10-errors-and-failure-modes.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

- The unit of synchronization.
- The ordering model used during replication.
- The rules for sync state tracking.
- Acceptance and rejection criteria for incoming data.
- Consistency and replay protection guarantees.
- Failure and rejection behavior during sync.

This specification does not cover the following:

- Network transport selection or peer discovery (see [08-network-transport-requirements.md](08-network-transport-requirements.md)).
- Encryption algorithms or key derivation (see [04-cryptography.md](04-cryptography.md)).
- [Access control](06-access-control-model.md) semantics or ACL evaluation logic.
- [Application-level meaning of graph objects](02-object-model.md).
- Conflict resolution beyond protocol-level rejection.
- Storage engine layout or indexing strategy (see [03-data/01-sqlite-layout.md](../03-data/01-sqlite-layout.md)).

## 3. Consistency guarantees

The protocol does not guarantee:

- Global total ordering across nodes.
- Conflict-free convergence at the application level.
- Automatic reconciliation of concurrent writes.

### 4. Peer-level handling

These actions are policy decisions and are not mandated by this specification.
