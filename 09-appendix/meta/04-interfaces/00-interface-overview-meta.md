



# 00 Interface overview

## 1. Purpose and scope

This document summarizes the interface surfaces for the 2WAY backend: local HTTP, local WebSocket, and internal manager APIs. It establishes boundaries and posture without redefining protocol or schema details.

This overview references:

* [04-interfaces/**](./)
* [01-local-http-api.md](01-local-http-api.md)
* [02-websocket-events.md](02-websocket-events.md)
* [03-internal-apis-between-components.md](03-internal-apis-between-components.md)
* [04-error-model.md](04-error-model.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Declaring the backend interface surfaces and their scope.
* Summarizing authentication and error posture across interfaces.
* Establishing interface-level forbidden behaviors.

This specification does not cover the following:

* Protocol transport requirements (see [01-protocol/08-network-transport-requirements.md](../01-protocol/08-network-transport-requirements.md)).
* Database schemas and persistence (see [03-data/**](../03-data/)).
* Manager implementation details (see [02-architecture/managers/**](../02-architecture/managers/)).
