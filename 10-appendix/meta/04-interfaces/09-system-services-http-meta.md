



# 09 System Services HTTP Interfaces

## 1. Purpose and scope

Defines the local HTTP contracts for system services enumerated in the system service architecture specification.

This document references:

* [02-architecture/services-and-apps/02-system-services.md](../../../02-architecture/services-and-apps/02-system-services.md)
* [02-architecture/services-and-apps/05-operation-context.md](../../../02-architecture/services-and-apps/05-operation-context.md)
* [04-interfaces/04-error-model.md](../../../04-interfaces/04-error-model.md)
* [04-interfaces/11-ops-http.md](../../../04-interfaces/11-ops-http.md)
* [01-protocol/10-errors-and-failure-modes.md](../../../01-protocol/10-errors-and-failure-modes.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Declaring HTTP routes, request/response shapes, and error mappings for system services.
* Recording OperationContext requirements and fail-closed validation order.
* Declaring the app service diagnostics snapshot schema.

This specification does not cover the following:

* Internal manager APIs.
* Concrete UI behavior.
