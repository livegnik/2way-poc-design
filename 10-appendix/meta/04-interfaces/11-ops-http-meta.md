



# 11 Ops HTTP Interfaces

## 1. Purpose and scope

Defines administrative HTTP endpoints under `/system/ops/*` and the client telemetry ingestion surface.

This document references:

* [02-architecture/services-and-apps/02-system-services.md](../../../02-architecture/services-and-apps/02-system-services.md)
* [02-architecture/managers/13-health-manager.md](../../../02-architecture/managers/13-health-manager.md)
* [04-interfaces/04-error-model.md](../../../04-interfaces/04-error-model.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Declaring ops routes and payloads.
* Recording admin gating requirements.
* Declaring the health snapshot schema and telemetry payload constraints.
* Declaring ops route enablement gating and error mapping, including `ERR_SVC_SYS_DISABLED` when routes are disabled.

This specification does not cover the following:

* WebSocket dashboard delivery.
