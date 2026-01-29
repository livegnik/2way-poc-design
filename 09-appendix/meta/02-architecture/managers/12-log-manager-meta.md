



## 1. Purpose and scope

The Log Manager is the authoritative component responsible for the scope described below. The Log Manager is the sole authority for structured logging, audit capture, diagnostics, and notification bridging inside the 2WAY backend. It ingests structured log records from every manager and service, enforces mandatory metadata, normalizes each record, and routes it to the configured sinks (local files, stdout, in-memory buffers, and Event Manager bridges) without allowing any caller to bypass protocol-defined observability rules.

This specification defines the log record model, responsibility boundaries, ingestion and routing pipeline, configuration surface, retention and query posture, security constraints, and component interactions. It does not define frontend tooling, UI dashboards, or external SIEM integrations.

This specification consumes the protocol contracts defined in:

* [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md)
* [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md)
* [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md)
* [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md)
* [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md)
* [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md)

Those files remain normative for log classification, [OperationContext](../services-and-apps/05-operation-context.md) semantics, identifier rejection requirements, trace correlation, DoS Guard admission telemetry, and failure handling behavior.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Owning every backend logging surface. No component writes logs directly to stdout, files, or remote channels. All records pass through [Log Manager](12-log-manager.md).
* Enforcing the structured record format defined in this specification and ensuring records include the [OperationContext](../services-and-apps/05-operation-context.md) metadata necessary to map failures back to requesters or peers.
* Maintaining separate pipelines for audit logs, security logs, operational diagnostics, and development traces without allowing cross-contamination, satisfying the observability requirements in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Applying routing policies from `log.*` configuration and guaranteeing that mandatory sinks (local audit file, stdout) are always populated if enabled so protocol-defined failure visibility ([01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md)) is preserved.
* Bridging critical events to [Event Manager](11-event-manager.md) (for example `security.*` notifications) without duplicating [Event Manager](11-event-manager.md) responsibilities, ensuring the failure propagation posture in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md) remains intact.
* Providing bounded retention per sink, including rolling files with integrity markers so audit logs remain verifiable.
* Guaranteeing that identifier and namespace rejection events mandated by [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md) are recorded as structured logs so [Graph Manager](07-graph-manager.md) and [Schema Manager](05-schema-manager.md) satisfy the protocol logging requirement.
* Exposing structured log query APIs to managers and admin tooling (read-only, rate limited) as described in Section 6.2.
* Emitting health signals to [Health Manager](13-health-manager.md) and [Log Manager](12-log-manager.md) self-diagnostics (meta logs) when sinks or pipelines degrade.
* Forwarding abuse and alarm conditions to [DoS Guard Manager](14-dos-guard-manager.md) via structured `security.*` records and optional alert events, without shifting admission control responsibilities, and ensuring per [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md) that challenge metadata is logged while private puzzle payloads stay out of sinks.

This specification does not cover the following:

* Schema validation, ACL enforcement, or graph writes. [Log Manager](12-log-manager.md) never mutates the graph and never participates in [OperationContext](../services-and-apps/05-operation-context.md) authorization.
* Transport-level telemetry for remote peers. [Network Manager](10-network-manager.md) and [DoS Guard Manager](14-dos-guard-manager.md) own admission telemetry and challenge state. [Log Manager](12-log-manager.md) only records what they emit.
* Event subscription semantics. [Event Manager](11-event-manager.md) owns event delivery. [Log Manager](12-log-manager.md) only optionally mirrors high-severity records into the event pipeline according to the interaction rules in Section 9.
* UI dashboards, CLI formatting, or external SIEM connectors. Those integrations sit outside the PoC scope.
