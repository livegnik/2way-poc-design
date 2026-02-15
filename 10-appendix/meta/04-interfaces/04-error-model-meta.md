



# 04 Error model

## 1. Purpose and scope

Defines the canonical error shape, categories, and transport mapping for 2WAY. It establishes a uniform error representation across managers and interfaces.

This document references:

* [01-protocol/10-errors-and-failure-modes.md](../../../01-protocol/10-errors-and-failure-modes.md)
* [04-interfaces/01-local-http-api.md](../../../04-interfaces/01-local-http-api.md)
* [04-interfaces/02-websocket-events.md](../../../04-interfaces/02-websocket-events.md)
* [02-architecture/services-and-apps/04-frontend-apps.md](../../../02-architecture/services-and-apps/04-frontend-apps.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining the ErrorDetail shape and canonical codes.
* Establishing error categories and precedence.
* Defining protocol `ERR_*` normalization when surfaced through interface payloads.
* Defining service `ERR_*` code-to-category and code-to-HTTP mappings.
* Defining service availability error mappings (`ERR_SVC_SYS_*`, `ERR_SVC_APP_*`) for interface surfaces where applicable.
* Defining authoritative service code naming rules (bare service-family roots forbidden) and required availability metadata fields/state-retry mapping for implementation.
* Defining parent-scoped service families (`ERR_SVC_SYS_<SERVICE>_*`, `ERR_SVC_APP_*`) and manager-family rules (`ERR_MNG_<MANAGER>_*`) plus legacy-name rejection.
* Mapping manager errors to interface responses with deterministic transport status rules.

This specification does not cover the following:

* UI presentation or end-user messaging.
* Non-deterministic debugging or logging formats.
