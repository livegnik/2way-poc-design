



# 07 Sequences and ordering

## 1. Purpose and scope

This document defines sequencing and ordering guarantees for the 2WAY backend, including global sequence allocation and per-peer sync cursors. It specifies monotonicity and failure posture for sequence updates. It does not define protocol semantics or sync policy. Terminology is defined in [00-scope/03-definitions-and-terminology.md](../../../00-scope/03-definitions-and-terminology.md).

This specification consumes and is constrained by the protocol contracts defined in:

- [01-protocol/02-object-model.md](../../../01-protocol/02-object-model.md)
- [01-protocol/03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)
- [01-protocol/07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
- [01-protocol/10-errors-and-failure-modes.md](../../../01-protocol/10-errors-and-failure-modes.md)
- [01-protocol/11-versioning-and-compatibility.md](../../../01-protocol/11-versioning-and-compatibility.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining monotonicity requirements for global and per-peer sequence cursors
* Defining Storage Manager ownership of sequence allocation and updates
* Defining failure posture for missing or non-monotonic cursor updates
* Defining the atomicity requirements for sequence advancement

This specification does not cover the following:

* Sync eligibility policy, which is owned by [State Manager](../../../02-architecture/managers/09-state-manager.md)
* Schema validation or ACL enforcement, which are owned by [Schema Manager](../../../02-architecture/managers/05-schema-manager.md) and [ACL Manager](../../../02-architecture/managers/06-acl-manager.md)
* Migration ordering, which is defined in [03-data/05-migrations-and-upgrades.md](../../../03-data/05-migrations-and-upgrades.md)
