



# 05 Migrations and upgrades

Defines the migration ordering rules, idempotency guarantees, and upgrade posture for backend SQLite schemas. Specifies failure handling, allowed behaviors, and migration identifiers.

For the meta specifications, see [05-migrations-and-upgrades meta](../10-appendix/meta/03-data/05-migrations-and-upgrades-meta.md).

## 1. Invariants and guarantees

Across all migration operations defined in this file, the following invariants hold:

* Migrations are strictly ordered and applied sequentially.
* Each migration is idempotent and safe to rerun.
* Partial migration application must never declare readiness.
* Migration ordering is deterministic given the same on-disk migration set.
* Migration application is atomic per migration file.
* Migration failures fail closed and prevent further writes.

## 2. Migration identifiers and ordering

### 2.1 Identifier format

Migration identifiers must follow the format:

* `NNN_description`

Where:

* `NNN` is a zero-padded, base-10 integer sequence.
* The sequence starts at `001`.
* The `description` segment is lower_snake_case.

Examples:

* `001_init`
* `002_add_peer_indexes`

### 2.2 Ordering rules

* Migrations are ordered by the numeric prefix.
* Ordering is contiguous with no gaps.
* Duplicate numeric prefixes are forbidden.
* Applied migrations must form a prefix of the on-disk migration list.

If any of these rules are violated, migration application must fail closed.

## 3. Idempotency and reapplication

* Each migration must be safe to re-run without changing results.
* `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` are required for schema creation.
* Schema updates must be written so that repeated execution does not introduce duplicate data or inconsistent schema state.
* The migration runner must skip migrations already recorded in `schema_migrations`.

## 4. Upgrade policy

* Upgrades are forward-only. Downgrades are forbidden.
* If the migration history on disk is missing any previously applied migration, startup must fail closed.
* If a migration fails to apply, no subsequent migrations may run in that session.
* A failed migration must not be recorded as applied.

## 5. Failure posture

* Any migration ordering error, missing migration, or execution failure is a fatal error.
* The system must not accept any writes while migration errors exist.
* Migration failures must surface through the standard storage error model in [01-protocol/10-errors-and-failure-modes.md](../01-protocol/10-errors-and-failure-modes.md).

## 6. Explicitly forbidden behavior

The following behaviors are forbidden:

* Applying migrations out of order or skipping sequence numbers.
* Running migrations while graph write transactions are active.
* Modifying or deleting the `schema_migrations` history outside of the Storage Manager.
* Applying migrations that silently change data semantics without a new migration identifier.
