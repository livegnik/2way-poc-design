



# 00 Services and Apps Overview

Defines how services and apps fit into the manager-centric 2WAY architecture. Specifies shared invariants, trust boundaries, and lifecycle ordering for services and apps. Summarizes end-to-end flows for local requests and remote sync packages.

For the meta specifications, see [00-services-and-apps-overview meta](../09-appendix/meta/02-architecture/services-and-apps/00-services-and-apps-overview-meta.md).

## 1. Service and application taxonomy

The architecture separates backend orchestration from application identity and frontend experiences. The key constructs are:

| Construct | Definition | Scope | Execution location |
| --- | --- | --- | --- |
| System service | Mandatory backend service that ships with every node and runs under `app_0`. | Platform-wide | Backend process |
| App backend extension service | Optional backend service bound to one app slug and `app_id`. | Single app | Backend process |
| Application (app) | Registered identity with schemas, ACL policy, and UX semantics. | Single app | [App Manager](../managers/08-app-manager.md) registry |
| Frontend app | Untrusted client surface that consumes backend APIs or sync flows. | Single app | Outside backend |

The taxonomy is formalized in [02-architecture/services-and-apps/01-services-vs-apps.md](01-services-vs-apps.md). The operational contracts for each class are defined in [02-architecture/services-and-apps/02-system-services.md](02-system-services.md), [02-architecture/services-and-apps/03-app-backend-extensions.md](03-app-backend-extensions.md), and [02-architecture/services-and-apps/04-frontend-apps.md](04-frontend-apps.md).

## 2. Shared invariants

All services and apps must uphold the following invariants:

1. **Manager-only authority**: Managers own protocol invariants, persistence, cryptography, authorization, and transport. Services orchestrate manager calls and never bypass them.
2. **[OperationContext](05-operation-context.md) discipline**: Every request and job supplies a complete, immutable [OperationContext](05-operation-context.md) as defined in [02-architecture/services-and-apps/05-operation-context.md](05-operation-context.md).
3. **Fail-closed posture**: Missing or malformed inputs are rejected before schema or ACL evaluation. Ambiguous cases never default to success.
4. **Trust boundaries**: Services run in-process but are treated as untrusted by managers. Frontend apps are fully untrusted clients.
5. **App isolation**: App domains are isolated by `app_id`. Cross-app access is allowed only when schema and ACL policy explicitly permit it.

## 3. End-to-end flow summary

Services and apps participate in a single data-flow pipeline governed by managers. The entry path differs for local requests versus remote sync packages, but both converge on the manager sequencing rules.

1. A frontend app submits a request through the interface layer ([04-interfaces/**](../../04-interfaces/)). [Auth Manager](../managers/04-auth-manager.md) validates credentials and binds local identity. [App Manager](../managers/08-app-manager.md) resolves the `app_id`. The interface layer then constructs the [OperationContext](05-operation-context.md).
2. A remote peer submits a sync package through [Network Manager](../managers/10-network-manager.md). [DoS Guard Manager](../managers/14-dos-guard-manager.md) admission, [Key Manager](../managers/03-key-manager.md) verification, and [State Manager](../managers/09-state-manager.md) ordering occur before any graph mutation; [State Manager](../managers/09-state-manager.md) constructs the remote [OperationContext](05-operation-context.md).
3. The service (system or extension) validates input and invokes managers in the required order, with [Graph Manager](../managers/07-graph-manager.md) orchestrating the sequence (structural validation -> schema validation -> ACL evaluation -> graph sequencing -> persistence -> event emission) as described in [02-architecture/04-data-flow-overview.md](../04-data-flow-overview.md).
4. Manager responses propagate back to the caller unchanged, and [Log Manager](../managers/12-log-manager.md) records a full audit trail.

[OperationContext](05-operation-context.md) construction is owned by the interface layer for local requests (after [Auth Manager](../managers/04-auth-manager.md) + [App Manager](../managers/08-app-manager.md) binding) and by [State Manager](../managers/09-state-manager.md) for remote sync packages. The resulting context is immutable for the lifetime of the operation.

Services and apps never create alternate write paths. Derived caches are allowed but non-authoritative and rebuilt from graph state.

## 4. Lifecycle and readiness

Services and apps follow a deterministic lifecycle so readiness is observable and fail-closed:

* Managers initialize first and declare readiness.
* [App Manager](../managers/08-app-manager.md) loads application identities and extension metadata.
* System services start and register their surfaces.
* App extension services load only after their owning app schema validates.
* Frontend endpoints and scheduled jobs register only after readiness gates pass.

Shutdown reverses this order. Extension services must be unloadable without global impact, and frontend apps must tolerate missing or disabled extensions.

## 5. Document map

Use the following documents for detailed requirements:

* [02-architecture/services-and-apps/01-services-vs-apps.md](01-services-vs-apps.md) for taxonomy, invariants, and shared rules.
* [02-architecture/services-and-apps/02-system-services.md](02-system-services.md) for mandatory system services and their contracts.
* [02-architecture/services-and-apps/03-app-backend-extensions.md](03-app-backend-extensions.md) for app extension lifecycle, packaging, and constraints.
* [02-architecture/services-and-apps/04-frontend-apps.md](04-frontend-apps.md) for frontend app responsibilities and security posture.
* [02-architecture/services-and-apps/05-operation-context.md](05-operation-context.md) for [OperationContext](05-operation-context.md) structure and lifecycle rules.

Together these specifications define how services and apps operate safely within the 2WAY manager fabric.
