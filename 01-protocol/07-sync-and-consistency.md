



# 07 Sync and consistency

Defines synchronization units, ordering rules, and validation requirements for 2WAY replication. Specifies sync state tracking, acceptance criteria, and rejection behavior for envelopes. Defines consistency guarantees, conflict handling, and invariants during sync.

For the meta specifications, see [07-sync-and-consistency meta](../10-appendix/meta/01-protocol/07-sync-and-consistency-meta.md).

## 1. Sync model overview

2WAY uses explicit, envelope-based synchronization between peers.

Synchronization is:

- Pull-based and push-based depending on peer role.
- Incremental and stateful.
- Scoped by [sync domain](01-identifiers-and-namespaces.md).
- Strictly ordered per sender.

Nodes never perform full graph replication. Only objects belonging to explicitly shared domains are eligible for sync.

## 2. Unit of synchronization

### 2.1 Sync package envelope

The atomic unit of synchronization is the sync package envelope defined in [03-serialization-and-envelopes.md](03-serialization-and-envelopes.md). It carries a graph message envelope plus sync metadata.

A sync package envelope contains:

- A graph message envelope with one or more operations.
- `sender_identity` identifying the sending node ([05-keys-and-identity.md](05-keys-and-identity.md)).
- `sync_domain`, `from_seq`, and `to_seq` metadata used for ordering and replay protection.
- A [signature](04-cryptography.md) covering the sync package contents.

An envelope is indivisible. Partial acceptance is forbidden.

### 2.2 Object constraints

Objects within an envelope must satisfy all of the following:

- All operations share the same `owner_identity` and `app_id`.
- All objects are created by the same operation batch.
- All objects belong to the same sync domain.
- All objects are valid according to their [schema](../02-architecture/managers/05-schema-manager.md).

Violation of any constraint causes rejection of the entire envelope.

## 3. Ordering model

### 3.1 Global sequence

Each node assigns a strictly monotonic global sequence number to every envelope it accepts locally (see [03-serialization-and-envelopes.md](03-serialization-and-envelopes.md)).

Properties:

- Global sequence is local to the assigning node.
- Sequence numbers are never reused.
- Sequence numbers define a total order of envelopes on that node.

Global sequence numbers are used exclusively for sync ordering and replay detection (see [10-errors-and-failure-modes.md](10-errors-and-failure-modes.md)).

### 3.2 Domain sequence tracking

For each peer and each domain, the receiving node tracks:

- The highest accepted global sequence value.
- Whether gaps exist in the observed sequence.

Incoming sync packages must advance the sender's global sequence monotonically using `from_seq` and `to_seq`. Packages that would regress or overlap known sequence state are rejected.

## 4. Sync state

### 4.1 Sync state definition

Sync state is maintained per peer and per domain.

Sync state includes:

- Highest accepted global sequence number.
- Known [revocation state](05-keys-and-identity.md) affecting the peer.
- Domain visibility constraints.

Sync state is authoritative for acceptance decisions.

### 4.2 State advancement

Sync state advances only when an envelope is fully accepted and persisted.

Rejected envelopes do not modify sync state.

## 5. Validation and acceptance

### 5.1 Mandatory validation stages

Each incoming envelope must pass, in order:

- [Structural validation](03-serialization-and-envelopes.md) of the sync package envelope.
- [Signature verification](04-cryptography.md) against `sender_identity`.
- [Sequence ordering validation](10-errors-and-failure-modes.md) using `from_seq` and `to_seq` against sync_state.
- [Structural validation](03-serialization-and-envelopes.md) of the inner graph message envelope.
- [Domain membership](01-identifiers-and-namespaces.md) validation.
- [Schema validation](../02-architecture/managers/05-schema-manager.md) of all objects.
- [Ownership](02-object-model.md) and immutability validation.
- [Access control](06-access-control-model.md) validation.

Failure at any stage results in rejection.

### 5.2 Acceptance rules

An envelope is accepted if and only if:

- The sender identity exists and is not revoked (see [05-keys-and-identity.md](05-keys-and-identity.md)).
- The [signature](04-cryptography.md) is valid for the sync package.
- The domain is known and permitted for the peer (see [01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).
- All objects are [schema-valid](../02-architecture/managers/05-schema-manager.md).
- The author (operation `owner_identity`) is permitted to create the objects (see [06-access-control-model.md](06-access-control-model.md)).
- Ownership invariants are preserved (see [02-object-model.md](02-object-model.md)).
- The global sequence advances sync state correctly.

Acceptance is atomic.

### 5.3 Forbidden behaviors

The following behaviors are forbidden and must be rejected:

- Replaying previously accepted [envelopes](03-serialization-and-envelopes.md).
- Introducing gaps or overlaps in declared sequence progression.
- Modifying objects owned by a different identity without [authorization](06-access-control-model.md).
- Creating objects in unauthorized domains (see [01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).
- Mixing objects from multiple domains in one [envelope](03-serialization-and-envelopes.md).
- Referencing unknown or incompatible [schema definitions](../02-architecture/managers/05-schema-manager.md).

## 6. Consistency guarantees

The protocol guarantees:

- Deterministic acceptance or rejection of [envelopes](03-serialization-and-envelopes.md).
- Strict per-sender ordering.
- Replay resistance.
- No partial application of operations.
- Tamper-evident replication.

## 7. Conflict handling

### 7.1 Conflict definition

A conflict occurs when a valid envelope proposes state changes that violate [schema rules](../02-architecture/managers/05-schema-manager.md), [ownership invariants](02-object-model.md), or immutability guarantees when applied to current local state.

### 7.2 Resolution behavior

Conflict resolution is rejection-based.

Rules:

- The first valid envelope accepted is authoritative.
- Conflicting envelopes are rejected.
- No merge or rollback is performed at the protocol level.

Application-level conflict handling is defined by app and flow specifications layered above protocol sync rules.

## 8. Failure and rejection behavior

### 8.1 Rejection handling

On rejection:

- The envelope is discarded.
- No state changes occur.
- Sync state is not advanced.

Rejection reasons may be logged for audit purposes (see [02-architecture/managers/12-log-manager.md](../02-architecture/managers/12-log-manager.md)).

### 8.2 Peer-level handling

Repeated invalid envelopes from a peer may result in:

- Temporary suspension of sync.
- Increased validation strictness.
- Rate limiting.

## 9. Trust boundaries and interactions

### 9.1 Inputs

Inputs:

- Signed envelopes from peers.
- Local sync state.
- Domain and [schema definitions](../02-architecture/managers/05-schema-manager.md).

### 9.2 Outputs

Outputs:

- Accepted envelopes persisted to [storage](../03-data/01-sqlite-layout.md).
- Updated sync state.
- Explicit acceptance or rejection outcomes.

### 9.3 Trust assumptions

Assumptions:

- Peers are untrusted.
- [Transport](08-network-transport-requirements.md) is untrusted.
- Local validation and storage components are trusted.

No peer-provided data is trusted without validation.

## 10. Invariants

The following invariants must always hold:

- Envelopes are immutable after acceptance.
- Global sequence numbers strictly increase per node.
- Sync state never regresses.
- Ownership and immutability rules are never bypassed.
- Partial acceptance never occurs.

Violation of any invariant indicates a fatal implementation error.
