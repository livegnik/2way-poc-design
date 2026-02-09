



# 10 Backup and restore flow

## 1. Purpose and scope

Defines how backups are created and restored while preserving ordering and integrity guarantees.

This specification references:

* [06-flows/10-backup-restore-flow.md](../../../06-flows/10-backup-restore-flow.md)
* [03-data/08-backup-restore-and-portability.md](../../../03-data/08-backup-restore-and-portability.md)
* [03-data/07-sequences-and-ordering.md](../../../03-data/07-sequences-and-ordering.md)

## 2. Responsibilities and boundaries

This specification is responsible for:

* Defining backup creation and restore validation steps.
* Declaring the invariants that prevent history rewind.
* Mapping backup and restore failures to error codes and transport outcomes.

This specification does not cover:

* External backup storage or transport mechanisms.
* UI workflows for backup management.
