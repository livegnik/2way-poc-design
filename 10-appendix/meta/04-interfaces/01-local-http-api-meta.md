



# 01 Local HTTP API

## 1. Purpose and scope

Defines the local HTTP interface used by the 2WAY backend for health, graph envelope submission, local graph read requests, and PoC app list/read calls. It is a local-only interface and does not cover remote sync.

This document references:

* [01-protocol/03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)
* [02-architecture/managers/04-auth-manager.md](../../../02-architecture/managers/04-auth-manager.md)
* [02-architecture/managers/07-graph-manager.md](../../../02-architecture/managers/07-graph-manager.md)
* [02-architecture/managers/13-health-manager.md](../../../02-architecture/managers/13-health-manager.md)
* [07-poc/02-feature-matrix.md](../../../07-poc/02-feature-matrix.md)
* [04-error-model.md](../../../04-interfaces/04-error-model.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining request/response shapes for local HTTP calls.
* Declaring authentication and trace handling.
* Establishing error mapping for HTTP responses.
* Declaring the health snapshot schema returned by admin health endpoints.
* Declaring the local graph read request/response shape that binds to Graph Manager reads.
* Declaring PoC app list/read routes that bind to Graph Manager reads.
* Declaring app service availability mappings for `ERR_SVC_APP_*` on app-scoped local routes.

This specification does not cover the following:

* Transport for remote peers (see [01-protocol/08-network-transport-requirements.md](../../../01-protocol/08-network-transport-requirements.md)).
* UI semantics or frontend application behavior.
