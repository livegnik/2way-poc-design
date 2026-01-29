



## 1. Purpose and scope

The Health Manager is the authoritative component that evaluates, aggregates, and publishes the liveness and readiness state of the 2WAY node runtime. It collects health signals from all managers, internal services, and runtime subsystems; enforces the fail-closed posture defined in the protocol; and exposes a single source of truth to operators, diagnostic tools, and optionally Event Manager when critical transitions occur. Health Manager does not mutate graph state or perform remediation. Its role is detection, classification, and publication.

This specification defines the health classification model, responsibilities, input and output contracts, internal engines, configuration surface, and interactions with other managers. It references only the protocol contracts defined in:

* [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md)
* [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md)
* [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md)
* [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md)
* [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md)

Those files remain normative for all behaviors described here.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Owning the single authoritative readiness (`ready`/`not_ready`) and liveness (`alive`/`dead`) state for the node runtime, keeping these states aligned with the fail-closed rules in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Collecting periodic health samples and event-driven signals from every manager ([Config Manager](01-config-manager.md), [Storage Manager](02-storage-manager.md), [Graph Manager](07-graph-manager.md), [Schema Manager](05-schema-manager.md), [ACL Manager](06-acl-manager.md), [Key Manager](03-key-manager.md), [Auth Manager](04-auth-manager.md), [App Manager](08-app-manager.md), [State Manager](09-state-manager.md), [Network Manager](10-network-manager.md), [Event Manager](11-event-manager.md), [Log Manager](12-log-manager.md), [DoS Guard Manager](14-dos-guard-manager.md)) plus critical services (HTTP/WebSocket loop, scheduler, transport adapters).
* Evaluating collected signals against deterministic thresholds (latency ceilings, queue depth caps, error rates) and generating health conclusions per subsystem.
* Publishing health state via in-process subscription APIs, the admin HTTP surface described in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) ([OperationContext](../services-and-apps/05-operation-context.md) driven), and optional [Event Manager](11-event-manager.md) notifications (`system.health_state_changed`, `security.health_degraded`) without leaking sensitive metadata.
* Recording health transitions as structured logs routed through [Log Manager](12-log-manager.md).
* Enforcing access control for health queries. Only administrative identities defined by [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md) can retrieve privileged health details.
* Providing a single place where [DoS Guard Manager](14-dos-guard-manager.md), [Log Manager](12-log-manager.md), and operators can learn when the node runtime intentionally stops accepting traffic due to local degradation, aligning with DoS Guard escalation rules in [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).

This specification does not cover the following:

* Automatic remediation, restart logic, or hardware-level monitoring.
* Service-specific diagnostics or deep metrics (e.g., [Graph Manager](07-graph-manager.md) internal counters). [Health Manager](13-health-manager.md) references only the signals that other managers emit.
* UI dashboards, notification routing outside [Event Manager](11-event-manager.md), or long-term metrics retention.
