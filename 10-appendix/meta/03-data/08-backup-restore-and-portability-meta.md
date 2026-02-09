



# 08 Backup, restore, and portability

## 1. Purpose and scope

This document defines the backup, restore, and portability posture for the 2WAY backend SQLite database. It specifies ordering guarantees and fail-closed behavior. It does not define schema or migration contents. Terminology is defined in [00-scope/03-definitions-and-terminology.md](../../../00-scope/03-definitions-and-terminology.md).

This specification consumes and is constrained by the protocol contracts defined in:

- [01-protocol/03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)
- [01-protocol/07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
- [01-protocol/10-errors-and-failure-modes.md](../../../01-protocol/10-errors-and-failure-modes.md)
- [01-protocol/11-versioning-and-compatibility.md](../../../01-protocol/11-versioning-and-compatibility.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining backup consistency requirements
* Defining restore validation and ordering guarantees
* Defining Storage Manager ownership of backup and restore operations
* Defining failure posture for restore incompatibilities

This specification does not cover the following:

* Migration ordering, which is defined in [03-data/05-migrations-and-upgrades.md](../../../03-data/05-migrations-and-upgrades.md)
* Storage budgets, which are defined in [03-data/06-storage-limits-and-budgets.md](../../../03-data/06-storage-limits-and-budgets.md)
* Indexing requirements, which are defined in [03-data/04-indexing-strategy.md](../../../03-data/04-indexing-strategy.md)
