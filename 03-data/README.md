# 03 Data

This folder defines the persistent storage model for the 2WAY backend. It specifies the SQLite
layout, system and per-app tables, sequencing state, migrations, limits, backup/restore, and
indexing posture required to preserve the protocol's ordering and immutability guarantees.

If a storage requirement conflicts with another folder, record the exception as an ADR and treat
this folder as the authoritative source for persistence behavior.

## What lives here

- [`00-data-overview.md`](00-data-overview.md) - Data model overview and persistence scope.
- [`01-sqlite-layout.md`](01-sqlite-layout.md) - SQLite topology, table families, and sequencing rules.
- [`02-system-tables.md`](02-system-tables.md) - Global system tables and access rules.
- [`03-per-app-tables.md`](03-per-app-tables.md) - Per-app graph tables and immutability rules.
- [`04-indexing-strategy.md`](04-indexing-strategy.md) - Index requirements and maintenance posture.
- [`05-migrations-and-upgrades.md`](05-migrations-and-upgrades.md) - Migration rules and upgrade flow.
- [`06-storage-limits-and-budgets.md`](06-storage-limits-and-budgets.md) - Storage limits and budgets.
- [`07-sequences-and-ordering.md`](07-sequences-and-ordering.md) - Sequencing guarantees and ordering.
- [`08-backup-restore-and-portability.md`](08-backup-restore-and-portability.md) - Backup, restore, and portability rules.

Each document has a corresponding meta specification in [`09-appendix/meta/03-data/`](../09-appendix/meta/03-data/).

## How to read

1. Start with [`00-data-overview.md`](00-data-overview.md) for scope and persistence posture.
2. Read [`01-sqlite-layout.md`](01-sqlite-layout.md) for the storage model and invariants.
3. Read [`02-system-tables.md`](02-system-tables.md) and [`03-per-app-tables.md`](03-per-app-tables.md) for table rules.
4. Use [`04-indexing-strategy.md`](04-indexing-strategy.md) for index guarantees and constraints.
5. Finish with [`05-migrations-and-upgrades.md`](05-migrations-and-upgrades.md),
   [`06-storage-limits-and-budgets.md`](06-storage-limits-and-budgets.md),
   [`07-sequences-and-ordering.md`](07-sequences-and-ordering.md), and
   [`08-backup-restore-and-portability.md`](08-backup-restore-and-portability.md).

## Key guarantees this folder enforces

- Storage Manager is the only component permitted to issue SQL statements.
- Graph Manager is the only write path for graph objects.
- Persistent graph objects are append-only; deletions are forbidden.
- Immutable metadata columns never change after insertion.
- Each accepted envelope maps to exactly one committed transaction; partial acceptance is forbidden.
- `global_seq` is strictly monotonic and advances only after commit.
- Domain and peer sync cursors advance only after successful persistence.
- Sequence values are never supplied by callers and never reused.
- Cross-app references are forbidden; `app_id` scopes all object tables.
- System tables are node-local and never part of sync.
- Derived tables (`app_N_type`, `app_N_log`) are non-authoritative and never synced.
- Referential integrity is enforced by protocol validation, not SQLite foreign keys.
- Indexes are advisory for performance only and must never affect correctness.
- Migrations are ordered, idempotent, and fail closed; downgrades are not supported.
- Storage limits and budgets are enforced locally and must not weaken validation or ordering.
- Backups preserve ordering and integrity; restores never rewrite accepted history.
- Missing tables, migration failures, or invariant violations fail closed.

## Using this folder in reviews

- Treat any direct SQL access outside Storage Manager as non-compliant.
- Verify sequencing, sync cursor advancement, and atomicity rules at every write path.
- Ensure storage constraints never weaken protocol validation or authorization.
