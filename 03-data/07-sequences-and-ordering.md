



# 07 Sequences and ordering

Defines global and per-domain sequencing rules for the backend. Specifies monotonicity, ordering invariants, and failure handling for sequence cursors.

For the meta specifications, see [07-sequences-and-ordering meta](../10-appendix/meta/03-data/07-sequences-and-ordering-meta.md).

## 1. Invariants and guarantees

Across all sequence cursors defined in this file, the following invariants hold:

* `global_seq` is strictly monotonic and advances by exactly one for each accepted write.
* Sync cursors are monotonic per `(peer_id, sync_domain)` and never decrease.
* Domain cursors are monotonic per `(peer_id, sync_domain)` and never decrease.
* Sequence cursors advance only after successful validation and commit.
* Sequence cursor updates are atomic with their associated state changes.

## 2. Global sequence

### 2.1 Ownership

* The `global_seq` cursor is owned by the Storage Manager.
* No other component may mutate the `global_seq` row directly.

### 2.2 Allocation

* The Storage Manager must allocate the next `global_seq` value within a write transaction.
* Each allocation increments the sequence by exactly one.
* The single `global_seq` row must exist at all times.

## 3. Sync cursors

### 3.1 Scope

* The sync cursor is tracked per `(peer_id, sync_domain)` in `sync_state`.
* The cursor represents the last accepted remote global sequence.

### 3.2 Monotonicity

* The cursor must never decrease.
* Attempts to set a lower value must fail closed.
* The cursor is advanced only after a successful ingest.

## 4. Domain cursors

### 4.1 Scope

* The domain cursor is tracked per `(peer_id, sync_domain)` in `domain_seq`.
* The cursor supports eligibility checks for remote sync flows.

### 4.2 Monotonicity

* The cursor must never decrease.
* Attempts to set a lower value must fail closed.
* The cursor is advanced only after successful ingest.

## 5. Failure posture

* Missing cursors, invalid cursor values, or non-monotonic updates are fatal errors.
* Sequence failures must not allow partial writes.
* Errors surface through the standard storage error model in [01-protocol/10-errors-and-failure-modes.md](../01-protocol/10-errors-and-failure-modes.md).

## 6. Explicitly forbidden behavior

The following behaviors are forbidden:

* Resetting or decreasing any cursor in `global_seq`, `sync_state`, or `domain_seq`.
* Advancing cursors without completing associated validations and commits.
* Bypassing Storage Manager sequencing APIs.
