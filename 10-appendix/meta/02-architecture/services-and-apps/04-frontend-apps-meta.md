



# 04 Frontend Apps

## 1. Purpose and scope

Frontend applications are the only components that interpret 2WAY state on behalf of end users and translate their intent into requests that the backend can evaluate. They operate entirely outside the backend process, run on untrusted devices, and must consume published APIs, sync surfaces, and envelopes without inventing bespoke shortcuts. This overview defines the implementation-ready contract for frontend apps so every surface behaves consistently regardless of product, framework, or deployment.

The document establishes how frontend apps participate in [OperationContext](../../../../02-architecture/services-and-apps/05-operation-context.md) construction, authenticate, honor backend admission decisions, respect ACL limits, handle offline behavior, and report telemetry. It prescribes local storage rules, error handling posture, configuration, release and update mechanics, and secure UX expectations so any conforming frontend can be audited alongside backend components. The specification also enumerates the obligations frontend apps inherit when interacting with system services, app extensions, sync flows, and peer devices.

This overview references:

* [00-scope/**](../../00-scope/)
* [01-protocol/**](../../01-protocol/)
* [02-architecture/01-component-model.md](../../../../02-architecture/01-component-model.md)
* [02-architecture/04-data-flow-overview.md](../../../../02-architecture/04-data-flow-overview.md)
* [02-architecture/managers/**](../../../../02-architecture/managers/00-managers-overview.md)
* [02-architecture/managers/00-managers-overview.md](../../../../02-architecture/managers/00-managers-overview.md)
* [02-architecture/services-and-apps/**](./)
* [02-architecture/services-and-apps/01-services-vs-apps.md](../../../../02-architecture/services-and-apps/01-services-vs-apps.md)
* [02-architecture/services-and-apps/02-system-services.md](../../../../02-architecture/services-and-apps/02-system-services.md)
* [02-architecture/services-and-apps/03-app-backend-extensions.md](../../../../02-architecture/services-and-apps/03-app-backend-extensions.md)
* [02-architecture/services-and-apps/05-operation-context.md](../../../../02-architecture/services-and-apps/05-operation-context.md)
* [04-interfaces/**](../../04-interfaces/)
* [05-security/**](../../05-security/)
* [06-flows/**](../../06-flows/)

### 1.1 Responsibilities and boundaries

This overview is responsible for the following:

* Defining the canonical frontend app model, including layers, execution contexts, and how each context interacts with backend services and managers.
* Describing how frontend apps assemble [OperationContext](../../../../02-architecture/services-and-apps/05-operation-context.md) inputs, authenticate users and devices, request capabilities, and respect ACL policy.
* Detailing transport, sync, configuration, storage, and offline requirements so apps cannot weaken protocol guarantees.
* Capturing observability, telemetry, logging, and diagnostics obligations for frontend behavior so operators can audit requests end-to-end.
* Outlining security, privacy, release, and supply-chain controls for distributing and updating frontend apps across devices.

This overview does not cover the following:

* Backend manager or service implementation details ([02-architecture/managers/**](../managers/), [02-architecture/services-and-apps/02-system-services.md](../../../../02-architecture/services-and-apps/02-system-services.md), [02-architecture/services-and-apps/03-app-backend-extensions.md](../../../../02-architecture/services-and-apps/03-app-backend-extensions.md)).
* Interface definitions already captured in [04-interfaces/**](../../../../04-interfaces/00-interface-overview.md), except where this document must declare missing shapes to keep frontend development unblocked.
* Product-specific UX copy, visual design, or marketing requirements.

## 2. Implementation checklist

Meeting this checklist ensures frontend apps uphold the same structural guarantees as backend components, letting any deployment trust that user intent, access control, and state transitions remain verifiable from UI to graph commit.
