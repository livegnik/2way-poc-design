



# 10 HTTP Interface Conventions

Defines shared requirements that apply to all local HTTP interfaces.

For the meta specifications, see [10-http-conventions meta](../10-appendix/meta/04-interfaces/10-http-conventions-meta.md).

## 1. Purpose and scope

This specification defines common constraints for local HTTP interfaces. It does not define endpoint-specific request or response shapes.

## 2. Common requirements

All local HTTP interfaces:

* **MUST** be bound to local transport only and **MUST NOT** be exposed to untrusted networks.
* **MUST** authenticate write paths via [Auth Manager](../02-architecture/managers/04-auth-manager.md) and **MUST** build an [OperationContext](../02-architecture/services-and-apps/05-operation-context.md).
* **MUST** use the canonical error model in [04-error-model.md](04-error-model.md).
* **MUST** return deterministic errors and **MUST NOT** leak internal stack traces.

## 3. Related interface specifications

Endpoint-level contracts are defined in:

* [01-local-http-api.md](01-local-http-api.md)
* [06-app-lifecycle.md](06-app-lifecycle.md)
* [09-system-services-http.md](09-system-services-http.md)
* [11-ops-http.md](11-ops-http.md)
* [12-upload-http.md](12-upload-http.md)
