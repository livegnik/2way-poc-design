



# 00 Data overview

Defines the storage posture for 2WAY. Summarizes database layout, sequencing guarantees, migration behavior, limits, and backup/restore expectations. Constrains how Storage Manager persists graph objects and how other managers interact with persistent data.

For the meta specifications, see [00-data-overview meta](../09-appendix/meta/03-data/00-data-overview-meta.md).

## 1. Purpose and scope

This overview establishes the data layer's boundaries, invariants, and responsibilities. It orients the reader to the data specifications in this folder and the guarantees they collectively provide. It does not restate table schemas or index definitions in full; those live in their dedicated files.

## 2. Core invariants

Across all data layer components and operations, the following invariants hold:

* Storage Manager is the only component permitted to execute raw SQL statements.
* Graph Manager is the only component permitted to author persistent graph mutations.
* All accepted envelopes are applied atomically or not at all.
* `global_seq` advances strictly monotonically and only after commit.
* Domain and peer sync cursors never advance on rejection.
* Schema, ACL, and validation failures are detected before persistence.
* Data corruption, invariant violations, or migration failures cause fail-closed behavior.

These invariants apply to local writes, remote sync ingestion, maintenance tasks, and backup/restore workflows.

## 3. Data layout and table families

The data layer is anchored by a single SQLite database. It contains:

* Global system tables for identities, apps, peers, settings, sync state, and sequencing.
* Per-app table families with deterministic prefixes (`app_N_*`) for Parents, Attributes, Edges, Ratings, and type mappings.
* Log tables owned by Storage Manager for internal operational records.

Details live in:

* [01-sqlite-layout.md](01-sqlite-layout.md)
* [02-system-tables.md](02-system-tables.md)
* [03-per-app-tables.md](03-per-app-tables.md)

## 4. Sequencing and sync state

Sequencing and sync state are first-class storage concerns:

* `global_seq` is the authoritative, monotonic commit sequence across the database.
* Domain and peer cursors track sync progress and never move backwards.
* Sequence gaps may exist due to failed transactions, but committed values are strictly increasing.

Sequencing rules and ordering constraints are defined in:

* [07-sequences-and-ordering.md](07-sequences-and-ordering.md)
* [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md)

## 5. Indexing posture

Indexes are required for performance but never for correctness. Storage Manager may rebuild or verify indexes as needed, provided column contracts remain stable. Index definitions and guarantees are specified in:

* [04-indexing-strategy.md](04-indexing-strategy.md)

## 6. Migrations and upgrades

Migrations are strictly ordered, idempotent, and verified on startup. Storage Manager applies migrations before any other manager can read or write data. The migration posture is defined in:

* [05-migrations-and-upgrades.md](05-migrations-and-upgrades.md)

## 7. Storage limits and budgets

The data layer enforces resource limits to protect availability:

* Per-payload size limits.
* Per-table row budgets.
* Global constraints that prevent runaway growth.

Limits and enforcement rules are specified in:

* [06-storage-limits-and-budgets.md](06-storage-limits-and-budgets.md)

## 8. Backup, restore, and portability

Backup and restore must preserve sequence integrity, schema compatibility, and sync safety. Portability defines how a node can be moved or replicated without violating invariants. Requirements are defined in:

* [08-backup-restore-and-portability.md](08-backup-restore-and-portability.md)

## 9. Forbidden behaviors

The following behaviors are explicitly forbidden:

* Direct SQL access outside Storage Manager.
* Cross-app object references.
* Manual modification of sequencing tables.
* Sync cursor advancement on rejection.
* Partial acceptance of envelopes.
* Silent migration failures or schema drift.

## 10. Manager interaction contracts

* Storage Manager exposes persistence primitives only to Graph Manager and State Manager.
* Schema Manager and ACL Manager must complete validation before any persistence occurs.
* Network Manager and State Manager treat sync ingestion as untrusted input, but persistence still follows the same invariants.

Detailed manager responsibilities are defined in [02-architecture/managers/**](../02-architecture/managers/).
