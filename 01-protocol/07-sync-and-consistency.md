



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
- [09-errors-and-failure-modes.md](09-errors-and-failure-modes.md)

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

## 3. Sync model overview

2WAY uses explicit, envelope-based synchronization between peers.

Synchronization is:

- Pull-based and push-based depending on peer role.
- Incremental and stateful.
- Scoped by [sync domain](01-identifiers-and-namespaces.md).
- Strictly ordered per sender.

Nodes never perform full graph replication. Only objects belonging to explicitly shared domains are eligible for sync.

## 4. Unit of synchronization

### 4.1 Envelope

The atomic unit of synchronization is the [envelope](03-serialization-and-envelopes.md).

An envelope contains:

- A single authored operation.
- One or more graph objects produced by that operation.
- Author identity reference ([05-keys-and-identity.md](05-keys-and-identity.md)).
- Domain identifier ([01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).
- Global sequence number assigned by the originating node.
- [Signature](04-cryptography.md) covering the envelope contents.

An envelope is indivisible. Partial acceptance is forbidden.

### 4.2 Object constraints

Objects within an envelope must satisfy all of the following:

- All objects share the same author.
- All objects are created by the same operation.
- All objects belong to the same sync domain.
- All objects are valid according to their [schema](../02-architecture/managers/05-schema-manager.md).

Violation of any constraint causes rejection of the entire envelope.

## 5. Ordering model

### 5.1 Global sequence

Each node assigns a strictly monotonic global sequence number to every envelope it accepts locally (see [03-serialization-and-envelopes.md](03-serialization-and-envelopes.md)).

Properties:

- Global sequence is local to the assigning node.
- Sequence numbers are never reused.
- Sequence numbers define a total order of envelopes on that node.

Global sequence numbers are used exclusively for sync ordering and replay detection (see [09-errors-and-failure-modes.md](09-errors-and-failure-modes.md)).

### 5.2 Domain sequence tracking

For each peer and each domain, the receiving node tracks:

- The highest accepted global sequence value.
- Whether gaps exist in the observed sequence.

Incoming envelopes must advance the known sequence monotonically. Envelopes that would regress or overlap known sequence state are rejected.

## 6. Sync state

### 6.1 Sync state definition

Sync state is maintained per peer and per domain.

Sync state includes:

- Highest accepted global sequence number.
- Known [revocation state](05-keys-and-identity.md) affecting the peer.
- Domain visibility constraints.

Sync state is authoritative for acceptance decisions.

### 6.2 State advancement

Sync state advances only when an envelope is fully accepted and persisted.

Rejected envelopes do not modify sync state.

## 7. Validation and acceptance

### 7.1 Mandatory validation stages

Each incoming envelope must pass, in order:

- [Structural validation](03-serialization-and-envelopes.md) of the envelope.
- [Signature verification](04-cryptography.md) against the author identity.
- [Domain membership](01-identifiers-and-namespaces.md) validation.
- [Schema validation](../02-architecture/managers/05-schema-manager.md) of all objects.
- [Ownership](02-object-model.md) and immutability validation.
- [Access control](06-access-control-model.md) validation.
- [Sequence ordering validation](09-errors-and-failure-modes.md).

Failure at any stage results in rejection.

### 7.2 Acceptance rules

An envelope is accepted if and only if:

- The author identity exists and is not revoked (see [05-keys-and-identity.md](05-keys-and-identity.md)).
- The [signature](04-cryptography.md) is valid.
- The domain is known and permitted for the peer (see [01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).
- All objects are [schema-valid](../02-architecture/managers/05-schema-manager.md).
- The author is permitted to create the objects (see [06-access-control-model.md](06-access-control-model.md)).
- Ownership invariants are preserved (see [02-object-model.md](02-object-model.md)).
- The global sequence advances sync state correctly.

Acceptance is atomic.

### 7.3 Forbidden behaviors

The following behaviors are forbidden and must be rejected:

- Replaying previously accepted [envelopes](03-serialization-and-envelopes.md).
- Introducing gaps or overlaps in declared sequence progression.
- Modifying objects owned by a different identity without [authorization](06-access-control-model.md).
- Creating objects in unauthorized domains (see [01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).
- Mixing objects from multiple domains in one [envelope](03-serialization-and-envelopes.md).
- Referencing unknown or incompatible [schema definitions](../02-architecture/managers/05-schema-manager.md).

## 8. Consistency guarantees

The protocol guarantees:

- Deterministic acceptance or rejection of [envelopes](03-serialization-and-envelopes.md).
- Strict per-sender ordering.
- Replay resistance.
- No partial application of operations.
- Tamper-evident replication.

The protocol does not guarantee:

- Global total ordering across nodes.
- Conflict-free convergence at the application level.
- Automatic reconciliation of concurrent writes.

## 9. Conflict handling

### 9.1 Conflict definition

A conflict occurs when a valid envelope proposes state changes that violate [schema rules](../02-architecture/managers/05-schema-manager.md), [ownership invariants](02-object-model.md), or immutability guarantees when applied to current local state.

### 9.2 Resolution behavior

Conflict resolution is rejection-based.

Rules:

- The first valid envelope accepted is authoritative.
- Conflicting envelopes are rejected.
- No merge or rollback is performed at the protocol level.

Application-level conflict handling is outside the scope of this specification.

## 10. Failure and rejection behavior

### 10.1 Rejection handling

On rejection:

- The envelope is discarded.
- No state changes occur.
- Sync state is not advanced.

Rejection reasons may be logged for audit purposes (see [02-architecture/managers/12-log-manager.md](../02-architecture/managers/12-log-manager.md)).

### 10.2 Peer-level handling

Repeated invalid envelopes from a peer may result in:

- Temporary suspension of sync.
- Increased validation strictness.
- Rate limiting.

These actions are policy decisions and are not mandated by this specification.

## 11. Trust boundaries and interactions

### 11.1 Inputs

Inputs:

- Signed envelopes from peers.
- Local sync state.
- Domain and [schema definitions](../02-architecture/managers/05-schema-manager.md).

### 11.2 Outputs

Outputs:

- Accepted envelopes persisted to [storage](../03-data/01-sqlite-layout.md).
- Updated sync state.
- Explicit acceptance or rejection outcomes.

### 11.3 Trust assumptions

Assumptions:

- Peers are untrusted.
- [Transport](08-network-transport-requirements.md) is untrusted.
- Local validation and storage components are trusted.

No peer-provided data is trusted without validation.

## 12. Invariants

The following invariants must always hold:

- Envelopes are immutable after acceptance.
- Global sequence numbers strictly increase per node.
- Sync state never regresses.
- Ownership and immutability rules are never bypassed.
- Partial acceptance never occurs.

Violation of any invariant indicates a fatal implementation error.
