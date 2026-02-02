



# 07 Conflict resolution flow

This flow defines how conflicting operations are handled. The PoC uses deterministic ordering and does not merge conflicting writes.

For the meta specifications, see [07-conflict-resolution-flow-meta.md](../09-appendix/meta/06-flows/07-conflict-resolution-flow-meta.md).

## 1. Inputs

* Concurrent or out-of-order envelopes from local or remote sources.
* State Manager sequence ranges and sync metadata.

## 2. Flow

1) State Manager validates sequence ordering for remote envelopes.
2) Graph Manager applies envelopes in global_seq order.
3) If a conflict is detected (e.g., write violates ACL or schema due to prior state), the envelope is rejected.
4) Rejections are recorded in peer sync state and propagated to the caller.

## 3. Allowed behavior

* Deterministic ordering decides the authoritative history.
* Rejected operations remain rejected even if later envelopes would have allowed them.

## 4. Forbidden behavior

* Merging conflicting writes.
* Accepting out-of-order sequences.
* Rewriting accepted history.

## 5. Failure behavior

* Conflicting envelopes are rejected without partial writes.
* Rejection is visible to the caller and to sync state.
