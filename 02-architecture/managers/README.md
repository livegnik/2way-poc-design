



# Managers

This folder specifies the singleton managers that enforce the 2WAY backend. Each manager owns a
single responsibility, exposes a strict interface, and participates in the enforced validation,
authorization, sequencing, and observability pipeline.

If a manager requirement conflicts with other folders, record the exception as an ADR and treat this
folder as the authoritative source for manager responsibilities and boundaries.

## What lives here

- [`00-managers-overview.md`](00-managers-overview.md) - System-wide manager invariants, dependencies, and execution flows.
- [`01-config-manager.md`](01-config-manager.md) - Configuration ingestion and reload sequencing.
- [`02-storage-manager.md`](02-storage-manager.md) - SQLite lifecycle, transactions, and sequence allocation.
- [`03-key-manager.md`](03-key-manager.md) - Private key custody and cryptographic operations.
- [`04-auth-manager.md`](04-auth-manager.md) - Session validation and `OperationContext` binding for local calls.
- [`05-schema-manager.md`](05-schema-manager.md) - Schema compilation, type resolution, and validation.
- [`06-acl-manager.md`](06-acl-manager.md) - Authorization for all reads and writes.
- [`07-graph-manager.md`](07-graph-manager.md) - Single write path and authoritative read surface.
- [`08-app-manager.md`](08-app-manager.md) - App registration, app identities, and extension wiring.
- [`09-state-manager.md`](09-state-manager.md) - Sync metadata and package coordination.
- [`10-network-manager.md`](10-network-manager.md) - Transport surfaces and edge cryptography.
- [`11-event-manager.md`](11-event-manager.md) - Event publication and subscriber enforcement.
- [`12-log-manager.md`](12-log-manager.md) - Structured logging and audit sinks.
- [`13-health-manager.md`](13-health-manager.md) - Readiness/liveness aggregation.
- [`14-dos-guard-manager.md`](14-dos-guard-manager.md) - Admission control and client puzzles.

Each document has a corresponding meta specification in [`09-appendix/meta/02-architecture/managers/`](../../09-appendix/meta/02-architecture/managers/).

## How to read

1. Start with [`00-managers-overview.md`](00-managers-overview.md) for the shared invariants and dependencies.
2. Read the core enforcement managers ([`02-storage-manager.md`](02-storage-manager.md),
   [`05-schema-manager.md`](05-schema-manager.md), [`06-acl-manager.md`](06-acl-manager.md),
   [`07-graph-manager.md`](07-graph-manager.md)) in order.
3. Review edge managers ([`03-key-manager.md`](03-key-manager.md), [`10-network-manager.md`](10-network-manager.md),
   [`14-dos-guard-manager.md`](14-dos-guard-manager.md)) for ingress/egress guarantees.
4. Finish with observability and control ([`11-event-manager.md`](11-event-manager.md),
   [`12-log-manager.md`](12-log-manager.md), [`13-health-manager.md`](13-health-manager.md),
   [`01-config-manager.md`](01-config-manager.md)).

## Key guarantees this folder enforces

- Managers are singleton authorities with non-overlapping responsibilities.
- Managers communicate only through validated in-process APIs; dependency cycles are forbidden.
- Graph Manager is the only write path; Storage Manager is the only raw database path.
- Schema Manager is the only schema interpreter; ACL Manager is the only authorization authority.
- Key Manager is the only component that accesses private keys.
- Auth Manager binds local requests to a complete [`OperationContext`](../services-and-apps/05-operation-context.md).
- State Manager coordinates sync metadata and package construction; it does not write graph state.
- Network Manager owns transport and admission, gated by DoS Guard Manager.
- Protocol validation order is fixed: structural -> schema -> ACL -> persistence.
- App namespaces remain isolated across managers; mixed-context envelopes are rejected.
- Configuration and graph data are separate; only Config Manager updates configuration.
- Log Manager is the only structured logging surface; Event Manager is the only event surface.
- Health Manager is the only readiness/liveness authority; readiness gates admissions.
- Failures are fail-closed; invalid input produces no partial state or side effects.

## Using this folder in reviews

- Treat any manager bypass or overlapping authority as non-compliant.
- Verify that manager dependencies and ordering follow [`00-managers-overview.md`](00-managers-overview.md).
- Ensure admission, validation, sequencing, and observability flow through the owning managers only.
