



# 10 Backup and restore flow

This flow defines how node backups are created and restored while preserving ordering and integrity.

For the meta specifications, see [10-backup-restore-flow-meta.md](../09-appendix/meta/06-flows/10-backup-restore-flow-meta.md).

## 1. Inputs

* Backup request from an authorized admin.
* Restore request with a backup artifact.

## 2. Backup flow

1) Storage Manager enters a consistent read state.
2) Database is copied to a backup file atomically.
3) Backup metadata includes the global sequence at time of backup.

## 3. Restore flow

1) Storage Manager validates the backup file and global sequence.
2) Restore is rejected if it would rewind global_seq.
3) Database file is replaced atomically.
4) Managers reload from restored state.

## 4. Allowed behavior

* Offline restores for recovery.
* Backups during normal operation if consistency is preserved.

## 5. Forbidden behavior

* Restores that rewind accepted history.
* Partial restores that skip required tables.

## 6. Failure behavior

* Failed restore leaves the existing database intact.
* Backup failures do not affect live state.
