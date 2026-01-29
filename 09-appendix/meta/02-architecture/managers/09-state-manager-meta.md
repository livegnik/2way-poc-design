



# 09 State Manager

## 1. Purpose and scope

The State Manager is the authoritative component responsible for the scope described below. This document specifies the State Manager component within the 2WAY architecture. The State Manager is responsible for maintaining authoritative local state progression, coordinating accepted graph mutations, enforcing deterministic ordering guarantees, tracking synchronization progress with peers, and ensuring durability and recoverability of all state transitions required by the protocol.

The State Manager acts as the single coordination layer between [Graph Manager](07-graph-manager.md), [Network Manager](10-network-manager.md), and [Storage Manager](02-storage-manager.md) for all stateful operations that affect protocol-visible progression. It does not author graph mutations, perform cryptographic validation, or apply access control decisions. It ensures that only fully verified, correctly ordered, and durably persisted state transitions are exposed to internal components or propagated to peers. This specification defines state ownership, internal engines and phases, ordering rules, sync metadata handling, startup and shutdown behavior, failure handling, and explicit trust boundaries. It is an architectural specification, not an implementation.

This specification consumes the protocol contracts defined in:

* [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md)
* [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md)
* [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md)
* [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md)

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
* DoS mitigation, client puzzles, or connection throttling, which are defined for [Network Manager](10-network-manager.md) and [DoS Guard Manager](14-dos-guard-manager.md) in [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Application-specific logic or derived analytics.
* Storage engine implementation details beyond required persistence contracts.
