



# 12 Log Manager

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
