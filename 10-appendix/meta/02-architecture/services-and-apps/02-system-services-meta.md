



# 02 System Services

## 1. Purpose and scope

System services are the mandatory backend orchestration layers that translate baseline 2WAY capabilities into concrete APIs, scheduled jobs, and automation that every conforming node must expose. They provide provisioning, registry, identity, sync, and operational workflows that all applications rely on regardless of custom code. This overview defines the implementation contract for those services so independent teams can ship compatible runtimes without renegotiating behaviors on a per deployment basis.

This overview establishes the ownership boundaries between system services and protocol managers, codifies the [OperationContext](../../../../02-architecture/services-and-apps/05-operation-context.md) and capability requirements that every service invocation must satisfy, prescribes lifecycle sequencing, and provides an implementation-ready catalog for the default service lineup that ships with the proof of concept. It treats inputs, configuration, observability, and failure handling with the same fail-closed posture mandated elsewhere in the architecture corpus, ensuring these services can never weaken protocol guarantees.

This overview references:

* [01-protocol/**](../../01-protocol/)
* [02-architecture/01-component-model.md](../../../../02-architecture/01-component-model.md)
* [02-architecture/04-data-flow-overview.md](../../../../02-architecture/04-data-flow-overview.md)
* [02-architecture/managers/**](../../../../02-architecture/managers/00-managers-overview.md)
* [02-architecture/managers/00-managers-overview.md](../../../../02-architecture/managers/00-managers-overview.md)
* [02-architecture/services-and-apps/**](./)
* [02-architecture/services-and-apps/01-services-vs-apps.md](../../../../02-architecture/services-and-apps/01-services-vs-apps.md)
* [02-architecture/services-and-apps/05-operation-context.md](../../../../02-architecture/services-and-apps/05-operation-context.md)
* [04-interfaces/**](../../04-interfaces/)
* [05-security/**](../../05-security/)

## 2. Responsibilities and boundaries

This overview is responsible for the following:

* Defining the mandatory system service model for a conforming node, including required services, their responsibilities, and their interface surfaces.
* Defining strict ownership boundaries between system services, managers, apps, and interface layers.
* Defining [OperationContext](../../../../02-architecture/services-and-apps/05-operation-context.md) requirements, capability encoding requirements, and fail-closed behavior for every system service invocation.
* Defining lifecycle sequencing for service startup, readiness gating, shutdown, and upgrades.
* Defining configuration namespaces, schema obligations, capability catalogs, ACL templates, and observability requirements for system services.
* Defining service to manager integration contracts in terms of inputs, outputs, and trust boundaries, including [DoS Guard Manager](../../../../02-architecture/managers/14-dos-guard-manager.md) and [Health Manager](../../../../02-architecture/managers/13-health-manager.md) admission behavior.
* Defining the canonical mandatory system service catalog for the proof of concept, with implementable flows, failure handling, and surface shapes.

This overview does not cover the following:

* Manager internal design, database schemas, or implementation details beyond what system services must rely on via manager APIs.
* App specific business logic beyond the optional app service model.
* Network transport implementation, peer discovery implementation, or handshake protocol details, which are owned by [Network Manager](../../../../02-architecture/managers/10-network-manager.md) and [State Manager](../../../../02-architecture/managers/09-state-manager.md).
* Cryptographic primitive implementation, key storage formats, or private-key signing and decryption algorithms, which are owned by [Key Manager](../../../../02-architecture/managers/03-key-manager.md) and the relevant manager pipelines.
* Full HTTP and WebSocket interface documentation, which is owned by [04-interfaces/**](../../04-interfaces/), except where this file must declare missing shapes to keep implementation unblocked.
* Any future or speculative services not listed in the proof of concept catalog.
