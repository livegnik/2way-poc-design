



# 09 Privacy, selective sync, and domain scoping

This document defines how privacy is preserved through selective sync, visibility rules, and metadata minimization.

For the meta specifications, see [09-privacy-selective-sync-and-domain-scoping-meta.md](../09-appendix/meta/05-security/09-privacy-selective-sync-and-domain-scoping-meta.md).

## 1. Domain scoping

* Sync domains are explicit and app-scoped.
* Domain selection limits which objects are eligible for sync.
* Cross-domain leakage is forbidden.

## 2. Selective sync

* State Manager selects only objects within the requested domain.
* ACL visibility rules are enforced before export.
* Per-peer sync state limits exposure to required ranges.

## 3. Metadata minimization

* Only required metadata is included in sync envelopes.
* Peer identity exposure is limited to required handshake fields.
* Local-only fields never leave the node.

## 4. Failure posture

* Domain violations are rejected.
* Privacy violations are treated as authorization failures.
