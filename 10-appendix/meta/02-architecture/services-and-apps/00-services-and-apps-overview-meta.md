



# 00 Services and Apps Overview

## 1. Purpose and scope

This overview defines how backend services and applications fit into the 2WAY architecture. It summarizes the shared responsibilities, trust boundaries, and lifecycle guarantees that apply across system services, app services, and frontend apps. It connects the component model and manager contracts to the concrete service and app specifications without repeating their detailed rules.

This overview is descriptive and binding for structure and boundaries, but it does not restate protocol mechanics, schema grammar, ACL syntax, or interface shapes. Those details remain authoritative in their dedicated specifications.

This overview references:

* [01-protocol/**](../../01-protocol/)
* [02-architecture/01-component-model.md](../../../../02-architecture/01-component-model.md)
* [02-architecture/04-data-flow-overview.md](../../../../02-architecture/04-data-flow-overview.md)
* [02-architecture/managers/**](../../../../02-architecture/managers/00-managers-overview.md)
* [02-architecture/managers/00-managers-overview.md](../../../../02-architecture/managers/00-managers-overview.md)
* [02-architecture/services-and-apps/**](./)
* [02-architecture/services-and-apps/01-services-vs-apps.md](../../../../02-architecture/services-and-apps/01-services-vs-apps.md)
* [02-architecture/services-and-apps/02-system-services.md](../../../../02-architecture/services-and-apps/02-system-services.md)
* [02-architecture/services-and-apps/03-app-services.md](../../../../02-architecture/services-and-apps/03-app-services.md)
* [02-architecture/services-and-apps/04-frontend-apps.md](../../../../02-architecture/services-and-apps/04-frontend-apps.md)
* [02-architecture/services-and-apps/05-operation-context.md](../../../../02-architecture/services-and-apps/05-operation-context.md)
* [04-interfaces/**](../../04-interfaces/)

## 2. Responsibilities and boundaries

This overview is responsible for the following:

* Explaining the role of services and apps within the manager-centric architecture.
* Summarizing the classes of services and applications and how they are distinguished.
* Highlighting shared invariants: [OperationContext](../../../../02-architecture/services-and-apps/05-operation-context.md) discipline, manager-only state access, and fail-closed behavior.
* Describing how services and apps compose into end-to-end request and sync flows.

This overview does not cover the following:

* Protocol object formats, envelope serialization, or cryptographic details ([01-protocol/**](../../01-protocol/)).
* Manager implementation details beyond their published APIs ([02-architecture/managers/**](../managers/)).
* Frontend UX or product-specific behavior beyond required trust boundaries.

## 3. Service and application taxonomy

The architecture separates backend orchestration from application identity and frontend experiences. The key constructs are:

| Construct | Definition | Scope | Execution location |
| --- | --- | --- | --- |
| System service | Mandatory backend service that ships with every node and runs under `app_0`. | Platform-wide | Backend process |
| App service | Optional backend service bound to one app slug and `app_id`. | Single app | Backend process |
| Application (app) | Registered identity with schemas, ACL policy, and UX semantics. | Single app | [App Manager](../../../../02-architecture/managers/08-app-manager.md) registry |
| Frontend app | Untrusted client surface that consumes backend APIs or sync flows. | Single app | Outside backend |

The taxonomy is formalized in [02-architecture/services-and-apps/01-services-vs-apps.md](../../../../02-architecture/services-and-apps/01-services-vs-apps.md). The operational contracts for each class are defined in [02-architecture/services-and-apps/02-system-services.md](../../../../02-architecture/services-and-apps/02-system-services.md), [02-architecture/services-and-apps/03-app-services.md](../../../../02-architecture/services-and-apps/03-app-services.md), and [02-architecture/services-and-apps/04-frontend-apps.md](../../../../02-architecture/services-and-apps/04-frontend-apps.md).
