# 11 Event Manager

## 1. Purpose and scope

The Event Manager is the sole publication and subscription authority for backend events in the 2WAY node. It receives post-commit facts from managers, normalizes them into immutable notifications, enforces audience and ACL constraints, and delivers them to subscribers over the single local WebSocket surface defined in `00-scope/01-scope-and-goals.md`. It also provides an internal bus so managers can observe lifecycle transitions, abuse reports, and health changes without rolling their own delivery surfaces.

This specification defines the event model, internal engines, ordering guarantees, subscription semantics, configuration surface, and trust boundaries. It does not redefine schema semantics, persistence rules, or transport encodings that are owned elsewhere in the repository.

This specification consumes the protocol contracts defined in:
* `01-protocol/00-protocol-overview.md`
* `01-protocol/02-object-model.md`
* `01-protocol/03-serialization-and-envelopes.md`
* `01-protocol/05-keys-and-identity.md`
* `01-protocol/06-access-control-model.md`
* `01-protocol/07-sync-and-consistency.md`
* `01-protocol/08-network-transport-requirements.md`
* `01-protocol/09-errors-and-failure-modes.md`

Those files remain normative for all behaviors described here.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Owning all publication surfaces for backend events and enforcing the invariant from `00-scope/00-scope-overview.md` that all state change notifications flow through Event Manager.
* Accepting normalized event descriptors from Graph Manager, App Manager, Config Manager, Network Manager, Health Manager, DoS Guard Manager, and Log Manager after those managers complete their own validation and commit phases, ensuring sequencing rules in `01-protocol/07-sync-and-consistency.md` remain intact.
* Binding event metadata to `OperationContext`-derived visibility rules so that subscribers can only see events they are authorized to observe under `01-protocol/06-access-control-model.md`.
* Maintaining the single WebSocket delivery surface, including admission, subscription filtering, flow control, resume tokens, and delivery telemetry required to satisfy the frontend boundary described in `01-protocol/05-keys-and-identity.md` and `01-protocol/08-network-transport-requirements.md`.
* Providing a deterministic classification and routing engine for domain events, system lifecycle events, and abuse/telemetry events while preserving naming conventions mandated by `01-protocol/00-protocol-overview.md`.
* Emitting audit signals to Log Manager whenever subscriptions change state, buffers overflow, delivery is suppressed, or component health transitions, ensuring observability posture matches `01-protocol/09-errors-and-failure-modes.md`.
* Enforcing per-connection and global resource limits sourced from `event.*` configuration so hostile subscribers cannot exhaust backend memory.
* Reporting readiness, liveness, and queue depth to Health Manager and DoS Guard Manager so event surfaces participate in the node-level fail-closed behavior defined across the architecture documents.

This specification does not cover the following:

* Schema validation, ACL evaluation of graph writes, graph mutation sequencing, or sync reconciliation; those remain owned by Schema Manager, ACL Manager, Graph Manager, and State Manager.
* Definition of HTTP or WebSocket route syntax; route naming lives in the interface specifications.
* Persistence of historical events, durable replay logs, or offline delivery guarantees. Event Manager delivers best-effort realtime notifications only.
* Remote sync propagation; State Manager and Network Manager own remote ingress and egress.
* Any UI behavior, payload interpretation, or client side retry policy. Clients must use the read APIs to inspect committed state.

## 3. Invariants and guarantees

Across all relevant contexts defined here, the following invariants hold:

* Event Manager never mutates graph state and never issues raw SQL; it relies on emitting managers to supply committed metadata exactly once, preserving the single write path defined in `01-protocol/00-protocol-overview.md`.
* Event payloads contain only identifiers, summary metadata, and constant signal fields. They never include full graph object bodies, private keys, or secrets so that object custody stays with Graph Manager and Key Manager per `01-protocol/02-object-model.md` and `01-protocol/05-keys-and-identity.md`.
* Domain events are anchored to the `global_seq` assigned by Graph Manager and are emitted strictly after commit, matching the sequencing posture in `01-protocol/07-sync-and-consistency.md`.
* System and telemetry events receive their own `event_seq` that is monotonic per source but never influence `global_seq`, maintaining the ordering guarantees from `01-protocol/07-sync-and-consistency.md`.
* Event Manager never trusts frontend-provided filter criteria without verifying them against the subscriber's immutable `OperationContext`, exactly as required by `01-protocol/00-protocol-overview.md`.
* Subscription identity is bound to the authenticated frontend session established by Auth Manager, and `OperationContext` remains immutable for the lifetime of the connection per `01-protocol/00-protocol-overview.md`.
* Event Manager does not buffer unbounded state. When limits are exceeded, connections are closed and the caller must fall back to the read API to recover, aligning with the fail-closed posture in `01-protocol/09-errors-and-failure-modes.md`.
* Event naming is stable, lower snake case, and versioned explicitly when schemas evolve, honoring the compatibility guarantees in `01-protocol/00-protocol-overview.md` and `01-protocol/10-versioning-and-compatibility.md`.
## 4. Event classification and structure

### 4.1 Event classes

| Class | Description | Primary sources | Scope anchor |
| --- | --- | --- | --- |
| `graph.*` domain events | Notifications that a graph envelope committed (creates, updates, rating changes, ACL mutations). | Graph Manager (post-commit hook shared with Schema and ACL enforcement). | `app_id`, `domain_id`, `global_seq`, object ids. |
| `system.*` lifecycle events | Node bootstrap, configuration changes, manager readiness shifts, health degradation, or recovery signals. | Config Manager, App Manager, Health Manager, Log Manager. | `node_id`, manager name, `event_seq`. |
| `network.*` transport events | Peer admission outcomes, disconnects, delivery failures, reachability hints, or DoS reactions. | Network Manager, DoS Guard Manager. | `peer_identity_id`, transport surface id, `event_seq`. |
| `security.*` abuse and audit events | Admin gated actions, authentication failures, challenge issuance, or revocation notices intended for monitoring surfaces. | Auth Manager, DoS Guard Manager, Log Manager. | `requester_identity_id`, route/admin scope, `event_seq`. |

Other classes may be added by apps through App Manager registration, but they must remain confined to the owning `app_id` and must declare their scope anchors up front.

Domain event payloads correspond directly to committed envelopes defined in `01-protocol/03-serialization-and-envelopes.md` and to graph objects defined in `01-protocol/02-object-model.md`, so they may only summarize state that already exists on disk.

### 4.2 Event envelope structure

Every emitted event is normalized into an immutable `EventEnvelope`:

| Field | Description |
| --- | --- |
| `event_id` | 128-bit random identifier unique per event envelope. |
| `event_type` | Lower snake case string such as `graph.object_mutated`, following the protocol naming conventions. |
| `source_manager` | Manager or app identifier that authored the event descriptor. |
| `sequence_anchor` | Either `global_seq` for domain events or a monotonic `event_seq` per source for non-domain events. |
| `scope` | `{ app_id, domain_id, requester_identity_id, peer_identity_id }` subset describing who may observe the event. |
| `audience_contract` | Hash of the ACL filter input plus optional subscription labels to detect staleness. |
| `payload_summary` | Constant-size metadata such as operation ids, object ids, rating ids, route names, or health status enumerations. No mutable graph content is embedded. |
| `resume_token` | `{ event_id, sequence_anchor, issued_at }` tuple used for resume requests. Tokens are opaque outside Event Manager. |
| `emitted_at` | Monotonic clock timestamp used for telemetry only. |

`scope` and `audience_contract` rely on the ACL inputs described in `01-protocol/06-access-control-model.md`, ensuring Event Manager never invents new authorization surfaces.

### 4.3 Event naming and compatibility

* Event names are stable and versioned. Backwards-incompatible changes require a new `event_type` suffix (for example `graph.object_mutated.v2`) while the old name continues until removed via an upgrade process defined in `01-protocol/10-versioning-and-compatibility.md`.
* App supplied event names are prefixed with the app slug (`app.contacts.message_created`).
* Event payload schemas are immutable once published. Additional optional fields may be added only when subscribers can deterministically detect their presence through the `event_type` versioning rule.

## 5. Event publication lifecycle

Event Manager operates as a staged pipeline. Phases must not be reordered or skipped.

### 5.1 Phase 1 - Source ingestion

* Managers emit `EventDescriptor` objects only after their own commit points per `01-protocol/07-sync-and-consistency.md` and include the authoritative `OperationContext` or a reduced visibility descriptor defined in `01-protocol/00-protocol-overview.md`.
* Descriptors enter the Event Manager via an in-process channel. Inputs from services are forbidden; only managers can emit descriptors.
* All descriptors are treated as trusted metadata but untrusted audience hints. Event Manager validates them before delivery.

### 5.2 Phase 2 - Normalization

* Descriptors are converted into `EventEnvelope` structures by adding `event_id`, `sequence_anchor`, and normalized `scope`.
* Invalid descriptors (missing identifiers, cross-app leakage, negative sequence anchors) are rejected and the emitting manager receives a synchronous error. Emitting managers must log failures through Log Manager.
* Normalization enforces that domain events cannot reference more than one `app_id` or `domain_id`.

### 5.3 Phase 3 - Audience binding

* For each envelope Event Manager derives an `audience_contract` describing the ACL inputs it will later use to authorize subscribers.
* Domain events call into ACL Manager with `{ OperationContext.requester_identity_id, scope, object_ids }` to produce a read-visibility capsule exactly as defined in `01-protocol/06-access-control-model.md`. Event Manager caches the capsule alongside the envelope for the life of the buffer window.
* System events bind to admin roles declared in configuration or to node-level observers. ACL Manager validates that bindings cannot cross app boundaries unless explicitly registered by App Manager, enforcing the cross-app isolation guarantees in `01-protocol/06-access-control-model.md`.

### 5.4 Phase 4 - Delivery

* Envelopes enter per-class priority queues with deterministic ordering: domain queues order strictly by `global_seq`; system and network queues order by `(source_manager, event_seq)`.
* Subscription filters pull from the relevant queues, re-validating the `audience_contract` against the subscriber's immutable `OperationContext`.
* Upon successful filtering, Event Manager enqueues a delivery unit onto the subscriber's buffer. Delivery adds `resume_token` state.
* Delivery completion triggers telemetry updates and optional success counters; failure or drops emit rejection events to Log Manager.

## 6. Subscription model and WebSocket delivery

### 6.1 Connection setup

1. HTTP layer receives an `Upgrade: websocket` request at the `/events` route.
2. Auth Manager authenticates the requester, producing an `OperationContext` with `requester_identity_id`, `app_id`, `domain_scope`, and `trace_id`.
3. Successful authentication hands the socket to Event Manager along with the immutable `OperationContext` and requested filters.
4. Event Manager validates requested filters against `OperationContext` (for example, a subscriber may not ask for another app's domain).
5. On success, Event Manager assigns a `connection_id`, registers the subscription, and begins heartbeats. On failure it rejects with an authentication or authorization error mapped to `01-protocol/09-errors-and-failure-modes.md`.

### 6.2 Subscription filters

* Required parameters: `app_id` (must match `OperationContext.app_id`) and `subscription_type` (`graph`, `system`, `network`, `security`, or app-defined channel).
* Optional parameters: `domain_id` (must be a subset of allowed domains), `object_ids`, `peer_identity_id`, `event_type`.
* Filters are immutable for the lifetime of the connection; resubscription requires opening a new connection.
* Admin-only subscription types (`system.*`, `security.*`) additionally require `OperationContext` to carry the admin gating bit set by Auth Manager.

### 6.3 Delivery semantics

* Delivery is best effort and at-most-once. If a client misses an event, it must perform a read via HTTP using `global_seq` or other identifiers to recover the state, matching the recovery expectations in `01-protocol/07-sync-and-consistency.md`.
* Each connection maintains a sliding buffer of `event.queue.per_connection` entries. Clients must ACK events (by sending `{"type":"ack","resume_token":...}` messages) to advance the window.
* When a buffer overflows due to missing ACKs or slow consumption, Event Manager closes the connection with a `buffer_overflow` error and emits a `security.subscription_dropped` event.

### 6.4 Heartbeats and resume

* Heartbeats are sent every `event.delivery.heartbeat_interval_ms`. If no response is received within two intervals the connection is closed.
* Clients may reconnect with a `resume_token`. Event Manager validates the token and, if still within the buffered retention window (`event.delivery.resume_window`), replays pending events in order. Otherwise it instructs the client to perform an HTTP catch-up read.

### 6.5 Backpressure and throttling

* Global concurrent connection counts, per-identity connection counts, and per-app totals are enforced before accepting a subscription.
* Rate limiting of message sends per connection ensures a single subscriber cannot starve others. Limits are expressed as `event.delivery.max_msgs_per_sec` and are enforced with token buckets.
* DoS Guard Manager may instruct Event Manager to temporarily deny new subscriptions if abuse is detected, consistent with the directives in `01-protocol/11-dos-guard-and-client-puzzles.md`.

## 7. Internal engines and data paths

Event Manager is composed of six mandatory internal engines. These engines define strict phase boundaries and must not be collapsed, reordered, or bypassed. Each engine exposes explicit inputs, outputs, and failure signaling so implementers can build to a deterministic contract.

### 7.1 Source Intake Engine

The Source Intake Engine is the only ingress for manager-authored `EventDescriptor` objects.

Responsibilities:

* Register a dedicated intake channel for each manager allowed to emit descriptors.
* Validate descriptor completeness (source name, event type, sequence anchor, scope hints, payload summary) and reject descriptors that reference multiple apps or domains.
* Enforce that descriptors are submitted only after the emitting manager's commit point, reflecting the post-commit sequencing rules in `01-protocol/07-sync-and-consistency.md`.
* Assign a per-source `local_order` counter to preserve FIFO semantics downstream.
* Apply per-source and global backpressure based on `event.queue.total_ceiling`.

Outputs:

* Validated descriptors forwarded to the Normalization Engine, tagged with `{source_manager, local_order}`.

Failure behavior:

* Validation failures return synchronous errors (`invalid_descriptor`, `scope_violation`, `queue_full`) to the emitter and emit a `system.event_descriptor_rejected` telemetry event.

Constraints:

* Intake must not mutate descriptor payloads beyond tagging.
* Intake must never drop descriptors silently; drops must be reported to Log Manager and Telemetry Engine.

### 7.2 Normalization Engine

The Normalization Engine converts descriptors into immutable `EventEnvelope` structures.

Responsibilities:

* Assign `event_id` and `emitted_at`.
* Determine whether the sequence anchor is `global_seq` (domain events) or internal `event_seq`.
* Enforce app and domain isolation; descriptors spanning multiple apps are rejected with `security.cross_app_violation`.
* Maintain per-class queues sized according to `event.queue.total_ceiling`, preserving ordering by `(class, sequence_anchor, source_order)`.
* Populate the resume index mapping `event_id` to `(sequence_anchor, queue_pointer)` for reconnect handling.

Failure behavior:

* On queue saturation, apply deterministic shedding (drop lower priority classes before `graph.*`) and emit `system.event_queue_overflow`.

Constraints:

* Normalization may not reorder descriptors across classes or mutate payload summaries.
* Resume metadata must be written before the envelope becomes visible to downstream engines.

### 7.3 Audience Engine

The Audience Engine derives immutable `audience_contract` capsules used during delivery.

Responsibilities:

* Batch envelopes by `(app_id, domain_id, subscription_type)` and request ACL capsules from ACL Manager.
* Encode the originating `OperationContext` identity and scope inside the capsule to prevent reuse by other identities.
* Cache capsules until the envelope ages out of `event.delivery.resume_window` or all subscribers ACK it.
* Surface readiness false if ACL Manager is unavailable, preventing further delivery.

Outputs:

* Envelope plus capsule id pairs handed to the Delivery Engine.

Failure behavior:

* ACL failures or outages halt progression of affected envelopes; Event Manager does not downgrade or infer scope.

Constraints:

* Capsules must remain <256 bytes and include enough metadata for stateless evaluation.
* Capsules must not be shared across app boundaries unless App Manager explicitly registered the cross-app channel.

### 7.4 Subscription Registry Engine

The Subscription Registry Engine governs WebSocket lifecycles and subscription state.

Responsibilities:

* Accept upgrade requests only after Auth Manager supplies a valid `OperationContext`, as required by `01-protocol/00-protocol-overview.md`.
* Validate requested filters (app, domains, event classes) against `OperationContext` and admin gating bits.
* Compile filters into deterministic matchers referencing capsule ids and scope metadata.
* Manage resume tokens: verify the HMAC, locate referenced events in the resume index, and preload pending envelopes into the connection buffer.
* Track per-connection state `{connection_id, operation_context, filters, buffer_state, last_ack_token, heartbeat_deadline}` and enforce heartbeat timers.

Failure behavior:

* Any filter or resume validation failure results in immediate connection close with a typed error and `security.subscription_rejected` telemetry.

Constraints:

* Filters are immutable for the life of the connection; modifications require reconnect.
* The registry must run in a single-threaded reactor per listener, delegating heavy work to worker pools without reordering completion events.

### 7.5 Delivery Engine

The Delivery Engine moves envelopes from class queues to subscriber buffers and over the WebSocket transport.

Responsibilities:

* Consume per-class queues using weighted round-robin (graph > security > network > system by default) while preventing starvation.
* Evaluate each envelope against registered subscriptions using the cached capsule constraints.
* Write matching envelopes into per-connection ring buffers sized by `event.queue.per_connection` and track ACK progress.
* Apply backpressure when total buffered events reach `event.queue.total_ceiling` by signaling Source Intake to pause lower-priority classes.
* Serialize envelopes into deterministic JSON payloads and send them via the WebSocket adapter, capturing send success/failure telemetry.

Failure behavior:

* Missing ACKs beyond the heartbeat interval trigger buffer overflow handling and connection closure with `buffer_overflow`.
* Repeated send failures increment per-connection error counters and may force teardown.

Constraints:

* Delivery may not mutate envelope contents beyond framing.
* Delivery must not implement implicit retry; reconnect and replay responsibilities remain with clients using resume tokens and read APIs.

### 7.6 Telemetry Engine

The Telemetry Engine provides observability across all engines.

Responsibilities:

* Sample queue depth, production/delivery/drop counters per class, per-connection ACK latency, heartbeat failures, and subscription rejection reasons.
* Emit readiness/liveness to Health Manager each `event.telemetry.heartbeat_interval_ms` and log state changes via Log Manager.
* Forward repeated buffer overflows or subscription rejections to DoS Guard Manager for abuse mitigation.
* Raise `system.event_pipeline_degraded` when any engine signals saturation beyond `event.telemetry.degraded_threshold_ms` or when dependencies (ACL Manager, Config Manager) are unavailable.

Constraints:

* Telemetry must never include object identifiers or payload summaries that violate subscriber isolation.

Engines communicate exclusively via bounded lock-free queues. The flow is strictly Source Intake -> Normalization -> Audience -> Delivery, with Subscription Registry wrapping ingress/egress and Telemetry observing all stages. No shortcuts or bypass paths are permitted.

## 8. Configuration surface (`event.*`)

Event Manager owns the `event.*` namespace in Config Manager. The following keys are normative:

| Key | Type | Reloadable | Description |
| --- | --- | --- | --- |
| `event.websocket.max_connections` | Integer | Yes | Global hard cap on concurrent WebSocket subscriptions. |
| `event.websocket.max_connections_per_identity` | Integer | Yes | Per `requester_identity_id` cap to prevent identity-level abuse. |
| `event.queue.per_connection` | Integer | Yes | Buffer depth per connection before overflow occurs. |
| `event.queue.total_ceiling` | Integer | No | Maximum total queued events across all connections; exceeding this triggers connection shedding. |
| `event.delivery.heartbeat_interval_ms` | Integer | Yes | Interval between heartbeats. Must be >= 5000 ms. |
| `event.delivery.resume_window` | Integer (event count) | Yes | Number of most recent events retained per class for resume requests. |
| `event.delivery.max_msgs_per_sec` | Integer | Yes | Throttle per connection send rate. |
| `event.telemetry.emit_samples` | Boolean | Yes | Enables verbose telemetry emission to Log Manager for debugging. |
| `event.security.admin_channels` | List | No | Explicit list of event types that require admin gating. |

Startup fails if required keys are missing or invalid. Reload follows Config Manager's prepare/commit flow, and Event Manager must acknowledge or veto reloads based on whether new limits can be applied without dropping existing connections.

## 9. Component interactions

### 9.1 Graph Manager

* Provides post-commit event descriptors for every envelope. Each descriptor includes affected object ids, `global_seq`, `app_id`, `domain_id`, and the submitting `OperationContext`, matching the data that must already be persisted per `01-protocol/07-sync-and-consistency.md`.
* Graph Manager never attempts to deliver events on its own and fails if Event Manager rejects the descriptor, ensuring a single deterministic notification path.

### 9.2 ACL Manager

* Supplies read visibility capsules used as `audience_contract` inputs. Capsules are immutable for the lifetime of the envelope.
* ACL Manager is never invoked in the WebSocket hot path for every message; instead Event Manager reuses the capsule but verifies that the subscriber's `OperationContext` matches the recorded parameters, ensuring authorization remains identical to `01-protocol/06-access-control-model.md`.

### 9.3 Auth Manager and HTTP layer

* Auth Manager authenticates WebSocket upgrades and attaches `OperationContext`.
* Event Manager relies on Auth Manager's admin gating bit to decide if a subscriber can request `system.*` or `security.*` channels.

### 9.4 Config Manager

* Supplies the `event.*` namespace snapshots. Event Manager must request revalidation before applying reloads and must publish readiness false if configuration cannot be applied.

### 9.5 App Manager and services

* App Manager registers app-prefixed event types and declares their scope anchors. Event Manager enforces those declarations at runtime.
* Services may request Event Manager to emit custom app events only through App Manager-validated descriptors; direct service-to-event-manager calls are forbidden.

### 9.6 Network Manager and DoS Guard Manager

* Network Manager emits connection lifecycle events (`network.peer_admitted`, `network.peer_dropped`, `network.delivery_failed`) with peer identity metadata.
* DoS Guard Manager emits abuse events and may instruct Event Manager to close or deny WebSocket subscriptions when abuse thresholds are crossed.

### 9.7 Log Manager

* Receives audit logs for subscription lifecycle, buffer drops, authorization failures, and abnormal delivery latencies.
* Receives copies of critical `security.*` events so they can be persisted to log sinks distinct from transient WebSocket delivery.

### 9.8 Health Manager

* Consumes readiness, liveness, and queue depth metrics. Event Manager must mark readiness false when no WebSocket listener is available or when intake queues are saturated.

### 9.9 Storage Manager

* Event Manager does not call Storage Manager directly. Any requirement for historical replay must be implemented via services reading the graph. This keeps the read/write boundary intact.

## 10. Failure handling and rejection behavior

* Structural descriptor failures result in synchronous rejection to the emitting manager, which must handle the failure per its own specification. Event Manager logs the failure with context and drops the descriptor, honoring the precedence rules in `01-protocol/09-errors-and-failure-modes.md`.
* Subscription authentication failures are surfaced immediately to the HTTP layer. No socket upgrade occurs.
* Authorization failures after upgrade (for example, requesting a domain outside `OperationContext`) cause the connection to close with `permission_denied`.
* Buffer overflows, heartbeat timeouts, or invalid ACKs close the connection and emit a `security.subscription_dropped` event so that failures remain observable per `01-protocol/09-errors-and-failure-modes.md`.
* Event Manager never retries deliveries after closing a connection. Clients must reconnect and issue catch-up reads, preserving the best-effort semantics required by `01-protocol/07-sync-and-consistency.md`.

## 11. Security and trust boundary constraints

* The WebSocket surface is a strict trust boundary described in `01-protocol/05-keys-and-identity.md` and `01-protocol/08-network-transport-requirements.md`. Event Manager treats all incoming frames (ACKs, resume requests) as untrusted until validated.
* Subscribers cannot observe objects, identifiers, or sequences they could not read via the normal API. All authorization decisions defer to ACL Manager capsules plus the subscriber's `OperationContext`, matching the access rules in `01-protocol/06-access-control-model.md`.
* Event Manager never leaks peer topology, secret configuration, or transport metadata that the subscriber's `OperationContext` is not cleared to see, preserving the secrecy posture in `01-protocol/05-keys-and-identity.md`.
* Resume tokens are cryptographically opaque (HMAC with a key stored in process memory). Clients cannot forge resume positions.

## 12. State, persistence, and backpressure constraints

* Event Manager persists no durable event log. It retains only `event.delivery.resume_window` entries in memory per class to service short reconnects.
* Per-connection buffers are stored in bounded ring buffers. The only mutable per-connection state is `{ OperationContext, subscription filters, last_ack_token, queue }`.
* On process restart, all subscriptions are lost, buffers are discarded, and clients must reconnect. This is acceptable because committed state remains in the graph and can be replayed via reads per `01-protocol/07-sync-and-consistency.md`.

## 13. Observability and telemetry outputs

Event Manager emits the following telemetry:

* Readiness flag indicating whether the WebSocket listener and intake engines are healthy.
* Liveness flag indicating runtime loop progress.
* Counters per event class (produced, delivered, dropped).
* Per-connection utilization, buffer depth, and ACK latency histograms.
* Rate of subscription failures by reason (`auth_failed`, `acl_denied`, `filter_invalid`, `buffer_overflow`).
* Network and DoS Guard instructions recorded as events so administrators can correlate cause and effect.

Telemetry is routed through Health Manager for aggregated status and through Log Manager for audit records. Optional verbose samples controlled by `event.telemetry.emit_samples` include the `event_type` and `scope.app_id` but never include `object_ids`.

Telemetry classification aligns with the observability requirements in `01-protocol/09-errors-and-failure-modes.md`, ensuring the same failure taxonomy is visible at the event surface.

## 14. Forbidden behaviors and compliance checklist

The following actions violate this specification:

* Allowing any manager, service, or app to publish events outside Event Manager.
* Embedding mutable graph data, private keys, or secrets in events.
* Delivering events before Graph Manager commits the underlying envelope or before Network Manager verifies transport invariants.
* Authorizing subscriptions solely on client provided metadata without consulting `OperationContext` and ACL capsules.
* Persisting event history in SQLite or attempting to use Event Manager as a durable queue.
* Allowing event filters to span multiple apps or domains unless App Manager explicitly registered the cross-app subscription.

Implementations must demonstrate that all the guarantees, limits, and fail-closed behaviors described above are enforced before the Event Manager surface is considered complete.
