



# 12 Log Manager

Defines log record ingestion, validation, normalization, routing, and sink delivery. Specifies log classes, record schema, retention, and query behavior. Defines failure handling, limits, and trust boundaries for logging.

For the meta specifications, see [12-log-manager meta](../../10-appendix/meta/02-architecture/managers/12-log-manager-meta.md).

Defines structured log ingestion, normalization, routing, and retention for backend records.

Specifies log classes, required metadata, sink behavior, and query constraints.

Defines configuration, failure handling, and security constraints for logging.

## 1. Invariants and guarantees

Across all relevant contexts defined here, the following invariants hold:

* [Log Manager](12-log-manager.md) is the only component allowed to emit structured logs, satisfying the manager invariants described in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* All log records are immutable once accepted. They cannot be edited, deleted, or re-ordered. Retention only expires records based on configured windows.
* Every record is tagged with [OperationContext](../services-and-apps/05-operation-context.md) identifiers (requester identity, app id, trace id, remote/local flag) when an [OperationContext](../services-and-apps/05-operation-context.md) exists. Internal background records use a generated context token so downstream correlation remains deterministic per [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Audit and security logs fail closed. If the primary sink is unavailable, the request that produced the log is rejected unless the emitting manager explicitly overrides per [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* [Log Manager](12-log-manager.md) never infers identities or ACL outcomes. It records the precise inputs supplied by the emitting manager, matching [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md) and [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Logging never mutates graph state and never changes [OperationContext](../services-and-apps/05-operation-context.md) sequencing or ordering, preserving the monotonic guarantees in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Records are serialized using ASCII-safe JSON lines with deterministic field ordering so that replay and auditing remain consistent across nodes.
* [Log Manager](12-log-manager.md) itself produces meta logs when its sinks degrade, so logging failures are observable via the same pipeline.

## 2. Log record classification and structure

### 2.1 Record classes

| Class           | Description                                                                                                                                                                                | Required fields                                                                                 | Primary consumers                       |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- | --------------------------------------- |
| `audit.*`       | Immutable records of user-visible state changes (provisioning, ACL decisions, schema updates) referencing graph objects defined in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).                       | `operation_context`, `global_seq` (if applicable), `actor_identity_id`, `target_ids`, `result`. | Compliance review, peer remediation.    |
| `security.*`    | Authentication failures, admin-gated actions, abuse signals, DoS triggers mandated by [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md), [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md), and the admission logging rules in [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md) (log metadata only, never puzzle payloads). | `operation_context`, `requester_identity_id`, `route`, `failure_code`, `challenge_state`.       | Security monitoring, [DoS Guard Manager](14-dos-guard-manager.md). |
| `operational.*` | Manager lifecycle events, configuration reloads, resource pressure, queue sizes.                                                                                                           | `component`, `state`, `limits`, `latency_ms`.                                                   | [Health Manager](13-health-manager.md), operators.              |
| `diagnostic.*`  | Developer-focused traces gated by configuration. Never emitted in production mode unless `log.diagnostic.enabled` is true.                                                                 | `component`, `message`, `trace_id`.                                                             | Development tooling.                    |

App backends may define additional subclasses under their own namespace (`app.<slug>.audit.*`) but must register them with [Log Manager](12-log-manager.md) via [App Manager](08-app-manager.md) so routing policies remain explicit.

Identifier or namespace violations described in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md) must emit `audit.*` (if the rejection corresponds to a user-visible state change) or `operational.*` logs so the mandatory "record the rejection in the local log" requirement is fulfilled regardless of which manager detects the error.

### 2.2 Log record structure

Every record adheres to the format defined in this specification. Fields include:

| Field               | Description                                                                                                                                                                                                           |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `record_id`         | 128-bit random identifier assigned by [Log Manager](12-log-manager.md).                                                                                                                                                                    |
| `timestamp`         | Monotonic clock timestamp plus wall clock ISO8601 time, both captured at ingestion.                                                                                                                                   |
| `class`             | One of the classes listed above.                                                                                                                                                                                      |
| `component`         | Emitting manager or service name.                                                                                                                                                                                     |
| `operation_context` | Serialized snapshot of the [OperationContext](../services-and-apps/05-operation-context.md) (requester identity id, app id, domain scope, trace id, remote flag) exactly as defined in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md), copying `trace_id` from envelopes per [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md). Absent only for manager bootstrap logs. |
| `category`          | Manager-specific subtype (for example `auth.token_missing`).                                                                                                                                                          |
| `severity`          | Enum (`debug`, `info`, `warn`, `error`, `critical`).                                                                                                                                                                  |
| `payload`           | Structured JSON object containing additional fields defined by the emitting manager.                                                                                                                                  |
| `sinks`             | Computed list of sink identifiers that accepted the record. Used for audit verification.                                                                                                                              |
| `integrity_hash`    | HMAC over the canonicalized record serialized for sinks that require tamper detection.                                                                                                                                |

Records that correspond to committed graph operations must include `global_seq` and operation references to satisfy the auditing guarantees in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).

## 3. Log ingestion and routing lifecycle

[Log Manager](12-log-manager.md) executes a strict ingestion pipeline. Phases must not be reordered or bypassed.

### 3.1 Submission

* Managers invoke the [Log Manager](12-log-manager.md) interface with a fully populated record template and their current [OperationContext](../services-and-apps/05-operation-context.md), matching the construction rules in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Submission occurs via in-process channels. Direct file writes, stdout writes, or network calls are forbidden.
* The submission API enforces backpressure. If the per-component queue is full, the caller receives an explicit `log_queue_full` error and is responsible for retry semantics defined in their spec.

### 3.2 Validation

* [Log Manager](12-log-manager.md) validates the record structure against the schema described in Section 4. Missing required fields, invalid severities, or cross-app leakage cause rejection and synchronous error reporting to the caller.
* Validation ensures the [OperationContext](../services-and-apps/05-operation-context.md) belongs to the emitting manager's declared app scope, preventing unauthorized log injection and enforcing the domain rules in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Validation failures are recorded as `operational.log_validation_failed` entries so the condition is observable.

### 3.3 Normalization

* [Log Manager](12-log-manager.md) assigns `record_id`, stamps timestamps, canonicalizes field ordering, and computes `integrity_hash` for sinks that require tamper detection.
* Records are written into the in-memory journal ring buffer sized by `log.ingest.journal_size`. The journal provides the source of truth for fan-out to sinks and short-lived query APIs.

### 3.4 Routing

* The routing engine consults `log.*` configuration to determine sinks (stdout, rolling files, [Event Manager](11-event-manager.md) feed, telemetry adapters).
* Sinks are evaluated in priority order: audit file -> security file -> stdout -> diagnostic file -> [Event Manager](11-event-manager.md).
* Each sink acknowledges success or declares failure with explicit error codes. Failures are emitted as `operational.log_sink_failed` records and, for mandatory sinks, cause the originating request to fail closed.

### 3.5 Persistence and notification

* File sinks append JSON lines plus chain hashes, as described in Section 12.
* The [Event Manager](11-event-manager.md) bridge emits `system.log_record_created` or `security.log_alert` events referencing the log `record_id` but never attaches the payload for confidential classes. Subscribers fetch the record via the query API under ACL restrictions.
* Telemetry counters update queue depth, sink throughput, and failure metrics for [Health Manager](13-health-manager.md) consumption.

## 4. Inputs and outputs

### 4.1 Inputs

* Structured record submissions from managers and services, carrying [OperationContext](../services-and-apps/05-operation-context.md) metadata.
* Config snapshots from [Config Manager](01-config-manager.md) (`log.*` namespace).
* Health and readiness queries from [Health Manager](13-health-manager.md).
* Retention policy commands initiated by administrative tooling (rotate now, flush sink, snapshot hash chain).

All inputs are trusted only if they originate from registered managers or the backend control plane.

### 4.2 Outputs

* Writable sinks: stdout, stderr (optional), rolling JSON files per class, in-memory query buffers, and optional [Event Manager](11-event-manager.md) signals.
* Read-only query interface that delivers records matching filter criteria (class, component, time window) with pagination and ACL enforcement per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* [Health Manager](13-health-manager.md) signals for readiness (all mandatory sinks writable) and liveness (ingestion loop making progress).
* Integrity attestations: per-file HMAC headers and periodic digest exports for administrative verification.
* Structured alert signals derived from `security.*` records for [DoS Guard Manager](14-dos-guard-manager.md) consumption. Alert forwarding uses [Event Manager](11-event-manager.md) bridging where enabled. It does not include raw confidential payloads.

## 5. Configuration surface (`log.*`)

[Log Manager](12-log-manager.md) owns the `log.*` namespace inside [Config Manager](01-config-manager.md). Primary keys include:

| Key                           | Type                                    | Reloadable | Description                                                                     |
| ----------------------------- | --------------------------------------- | ---------- | ------------------------------------------------------------------------------- |
| `log.level.default`           | Enum (`debug`, `info`, `warn`, `error`) | Yes        | Baseline severity threshold.                                                    |
| `log.level.<component>`       | Enum                                    | Yes        | Per-component overrides.                                                        |
| `log.audit.file_path`         | Path                                    | No         | Absolute path for audit log file. Must reside within the backend writable root. |
| `log.security.file_path`      | Path                                    | No         | Absolute path for security log file.                                            |
| `log.operational.file_path`   | Path                                    | Yes        | Optional operational log file.                                                  |
| `log.stdout.enabled`          | Boolean                                 | Yes        | Enables stdout sink. Required for development mode.                             |
| `log.event_bridge.enabled`    | Boolean                                 | Yes        | Enables the optional [Event Manager](11-event-manager.md) bridge described in Section 9.               |
| `log.retention.days.audit`    | Integer                                 | Yes        | Retention window for audit logs.                                                |
| `log.retention.days.security` | Integer                                 | Yes        | Retention window for security logs.                                             |
| `log.ingest.journal_size`     | Integer                                 | Yes        | Size (in records) of the in-memory ingestion journal.                           |
| `log.diagnostic.enabled`      | Boolean                                 | Yes        | Allows `diagnostic.*` logs to be emitted.                                       |

Startup fails if mandatory keys are missing or invalid. Reloads follow [Config Manager](01-config-manager.md)'s prepare or commit flow. [Log Manager](12-log-manager.md) must acknowledge the reload only after verifying new sinks or limits can be applied without data loss.

## 6. Internal engines and data paths

[Log Manager](12-log-manager.md) is composed of five mandatory internal engines. These engines define strict phase boundaries and must not be collapsed or bypassed.

### 6.1 Submission Engine

Responsibilities:

* Expose in-process submission APIs for managers and services.
* Enforce per-component queue limits and backpressure.
* Tag submissions with the caller's component id and source thread for diagnostics.

Failure behavior:

* If the queue is full, return `log_queue_full` to the caller and emit `operational.log_queue_saturated`.

Constraints:

* Submission Engine never performs normalization or routing. It only buffers records for validation.

### 6.2 Validation Engine

Responsibilities:

* Validate record structure, severity, [OperationContext](../services-and-apps/05-operation-context.md) scope, and class-specific requirements.
* Reject malformed records synchronously with a descriptive error code.

Failure behavior:

* Validation failures generate `operational.log_validation_failed` entries while preserving the original payload for forensic review.

Constraints:

* Validation Engine must not mutate payload fields beyond canonicalizing key order for hash computation.

### 6.3 Normalization Engine

Responsibilities:

* Assign `record_id`, timestamps, and `integrity_hash`.
* Write records to the ingestion journal ring buffer.
* Maintain per-class sequence numbers to support deterministic ordering within sinks.

Failure behavior:

* Journal write failures (for example due to memory pressure) set readiness false and backpressure submissions until capacity is restored.

Constraints:

* Normalization does not drop records silently. It either accepts them fully or returns an error to the Submission Engine.

### 6.4 Routing Engine

Responsibilities:

* Evaluate routing policies and dispatch records to sink adapters.
* Track sink state (ready, degraded, failed) and surface transitions to [Health Manager](13-health-manager.md).
* Invoke the [Event Manager](11-event-manager.md) bridge when `log.event_bridge.enabled` is true.

Failure behavior:

* Mandatory sink failure results in `critical` severity logs plus readiness false. Optional sink failure produces `warn` severity logs but does not block ingestion.

Constraints:

* Routing Engine never modifies record contents beyond adding sink metadata.

### 6.5 Sink Adapter Engine

Responsibilities:

* Implement concrete sinks (stdout writer, rolling file writer with hash chaining, in-memory query cache, [Event Manager](11-event-manager.md) producer).
* Enforce retention windows: delete or archive files older than configured thresholds after verifying integrity hashes.
* Serve read-only query requests by scanning the journal or file tail, applying filters and ACL decisions (admin-only for security or audit logs).

Failure behavior:

* Sink errors must include explicit OS error codes and path metadata for debugging.

Constraints:

* Sink adapters must not block ingestion. File IO occurs asynchronously with bounded buffers.

## 7. Component interactions

* **[Config Manager](01-config-manager.md)**: Supplies `log.*` snapshots. [Log Manager](12-log-manager.md) participates in the prepare and commit reload handshake and emits `operational.config_reload_applied` or `operational.config_reload_rejected` logs.
* **[Event Manager](11-event-manager.md)**: Receives high-priority log-derived events (`system.log_record_created`, `security.log_alert`). [Event Manager](11-event-manager.md) never writes logs. The bridge is one-way.
* **[Health Manager](13-health-manager.md)**: Consumes readiness and liveness data plus sink metrics (queue depth, flush latency). [Log Manager](12-log-manager.md) must flag readiness false when mandatory sinks or the journal are unavailable.
* **[Auth Manager](04-auth-manager.md)**: Provides [OperationContext](../services-and-apps/05-operation-context.md) for HTTP and WebSocket calls. [Log Manager](12-log-manager.md) relies on this context to tag audit entries.
* **[Network Manager](10-network-manager.md) and [DoS Guard Manager](14-dos-guard-manager.md)**: Emit security logs for admission decisions per [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md). [Log Manager](12-log-manager.md) ensures those logs are routed to security sinks and optionally to [Event Manager](11-event-manager.md) while preserving the requirement to log challenge metadata but not raw puzzle payloads. [DoS Guard Manager](14-dos-guard-manager.md) may consume derived alert signals, but [Log Manager](12-log-manager.md) does not initiate mitigations.
* **[Storage Manager](02-storage-manager.md)**: Not used directly. Log retention occurs via filesystem operations performed by [Log Manager](12-log-manager.md) itself.
* **[App Manager](08-app-manager.md)**: Registers app-defined log namespaces and enforces that app services can only emit logs through approved channels.

## 8. Failure handling and rejection behavior

* If validation fails, the caller receives a `log_validation_failed` error and must decide whether to retry or fail their operation, following the rejection precedence rules in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). [Log Manager](12-log-manager.md) records the failure as an operational log.
* If a mandatory sink fails, [Log Manager](12-log-manager.md) marks readiness false, emits a `critical` log, and instructs the caller to reject the original request if logging is part of the acceptance criteria (for example audit-required flows), preserving the fail-closed posture in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* If the in-memory journal is exhausted, [Log Manager](12-log-manager.md) backpressures new submissions and emits `operational.log_journal_full`. Managers experiencing backpressure must either retry with bounded attempts or fail closed, as required by [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Identifier or namespace violations defined in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md) are always captured as `audit.*` or `operational.*` records so that the "record the rejection in the local log" requirement is satisfied regardless of which manager surfaces the error.
* [Log Manager](12-log-manager.md) never drops accepted records silently. If a sink cannot be written after acceptance, the entire process halts (readiness false) until the operator intervenes, ensuring the integrity guarantees described in Section 12.

## 9. Security and trust boundary constraints

* [Log Manager](12-log-manager.md) treats all submission payloads as untrusted. Validation ensures no caller can inject scripts, binary blobs, or unbounded data into sinks.
* Security and audit logs are stored in separate files with restricted file permissions so that secrecy guarantees from [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md) and [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md) remain intact.
* Query APIs enforce ACLs: only admin [OperationContext](../services-and-apps/05-operation-context.md) identities (as defined in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md)) can read security or audit logs. Operational logs may be exposed to broader system operators.
* Integrity hashes use a key stored in process memory that never leaves [Key Manager](03-key-manager.md) custody boundaries described in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md). Operators can export digest snapshots for remote verification.
* [Event Manager](11-event-manager.md) bridges never include the full payload for security or audit entries. Subscribers must possess the right privileges to fetch details via the query API, mirroring the trust boundary rules in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).

## 10. Retention, storage, and backpressure

* Rolling files rotate when size exceeds `log.retention.max_file_mb` (default 100 MB) or when age exceeds configured retention days so that historical audit trails remain aligned with the sequencing expectations in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Before deletion, [Log Manager](12-log-manager.md) writes a manifest containing the file's hash and rotation metadata so integrity proofs remain verifiable.
* In-memory journals store at minimum the last `log.ingest.journal_size` records per class. Older entries are flushed to disk and removed.
* Backpressure thresholds are configurable per class. Security and audit logs reserve capacity to prevent operational chatter from starving critical records.

## 11. Observability and telemetry outputs

[Log Manager](12-log-manager.md) emits the following telemetry:

* Queue depth per component and per class.
* Sink flush latency histograms (files, stdout, event bridge).
* Counts of validation failures, sink failures, and backpressure activations.
* Readiness and liveness flags for [Health Manager](13-health-manager.md).
* Chain hash status for audit or security files (latest block id, last verified timestamp).

Telemetry is routed through [Health Manager](13-health-manager.md) and also recorded as `operational.*` log entries so operators can audit the logging subsystem itself.

## 12. Forbidden behaviors and compliance checklist

The following actions violate this specification:

* Bypassing [Log Manager](12-log-manager.md) by writing directly to stdout, files, or [Event Manager](11-event-manager.md).
  * Exception: the debug logger utility defined in [15-debug-logger.md](../15-debug-logger.md) may emit developer-only diagnostic lines when explicitly enabled; it must not emit structured audit/security/operational records.
* Emitting unstructured text logs or logs without [OperationContext](../services-and-apps/05-operation-context.md) metadata when one exists.
* Rewriting or deleting accepted log entries prior to retention expiry.
* Emitting security or audit payloads through [Event Manager](11-event-manager.md) or other broadcasts that bypass ACL-enforced query APIs.
* Allowing app services to register sinks or routing policies without [App Manager](08-app-manager.md) mediation.

Implementations must demonstrate adherence to the ingestion pipeline, sink integrity guarantees, configuration contracts, and fail-closed behavior described above before the [Log Manager](12-log-manager.md) can be considered complete.
