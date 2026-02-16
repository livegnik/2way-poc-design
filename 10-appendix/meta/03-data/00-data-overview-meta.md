



# 00 Data overview

## 1. Purpose and scope

This document defines the role and posture of the 2WAY data layer. It summarizes storage boundaries, sequencing guarantees, migration behavior, and data lifecycle constraints, without redefining detailed schemas or index definitions.

This overview references:

* [03-data/**](./)
* [01-sqlite-layout.md](../../../03-data/01-sqlite-layout.md)
* [02-system-tables.md](../../../03-data/02-system-tables.md)
* [03-per-app-tables.md](../../../03-data/03-per-app-tables.md)
* [04-indexing-strategy.md](../../../03-data/04-indexing-strategy.md)
* [05-migrations-and-upgrades.md](../../../03-data/05-migrations-and-upgrades.md)
* [06-storage-limits-and-budgets.md](../../../03-data/06-storage-limits-and-budgets.md)
* [07-sequences-and-ordering.md](../../../03-data/07-sequences-and-ordering.md)
* [08-backup-restore-and-portability.md](../../../03-data/08-backup-restore-and-portability.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Establishing data layer invariants and storage posture.
* Summarizing how system tables and per-app tables compose.
* Defining the sequencing and sync state expectations at a high level.
* Describing how migrations, limits, and backups fit into the persistence lifecycle.
* Declaring requirement-ID anchors used by generated data-model references.

This specification does not cover the following:

* Concrete schema definitions or column layouts (see [01-sqlite-layout.md](../../../03-data/01-sqlite-layout.md)).
* Index DDL or optimization details (see [04-indexing-strategy.md](../../../03-data/04-indexing-strategy.md)).
* Manager-specific logic or validation pipelines (see [02-architecture/managers/**](../02-architecture/managers/)).
