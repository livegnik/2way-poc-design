



# 07 Sync and consistency

## 1. Purpose and scope

This document defines the protocol-level synchronization and consistency rules for 2WAY. It specifies how graph state is exchanged between peers, how ordering and integrity are enforced, and which guarantees are provided. It is limited to protocol semantics. It does not define transport mechanisms, cryptographic primitives, access control rules, or storage internals beyond what is required for correctness of sync.


## 2. Responsibilities

This specification defines:

- The unit of synchronization.
- The ordering model used during replication.
- The rules for sync state tracking.
- Acceptance and rejection criteria for incoming data.
- Consistency and replay protection guarantees.
- Failure and rejection behavior during sync.

This specification does not define:

- Network transport selection or peer discovery.
- Encryption algorithms or key derivation.
- Access control semantics or ACL evaluation logic.
- Application-level meaning of graph objects.
- Conflict resolution beyond protocol-level rejection.
- Storage engine layout or indexing strategy.

## 3. Sync model overview

2WAY uses explicit, envelope-based synchronization between peers.

Synchronization is:

- Pull-based and push-based depending on peer role.
- Incremental and stateful.
- Scoped by sync domain.
- Strictly ordered per sender.

Nodes never perform full graph replication. Only objects belonging to explicitly shared domains are eligible for sync.

## 4. Unit of synchronization

### 4.1 Envelope

The atomic unit of synchronization is the envelope.

An envelope contains:

- A single authored operation.
- One or more graph objects produced by that operation.
- Author identity reference.
- Domain identifier.
- Global sequence number assigned by the originating node.
- Signature covering the envelope contents.

An envelope is indivisible. Partial acceptance is forbidden.

### 4.2 Object constraints

Objects within an envelope must satisfy all of the following:

- All objects share the same author.
- All objects are created by the same operation.
- All objects belong to the same sync domain.
- All objects are valid according to their schema.

Violation of any constraint causes rejection of the entire envelope.

## 5. Ordering model

### 5.1 Global sequence

Each node assigns a strictly monotonic global sequence number to every envelope it accepts locally.

Properties:

- Global sequence is local to the assigning node.
- Sequence numbers are never reused.
- Sequence numbers define a total order of envelopes on that node.

Global sequence numbers are used exclusively for sync ordering and replay detection.

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
- Known revocation state affecting the peer.
- Domain visibility constraints.

Sync state is authoritative for acceptance decisions.

### 6.2 State advancement

Sync state advances only when an envelope is fully accepted and persisted.

Rejected envelopes do not modify sync state.

## 7. Validation and acceptance

### 7.1 Mandatory validation stages

Each incoming envelope must pass, in order:

- Structural validation of the envelope.
- Signature verification against the author identity.
- Domain membership validation.
- Schema validation of all objects.
- Ownership and immutability validation.
- Access control validation.
- Sequence ordering validation.

Failure at any stage results in rejection.

### 7.2 Acceptance rules

An envelope is accepted if and only if:

- The author identity exists and is not revoked.
- The signature is valid.
- The domain is known and permitted for the peer.
- All objects are schema-valid.
- The author is permitted to create the objects.
- Ownership invariants are preserved.
- The global sequence advances sync state correctly.

Acceptance is atomic.

### 7.3 Forbidden behaviors

The following behaviors are forbidden and must be rejected:

- Replaying previously accepted envelopes.
- Introducing gaps or overlaps in declared sequence progression.
- Modifying objects owned by a different identity without authorization.
- Creating objects in unauthorized domains.
- Mixing objects from multiple domains in one envelope.
- Referencing unknown or incompatible schema definitions.

## 8. Consistency guarantees

The protocol guarantees:

- Deterministic acceptance or rejection of envelopes.
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

A conflict occurs when a valid envelope proposes state changes that violate schema rules, ownership invariants, or immutability guarantees when applied to current local state.

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

Rejection reasons may be logged for audit purposes.

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
- Domain and schema definitions.

### 11.2 Outputs

Outputs:

- Accepted envelopes persisted to storage.
- Updated sync state.
- Explicit acceptance or rejection outcomes.

### 11.3 Trust assumptions

Assumptions:

- Peers are untrusted.
- Transport is untrusted.
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
