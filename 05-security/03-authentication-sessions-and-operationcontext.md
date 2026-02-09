



# 03 Authentication, sessions, and OperationContext

This document defines how authenticated auth tokens map to OperationContext and how those contexts are used by the kernel.

For the meta specifications, see [03-authentication-sessions-and-operationcontext-meta.md](../10-appendix/meta/05-security/03-authentication-sessions-and-operationcontext-meta.md).

## 1. Authentication boundary

* Auth Manager is the only component allowed to resolve frontend auth tokens and registration signatures.
* Auth tokens map to a single backend identity.
* Auth tokens include expiry and revocation state enforced by Auth Manager.
* Auth token validation produces OperationContext inputs but does not authorize actions.

## 2. OperationContext integrity

* OperationContext is immutable once constructed.
* Contexts are scoped to a single app_id and capability.
* Contexts declare caller type (user, service, automation, delegation).

## 3. Failure posture

* Invalid auth tokens are rejected without side effects.
* Expired or revoked auth tokens are rejected without side effects.
* Missing or malformed context fields are rejected.
* Contexts from untrusted sources are never accepted.
