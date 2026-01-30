



# 02 Architecture

This folder defines how the 2WAY backend enforces the protocol. It specifies manager and service
boundaries, trust posture, runtime topologies, and the only permitted data flows. These documents
turn protocol rules into concrete responsibilities and sequencing guarantees.

If an architectural requirement conflicts with another folder, record the exception as an ADR and
treat this folder as the authoritative source for backend enforcement behavior.

## What lives here

- `00-architecture-overview.md` - Architectural posture, invariants, and data-flow sequencing.
- `01-component-model.md` - Manager and service boundaries and responsibilities.
- `02-runtime-topologies.md` - Conforming deployment topologies and constraints.
- `03-trust-boundaries.md` - Trust boundary definitions and fail-closed posture.
- `04-data-flow-overview.md` - The only permitted runtime data flows.
- `managers/` - Normative specifications for each manager and its authority.
- `services-and-apps/` - Service, app, and `OperationContext` specifications.

Each document has a corresponding meta specification in `09-appendix/meta/02-architecture/`.

## How to read

1. Start with `00-architecture-overview.md` for posture and invariants.
2. Read `01-component-model.md` to learn manager and service boundaries.
3. Use `03-trust-boundaries.md` for fail-closed trust posture.
4. Read `04-data-flow-overview.md` to understand the only permitted flows.
5. Reference `managers/` and `services-and-apps/` for component-level detail.

## Key guarantees this folder enforces

- The backend is a long-lived process composed of singleton managers and services.
- Managers are the sole authorities for their domains; responsibilities do not overlap.
- Graph Manager is the only write authority; Storage Manager is the only raw database authority.
- Schema Manager is the only schema interpreter; ACL Manager is the only authorization authority.
- Key Manager is the only component allowed to access private keys.
- Network access is owned by Network Manager, gated by DoS Guard Manager admission control.
- State Manager is the only producer and consumer of sync packages.
- Services are untrusted, cannot bypass managers, and never touch storage, keys, or sockets directly.
- All request-scoped work is bound to a complete, immutable `OperationContext`.
- Trust boundaries fail closed; violations are rejected without side effects.
- Accepted writes are sequenced monotonically and applied atomically.
- Ratings provide suppression semantics; there is no delete path.
- Derived data and caches are non-authoritative and never become write paths.
- Events and logs are read-only outputs and cannot mutate state.

## Using this folder in reviews

- Treat any bypass of manager boundaries or data-flow sequencing as non-compliant.
- Ensure service logic does not assume authority or touch forbidden resources.
- Verify failure paths reject early and do not create partial state.
