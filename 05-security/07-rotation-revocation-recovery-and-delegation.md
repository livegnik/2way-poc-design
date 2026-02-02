



# 07 Rotation, revocation, recovery, and delegation

This document defines how keys and identities are rotated, revoked, and delegated.

For the meta specifications, see [07-rotation-revocation-recovery-and-delegation-meta.md](../09-appendix/meta/05-security/07-rotation-revocation-recovery-and-delegation-meta.md).

## 1. Rotation

* Identities may add new keys via graph objects.
* Old keys remain visible for verification of historical envelopes.
* Rotation events are append-only.

## 2. Revocation

* Revocation is recorded as graph objects or ratings.
* Revocation takes precedence over key usage going forward.
* Revocation does not invalidate historical accepted envelopes.

## 3. Recovery and alarm keys

* Recovery keys are scoped to identity recovery actions.
* Alarm keys can trigger immediate revocation workflows.
* Recovery actions are audited and require explicit authorization.

## 4. Delegation

* Delegated keys are scoped to specific capabilities.
* Delegation is bound to the identity graph and ACL rules.
* Delegated authority is limited by time and scope.

## 5. Failure posture

* Invalid or missing rotation proofs reject changes.
* Ambiguous delegation or scope mismatch is rejected.
