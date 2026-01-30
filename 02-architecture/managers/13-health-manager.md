



# 13 Health Manager

Defines health signal ingestion, evaluation, and readiness/liveness publication. Specifies component states, thresholds, snapshots, and notification behavior. Defines failure handling, access control, and telemetry outputs for health.

For the meta specifications, see [13-health-manager meta](../09-appendix/meta/02-architecture/managers/13-health-manager-meta.md).

Defines health signal aggregation, readiness/liveness evaluation, and publication.
Specifies inputs, thresholds, snapshots, and admin access constraints.
Defines configuration, failure handling, and manager interactions for health.

## 1. Invariants and guarantees

Across all relevant contexts defined here, the following invariants hold:

* Readiness and liveness are represented as immutable snapshots with monotonically increasing `health_seq`. Once published, a health snapshot is never edited; a new snapshot is produced when state changes.
* Health evaluation never mutates graph state, never accesses raw storage, and never bypasses the fail-closed ordering in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Health signals are treated as untrusted input until validated against configured ranges. Malformed or missing signals cause the corresponding subsystem to be marked `unknown`, and repeated failures escalate to `degraded` or `failed`.
* All public health outputs are tagged with [OperationContext](../services-and-apps/05-operation-context.md) metadata when exposed via HTTP so that audit trails remain consistent with [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* [Health Manager](13-health-manager.md) never downgrades errors reported by other managers. If a manager declares `failed`, [Health Manager](13-health-manager.md) propagates that status intact. It may escalate severity (e.g., from `degraded` to `failed`) but never suppress it.
* Publishing `ready=false` or `alive=false` triggers [Event Manager](11-event-manager.md) and [Log Manager](12-log-manager.md) notifications exactly once per transition.
* Health state is queryable even when the node runtime transitions to `not_ready`, ensuring operators can observe the cause of failure.

## 2. Health classification and structure

### 2.1 Component states

Each monitored subsystem reports one of the following states:

| State      | Description                                                                           |
| ---------- | ------------------------------------------------------------------------------------- |
| `healthy`  | Within configured limits.                                                             |
| `degraded` | Operating but exceeding warning thresholds (latency, queue depth, error rate).        |
| `failed`   | Hard failure. Subsystem is not functioning.                                           |
| `unknown`  | No recent data within timeout window. Treated as `degraded` for readiness evaluation. |

### 2.2 Readiness and liveness evaluation

* **Readiness** (`ready`/`not_ready`). The node runtime is ready only if all critical subsystems ([Config Manager](01-config-manager.md), [Storage Manager](02-storage-manager.md), [Graph Manager](07-graph-manager.md), [Schema Manager](05-schema-manager.md), [ACL Manager](06-acl-manager.md), [Key Manager](03-key-manager.md), [Auth Manager](04-auth-manager.md), [State Manager](09-state-manager.md), [Network Manager](10-network-manager.md), [Event Manager](11-event-manager.md), [Log Manager](12-log-manager.md), [DoS Guard Manager](14-dos-guard-manager.md)) report `healthy`. Subsystems marked `degraded` force `ready=false`, honoring the fail-closed guidance in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). `unknown` subsystems force `ready=false` until a signal arrives. Optional subsystems (app extensions) do not block readiness unless flagged as critical in configuration.
* **Liveness** (`alive`/`dead`). Liveness remains `alive` until the [Health Manager](13-health-manager.md) becomes unreachable or explicitly marked `dead`. Long-term inability to collect signals (e.g., scheduler stalled) transitions to `dead`. `dead` implies `ready=false`.

### 2.3 Health snapshot structure

Each published snapshot contains:

| Field             | Description                                                            |
| ----------------- | ---------------------------------------------------------------------- |
| `health_seq`      | Monotonic integer incremented on each state change.                    |
| `published_at`    | Monotonic clock timestamp plus wall clock time.                        |
| `readiness`       | `ready` or `not_ready`.                                                |
| `liveness`        | `alive` or `dead`.                                                     |
| `components`      | Map from component name to `{ state, reason_code, last_reported_at }`. |
| `last_transition` | `{ from: {readiness, liveness}, to: {readiness, liveness}, cause }`.   |
| `outputs`         | List of sinks notified ([Log Manager](12-log-manager.md), [Event Manager](11-event-manager.md), in-process).       |

## 3. Inputs and outputs

### 3.1 Inputs

* Periodic heartbeats sent by managers over an in-process channel containing `{ component, state, metrics, timestamp }`.
* Event-driven alerts (e.g., `operational.log_sink_failed`, `network.transport_failed`) forwarded by emitting managers.
* Config snapshots from [Config Manager](01-config-manager.md) (`health.*` namespace) specifying thresholds, sampling intervals, and component criticality.
* Operator-triggered commands (force re-evaluation, dump last snapshot) authenticated via administrative [OperationContext](../services-and-apps/05-operation-context.md) per [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).

### 3.2 Outputs

* Current health snapshot accessible via in-process API (`HealthManager.get_snapshot()`).
* Admin HTTP endpoint (`/admin/health`) returning the snapshot with optional component filters. The endpoint enforces [OperationContext](../services-and-apps/05-operation-context.md) and ACL semantics defined by [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) and [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* [Event Manager](11-event-manager.md) notifications on transitions (`system.health_state_changed`, `security.health_degraded`).
* Structured log records describing component state changes and global readiness and liveness transitions, routed through [Log Manager](12-log-manager.md).

## 4. Health signal ingestion pipeline

[Health Manager](13-health-manager.md) processes signals through the following phases:

1. **Submission**: Components push signals into the ingestion queue. Backpressure applies if the queue reaches `health.ingest.max_signals`. Network telemetry forwarded through [Network Manager](10-network-manager.md) must respect the advisory-only guarantees in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).
2. **Validation**: Signals are checked for freshness, component identity, and schema correctness. Invalid signals are rejected and logged.
3. **Normalization**: Valid signals are canonicalized into a fixed structure `{ component, state, metrics, expires_at }`. Expiration time is computed from `health.component_timeout`.
4. **Evaluation**: A deterministic evaluator aggregates all component states, applies thresholds, and determines global readiness and liveness according to Section 4.2.
5. **Publication**: If the computed readiness and liveness differs from the current snapshot, a new snapshot is emitted, [Event Manager](11-event-manager.md) and [Log Manager](12-log-manager.md) are notified, and `health_seq` increments. Even when the global state is unchanged, component-level deltas are published to interested subscribers.

## 5. Configuration surface (`health.*`)

Key configuration entries owned by [Health Manager](13-health-manager.md) include:

| Key                           | Type    | Reloadable | Description                                                                            |
| ----------------------------- | ------- | ---------- | -------------------------------------------------------------------------------------- |
| `health.poll_interval_ms`     | Integer | Yes        | How often [Health Manager](13-health-manager.md) requests heartbeats from components.                          |
| `health.component_timeout_ms` | Integer | Yes        | How long a signal remains valid before the component becomes `unknown`.                |
| `health.degraded.latency_ms`  | Map     | Yes        | Per-component latency thresholds that trigger `degraded`.                              |
| `health.degraded.queue_depth` | Map     | Yes        | Queue depth thresholds.                                                                |
| `health.critical_components`  | List    | Yes        | Components that block readiness when not `healthy`. Defaults to all protocol managers. |
| `health.event_notifications`  | Boolean | Yes        | Enables [Event Manager](11-event-manager.md) bridge.                                                          |
| `health.log_notifications`    | Boolean | Yes        | Enables structured log emission (always on in production).                             |
| `health.admin_acl_role`       | String  | Yes        | ACL role required to access detailed health data via HTTP.                             |

Configuration reloads follow [Config Manager](01-config-manager.md)'s prepare/commit flow. [Health Manager](13-health-manager.md) validates that thresholds are non-negative and that all listed components are registered.

## 6. Internal engines and data paths

[Health Manager](13-health-manager.md) is composed of four mandatory engines:

### 6.1 Signal Intake Engine

Responsibilities:

* Accept heartbeat submissions and alerts from managers via in-process channels.
* Enforce per-component and global queue limits.
* Tag each submission with receipt time for expiration tracking.

Failure behavior:

* If the queue is saturated, emit `health.signal_queue_full` logs and drop lowest-priority optional components first before affecting critical components.

### 6.2 Validation Engine

Responsibilities:

* Ensure each signal references a known component and contains required fields (`state`, `metrics`, `timestamp`).
* Reject signals older than `health.component_timeout_ms`.
* Normalize component identifiers.

Failure behavior:

* Invalid signals are logged as `health.signal_invalid` and counted toward component failure metrics. Repeated invalid signals mark the component `failed`.

### 6.3 Evaluation Engine

Responsibilities:

* Merge the latest valid signal per component into the current state table.
* Apply threshold logic (latency, queue depth, error rates) to determine `healthy`, `degraded`, `failed`, or `unknown`.
* Compute readiness and liveness per Section 4.2.

Failure behavior:

* If evaluation fails (e.g., due to internal error), [Health Manager](13-health-manager.md) marks readiness false, emits `critical` logs, and requests operator intervention in accordance with the fail-closed posture defined in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

### 6.4 Publication Engine

Responsibilities:

* Emit health snapshots to registered subscribers, HTTP cache, [Log Manager](12-log-manager.md), and [Event Manager](11-event-manager.md) (when enabled).
* Rate-limit redundant notifications; snapshots are published only when state changes or when explicitly requested.
* Maintain the `health_seq` counter.

Failure behavior:

* Publication failures trigger retries with exponential backoff. After `health.publication.max_retries` failures, readiness is set to false and a `critical` log is emitted per the same fail-closed rules in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

## 7. Component interactions

* **[Config Manager](01-config-manager.md)**: Provides `health.*` snapshots. [Health Manager](13-health-manager.md) observes the prepare/commit flow and applies new thresholds atomically.
* **[Log Manager](12-log-manager.md)**: Receives structured logs for every component transition and global readiness and liveness change.
* **[Event Manager](11-event-manager.md)**: Receives notifications when readiness or liveness changes, or when a component transitions to `failed` if `health.event_notifications` is true.
* **[DoS Guard Manager](14-dos-guard-manager.md)**: Consumes health state to adjust admission policy. [Health Manager](13-health-manager.md) ensures [DoS Guard Manager](14-dos-guard-manager.md) is informed when readiness changes to support escalation semantics in [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* **[Network Manager](10-network-manager.md)**: Supplies transport-level telemetry (connection counts, listener status) as part of its heartbeat, following the signaling guarantees and trust boundaries defined in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).
* **[State Manager](09-state-manager.md) / [Graph Manager](07-graph-manager.md) / [Storage Manager](02-storage-manager.md) / [Schema Manager](05-schema-manager.md) / [ACL Manager](06-acl-manager.md) / [Key Manager](03-key-manager.md) / [Auth Manager](04-auth-manager.md) / [App Manager](08-app-manager.md) / [Event Manager](11-event-manager.md) / [Log Manager](12-log-manager.md)**: Each emits health signals. [Health Manager](13-health-manager.md) enforces that all critical managers participate.

## 8. Failure handling and rejection behavior

* [Health Manager](13-health-manager.md) follows the precedence rules in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). Validation failures are classified as structural; evaluator failures are resource-level; sink notification failures are environmental.
* When [Health Manager](13-health-manager.md) itself encounters a fatal error, it emits `health.manager_failed` logs, sets liveness to `dead`, readiness to `not_ready`, and signals [Event Manager](11-event-manager.md) and [DoS Guard Manager](14-dos-guard-manager.md) to halt admissions, ensuring [DoS Guard Manager](14-dos-guard-manager.md) follows its fail-closed requirements in [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Missing signals for a component cause escalation: `unknown` after the timeout; `degraded` after two timeouts; `failed` after three consecutive timeouts or an explicit `failed` signal.

## 9. Security and trust boundaries

* Health queries via HTTP require an [OperationContext](../services-and-apps/05-operation-context.md) whose identity carries the admin ACL role defined in `health.admin_acl_role`, enforcing [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md) and binding to the identity primitives in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Health snapshots do not expose raw metrics for components unless the requester is authorized. Unprivileged callers receive only aggregate readiness and liveness state.
* All health data is transient. Persistent storage occurs only through [Log Manager](12-log-manager.md) (structured logs) and optional [Event Manager](11-event-manager.md) notifications.
* [Health Manager](13-health-manager.md) treats incoming signals as untrusted. Spoofed or malformed signals cannot change global state without passing validation.

## 10. Observability and telemetry

[Health Manager](13-health-manager.md) emits telemetry counters:

* Number of signals received per component.
* Signal validation failures per component.
* Time since last healthy signal for each component.
* Number of readiness and liveness transitions.
* Publication failures per sink (HTTP cache, [Event Manager](11-event-manager.md), [Log Manager](12-log-manager.md)).

Telemetry is emitted via [Log Manager](12-log-manager.md) (operational logs) and optionally aggregated by [Event Manager](11-event-manager.md) subscribers. [Health Manager](13-health-manager.md) also exposes an in-process subscription API for other managers that need to react quickly to state changes (e.g., [DoS Guard Manager](14-dos-guard-manager.md) adjusting admission difficulty).

## 11. Forbidden behaviors and compliance checklist

The following actions violate this specification:

* Allowing components to bypass [Health Manager](13-health-manager.md) and publish independent readiness indicators.
* Treating optional components as critical without registering them in `health.critical_components`.
* Editing or suppressing component failure signals once ingested.
* Publishing health snapshots without incrementing `health_seq` or without tagging sinks notified.
* Exposing health data to non-admin identities.

Implementations must demonstrate compliance with the ingestion pipeline, threshold evaluation, publication guarantees, security controls, and protocol references described above before the [Health Manager](13-health-manager.md) can be considered complete.
