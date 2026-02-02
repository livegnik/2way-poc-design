



# 03 Authentication, sessions, and OperationContext

This document defines how authenticated sessions map to OperationContext and how those contexts are used by the kernel.

For the meta specifications, see [03-authentication-sessions-and-operationcontext-meta.md](../09-appendix/meta/05-security/03-authentication-sessions-and-operationcontext-meta.md).

## 1. Authentication boundary

* Auth Manager is the only component allowed to resolve frontend credentials.
* Sessions map to a single backend identity.
* Session validation produces OperationContext inputs but does not authorize actions.

## 2. OperationContext integrity

* OperationContext is immutable once constructed.
* Contexts are scoped to a single app_id and capability.
* Contexts declare caller type (user, service, automation, delegation).

## 3. Failure posture

* Invalid sessions are rejected without side effects.
* Missing or malformed context fields are rejected.
* Contexts from untrusted sources are never accepted.
