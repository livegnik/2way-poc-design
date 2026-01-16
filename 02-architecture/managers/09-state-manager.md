



# 09 State Manager

## 1. Purpose and scope

This document specifies the State Manager component within the 2WAY architecture. The State Manager is responsible for maintaining authoritative local state progression, coordinating accepted graph mutations, enforcing deterministic ordering guarantees, tracking synchronization progress with peers, and ensuring durability and recoverability of all state transitions required by the protocol.

The State Manager acts as the single coordination layer between Graph Manager, Network Manager, and Storage Manager for all stateful operations that affect protocol-visible progression. It does not author graph mutations, perform cryptographic validation, or apply access control decisions. It ensures that only fully verified, correctly ordered, and durably persisted state transitions are exposed to internal components or propagated to peers.

This specification defines state ownership, internal engines and phases, ordering rules, sync metadata handling, startup and shutdown behavior, failure handling, and explicit trust boundaries. It is an architectural specification, not an implementation.

This specification references:

* [01-protocol/**](../../01-protocol/)
* [02-architecture/00-architecture-overview.md](../00-architecture-overview.md)
* [02-architecture/01-component-model.md](../01-component-model.md)
* [02-architecture/02-runtime-topologies.md](../02-runtime-topologies.md)
* [02-architecture/03-trust-boundaries.md](../03-trust-boundaries.md)
* [02-architecture/04-data-flow-overview.md](../04-data-flow-overview.md)
* [02-architecture/managers/**](../managers/)
* [02-architecture/services-and-apps/**](../services-and-apps/)

This specification consumes the protocol contracts defined in:

* [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md)
* [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md)
* [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md)
* [01-protocol/11-dos-guard-and-client-puzzles.md](../../01-protocol/11-dos-guard-and-client-puzzles.md)

Those files remain normative for all behaviors described here.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Maintaining authoritative local state progression metadata derived from committed graph operations defined in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* Tracking per-peer and per-domain synchronization state, including sequence position, gaps, suspension flags, and visibility eligibility, exactly as defined in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Coordinating inbound remote envelopes after [Network Manager](10-network-manager.md) verification and before [Graph Manager](07-graph-manager.md) application, preserving the envelope guarantees in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Coordinating outbound sync package construction strictly from committed state using the sync package format from [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Enforcing deterministic ordering, monotonicity, and replay protection for all state transitions, mirroring [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Persisting and recovering state metadata and sync checkpoints via [Storage Manager](02-storage-manager.md) so durability guarantees expected by [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) are upheld.
* Providing read-only state views required for internal coordination and observability.
* Managing startup reconstruction and shutdown flushing of state.
* Failing closed when ordering, durability, or integrity guarantees cannot be met.

This specification does not cover the following:

* Cryptographic verification, encryption, signing, or identity resolution, which are governed by [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md) and upstream managers.
* Schema validation, semantic validation, or authorization decisions.
* Direct mutation of canonical graph objects.
* Network transport, peer discovery, or routing, which are governed by the requirements in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).
* DoS mitigation, client puzzles, or connection throttling, which are defined for [Network Manager](10-network-manager.md) and [DoS Guard Manager](14-dos-guard-manager.md) in [01-protocol/11-dos-guard-and-client-puzzles.md](../../01-protocol/11-dos-guard-and-client-puzzles.md).
* Application-specific logic or derived analytics.
* Storage engine implementation details beyond required persistence contracts.

## 3. State domain and ownership

### 3.1 Canonical graph state relationship

Canonical graph state consists of objects defined by the protocol object model in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md), including Parents, Attributes, Edges, Ratings, and ACLs, together with immutable commit metadata such as node-local `global_seq` identifiers, author identity, and domain attribution.

Graph Manager is the sole component permitted to mutate canonical graph state. The State Manager never writes graph objects directly. Instead, it observes commit notifications and persistence confirmations in order to maintain authoritative progression metadata and to gate synchronization behavior.

### 3.2 State metadata owned by State Manager

The State Manager owns and persists the following categories of state metadata defined for sync decisions in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md):

* Local commit height and commit checkpoints.
* Per-peer and per-domain sync state.
* Inbound and outbound sequence markers.
* Gap detection and suspension flags.
* Domain visibility and export eligibility markers.
* Recovery markers indicating last safe state.

This metadata is authoritative and must be consistent with persisted graph state at all times.

### 3.3 Derived and transient structures

The State Manager may maintain derived or transient structures such as:

* Per-peer inbound queues.
* Per-peer outbound backlog indexes.
* Snapshot indices for read-only queries.

All such structures must be derived exclusively from persisted canonical state and persisted metadata defined by the protocol documents. They must be fully reconstructible during startup and must not introduce new authoritative state.

## 4. Internal engines and execution phases

All engines operate on graph message envelopes and sync packages defined in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md), and on sync metadata rules in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).

### 4.1 State Engine

The State Engine is the core coordination engine responsible for:

* Observing commit events from Graph Manager.
* Updating local progression metadata.
* Managing derived state surfaces.
* Enforcing global invariants.

It operates serially with respect to state mutations and never allows concurrent writers. [OperationContext](../services-and-apps/05-operation-context.md) instances it raises for [Graph Manager](07-graph-manager.md) must follow the remote invocation shape defined in Section 9.4 of [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).

### 4.2 Sync Engine

The Sync Engine is responsible for:

* Validating inbound sync package metadata.
* Managing per-peer sync progression.
* Constructing outbound sync packages.
* Enforcing ordering and visibility rules.

The Sync Engine does not apply graph mutations directly and never bypasses the State Engine. Its acceptance rules and per-peer progression tracking are identical to the invariants defined in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).

### 4.3 Recovery Engine

The Recovery Engine is responsible for:

* Startup reconstruction from persisted storage.
* Validation of metadata consistency.
* Detection of irrecoverable divergence.
* Controlled fail-fast behavior when invariants are violated.

It verifies that persisted metadata and [Storage Manager](02-storage-manager.md) checkpoints satisfy the invariants required by [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) before permitting any sync traffic.

### 4.4 Read Surface Engine

The Read Surface Engine exposes strictly read-only views of state metadata to internal components. It guarantees that no partially applied or speculative state is ever visible, so all consumers observe only the durable outcomes required by [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

## 5. Ordering and determinism

### 5.1 Global ordering guarantees

All committed graph operations are totally ordered by the monotonic, node-local `global_seq` assigned by [Graph Manager](07-graph-manager.md) when applying the envelopes defined in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md). This ordering model is identical to Section 5 of [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). The State Manager observes this order and ensures that:

* No derived state reflects out-of-order commits.
* No outbound sync package violates this order.
* No inbound envelope is applied outside the expected sequence.

### 5.2 Inbound ordering enforcement

For each peer and domain, the State Manager enforces:

* Strict monotonic sequence advancement.
* No overlap or replay of previously accepted sequences.
* No gaps unless explicitly permitted by protocol rules.

Any violation results in rejection before [Graph Manager](07-graph-manager.md) invocation using the sync integrity error classes in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

### 5.3 Deterministic behavior

Given identical persisted state and identical inputs, the State Manager must always produce identical acceptance or rejection outcomes. No non-deterministic inputs, timestamps, or external state may influence decisions, mirroring the deterministic guarantees mandated in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).

## 6. Inbound remote envelope handling

### 6.1 Inbound processing stages

Inbound remote data is processed in the following stages:

1. Receipt from [Network Manager](10-network-manager.md) after cryptographic verification per [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md) and framing guarantees from [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).
2. Validation of peer identity, domain eligibility, and declared sequence range using sync package metadata from [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
3. Admission or rejection based on current sync state defined in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
4. Construction of a remote operation context.
5. Submission to [Graph Manager](07-graph-manager.md) for validation and persistence.
6. Observation of commit result and metadata update.

At no point may inbound data bypass any stage, ensuring every envelope honors the rejection rules enumerated in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

### 6.2 Operation context construction

For each inbound envelope, the State Manager constructs an [OperationContext](../services-and-apps/05-operation-context.md) (per [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md)) that includes:

* Remote origin flag.
* Peer identity.
* Sync domain.
* Trace and correlation identifiers.

This context is immutable once constructed.

### 6.3 Rejection behavior

Rejected inbound envelopes:

* Do not mutate canonical state.
* Do not advance sync state.
* Are logged with deterministic error classification mapped to the sync integrity and cryptographic error classes from [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).
* Do not leak internal state details to peers.

## 7. Outbound synchronization

### 7.1 Package construction

Outbound sync packages are constructed exclusively from committed graph state and authoritative metadata. Each package follows the structure in Section 9 of [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and therefore includes:

* A contiguous sequence range covering `from_seq` through `to_seq`.
* Domain attribution via `sync_domain` plus sender identity metadata.
* Required protocol metadata including `sender_identity` and `signature`.

No speculative or uncommitted data may be included.

### 7.2 Progress advancement

Outbound sync progress advances only after successful handoff to [Network Manager](10-network-manager.md) and confirmation that the package left the State Manager boundary. Transmission failure does not advance progress, preserving the advancement rules defined in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).

### 7.3 Visibility enforcement

Outbound packages must respect domain visibility and revocation rules described in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) and the violation codes defined in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md). The State Manager must never export data a peer is not eligible to receive.

## 8. Persistence and durability

### 8.1 Persistence contract

The State Manager persists all authoritative metadata via [Storage Manager](02-storage-manager.md). It does not implement its own storage layer and does not bypass transactional boundaries, ensuring that `global_seq`, sync checkpoints, and recovery markers always satisfy the durability rules that [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) assumes.

### 8.2 Atomicity requirements

State metadata updates that depend on graph commits must be atomic with respect to commit observation. Partial updates are forbidden so that no package violates the rejection guarantees in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

### 8.3 No shadow persistence

The State Manager must not maintain shadow copies of authoritative state outside Storage Manager.

## 9. Startup behavior

### 9.1 Initialization sequence

On startup, the State Manager performs the following steps in order:

1. Load persisted metadata from [Storage Manager](02-storage-manager.md).
2. Query [Graph Manager](07-graph-manager.md) or [Storage Manager](02-storage-manager.md) for highest committed sequence.
3. Validate consistency between metadata and canonical state, ensuring sync checkpoints align with [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
4. Rebuild derived structures.
5. Expose readiness signal only after successful validation.

### 9.2 Readiness signal

The State Manager exposes readiness only when:

* All metadata is consistent with the invariants in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* No recovery errors are present.
* All internal engines are initialized.

## 10. Shutdown behavior

### 10.1 Graceful shutdown

On shutdown, the State Manager:

* Flushes any pending metadata updates.
* Halts admission of new inbound data.
* Freezes outbound sync progression.
* Ensures persisted state reflects a consistent checkpoint compatible with [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).

### 10.2 Forced shutdown

If forced shutdown occurs, recovery behavior must detect incomplete checkpoints and fail fast if consistency cannot be proven.

## 11. Failure handling

### 11.1 Ordering violations

Ordering violations result in immediate rejection and suspension of the offending peer domain until corrected. Rejections must be reported internally using the `ERR_SYNC_SEQUENCE_INVALID`, `ERR_SYNC_RANGE_MISMATCH`, or related classes defined in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

### 11.2 Persistence failures

Persistence failures result in:

* No state advancement.
* Suspension of affected operations.
* Escalation to observability and administrative channels using the resource error patterns from [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

### 11.3 Recovery failures

Any inconsistency between persisted metadata and canonical state results in fatal startup failure. Automatic repair or inference is forbidden per the recovery rules in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

### 11.4 Degraded operation

When durability guarantees cannot be met, the State Manager must refuse new state transitions while continuing to serve safe read-only views if possible.

## 12. State access and exposure

### 12.1 Read-only guarantees

All exposed state views are read-only and reflect only committed, durable state.

### 12.2 Access restrictions

Only trusted internal components may access State Manager read surfaces. No direct external access is permitted.

## 13. Trust boundaries

The State Manager trusts:

* [Network Manager](10-network-manager.md) for cryptographic verification and peer identity binding, as mandated in [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md) and bounded by the transport guarantees of [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).
* [Graph Manager](07-graph-manager.md) for validation, authorization, sequencing, and persistence of the canonical objects described in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* [Storage Manager](02-storage-manager.md) for durable storage semantics.

All remote inputs are treated as untrusted until validated.

## 14. Explicitly allowed behaviors

* Buffering validated inbound envelopes while preserving order.
* Temporarily suspending peers to preserve integrity.
* Rebuilding derived structures from persisted data.
* Serving read-only metadata to observability systems.
* Rejecting invalid or out-of-order inputs deterministically.

## 15. Explicitly forbidden behaviors

* Mutating canonical graph objects directly.
* Assigning or modifying global sequence identifiers.
* Advancing sync state without successful commit.
* Guessing or repairing missing metadata.
* Exposing speculative or partial state.
* Bypassing Network Manager or Graph Manager.

## 16. Invariants and guarantees

Across all components and contexts defined in this file, the following invariants hold:

* Canonical graph mutation occurs only via Graph Manager.
* State metadata is monotonic and authoritative.
* Sync progression never regresses.
* All exposed state is derived from committed, durable data.
* Recovery is deterministic and fail-closed.

These guarantees hold regardless of caller, execution context, input source, or peer behavior.

## 17. Compliance criteria

An implementation complies with this specification if and only if it satisfies all responsibilities, invariants, boundaries, and forbidden behavior constraints defined herein.
