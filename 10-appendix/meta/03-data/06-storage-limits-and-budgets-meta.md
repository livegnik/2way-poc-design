



# 06 Storage limits and budgets

## 1. Purpose and scope

This document defines local storage limits and budgets for the 2WAY backend SQLite database. It specifies enforcement boundaries, failure posture, and constraints that preserve protocol ordering and validation guarantees. It does not define schema or storage layout. Terminology is defined in [00-scope/03-definitions-and-terminology.md](../../../00-scope/03-definitions-and-terminology.md).

This specification consumes and is constrained by the protocol contracts defined in:

- [01-protocol/02-object-model.md](../../../01-protocol/02-object-model.md)
- [01-protocol/03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)
- [01-protocol/06-access-control-model.md](../../../01-protocol/06-access-control-model.md)
- [01-protocol/07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
- [01-protocol/10-errors-and-failure-modes.md](../../../01-protocol/10-errors-and-failure-modes.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining required storage budgets and enforcement posture
* Defining Storage Manager ownership of limit checks
* Defining failure behavior when budgets are exceeded
* Ensuring limits never weaken ordering or validation guarantees

This specification does not cover the following:

* Schema definitions, which are defined in [03-data/01-sqlite-layout.md](../../../03-data/01-sqlite-layout.md)
* Indexing requirements, which are defined in [03-data/04-indexing-strategy.md](../../../03-data/04-indexing-strategy.md)
* Migration ordering, which is defined in [03-data/05-migrations-and-upgrades.md](../../../03-data/05-migrations-and-upgrades.md)
* Backup and portability, which are defined in [03-data/08-backup-restore-and-portability.md](../../../03-data/08-backup-restore-and-portability.md)
