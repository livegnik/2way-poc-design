



# 08 Frontend Contract

## 1. Purpose and scope

Defines the frontend-facing contract implied by frontend app requirements, including allowed and forbidden surfaces.

This document references:

* [02-architecture/services-and-apps/04-frontend-apps.md](../../../02-architecture/services-and-apps/04-frontend-apps.md)
* [04-interfaces/01-local-http-api.md](../../../04-interfaces/01-local-http-api.md)
* [04-interfaces/02-websocket-events.md](../../../04-interfaces/02-websocket-events.md)
* [04-interfaces/04-error-model.md](../../../04-interfaces/04-error-model.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Declaring which routes frontends may call.
* Declaring forbidden surfaces and payload discipline.

This specification does not cover the following:

* New API routes or transport definitions.
* Frontend UI design or UX guidance.
