



# 08 Backup, restore, and portability

Defines how the backend database is backed up, restored, and moved between environments. Specifies ordering guarantees, failure posture, and portability rules.

For the meta specifications, see [08-backup-restore-and-portability meta](../09-appendix/meta/03-data/08-backup-restore-and-portability-meta.md).

## 1. Invariants and guarantees

Across all backup and restore operations defined in this file, the following invariants hold:

* Backups are consistent snapshots.
* Restore operations preserve ordering and never rewind `global_seq`.
* Backup and restore are owned by [Storage Manager](../02-architecture/managers/02-storage-manager.md).
* Backups never mutate the active database state.
* Restore fails closed on any incompatibility or ordering violation.

## 2. Backup requirements

* Backups must capture a consistent database snapshot.
* Backups must include all system and per-app tables.
* Backups must include the `schema_migrations` history.
* Backup files must be portable across machines of the same platform family.

## 3. Restore requirements

* Restore must not proceed if it would reduce `global_seq`.
* Restore must verify required tables and migration history.
* Restore must fail closed if the backup is missing critical tables.
* Restore must not rewrite accepted history.

## 4. Portability

* Backups are file-based and can be copied across nodes.
* Portability does not imply trust; restored nodes must still follow all protocol validation rules.
* Restored nodes must not accept writes if restore validation fails.

## 5. Failure posture

* Any backup or restore failure is fatal for the current operation.
* Partial restores are forbidden.
* Errors surface through the standard storage error model in [01-protocol/10-errors-and-failure-modes.md](../01-protocol/10-errors-and-failure-modes.md).

## 6. Explicitly forbidden behavior

The following behaviors are forbidden:

* Restoring a backup that would rewind `global_seq`.
* Restoring a backup with missing required tables.
* Modifying backup contents to bypass validation.
