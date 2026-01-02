



# 13 Health Manager

## 1. Purpose and scope

The Health Manager is the authoritative component that evaluates, aggregates, and publishes the liveness and readiness state of the 2WAY backend. It collects health signals from all managers, internal services, and runtime subsystems; enforces the fail-closed posture defined in the protocol; and exposes a single source of truth to operators, diagnostic tools, and (optionally) Event Manager when critical transitions occur. Health Manager does not mutate graph state or perform remediation. Its role is detection, classification, and publication.

This specification defines the health classification model, responsibilities, input/output contracts, internal engines, configuration surface, and interactions with other managers. It references only the protocol contracts defined in:

* `01-protocol/00-protocol-overview.md`
* `01-protocol/05-keys-and-identity.md`
* `01-protocol/06-access-control-model.md`
* `01-protocol/07-sync-and-consistency.md`
* `01-protocol/08-network-transport-requirements.md`
* `01-protocol/09-errors-and-failure-modes.md`

Those files remain normative for all behaviors described here.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Owning the single authoritative readiness (`ready`/`not_ready`) and liveness (`alive`/`dead`) state for the backend, keeping these states aligned with the fail-closed rules in `01-protocol/09-errors-and-failure-modes.md`.
* Collecting periodic health samples and event-driven signals from every manager (Config, Storage, Graph, Schema, ACL, Key, Auth, App, State, Network, Event, Log, DoS Guard) plus critical services (HTTP/WebSocket loop, scheduler, transport adapters).
* Evaluating collected signals against deterministic thresholds (latency ceilings, queue depth caps, error rates) and generating health conclusions per subsystem.
* Publishing health state via in-process subscription APIs, the admin HTTP surface, and optional Event Manager notifications (`system.health_state_changed`, `security.health_degraded`) without leaking sensitive metadata.
* Recording health transitions as structured logs routed through Log Manager.
* Enforcing access control for health queries. Only administrative identities defined by `01-protocol/06-access-control-model.md` can retrieve privileged health details.
* Providing a single place where DoS Guard, Log Manager, and operators can learn when the backend intentionally stops accepting traffic due to local degradation.

This specification does not cover the following:

* Automatic remediation, restart logic, or hardware-level monitoring.
* Service-specific diagnostics or deep metrics (e.g., Graph Manager internal counters). Health Manager references only the signals that other managers emit.
* UI dashboards, notification routing outside Event Manager, or long-term metrics retention.

## 3. Invariants and guarantees

Across all relevant contexts defined here, the following invariants hold:

* Readiness and liveness are represented as immutable snapshots with monotonically increasing `health_seq`. Once published, a health snapshot is never edited; a new snapshot is produced when state changes.
* Health evaluation never mutates graph state, never accesses raw storage, and never bypasses the fail-closed ordering in `01-protocol/09-errors-and-failure-modes.md`.
* Health signals are treated as untrusted input until validated against configured ranges. Malformed or missing signals cause the corresponding subsystem to be marked `unknown`, and repeated failures escalate to `degraded` or `failed`.
* All public health outputs are tagged with `OperationContext` metadata when exposed via HTTP so that audit trails remain consistent with `01-protocol/00-protocol-overview.md`.
* Health Manager never downgrades errors reported by other managers. If a manager declares `failed`, Health Manager propagates that status intact. It may escalate severity (e.g., from `degraded` to `failed`) but never suppress it.
* Publishing `ready=false` or `alive=false` triggers Event Manager and Log Manager notifications exactly once per transition.
* Health state is queryable even when the backend transitions to `not_ready`, ensuring operators can observe the cause of failure.

## 4. Health classification and structure

### 4.1 Component states

Each monitored subsystem reports one of the following states:

| State | Description |
| --- | --- |
| `healthy` | Within configured limits. |
| `degraded` | Operating but exceeding warning thresholds (latency, queue depth, error rate). |
| `failed` | Hard failure. Subsystem is not functioning. |
| `unknown` | No recent data within timeout window. Treated as `degraded` for readiness evaluation. |

### 4.2 Readiness and liveness evaluation

* **Readiness** (`ready`/`not_ready`): The backend is ready only if all critical subsystems (Config, Storage, Graph, Schema, ACL, Key, Auth, State, Network, Event, Log, DoS Guard) report `healthy`. Subsystems marked `degraded` force `ready=false`. `unknown` subsystems force `ready=false` until a signal arrives. Optional subsystems (app extensions) do not block readiness unless flagged as critical in configuration.
* **Liveness** (`alive`/`dead`): Liveness remains `alive` until the Health Manager becomes unreachable or explicitly marked `dead`. Long-term inability to collect signals (e.g., scheduler stalled) transitions to `dead`. `dead` implies `ready=false`.

### 4.3 Health snapshot structure

Each published snapshot contains:

| Field | Description |
| --- | --- |
| `health_seq` | Monotonic integer incremented on each state change. |
| `published_at` | Monotonic clock timestamp plus wall clock time. |
| `readiness` | `ready` or `not_ready`. |
| `liveness` | `alive` or `dead`. |
| `components` | Map from component name to `{ state, reason_code, last_reported_at }`. |
| `last_transition` | `{ from: {readiness, liveness}, to: {readiness, liveness}, cause }`. |
| `outputs` | List of sinks notified (Log Manager, Event Manager, in-process). |

## 5. Inputs and outputs

### 5.1 Inputs

* Periodic heartbeats sent by managers over an in-process channel containing `{ component, state, metrics, timestamp }`.
* Event-driven alerts (e.g., `operational.log_sink_failed`, `network.transport_failed`) forwarded by emitting managers.
* Config snapshots from Config Manager (`health.*` namespace) specifying thresholds, sampling intervals, and component criticality.
* Operator-triggered commands (force re-evaluation, dump last snapshot) authenticated via administrative OperationContext.

### 5.2 Outputs

* Current health snapshot accessible via in-process API (`HealthManager.get_snapshot()`).
* Admin HTTP endpoint (`/admin/health`) returning the snapshot with optional component filters.
* Event Manager notifications on transitions (`system.health_state_changed`, `security.health_degraded`).
* Structured log records describing component state changes and global readiness/liveness transitions.

## 6. Health signal ingestion pipeline

Health Manager processes signals through the following phases:

1. **Submission**: Components push signals into the ingestion queue. Backpressure applies if the queue reaches `health.ingest.max_signals`.
2. **Validation**: Signals are checked for freshness, component identity, and schema correctness. Invalid signals are rejected and logged.
3. **Normalization**: Valid signals are canonicalized into a fixed structure `{ component, state, metrics, expires_at }`. Expiration time is computed from `health.component_timeout`.
4. **Evaluation**: A deterministic evaluator aggregates all component states, applies thresholds, and determines global readiness and liveness according to Section 4.2.
5. **Publication**: If the computed readiness/liveness differs from the current snapshot, a new snapshot is emitted, Event Manager and Log Manager are notified, and `health_seq` increments. Even when the global state is unchanged, component-level deltas are published to interested subscribers.

## 7. Configuration surface (`health.*`)

Key configuration entries owned by Health Manager include:

| Key | Type | Reloadable | Description |
| --- | --- | --- | --- |
| `health.poll_interval_ms` | Integer | Yes | How often Health Manager requests heartbeats from components. |
| `health.component_timeout_ms` | Integer | Yes | How long a signal remains valid before the component becomes `unknown`. |
| `health.degraded.latency_ms` | Map | Yes | Per-component latency thresholds that trigger `degraded`. |
| `health.degraded.queue_depth` | Map | Yes | Queue depth thresholds. |
| `health.critical_components` | List | Yes | Components that block readiness when not `healthy`. Defaults to all protocol managers. |
| `health.event_notifications` | Boolean | Yes | Enables Event Manager bridge. |
| `health.log_notifications` | Boolean | Yes | Enables structured log emission (always on in production). |
| `health.admin_acl_role` | String | Yes | ACL role required to access detailed health data via HTTP. |

Configuration reloads follow Config Manager's prepare/commit flow. Health Manager validates that thresholds are non-negative and that all listed components are registered.

## 8. Internal engines and data paths

Health Manager is composed of four mandatory engines:

### 8.1 Signal Intake Engine

Responsibilities:

* Accept heartbeat submissions and alerts from managers via in-process channels.
* Enforce per-component and global queue limits.
* Tag each submission with receipt time for expiration tracking.

Failure behavior:

* If the queue is saturated, emit `health.signal_queue_full` logs and drop lowest-priority optional components first before affecting critical components.

### 8.2 Validation Engine

Responsibilities:

* Ensure each signal references a known component and contains required fields (`state`, `metrics`, `timestamp`).
* Reject signals older than `health.component_timeout_ms`.
* Normalize component identifiers.

Failure behavior:

* Invalid signals are logged as `health.signal_invalid` and counted toward component failure metrics. Repeated invalid signals mark the component `failed`.

### 8.3 Evaluation Engine

Responsibilities:

* Merge the latest valid signal per component into the current state table.
* Apply threshold logic (latency, queue depth, error rates) to determine `healthy`, `degraded`, `failed`, or `unknown`.
* Compute readiness and liveness per Section 4.2.

Failure behavior:

* If evaluation fails (e.g., due to internal error), Health Manager marks readiness false, emits `critical` logs, and requests operator intervention.

### 8.4 Publication Engine

Responsibilities:

* Emit health snapshots to registered subscribers, HTTP cache, Log Manager, and Event Manager (when enabled).
* Rate-limit redundant notifications; snapshots are published only when state changes or when explicitly requested.
* Maintain the `health_seq` counter.

Failure behavior:

* Publication failures trigger retries with exponential backoff. After `health.publication.max_retries` failures, readiness is set to false and a `critical` log is emitted.

## 9. Component interactions

* **Config Manager**: Provides `health.*` snapshots. Health Manager observes the prepare/commit flow and applies new thresholds atomically.
* **Log Manager**: Receives structured logs for every component transition and global readiness/liveness change.
* **Event Manager**: Receives notifications when readiness or liveness changes, or when a component transitions to `failed` if `health.event_notifications` is true.
* **DoS Guard Manager**: Consumes health state to adjust admission policy. Health Manager ensures DoS Guard is informed when readiness changes.
* **Network Manager**: Supplies transport-level telemetry (connection counts, listener status) as part of its heartbeat.
* **State Manager / Graph Manager / Storage Manager / Schema Manager / ACL Manager / Key Manager / Auth Manager / App Manager / Event Manager / Log Manager**: Each emits health signals. Health Manager enforces that all critical managers participate.

## 10. Failure handling and rejection behavior

* Health Manager follows the precedence rules in `01-protocol/09-errors-and-failure-modes.md`. Validation failures are classified as structural; evaluator failures are resource-level; sink notification failures are environmental.
* When Health Manager itself encounters a fatal error, it emits `health.manager_failed` logs, sets liveness to `dead`, readiness to `not_ready`, and signals Event Manager and DoS Guard to halt admissions.
* Missing signals for a component cause escalation: `unknown` after the timeout; `degraded` after two timeouts; `failed` after three consecutive timeouts or an explicit `failed` signal.

## 11. Security and trust boundaries

* Health queries via HTTP require an OperationContext whose identity carries the admin ACL role defined in `health.admin_acl_role`, enforcing `01-protocol/06-access-control-model.md`.
* Health snapshots do not expose raw metrics for components unless the requester is authorized. Unprivileged callers receive only aggregate readiness/liveness state.
* All health data is transient. Persistent storage occurs only through Log Manager (structured logs) and optional Event Manager notifications.
* Health Manager treats incoming signals as untrusted. Spoofed or malformed signals cannot change global state without passing validation.

## 12. Observability and telemetry

Health Manager emits telemetry counters:

* Number of signals received per component.
* Signal validation failures per component.
* Time since last healthy signal for each component.
* Number of readiness/liveness transitions.
* Publication failures per sink (HTTP cache, Event Manager, Log Manager).

Telemetry is emitted via Log Manager (operational logs) and optionally aggregated by Event Manager subscribers. Health Manager also exposes an in-process subscription API for other managers that need to react quickly to state changes (e.g., DoS Guard adjusting admission difficulty).

## 13. Forbidden behaviors and compliance checklist

The following actions violate this specification:

* Allowing components to bypass Health Manager and publish independent readiness indicators.
* Treating optional components as critical without registering them in `health.critical_components`.
* Editing or suppressing component failure signals once ingested.
* Publishing health snapshots without incrementing `health_seq` or without tagging sinks notified.
* Exposing health data to non-admin identities.

Implementations must demonstrate compliance with the ingestion pipeline, threshold evaluation, publication guarantees, security controls, and protocol references described above before the Health Manager can be considered complete.
