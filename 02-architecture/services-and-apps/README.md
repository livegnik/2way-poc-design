



# Services and apps

This folder defines how services and apps fit into the manager-centric 2WAY backend. It specifies
the taxonomy of services and apps, their trust boundaries, lifecycle rules, and the mandatory
`OperationContext` contract used to invoke managers.

If a requirement here conflicts with another folder, record the exception as an ADR and treat this
folder as the authoritative source for service/app roles and constraints.

## What lives here

- [`00-services-and-apps-overview.md`](00-services-and-apps-overview.md) - Taxonomy, invariants, and flow summary.
- [`01-services-vs-apps.md`](01-services-vs-apps.md) - Service/app boundaries and shared rules.
- [`02-system-services.md`](02-system-services.md) - Mandatory system services and their contracts.
- [`03-app-services.md`](03-app-services.md) - App service lifecycle and constraints.
- [`04-frontend-apps.md`](04-frontend-apps.md) - Frontend responsibilities and security posture.
- [`05-operation-context.md`](05-operation-context.md) - `OperationContext` structure and lifecycle.

Each document has a corresponding meta specification in [`10-appendix/meta/02-architecture/services-and-apps/`](../../10-appendix/meta/02-architecture/services-and-apps/).

## How to read

1. Start with [`00-services-and-apps-overview.md`](00-services-and-apps-overview.md) for taxonomy and invariants.
2. Read [`01-services-vs-apps.md`](01-services-vs-apps.md) for boundary rules.
3. Use [`02-system-services.md`](02-system-services.md) and [`03-app-services.md`](03-app-services.md) for backend service behavior.
4. Read [`04-frontend-apps.md`](04-frontend-apps.md) for client posture.
5. Keep [`05-operation-context.md`](05-operation-context.md) open for request context rules.

## Key guarantees this folder enforces

- Managers own protocol enforcement; services orchestrate only and never bypass managers.
- Services run in-process but are treated as untrusted by managers.
- Frontend apps are fully untrusted clients.
- Every request supplies a complete, immutable [`OperationContext`](05-operation-context.md).
- Local `OperationContext` construction is owned by Auth Manager and App Manager.
- Remote `OperationContext` construction is owned by State Manager.
- Validation order is fixed by managers: structural -> schema -> ACL -> sequencing -> persistence.
- App isolation is enforced by `app_id`; cross-app access requires explicit schema + ACL approval.
- Services and apps never create alternate write paths; derived caches are non-authoritative.
- System services and app services are unloadable without breaking global correctness.
- Startup/shutdown follows readiness gates; services register only after managers are ready.

## Using this folder in reviews

- Treat any service that touches storage, keys, or sockets directly as non-compliant.
- Verify [`OperationContext`](05-operation-context.md) binding for every service call and background job.
- Ensure app services can be removed without impacting core invariants.
