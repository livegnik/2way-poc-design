



# 05 Signed transport, sync integrity, and metadata

This document defines how signed envelopes, ordering, and sync metadata preserve integrity across local and remote flows.

For the meta specifications, see [05-signed-transport-sync-integrity-and-metadata-meta.md](../10-appendix/meta/05-security/05-signed-transport-sync-integrity-and-metadata-meta.md).

## 1. Signed envelopes

* All graph writes use envelopes defined in the protocol.
* Remote envelopes are signed by the sender identity.
* The signature binds the envelope bytes and declared metadata.

## 2. Replay protection

* Global ordering is enforced by monotonic `global_seq`.
* State Manager rejects envelopes that violate sequence ranges.
* Replayed or out-of-order envelopes are rejected.

## 3. Sync integrity

* Sync metadata includes domain, from_seq, and to_seq.
* State Manager validates domain scope before applying envelopes.
* Rejections are recorded in peer sync state.

## 4. Failure posture

* Invalid signatures or unsupported algorithms are rejected.
* Envelopes failing sync validation are not applied.
* No partial application of remote data is permitted.
