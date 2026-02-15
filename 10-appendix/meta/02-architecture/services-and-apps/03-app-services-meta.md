



# 03 App services

## 1. Purpose and scope

App services are optional in-process services that belong to a single registered application slug and `app_id`. They let independent app teams expand backend behavior without weakening the trust boundaries enforced by managers, system services, or the interface layer. App services never replace managers; they provide app-specific orchestration while remaining inside the platform's fail-closed posture.

This overview defines how app services are authored, registered, packaged, loaded, observed, and unloaded so they coexist with the 2WAY platform without renegotiating contracts on every release. It codifies lifecycle, configuration, schema, capability, observability, and failure semantics that match the rest of the architecture corpus, enabling reviewers to audit application-owned logic using the same criteria as system-owned logic.

This overview references:

* [01-protocol/**](../../01-protocol/)
* [02-architecture/01-component-model.md](../../../../02-architecture/01-component-model.md)
* [02-architecture/03-trust-boundaries.md](../../../../02-architecture/03-trust-boundaries.md)
* [02-architecture/04-data-flow-overview.md](../../../../02-architecture/04-data-flow-overview.md)
* [02-architecture/managers/**](../../../../02-architecture/managers/00-managers-overview.md)
* [02-architecture/managers/00-managers-overview.md](../../../../02-architecture/managers/00-managers-overview.md)
* [02-architecture/services-and-apps/**](./)
* [02-architecture/services-and-apps/01-services-vs-apps.md](../../../../02-architecture/services-and-apps/01-services-vs-apps.md)
* [02-architecture/services-and-apps/05-operation-context.md](../../../../02-architecture/services-and-apps/05-operation-context.md)
* [04-interfaces/**](../../04-interfaces/)
* [05-security/**](../../05-security/)

### 1.1 Responsibilities and boundaries

This overview is responsible for the following:

* Defining the mandatory app service model for a conforming node, including the lifecycle, surfaces, dependency requirements, and execution boundaries for every app service.
* Defining strict ownership rules between app services, managers, system services, and the interface layer so app-owned code never weakens the guarantees in [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md) and [02-architecture/01-component-model.md](../../../../02-architecture/01-component-model.md).
* Defining [OperationContext](../../../../02-architecture/services-and-apps/05-operation-context.md), capability catalog, configuration, schema, packaging, and observability requirements so app services integrate with managers using the same posture as system services.
* Defining admission, [DoS Guard Manager](../../../../02-architecture/managers/14-dos-guard-manager.md), and [Health Manager](../../../../02-architecture/managers/13-health-manager.md) expectations that gate app service readiness and resource usage.
* Defining app service availability error families (`ERR_SVC_APP_*`) and parent-scoped app service validation/capability families (`ERR_SVC_APP_*`) and when they must be surfaced.
* Defining a reusable checklist that implementers can follow to prove an app service meets all contractual obligations before shipment.

This overview does not cover the following:

* Manager internal design, database layout, cryptographic algorithms, or network transport mechanics, which remain owned by protocol managers as detailed in [02-architecture/managers/00-managers-overview.md](../../../../02-architecture/managers/00-managers-overview.md).
* Frontend UI implementations or transport encoding details, which belong to [04-interfaces/**](../../04-interfaces/) unless explicitly called out for missing shapes.
* App-specific product logic that does not cross the backend boundary defined in this document.
