



# 00 Architecture overview

## 1. Purpose and scope

This document defines the architectural role and posture of the 2WAY PoC backend. It explains how managers, services, runtime topologies, trust boundaries, and data flows compose into a single node, and it inventories every specification under [02-architecture/**](./). It captures invariants, allowed behaviors, and rejection posture at the architectural level without re-specifying schema, envelope, or transport details already defined elsewhere in the repository. Frontend presentation and UX flows are out of scope except where they cross a trust boundary.

This overview references:

* [01-protocol/**](../01-protocol/)
* [02-architecture/**](./)
* [02-architecture/managers/**](managers/)
* [02-architecture/services-and-apps](services-and-apps/)
* [02-architecture/01-component-model.md](../../../02-architecture/01-component-model.md)
* [02-architecture/02-runtime-topologies.md](../../../02-architecture/02-runtime-topologies.md)
* [02-architecture/03-trust-boundaries.md](../../../02-architecture/03-trust-boundaries.md)
* [02-architecture/04-data-flow-overview.md](../../../02-architecture/04-data-flow-overview.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Documenting the architectural intent and guarantees that bind all managers, services, and runtime arrangements.
* Summarizing the responsibilities of each companion document under [02-architecture](./) and describing how they are consumed together.
* Highlighting the mandatory trust boundaries, sequencing rules, and data flows that all implementations must preserve.

This specification does not cover the following:

* Schema definitions, envelope formats, serialization, or crypto mechanics (see [01-protocol/**](../01-protocol/)).
* [Database layouts](../../../03-data/01-sqlite-layout.md), query plans, deployment automation, or performance tuning details.
* UI workflows, frontend component structure, or domain semantics beyond architectural constraints.

## 3. Architectural documents and companion specifications

### 3.1 Core architecture specifications

* [01-component-model.md](../../../02-architecture/01-component-model.md) defines manager and service categories, invariants, and allowed/forbidden interactions for the backend component model.
* [02-runtime-topologies.md](../../../02-architecture/02-runtime-topologies.md) enumerates conforming runtime layouts, the placement of managers, storage, keys, and frontend clients, and the trust posture for each topology.
* [03-trust-boundaries.md](../../../02-architecture/03-trust-boundaries.md) documents every architectural trust boundary, the allowed flows across each boundary, and the rejection behavior when the boundary is violated.
* [04-data-flow-overview.md](../../../02-architecture/04-data-flow-overview.md) details bootstrap, provisioning, read, write, rating, event, sync, and derived-data flows plus the guarantees that bind them.

### 3.2 Manager specifications ([02-architecture/managers](managers/))

Each manager has a dedicated specification file that defines authoritative responsibilities and ownership:

* [managers/00-managers-overview.md](../../../02-architecture/managers/00-managers-overview.md) - landing page for manager responsibilities and dependency posture.
* [managers/01-config-manager.md](../../../02-architecture/managers/01-config-manager.md) - configuration loading, validation, and publication.
* [managers/02-storage-manager.md](../../../02-architecture/managers/02-storage-manager.md) - SQLite access boundaries, transaction guarantees, and persistence APIs.
* [managers/03-key-manager.md](../../../02-architecture/managers/03-key-manager.md) - key lifecycle, storage, signing, decryption, and revocation handling.
* [managers/04-auth-manager.md](../../../02-architecture/managers/04-auth-manager.md) - frontend authentication, session validation, and identity resolution rules.
* [managers/05-schema-manager.md](../../../02-architecture/managers/05-schema-manager.md) - schema definition handling, validation ordering, and namespace enforcement.
* [managers/06-acl-manager.md](../../../02-architecture/managers/06-acl-manager.md) - authorization inputs, evaluation semantics, and enforcement posture.
* [managers/07-graph-manager.md](../../../02-architecture/managers/07-graph-manager.md) - mutation orchestration, sequencing, and envelope application behavior.
* [managers/08-app-manager.md](../../../02-architecture/managers/08-app-manager.md) - app registration, lifecycle, extension loading, and namespace binding.
* [managers/09-state-manager.md](../../../02-architecture/managers/09-state-manager.md) - sync domain definitions, sequencing, reconciliation, and replay protection.
* [managers/10-network-manager.md](../../../02-architecture/managers/10-network-manager.md) - peer communication, transport abstraction, cryptographic binding, and DoS integration.
* [managers/11-event-manager.md](../../../02-architecture/managers/11-event-manager.md) - event emission, subscription semantics, and WebSocket delivery contracts.
* [managers/12-log-manager.md](../../../02-architecture/managers/12-log-manager.md) - audit, diagnostics, structured log formats, and access policies.
* [managers/13-health-manager.md](../../../02-architecture/managers/13-health-manager.md) - liveness checks, readiness signals, and failure reporting.
* [managers/14-dos-guard-manager.md](../../../02-architecture/managers/14-dos-guard-manager.md) - rate limiting, client puzzle enforcement, and abuse containment.

### 3.3 Services and apps specifications ([02-architecture/services-and-apps](services-and-apps/))

These documents define how system services, app extensions, and frontend experiences consume the managers:

* [services-and-apps/00-services-and-apps-overview.md](../../../02-architecture/services-and-apps/00-services-and-apps-overview.md) - scope and shared responsibilities of backend services and frontend apps.
* [services-and-apps/01-services-vs-apps.md](../../../02-architecture/services-and-apps/01-services-vs-apps.md) - differentiates long-lived system services from app-scoped extensions and UI apps.
* [services-and-apps/02-system-services.md](../../../02-architecture/services-and-apps/02-system-services.md) - expectations for built-in services that ship with the node.
* [services-and-apps/03-app-backend-extensions.md](../../../02-architecture/services-and-apps/03-app-backend-extensions.md) - constraints on optional backend extensions authored by apps.
* [services-and-apps/04-frontend-apps.md](../../../02-architecture/services-and-apps/04-frontend-apps.md) - frontend posture, allowed backend interactions, and trust boundaries.
* [services-and-apps/05-operation-context.md](../../../02-architecture/services-and-apps/05-operation-context.md) - definition of OperationContext, required fields, and propagation rules.

This overview, together with the referenced specifications in [02-architecture/**](./), defines the authoritative architecture contract for the PoC. All future changes to managers, services, runtime topologies, or data flows must preserve these guarantees or amend the relevant companion documents alongside this overview.
