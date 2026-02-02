



# 06 Storage limits and budgets

Defines local storage limits and budgets for the 2WAY backend SQLite database. Specifies enforcement posture, failure behavior, and constraints that must not weaken validation or ordering guarantees.

For the meta specifications, see [06-storage-limits-and-budgets meta](../09-appendix/meta/03-data/06-storage-limits-and-budgets-meta.md).

## 1. Invariants and guarantees

Across all limits defined in this file, the following invariants hold:

* Limits are enforced locally and fail closed when exceeded.
* Limits must never weaken validation, ordering, or ACL enforcement.
* Limit checks occur before committing any write that would exceed a budget.
* Limit enforcement must not advance `global_seq` or sync cursors.
* Limits are deterministic given identical storage state and inputs.

## 2. Ownership and enforcement boundary

* [Storage Manager](../02-architecture/managers/02-storage-manager.md) is the sole owner of storage budgets and enforcement.
* [Graph Manager](../02-architecture/managers/07-graph-manager.md) must invoke Storage Manager budget checks before committing writes.
* No other manager or service may bypass or disable storage limits.

## 3. Required limits

At minimum, the following limits must be enforced:

### 3.1 Database size budget

* A maximum on-disk database size in bytes.
* Writes that would exceed the budget must be rejected.

### 3.2 Per-app total row budget

* Maximum total rows across graph tables for a single app (`app_N_parent`, `app_N_attr`, `app_N_edge`, `app_N_rating`).
* Writes that would exceed the budget must be rejected.

### 3.3 Per-table row budget

* Maximum rows per app table to prevent a single object class from exhausting storage.
* Writes that would exceed the budget must be rejected.

### 3.4 Per-app log budget

* Maximum rows in `app_N_log` to bound operational storage.

### 3.5 Payload size budget

* Maximum payload size per write batch (or per envelope).
* Writes that exceed the budget must be rejected.

## 4. Failure posture

* Any budget breach results in rejection of the entire write batch.
* Partial writes are forbidden.
* Limits do not trigger automatic deletion or truncation.
* Errors surface through the standard storage error model in [01-protocol/10-errors-and-failure-modes.md](../01-protocol/10-errors-and-failure-modes.md).

## 5. Explicitly forbidden behavior

The following behaviors are forbidden:

* Silently truncating payloads to fit budgets.
* Bypassing limits for “trusted” callers.
* Advancing sequence cursors when budgets are exceeded.
* Auto-deleting data to satisfy budgets.

