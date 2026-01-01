# 12 Log Manager

## 1. Purpose and scope

The Log Manager is the sole authority for structured logging, audit capture, diagnostics, and notification bridging inside the 2WAY backend. It ingests structured log records from every manager and service, enforces mandatory metadata, normalizes each record, and routes it to the configured sinks (local files, stdout, in-memory buffers, and Event Manager bridges) without allowing any caller to bypass protocol-defined observability rules.

This specification defines the log record model, responsibility boundaries, ingestion and routing pipeline, configuration surface, retention and query posture, security constraints, and component interactions. It does not define frontend tooling, UI dashboards, or external SIEM integrations.

This specification consumes the protocol contracts defined in:

* `01-protocol/00-protocol-overview.md`
* `01-protocol/02-object-model.md`
* `01-protocol/05-keys-and-identity.md`
* `01-protocol/06-access-control-model.md`
* `01-protocol/07-sync-and-consistency.md`
* `01-protocol/08-network-transport-requirements.md`
* `01-protocol/09-errors-and-failure-modes.md`

Those files remain normative for log classification, OperationContext semantics, and failure handling behavior.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Owning every backend logging surface. No component writes logs directly to stdout, files, or remote channels. All records pass through Log Manager.
* Enforcing the structured record format defined in this specification and ensuring records include the OperationContext metadata necessary to map failures back to requesters or peers.
* Maintaining separate pipelines for audit logs, security logs, operational diagnostics, and development traces without allowing cross-contamination, satisfying the observability requirements in `01-protocol/09-errors-and-failure-modes.md`.
* Applying routing policies from `log.*` configuration and guaranteeing that mandatory sinks (local audit file, stdout) are always populated if enabled so protocol-defined failure visibility (`01-protocol/09-errors-and-failure-modes.md`) is preserved.
* Bridging critical events to Event Manager (for example `security.*` notifications) without duplicating Event Manager responsibilities, ensuring the failure propagation posture in `01-protocol/09-errors-and-failure-modes.md` remains intact.
* Providing bounded retention per sink, including rolling files with integrity markers so audit logs remain verifiable.
* Exposing structured log query APIs to managers and admin tooling (read-only, rate limited) as described in Section 6.2.
* Emitting health signals to Health Manager and Log Manager self-diagnostics (meta logs) when sinks or pipelines degrade.

This specification does not cover the following:

* Schema validation, ACL enforcement, or graph writes. Log Manager never mutates the graph and never participates in OperationContext authorization.
* Transport-level telemetry for remote peers. Network Manager and DoS Guard Manager own admission telemetry and challenge state; Log Manager only records what they emit.
* Event subscription semantics. Event Manager owns event delivery. Log Manager only optionally mirrors high-severity records into the event pipeline according to the interaction rules in Section 9.
* UI dashboards, CLI formatting, or external SIEM connectors. Those integrations sit outside the PoC scope.

## 3. Invariants and guarantees

Across all relevant contexts defined here, the following invariants hold:

* Log Manager is the only component allowed to emit structured logs, satisfying the invariant in `02-architecture/01-component-model.md`.
* All log records are immutable once accepted. They cannot be edited, deleted, or re-ordered; retention only expires records based on configured windows.
* Every record is tagged with `OperationContext` identifiers (requester identity, app id, trace id, remote/local flag) when an OperationContext exists. Internal background records use a generated context token so downstream correlation remains deterministic per `01-protocol/00-protocol-overview.md`.
* Audit and security logs fail closed. If the primary sink is unavailable, the request that produced the log is rejected unless the emitting manager explicitly overrides per `01-protocol/09-errors-and-failure-modes.md`.
* Log Manager never infers identities or ACL outcomes. It records the precise inputs supplied by the emitting manager, matching `01-protocol/05-keys-and-identity.md` and `01-protocol/06-access-control-model.md`.
* Logging never mutates graph state and never changes OperationContext sequencing or ordering, preserving the monotonic guarantees in `01-protocol/07-sync-and-consistency.md`.
* Records are serialized using ASCII-safe JSON lines with deterministic field ordering so that replay and auditing remain consistent across nodes.
* Log Manager itself produces meta logs when its sinks degrade, so logging failures are observable via the same pipeline.

## 4. Log record classification and structure

### 4.1 Record classes

| Class | Description | Required fields | Primary consumers |
| --- | --- | --- | --- |
| `audit.*` | Immutable records of user-visible state changes (provisioning, ACL decisions, schema updates) referencing graph objects defined in `01-protocol/02-object-model.md`. | `operation_context`, `global_seq` (if applicable), `actor_identity_id`, `target_ids`, `result`. | Compliance review, peer remediation. |
| `security.*` | Authentication failures, admin-gated actions, abuse signals, DoS triggers mandated by `01-protocol/08-network-transport-requirements.md` and `01-protocol/09-errors-and-failure-modes.md`. | `operation_context`, `requester_identity_id`, `route`, `failure_code`, `challenge_state`. | Security monitoring, DoS Guard Manager. |
| `operational.*` | Manager lifecycle events, configuration reloads, resource pressure, queue sizes. | `component`, `state`, `limits`, `latency_ms`. | Health Manager, operators. |
| `diagnostic.*` | Developer-focused traces gated by configuration. Never emitted in production mode unless `log.diagnostic.enabled` is true. | `component`, `message`, `trace_id`. | Development tooling. |

App backends may define additional subclasses under their own namespace (`app.<app_id>.audit.*`) but must register them with Log Manager via App Manager so routing policies remain explicit.

### 4.2 Log record structure

Every record adheres to the format defined in this specification. Fields include:

| Field | Description |
| --- | --- |
| `record_id` | 128-bit random identifier assigned by Log Manager. |
| `timestamp` | Monotonic clock timestamp plus wall clock ISO8601 time, both captured at ingestion. |
| `class` | One of the classes listed above. |
| `component` | Emitting manager or service name. |
| `operation_context` | Serialized snapshot of the OperationContext (requester identity id, app id, domain scope, trace id, remote flag) exactly as defined in `01-protocol/00-protocol-overview.md`. Absent only for manager bootstrap logs. |
| `category` | Manager-specific subtype (for example `auth.session_token_missing`). |
| `severity` | Enum (`debug`, `info`, `warn`, `error`, `critical`). |
| `payload` | Structured JSON object containing additional fields defined by the emitting manager. |
| `sinks` | Computed list of sink identifiers that accepted the record. Used for audit verification. |
| `integrity_hash` | HMAC over the canonicalized record serialized for sinks that require tamper detection. |

Records that correspond to committed graph operations must include `global_seq` and operation references to satisfy the auditing guarantees in `01-protocol/07-sync-and-consistency.md`.

## 5. Log ingestion and routing lifecycle

Log Manager executes a strict ingestion pipeline. Phases must not be reordered or bypassed.

### 5.1 Phase 1 - Submission

* Managers invoke the Log Manager interface with a fully populated record template and their current OperationContext, matching the construction rules in `01-protocol/00-protocol-overview.md`.
* Submission occurs via in-process channels. Direct file writes, stdout writes, or network calls are forbidden.
* The submission API enforces backpressure. If the per-component queue is full, the caller receives an explicit `log_queue_full` error and is responsible for retry semantics defined in their spec.

### 5.2 Phase 2 - Validation

* Log Manager validates the record structure against the schema described in Section 4. Missing required fields, invalid severities, or cross-app leakage cause rejection and synchronous error reporting to the caller.
* Validation ensures the OperationContext belongs to the emitting manager's declared app scope, preventing unauthorized log injection and enforcing the domain rules in `01-protocol/06-access-control-model.md`.
* Validation failures are recorded as `operational.log_validation_failed` entries so the condition is observable.

### 5.3 Phase 3 - Normalization

* Log Manager assigns `record_id`, stamps timestamps, canonicalizes field ordering, and computes `integrity_hash` for sinks that require tamper detection.
* Records are written into the in-memory journal ring buffer sized by `log.ingest.journal_size`. The journal provides the source of truth for fan-out to sinks and short-lived query APIs.

### 5.4 Phase 4 - Routing

* The routing engine consults `log.*` configuration to determine sinks (stdout, rolling files, Event Manager feed, telemetry adapters).
* Sinks are evaluated in priority order: audit file -> security file -> stdout -> diagnostic file -> Event Manager.
* Each sink acknowledges success or declares failure with explicit error codes. Failures are emitted as `operational.log_sink_failed` records and, for mandatory sinks, cause the originating request to fail closed.

### 5.5 Phase 5 - Persistence and notification

* File sinks append JSON lines plus chain hashes, as described in Section 12.
* The Event Manager bridge emits `system.log_record_created` or `security.log_alert` events referencing the log `record_id` but never attaches the payload for confidential classes; subscribers fetch the record via the query API under ACL restrictions.
* Telemetry counters update queue depth, sink throughput, and failure metrics for Health Manager consumption.

## 6. Inputs and outputs

### 6.1 Inputs

* Structured record submissions from managers and services, carrying OperationContext metadata.
* Config snapshots from Config Manager (`log.*` namespace).
* Health and readiness queries from Health Manager.
* Retention policy commands initiated by administrative tooling (rotate now, flush sink, snapshot hash chain).

All inputs are trusted only if they originate from registered managers or the backend control plane.

### 6.2 Outputs

* Writable sinks: stdout, stderr (optional), rolling JSON files per class, in-memory query buffers, and optional Event Manager signals.
* Read-only query interface that delivers records matching filter criteria (class, component, time window) with pagination and ACL enforcement per `01-protocol/06-access-control-model.md`.
* Health Manager signals for readiness (all mandatory sinks writable) and liveness (ingestion loop making progress).
* Integrity attestations: per-file HMAC headers and periodic digest exports for administrative verification.

## 7. Configuration surface (`log.*`)

Log Manager owns the `log.*` namespace inside Config Manager. Primary keys include:

| Key | Type | Reloadable | Description |
| --- | --- | --- | --- |
| `log.level.default` | Enum (`debug`, `info`, `warn`, `error`) | Yes | Baseline severity threshold. |
| `log.level.<component>` | Enum | Yes | Per-component overrides. |
| `log.audit.file_path` | Path | No | Absolute path for audit log file. Must reside within the backend writable root. |
| `log.security.file_path` | Path | No | Absolute path for security log file. |
| `log.operational.file_path` | Path | Yes | Optional operational log file. |
| `log.stdout.enabled` | Boolean | Yes | Enables stdout sink. Required for development mode. |
| `log.event_bridge.enabled` | Boolean | Yes | Enables the optional Event Manager bridge described in Section 9. |
| `log.retention.days.audit` | Integer | Yes | Retention window for audit logs. |
| `log.retention.days.security` | Integer | Yes | Retention window for security logs. |
| `log.ingest.journal_size` | Integer | Yes | Size (in records) of the in-memory ingestion journal. |
| `log.diagnostic.enabled` | Boolean | Yes | Allows `diagnostic.*` logs to be emitted. |

Startup fails if mandatory keys are missing or invalid. Reloads follow Config Manager's prepare/commit flow; Log Manager must acknowledge the reload only after verifying new sinks or limits can be applied without data loss.

## 8. Internal engines and data paths

Log Manager is composed of five mandatory internal engines. These engines define strict phase boundaries and must not be collapsed or bypassed.

### 8.1 Submission Engine

Responsibilities:

* Expose in-process submission APIs for managers and services.
* Enforce per-component queue limits and backpressure.
* Tag submissions with the caller's component id and source thread for diagnostics.

Failure behavior:

* If the queue is full, return `log_queue_full` to the caller and emit `operational.log_queue_saturated`.

Constraints:

* Submission Engine never performs normalization or routing. It only buffers records for validation.

### 8.2 Validation Engine

Responsibilities:

* Validate record structure, severity, OperationContext scope, and class-specific requirements.
* Reject malformed records synchronously with a descriptive error code.

Failure behavior:

* Validation failures generate `operational.log_validation_failed` entries while preserving the original payload for forensic review.

Constraints:

* Validation Engine must not mutate payload fields beyond canonicalizing key order for hash computation.

### 8.3 Normalization Engine

Responsibilities:

* Assign `record_id`, timestamps, and `integrity_hash`.
* Write records to the ingestion journal ring buffer.
* Maintain per-class sequence numbers to support deterministic ordering within sinks.

Failure behavior:

* Journal write failures (for example due to memory pressure) set readiness false and backpressure submissions until capacity is restored.

Constraints:

* Normalization does not drop records silently. It either accepts them fully or returns an error to the Submission Engine.

### 8.4 Routing Engine

Responsibilities:

* Evaluate routing policies and dispatch records to sink adapters.
* Track sink state (ready, degraded, failed) and surface transitions to Health Manager.
* Invoke the Event Manager bridge when `log.event_bridge.enabled` is true.

Failure behavior:

* Mandatory sink failure results in `critical` severity logs plus readiness false. Optional sink failure produces `warn` severity logs but does not block ingestion.

Constraints:

* Routing Engine never modifies record contents beyond adding sink metadata.

### 8.5 Sink Adapter Engine

Responsibilities:

* Implement concrete sinks (stdout writer, rolling file writer with hash chaining, in-memory query cache, Event Manager producer).
* Enforce retention windows: delete or archive files older than configured thresholds after verifying integrity hashes.
* Serve read-only query requests by scanning the journal or file tail, applying filters and ACL decisions (admin-only for security/audit logs).

Failure behavior:

* Sink errors must include explicit OS error codes and path metadata for debugging.

Constraints:

* Sink adapters must not block ingestion. File IO occurs asynchronously with bounded buffers.

## 9. Component interactions

* **Config Manager**: Supplies `log.*` snapshots. Log Manager participates in the prepare/commit reload handshake and emits `operational.config_reload_applied` or `operational.config_reload_rejected` logs.
* **Event Manager**: Receives high-priority log-derived events (`system.log_record_created`, `security.log_alert`). Event Manager never writes logs; the bridge is one-way.
* **Health Manager**: Consumes readiness/liveness data plus sink metrics (queue depth, flush latency). Log Manager must flag readiness false when mandatory sinks or the journal are unavailable.
* **Auth Manager**: Provides OperationContext for HTTP/WebSocket calls. Log Manager relies on this context to tag audit entries.
* **Network Manager / DoS Guard Manager**: Emit security logs for admission decisions. Log Manager ensures those logs are routed to security sinks and optionally to Event Manager.
* **Storage Manager**: Not used directly. Log retention occurs via filesystem operations performed by Log Manager itself.
* **App Manager**: Registers app-defined log namespaces and enforces that app extension services can only emit logs through approved channels.

## 10. Failure handling and rejection behavior

* If validation fails, the caller receives a `log_validation_failed` error and must decide whether to retry or fail their operation, following the rejection precedence rules in `01-protocol/09-errors-and-failure-modes.md`. Log Manager records the failure as an operational log.
* If a mandatory sink fails, Log Manager marks readiness false, emits a `critical` log, and instructs the caller to reject the original request if logging is part of the acceptance criteria (for example audit-required flows), preserving the fail-closed posture in `01-protocol/09-errors-and-failure-modes.md`.
* If the in-memory journal is exhausted, Log Manager backpressures new submissions and emits `operational.log_journal_full`. Managers experiencing backpressure must either retry with bounded attempts or fail closed, as required by `01-protocol/09-errors-and-failure-modes.md`.
* Log Manager never drops accepted records silently. If a sink cannot be written after acceptance, the entire process halts (readiness false) until the operator intervenes, ensuring the integrity guarantees described in Section 12.

## 11. Security and trust boundary constraints

* Log Manager treats all submission payloads as untrusted. Validation ensures no caller can inject scripts, binary blobs, or unbounded data into sinks.
* Security and audit logs are stored in separate files with restricted file permissions so that secrecy guarantees from `01-protocol/05-keys-and-identity.md` and `01-protocol/06-access-control-model.md` remain intact.
* Query APIs enforce ACLs: only admin OperationContext identities (as defined in `01-protocol/06-access-control-model.md`) can read security/audit logs; operational logs may be exposed to broader system operators.
* Integrity hashes use a key stored in process memory that never leaves Key Manager custody boundaries described in `01-protocol/05-keys-and-identity.md`. Operators can export digest snapshots for remote verification.
* Event Manager bridges never include the full payload for security or audit entries. Subscribers must possess the right privileges to fetch details via the query API, mirroring the trust boundary rules in `01-protocol/08-network-transport-requirements.md`.

## 12. Retention, storage, and backpressure

* Rolling files rotate when size exceeds `log.retention.max_file_mb` (default 100 MB) or when age exceeds configured retention days so that historical audit trails remain aligned with the sequencing expectations in `01-protocol/07-sync-and-consistency.md`.
* Before deletion, Log Manager writes a manifest containing the file's hash and rotation metadata so integrity proofs remain verifiable.
* In-memory journals store at minimum the last `log.ingest.journal_size` records per class. Older entries are flushed to disk and removed.
* Backpressure thresholds are configurable per class. Security and audit logs reserve capacity to prevent operational chatter from starving critical records.

## 13. Observability and telemetry outputs

Log Manager emits the following telemetry:

* Queue depth per component and per class.
* Sink flush latency histograms (files, stdout, event bridge).
* Counts of validation failures, sink failures, and backpressure activations.
* Readiness and liveness flags for Health Manager.
* Chain hash status for audit/security files (latest block id, last verified timestamp).

Telemetry is routed through Health Manager and also recorded as `operational.*` log entries so operators can audit the logging subsystem itself.

## 14. Forbidden behaviors and compliance checklist

The following actions violate this specification:

* Bypassing Log Manager by writing directly to stdout, files, or Event Manager.
* Emitting unstructured text logs or logs without OperationContext metadata when one exists.
* Rewriting or deleting accepted log entries prior to retention expiry.
* Emitting security/audit payloads through Event Manager or other broadcasts that bypass ACL-enforced query APIs.
* Allowing app extensions to register sinks or routing policies without App Manager mediation.

Implementations must demonstrate adherence to the ingestion pipeline, sink integrity guarantees, configuration contracts, and fail-closed behavior described above before the Log Manager can be considered complete.
