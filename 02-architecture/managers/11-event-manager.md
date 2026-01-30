



# 11 Event Manager

Defines the Event Manager publication pipeline, envelope normalization, and WebSocket delivery. Specifies event classes, ordering anchors, subscription gating, and resume behavior. Defines failure handling, limits, and telemetry outputs for event delivery.

For the meta specifications, see [11-event-manager meta](../09-appendix/meta/02-architecture/managers/11-event-manager-meta.md).


## 1. Invariants and guarantees

Across all relevant contexts defined in this specification, the following invariants hold:

* [Event Manager](11-event-manager.md) never mutates graph state and never issues raw SQL. It relies on emitting managers to supply committed metadata exactly once, preserving the single write path mandated by [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). 
* Event payloads contain only identifiers, summary metadata, and constant signal fields defined in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md); they never include full graph object bodies, private keys, secrets, or sensitive transport material. 
* Domain events are anchored to the `global_seq` assigned by [Graph Manager](07-graph-manager.md) and are emitted strictly after commit, honoring the ordering guarantees in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). 
* System, network, and security events use an internal `event_seq` that is monotonic per source and does not influence `global_seq`, ensuring separation of ordering contexts per [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). 
* [Event Manager](11-event-manager.md) never trusts subscriber provided filters without verifying them against the subscriber's immutable [OperationContext](../services-and-apps/05-operation-context.md) and the cached authorization capsule derived under [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md). 
* Subscription identity is bound to the authenticated frontend session, and [OperationContext](../services-and-apps/05-operation-context.md) remains immutable for the lifetime of the connection per [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md). 
* [Event Manager](11-event-manager.md) does not buffer unbounded state. When limits are exceeded, connections are closed and callers must fall back to read APIs for recovery, consistent with the fail closed rules in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). 
* Event naming is stable, lower snake case per segment, and versioned explicitly when schemas evolve, following the compatibility guarantees in [01-protocol/11-versioning-and-compatibility.md](../../01-protocol/11-versioning-and-compatibility.md). 
* [Event Manager](11-event-manager.md) is the only component allowed to deliver backend events to the local realtime surface. No other manager may open alternate realtime channels, preserving the trust boundaries in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).

These guarantees must hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 2. Event lifecycle

[Event Manager](11-event-manager.md) enforces a single lifecycle that begins with descriptors, classifies them, normalizes envelopes, and preserves the semantics described in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) throughout delivery.

### 2.1 EventDescriptor contract

Managers emit immutable `EventDescriptor` objects after their own commit points per [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). Descriptors use the schema below and represent the only ingress to [Event Manager](11-event-manager.md).

| Field | Description |
| --- | --- |
| `source_manager` | Canonical manager or registered app identifier that authored the descriptor. Descriptors from unregistered sources or direct services are rejected. |
| `event_class` | One of `graph`, `system`, `network`, `security`, or an [App Manager](08-app-manager.md) registered app channel. Class controls queue routing and ordering anchors. |
| `event_type` | Lower snake case event name owned by the emitting manager or app. Names must follow the compatibility rules from [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md). |
| `sequence_anchor_hint` | `global_seq` for graph events or a per source monotonic counter for other classes. Hints are validated and normalized before assignment. |
| `operation_context` | Immutable context supplied by the emitter that adheres to [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md). The structure captures requester identity, device identity, app scope, and audit metadata, or an explicit reduced visibility capsule if no requester exists. |
| `app_id` / `domain_id` | Required identifiers enforced by the namespace guarantees in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md). Cross app or cross domain descriptors are rejected. |
| `scope_hint` | Advisory subset of `{ app_id, domain_id, requester_identity_id, peer_identity_id }` used to constrain later audience derivation. |
| `payload_summary` | Deterministic metadata free of mutable graph objects, secrets, or protocol envelopes, following [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md). |
| `audience_hint` | Optional reference to ACL inputs already calculated by the emitting manager. [Event Manager](11-event-manager.md) treats hints as untrusted and revalidates them. |
| `resume_hint` | Optional tuple referencing `{ global_seq, local_order }` to accelerate resume index writes; it is never exposed outside [Event Manager](11-event-manager.md). |

Descriptors are appended only after the emitting manager finishes its commit phase and can prove the write succeeded. Services and frontend code must publish via the manager that owns the underlying operation or through [App Manager](08-app-manager.md) validated hooks; direct publication is forbidden.

### 2.2 Event classes

[Event Manager](11-event-manager.md) classifies events into a small fixed set of top level classes. Class membership controls ordering anchors, default priority, and subscription gating.

| Class                               | Description                                                                                                                                             | Primary sources                                                     | Scope anchor                                        |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | --------------------------------------------------- |
| `graph.*` domain events             | Notifications that a graph envelope committed, including creates, updates, ratings changes, and ACL mutations, without embedding mutable object bodies. | [Graph Manager](07-graph-manager.md) post commit hook.                                     | `app_id`, `domain_id`, `global_seq`, object ids.    |
| `system.*` lifecycle events         | Node bootstrap, configuration changes, manager readiness shifts, health degradation, recovery signals, and internal pipeline state transitions.         | [Config Manager](01-config-manager.md), [App Manager](08-app-manager.md), [Health Manager](13-health-manager.md), [Log Manager](12-log-manager.md).           | `node_id`, manager name, per source `event_seq`.    |
| `network.*` transport events        | Peer admission outcomes, disconnects, delivery failures, reachability signals, and DoS reactions that are safe for the intended audience.               | [Network Manager](10-network-manager.md), [DoS Guard Manager](14-dos-guard-manager.md).                                 | `peer_identity_id` and per source `event_seq`.      |
| `security.*` abuse and audit events | Admin gated actions, authentication failures, challenge issuance, and subscription enforcement outcomes intended for monitoring and incident response.  | [Auth Manager](04-auth-manager.md), [DoS Guard Manager](14-dos-guard-manager.md), [Log Manager](12-log-manager.md), [Event Manager](11-event-manager.md) itself. | `requester_identity_id` and per source `event_seq`. |

Apps may register additional app prefixed event types only through [App Manager](08-app-manager.md) registration. App event types must remain confined to the owning app and must declare scope anchors up front. 

### 2.3 Event envelope structure

Every emitted event is normalized into an immutable `EventEnvelope`. The envelope is the only unit that crosses the [Event Manager](11-event-manager.md) internal engine boundaries and the only unit delivered over the WebSocket.

| Field               | Description                                                                                                                                                |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `event_id`          | 128 bit random identifier unique per event envelope.                                                                                                       |
| `event_type`        | Lower snake case string such as `graph.object_mutated`, with dot separated hierarchy.                                                                      |
| `source_manager`    | Manager or app identifier that authored the event descriptor.                                                                                              |
| `sequence_anchor`   | Either `global_seq` for domain events, or a monotonic `event_seq` per source for non domain events.                                                        |
| `scope`             | Subset of `{ app_id, domain_id, requester_identity_id, peer_identity_id }` describing who may observe the event.                                           |
| `audience_contract` | Hash derived from ACL capsule inputs plus optional subscription labels, used to detect staleness and prevent cross identity reuse.                         |
| `payload_summary`   | Constant size metadata such as operation ids, object ids, rating ids, route names, peer ids, or health enumerations. No mutable graph content is embedded. |
| `resume_token`      | Opaque tuple `{ event_id, sequence_anchor, issued_at }` used for resume. Tokens are only meaningful to [Event Manager](11-event-manager.md).                                      |
| `emitted_at`        | Monotonic clock timestamp for telemetry only.                                                                                                              |

`scope` and `audience_contract` rely on access control inputs and do not introduce new authorization surfaces beyond those defined in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

### 2.4 Event naming and compatibility

* Event names are stable and versioned, matching the compatibility rules in [01-protocol/11-versioning-and-compatibility.md](../../01-protocol/11-versioning-and-compatibility.md).
* Backwards incompatible changes require a new `event_type` suffix or segment that is explicitly versioned, for example `graph.object_mutated.v2`, and the older name must remain valid until removed via the upgrade process defined in [01-protocol/11-versioning-and-compatibility.md](../../01-protocol/11-versioning-and-compatibility.md). 
* App supplied event names are prefixed with the app slug, for example `app.contacts.message_created`, so they remain confined to the namespaces described in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md). 
* Each dot separated segment must be lower snake case per [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Payload summaries are immutable once published for a given `event_type`. Optional fields may be added only when subscribers can deterministically detect presence, either by explicit `event_type` versioning or by an explicit schema contract that is already stable for that `event_type`, matching [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).

## 3. Event publication lifecycle

[Event Manager](11-event-manager.md) operates as a staged pipeline. Phases must not be reordered or skipped. 

### 3.1 Source ingestion

* Managers emit `EventDescriptor` objects only after their own commit points, and include the authoritative [OperationContext](../services-and-apps/05-operation-context.md), or a reduced visibility descriptor when the emitting manager has no requester context, matching the ordered write path defined in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). 
* Descriptors enter [Event Manager](11-event-manager.md) via an in process channel.
* Inputs from services are forbidden. Only managers may emit descriptors. App code and services must publish via [App Manager](08-app-manager.md) validated paths. 
* All descriptors are treated as trusted metadata but untrusted audience hints. [Event Manager](11-event-manager.md) validates them before any delivery. 

### 3.2 Normalization

* Descriptors are converted into `EventEnvelope` structures by adding `event_id`, `sequence_anchor`, normalized `scope`, and delivery metadata. 
* Invalid descriptors are rejected with a synchronous error to the emitting manager. Invalid includes missing identifiers, cross app leakage, negative anchors, malformed scope hints, or forbidden event class for the source. 
* Normalization enforces that domain events cannot reference more than one `app_id` or `domain_id`. 
* Normalization writes resume index entries before the envelope is visible to downstream engines.

### 3.3 Audience binding

* For each envelope, [Event Manager](11-event-manager.md) derives an `audience_contract` describing the authorization inputs it will later use to authorize subscribers. 
* For domain events, [Event Manager](11-event-manager.md) requests an ACL read visibility capsule from [ACL Manager](06-acl-manager.md) using `{ requester_identity_id, scope, object_ids }` and caches the capsule for the envelope retention lifetime, directly applying the authorization posture defined in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md). 
* For system and security events, [Event Manager](11-event-manager.md) binds to admin roles and observer scopes declared in configuration and validated by [ACL Manager](06-acl-manager.md). Cross app bindings are forbidden unless [App Manager](08-app-manager.md) explicitly registered a cross app channel. 
* [ACL Manager](06-acl-manager.md) must not be called in the per frame WebSocket hot path for every event. Capsules are designed to be reused for the envelope lifetime. 

### 3.4 Delivery

* Envelopes enter per class priority queues with deterministic ordering consistent with [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Domain queues order strictly by `global_seq` to maintain the commit ordering defined in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* System, network, and security queues order by `(source_manager, event_seq)` with a stable per source local order tie breaker so non-domain events retain their sequencing semantics from [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). 
* Subscription filters pull from relevant queues and re validate the `audience_contract` against the subscriber's immutable [OperationContext](../services-and-apps/05-operation-context.md) exactly as constructed in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* On match, [Event Manager](11-event-manager.md) enqueues a delivery unit into the subscriber buffer and updates resume tracking state.
* Delivery completion updates telemetry counters. Drops, suppressions, and enforcement actions emit audit events to [Log Manager](12-log-manager.md).

## 4. Subscription model and WebSocket delivery

### 4.1 Connection setup

1. HTTP layer receives an `Upgrade: websocket` request at the local event route surface, consistent with the local transport expectations in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).
2. [Auth Manager](04-auth-manager.md) authenticates the requester and attaches an immutable [OperationContext](../services-and-apps/05-operation-context.md) including `requester_identity_id`, `app_id`, domain scope, and trace id, consistent with [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md). 
3. The upgraded socket is handed to [Event Manager](11-event-manager.md) together with [OperationContext](../services-and-apps/05-operation-context.md) and requested subscription filters.
4. [Event Manager](11-event-manager.md) validates requested filters against [OperationContext](../services-and-apps/05-operation-context.md) and subscription gating rules.
5. On success, [Event Manager](11-event-manager.md) assigns a `connection_id`, registers the subscription, initializes per connection buffers, and begins heartbeats.
6. On failure, [Event Manager](11-event-manager.md) rejects with typed errors mapped to the system failure taxonomy defined in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). No partially authorized subscription state may persist.

### 4.2 Subscription filters

Required parameters:

* `app_id`, must match `[OperationContext](../services-and-apps/05-operation-context.md).app_id` so namespace isolation from [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md) is preserved.
* `subscription_type`, one of `graph`, `system`, `network`, `security`, or an app defined channel registered by [App Manager](08-app-manager.md), aligning with the event class definitions in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md). 

Optional parameters:

* `domain_id`, must be a subset of domains allowed by [OperationContext](../services-and-apps/05-operation-context.md), respecting [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* `object_ids`, only valid for channels that explicitly support object scoped subscriptions and only when ACL capsules permit visibility per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* `peer_identity_id`, only valid for `network.*` channels and only when the subscriber is authorized to observe peer metadata under [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* `event_type`, used to narrow within the subscribed class, never to widen. 

Filter rules:

* Filters are immutable for the lifetime of the connection. Changing filters requires opening a new connection. 
* Admin only channels, including `system.*` and `security.*`, additionally require the admin gating bit in [OperationContext](../services-and-apps/05-operation-context.md) as set by [Auth Manager](04-auth-manager.md) per [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md). 
* Filters must not span multiple apps or domains unless [App Manager](08-app-manager.md) explicitly registered a cross app subscription channel and [ACL Manager](06-acl-manager.md) validated its visibility semantics, preserving the isolation described in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md) and [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

### 4.3 Delivery semantics

* Delivery is best effort and at most once, matching the realtime delivery expectations in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). If a client misses an event, the client must recover using read APIs anchored by `global_seq` or other identifiers. 
* Events must not be treated as a durable queue, a transaction log, or a source of truth. The committed graph defined in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) remains the source of truth.
* Event envelopes delivered over the socket must be deterministic JSON as defined in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md), and stable field ordering is required for consistent client parsing and auditing.

### 4.4 Per connection buffer and ACK semantics

* Each connection maintains a sliding buffer sized by `event.queue.per_connection`, enforcing the bounded memory requirements of [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). 
* Each delivered envelope carries a `resume_token` constructed per [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Clients must ACK delivered envelopes by sending an ACK frame containing the `resume_token`. ACK frames are untrusted and must be validated against the authorization posture from [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* ACK advances the connection window and allows the [Event Manager](11-event-manager.md) to evict acknowledged envelopes from the per connection buffer when they age out of the global retention window.
* If the buffer overflows due to missing ACKs, slow consumption, or client misbehavior, [Event Manager](11-event-manager.md) closes the connection with a `buffer_overflow` error and emits a `security.subscription_dropped` event, failing closed per [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). 
* [Event Manager](11-event-manager.md) must never respond to buffer overflow by allocating more memory beyond configured caps.

### 4.5 Heartbeats and resume

* Heartbeats are sent every `event.delivery.heartbeat_interval_ms` to satisfy the readiness and liveness reporting obligations in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md). 
* If no heartbeat response is received within two intervals, the connection is closed and a drop event is emitted for audit, following the fail closed posture in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Clients may reconnect and present a `resume_token` constructed according to [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* [Event Manager](11-event-manager.md) validates the token cryptographically and structurally, and verifies the referenced event is still within the retention window `event.delivery.resume_window`, ensuring replay never exceeds the bounds defined in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* If valid and available, [Event Manager](11-event-manager.md) replays pending events in order, subject to current authorization rules.
* If unavailable, [Event Manager](11-event-manager.md) instructs the client to perform an HTTP catch up read. Resume must never trigger [Event Manager](11-event-manager.md) to read historical events from storage.

### 4.6 Backpressure, throttling, and connection admission

Admission limits:

* Global concurrent connection count limited by `event.websocket.max_connections`, ensuring realtime surfaces stay within the fail closed bounds in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Per identity connection count limited by `event.websocket.max_connections_per_identity` so a single identity cannot exhaust resources contrary to [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Per app totals may be enforced as a derived limit if declared in configuration and applied consistently.

Send throttling:

* Per connection send rate is limited by `event.delivery.max_msgs_per_sec` enforced by token buckets, maintaining the fairness constraints implied by [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md). 
* Throttling must preserve ordering for each connection. Dropping due to throttling is forbidden. If throttling cannot be applied without violating ordering and bounded memory, the connection must be closed.

Global backpressure:

* [Event Manager](11-event-manager.md) enforces a global queued event ceiling `event.queue.total_ceiling` as a hard limit derived from [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). 
* When global ceilings are approached, [Event Manager](11-event-manager.md) signals Source Intake to pause lower priority classes before affecting `graph.*`, maintaining the ordered delivery contract in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* When ceilings are exceeded, [Event Manager](11-event-manager.md) applies deterministic shedding only where permitted by this spec, and emits explicit telemetry and audit records to satisfy [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

DoS integration:

* [DoS Guard Manager](14-dos-guard-manager.md) may instruct [Event Manager](11-event-manager.md) to temporarily deny new subscriptions or close existing subscriptions when abuse thresholds are crossed, using the directive model defined in [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md). 
* [Event Manager](11-event-manager.md) must treat such instructions as authoritative for admission, but must still emit auditable outcomes and preserve fail closed behavior.

### 4.7 Startup and shutdown behavior

Startup requirements:

* [Event Manager](11-event-manager.md) must not accept WebSocket upgrades until [Config Manager](01-config-manager.md) has supplied a valid `event.*` snapshot and [Event Manager](11-event-manager.md) has validated all required keys and constraints, satisfying the readiness prerequisites outlined in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). 
* [Event Manager](11-event-manager.md) must register intake channels for all authorized manager sources before declaring readiness true to ensure sequencing matches [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* [Event Manager](11-event-manager.md) must register its readiness and liveness probes with [Health Manager](13-health-manager.md) during startup and must default readiness to false until all internal engines are running, matching the node lifecycle expectations in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md). 
* If [Event Manager](11-event-manager.md) cannot bind the WebSocket listener surface, readiness must remain false and the node must treat realtime delivery as unavailable, failing closed per [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

Shutdown requirements:

* On shutdown, [Event Manager](11-event-manager.md) must stop accepting new upgrades, then close existing connections with a typed shutdown reason that maps to the taxonomy defined in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Shutdown must flush audit logs for subscription closures to [Log Manager](12-log-manager.md) best effort, without blocking shutdown indefinitely.
* Shutdown must drop all in memory buffers and resume indexes. After restart, clients must reconnect and recover via reads, consistent with non durable semantics. 

## 5. Internal engines and data paths

[Event Manager](11-event-manager.md) is composed of six mandatory internal engines. These engines define strict phase boundaries and must not be collapsed, reordered, or bypassed. Each engine exposes explicit inputs, outputs, and failure signaling. 

Engines communicate exclusively via bounded queues. The flow is strictly Source Intake to Normalization to Audience Binding to Delivery, with Subscription Registry wrapping ingress and egress and Telemetry observing all stages. 

### 5.1 Source Intake Engine

The Source Intake Engine is the only ingress for manager authored `EventDescriptor` objects. 

Responsibilities:

* Register a dedicated intake channel for each manager allowed to emit descriptors.
* Validate descriptor completeness, including source name, event type, sequence anchor, scope hints, and payload summary, matching the descriptor rules in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md). 
* Reject descriptors that reference multiple apps or multiple domains to uphold the isolation rules from [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Enforce that descriptors are submitted only after the emitting manager's commit point, maintaining the ordered write path in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Assign a per source `local_order` counter to preserve FIFO semantics downstream.
* Apply per source and global backpressure based on `event.queue.total_ceiling` so intake respects the fail closed requirements in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

Outputs:

* Validated descriptors forwarded to the Normalization Engine, tagged with `{ source_manager, local_order }`.

Failure behavior:

* Validation failures return synchronous errors to the emitter, including `invalid_descriptor`, `scope_violation`, and `queue_full`, mapped to the taxonomy in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Every rejection must emit an auditable telemetry event and must be logged to [Log Manager](12-log-manager.md).

Constraints:

* Intake must not mutate descriptor payloads beyond tagging.
* Intake must never drop descriptors silently.

### 5.2 Normalization Engine

The Normalization Engine converts descriptors into immutable `EventEnvelope` structures. 

Responsibilities:

* Assign `event_id` and `emitted_at`, preserving the envelope structure defined in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Determine whether the sequence anchor is `global_seq` for domain events, or internal `event_seq` for non domain events, aligning with [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Enforce app and domain isolation. Descriptors spanning multiple apps are rejected and recorded as a security violation per [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Maintain per class queues sized according to `event.queue.total_ceiling`, preserving ordering by `(class, sequence_anchor, source_order)` so ordering constraints from [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) hold.
* Populate a resume index mapping `event_id` to a queue pointer and anchor information for reconnect handling.

Outputs:

* Immutable envelopes queued for Audience Binding, along with class and ordering metadata.

Failure behavior:

* On queue saturation, apply deterministic shedding of lower priority classes before affecting `graph.*`, and emit `system.event_queue_overflow`.
* If shedding is insufficient to restore bounded memory, the engine must force readiness false and trigger connection shedding, not memory growth.

Constraints:

* Normalization must not reorder within a class.
* Normalization must not mutate `payload_summary`, keeping the deterministic fields from [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) intact.

### 5.3 Audience Binding Engine

The Audience Binding Engine binds envelopes to an authorization capsule and an audience contract. 

Responsibilities:

* Batch envelopes by `(app_id, domain_id, subscription_type)` and request ACL capsules from [ACL Manager](06-acl-manager.md) as defined in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Encode the originating [OperationContext](../services-and-apps/05-operation-context.md) identity and scope inside the capsule to prevent reuse by other identities, leveraging the trust model in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Cache capsules until the envelope ages out of `event.delivery.resume_window` or until no subscribers can reference the envelope.
* Surface readiness false if [ACL Manager](06-acl-manager.md) is unavailable, preventing further delivery in accordance with [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

Outputs:

* Envelope and capsule pairs handed to the Delivery Engine.

Failure behavior:

* ACL failures or outages halt progression of affected envelopes. [Event Manager](11-event-manager.md) must not downgrade authorization, infer scope, or widen visibility.
* Authorization binding failures must be recorded as audit events and must be visible in telemetry, mapped to the taxonomy from [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

Constraints:

* Capsules must be small, bounded, and must not include secrets.
* Capsules must not be shared across app boundaries unless [App Manager](08-app-manager.md) explicitly registered the cross app channel.

### 5.4 Subscription Registry Engine

The Subscription Registry Engine governs WebSocket lifecycles and subscription state. 

Responsibilities:

* Accept upgrade requests only after [Auth Manager](04-auth-manager.md) supplies a valid [OperationContext](../services-and-apps/05-operation-context.md) per [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Validate requested filters against [OperationContext](../services-and-apps/05-operation-context.md) and admin gating bits.
* Compile filters into deterministic matchers referencing capsule ids and scope metadata so subscription scope stays aligned with [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Manage resume tokens, verify authenticity, locate referenced events in the resume index, and preload pending envelopes into the connection buffer exactly as described in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Track per connection state `{ connection_id, operation_context, filters, buffer_state, last_ack_token, heartbeat_deadline }` and enforce heartbeat timers.
* Emit auditable subscription lifecycle events for open, reject, close, overflow, resume accepted, and resume refused, using the [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md) taxonomy.

Failure behavior:

* Any filter validation failure results in immediate connection close with a typed error and a `security.subscription_rejected` audit event, adhering to [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Any resume token validation failure results in immediate close and a security audit event, without revealing whether the referenced token existed, honoring the secrecy requirements in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).

Constraints:

* Filters are immutable for the life of the connection.
* Registry must not block the reactor loop on heavy work. Any heavy work must be delegated without changing ordering or authorization outcomes.

### 5.5 Delivery Engine

The Delivery Engine moves envelopes from class queues to subscriber buffers and over the WebSocket transport. 

Responsibilities:

* Consume class queues using weighted round robin with a default priority ordering of `graph` then `security` then `network` then `system`, while preventing starvation so that ordering guarantees from [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) remain intact.
* Evaluate each envelope against registered subscriptions using cached capsule constraints derived from [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Write matching envelopes into per connection ring buffers sized by `event.queue.per_connection` and track ACK progress.
* Apply backpressure when total buffered events reach `event.queue.total_ceiling` by signaling Source Intake to pause lower priority classes, never exceeding the fail closed bounds from [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Serialize envelopes into deterministic JSON frames and send them via the WebSocket adapter described in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md), capturing send success and failure telemetry.

Failure behavior:

* Missing ACKs beyond configured limits trigger buffer overflow handling and connection closure with typed errors per [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Repeated send failures increment per connection error counters and may force teardown.
* Delivery must never retry silently after close. Clients must reconnect and recover via resume or read APIs. 

Constraints:

* Delivery may not mutate envelope contents beyond framing.
* Delivery must not implement implicit retries.

### 5.6 Telemetry Engine

The Telemetry Engine provides observability across all engines. 

Responsibilities:

* Sample queue depth, produced delivered dropped counters per class, per connection ACK latency, heartbeat failures, and subscription rejection reasons.
* Emit readiness and liveness to [Health Manager](13-health-manager.md) on `event.telemetry.heartbeat_interval_ms` cadence and log readiness transitions via [Log Manager](12-log-manager.md), satisfying the observability requirements in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Forward repeated buffer overflows or subscription rejections to [DoS Guard Manager](14-dos-guard-manager.md) for abuse mitigation.
* Raise `system.event_pipeline_degraded` when saturation persists beyond `event.telemetry.degraded_threshold_ms`, or when dependencies such as [ACL Manager](06-acl-manager.md) or [Config Manager](01-config-manager.md) are unavailable, ensuring fail closed signaling per [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

Constraints:

* Telemetry must never include object identifiers or payload summaries that violate subscriber isolation.
* Telemetry sampling must not allocate unbounded memory or introduce hot path contention.

## 6. Configuration surface, `event.*`

[Event Manager](11-event-manager.md) owns the `event.*` namespace in [Config Manager](01-config-manager.md). The following keys are normative. 

| Key                                            | Type                 | Reloadable | Description                                                                                                               |
| ---------------------------------------------- | -------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------- |
| `event.websocket.max_connections`              | Integer              | Yes        | Global hard cap on concurrent WebSocket subscriptions.                                                                    |
| `event.websocket.max_connections_per_identity` | Integer              | Yes        | Per `requester_identity_id` cap to prevent identity level abuse.                                                          |
| `event.queue.per_connection`                   | Integer              | Yes        | Buffer depth per connection before overflow occurs.                                                                       |
| `event.queue.total_ceiling`                    | Integer              | No         | Maximum total queued events across all connections. Exceeding triggers deterministic enforcement and connection shedding. |
| `event.delivery.heartbeat_interval_ms`         | Integer              | Yes        | Interval between heartbeats. Must be greater than or equal to 5000 ms.                                                    |
| `event.delivery.resume_window`                 | Integer, event count | Yes        | Number of most recent events retained per class for resume requests.                                                      |
| `event.delivery.max_msgs_per_sec`              | Integer              | Yes        | Per connection send throttle rate.                                                                                        |
| `event.telemetry.emit_samples`                 | Boolean              | Yes        | Enables verbose telemetry emission to [Log Manager](12-log-manager.md) for debugging.                                                          |
| `event.security.admin_channels`                | List                 | No         | Explicit list of event types requiring admin gating.                                                                      |

Validation rules:

* Startup fails if required keys are missing or invalid, matching the configuration constraints in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Reload follows [Config Manager](01-config-manager.md) prepare and commit flow. [Event Manager](11-event-manager.md) must acknowledge or veto reloads based on whether new limits can be applied safely without violating bounded memory, ordering, or authorization as mandated in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). 
* If a reload cannot be applied without dropping existing connections, [Event Manager](11-event-manager.md) must either veto, or apply a deterministic shedding plan that is explicitly logged, and must surface readiness transitions accordingly, satisfying the fail closed rules in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

## 7. Component interactions

### 7.1 [Graph Manager](07-graph-manager.md)

* Provides post commit event descriptors for every committed envelope per [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). Each descriptor includes affected object ids, `global_seq`, `app_id`, `domain_id`, and the submitting [OperationContext](../services-and-apps/05-operation-context.md). 
* [Graph Manager](07-graph-manager.md) never attempts to deliver events on its own and must treat [Event Manager](11-event-manager.md) rejection as a hard failure for the descriptor emission step, ensuring the single deterministic notification path required by [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). 

### 7.2 [ACL Manager](06-acl-manager.md)

* Supplies read visibility capsules used as `audience_contract` inputs, following the model in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Capsules are immutable for the envelope lifetime.
* [ACL Manager](06-acl-manager.md) is not invoked per delivered frame in the WebSocket hot path. [Event Manager](11-event-manager.md) reuses capsules but verifies subscriber identity and scope match the recorded capsule parameters. 

### 7.3 [Auth Manager](04-auth-manager.md) and HTTP layer

* [Auth Manager](04-auth-manager.md) authenticates WebSocket upgrades and attaches [OperationContext](../services-and-apps/05-operation-context.md) as described in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* [Event Manager](11-event-manager.md) relies on the admin gating bit to decide if a subscriber can request admin only channels, preserving the trust rules in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md). 

### 7.4 [Config Manager](01-config-manager.md)

* Supplies `event.*` namespace snapshots, enabling [Event Manager](11-event-manager.md) to enforce the limits referenced in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* [Event Manager](11-event-manager.md) must request revalidation before applying reloads per the prepare/commit rules in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* [Event Manager](11-event-manager.md) must publish readiness false if configuration cannot be applied safely, matching the fail closed requirement in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). 

### 7.5 [App Manager](08-app-manager.md) and services

* [App Manager](08-app-manager.md) registers app prefixed event types and declares their scope anchors per [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md). [Event Manager](11-event-manager.md) enforces those declarations at runtime. 
* Services may request [Event Manager](11-event-manager.md) to emit custom app events only through [App Manager](08-app-manager.md) validated descriptors. Direct service to [Event Manager](11-event-manager.md) calls are forbidden. 

### 7.6 [Network Manager](10-network-manager.md) and [DoS Guard Manager](14-dos-guard-manager.md)

* [Network Manager](10-network-manager.md) emits transport lifecycle events such as `network.peer_admitted`, `network.peer_dropped`, and `network.delivery_failed` with peer identity metadata appropriate for the intended audience, matching the transport obligations defined in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md). 
* [DoS Guard Manager](14-dos-guard-manager.md) emits abuse events and may instruct [Event Manager](11-event-manager.md) to close or deny subscriptions when abuse thresholds are crossed. 

### 7.7 [Log Manager](12-log-manager.md)

* Receives audit logs for subscription lifecycle, buffer drops, authorization failures, and abnormal delivery latencies so the failure taxonomy in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md) is persisted. 
* Receives copies of critical `security.*` events so they can be persisted to sinks distinct from transient WebSocket delivery. 
* Persistent notification feeds, if implemented, are owned by [Log Manager](12-log-manager.md) rather than [Event Manager](11-event-manager.md), because [Event Manager](11-event-manager.md) is explicitly non durable. The older high level design expectation of a unified, filterable notification feed aligns with [Log Manager](12-log-manager.md) persistence rather than realtime transient delivery.

### 7.8 [Health Manager](13-health-manager.md)

* Consumes readiness, liveness, and queue depth metrics required by [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* [Event Manager](11-event-manager.md) must mark readiness false when no listener is available, when dependencies are unavailable, or when intake queues are saturated, maintaining fail closed posture from [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). 

### 7.9 [Storage Manager](02-storage-manager.md)

* [Event Manager](11-event-manager.md) does not call [Storage Manager](02-storage-manager.md) directly.
* Historical replay must be implemented by clients and services reading committed state from the graph as described in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). 

## 8. Failure handling and rejection behavior

[Event Manager](11-event-manager.md) must fail closed. Failures must be explicit, auditable, and must not widen visibility or weaken ordering.

* Structural descriptor failures result in synchronous rejection to the emitting manager. [Event Manager](11-event-manager.md) logs the failure with context and drops the descriptor per the taxonomy in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). 
* Subscription authentication failures are surfaced immediately to the HTTP layer. No socket upgrade occurs, preserving the trust boundaries from [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md). 
* Authorization failures after upgrade, such as requesting a domain outside [OperationContext](../services-and-apps/05-operation-context.md), cause the connection to close with `permission_denied` mapped to [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). 
* Buffer overflows, heartbeat timeouts, invalid ACKs, invalid resume tokens, or malformed frames close the connection and emit security audit events, including `security.subscription_dropped` and `security.subscription_rejected`, satisfying [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). 
* [Event Manager](11-event-manager.md) never retries deliveries after closing a connection. Clients must reconnect and use resume or read APIs to recover, aligning with the realtime semantics in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). 
* Dependency outages, including [ACL Manager](06-acl-manager.md) outage or [Config Manager](01-config-manager.md) inability to supply valid config, must force readiness false and must halt delivery rather than bypassing authorization or limits, consistent with [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). 

## 9. Security and trust boundary constraints

* The WebSocket surface is a strict trust boundary defined in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md). [Event Manager](11-event-manager.md) treats all incoming frames as untrusted until validated. 
* Subscribers cannot observe objects, identifiers, or sequences they could not read via normal read APIs. Authorization decisions defer to ACL capsules plus the subscriber [OperationContext](../services-and-apps/05-operation-context.md) exactly as defined in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md). 
* [Event Manager](11-event-manager.md) must not leak peer topology, secret configuration, or transport metadata that the subscriber is not cleared to see. 
* Resume tokens are cryptographically opaque using an HMAC key stored only in process memory, matching the envelope guarantees in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md). Clients cannot forge resume positions. 
* [Event Manager](11-event-manager.md) must not allow cross app event visibility unless explicitly registered and validated.
* [Event Manager](11-event-manager.md) must not accept event descriptors from untrusted sources. Only manager to manager in process channels are permitted, consistent with [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).

## 10. State, persistence, and backpressure constraints

* [Event Manager](11-event-manager.md) persists no durable event log. It retains only `event.delivery.resume_window` entries in memory per class to service short reconnects, staying aligned with the realtime semantics of [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). 
* Per connection buffers are bounded ring buffers sized to comply with the resource ceilings defined in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). The only mutable per connection state is `{ [OperationContext](../services-and-apps/05-operation-context.md), subscription filters, last_ack_token, queue }`. 
* On process restart, all subscriptions are lost, buffers are discarded, and clients must reconnect. This is acceptable because committed state remains in the graph and can be recovered via reads per [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). 
* [Event Manager](11-event-manager.md) must never persist events in SQLite, must never attempt to use [Storage Manager](02-storage-manager.md) as an event replay backend, and must never allocate memory beyond configured bounds to satisfy slow consumers, complying with [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

## 11. Observability and telemetry outputs

[Event Manager](11-event-manager.md) emits the following telemetry:

* Readiness flag indicating whether the listener and critical engines are healthy, satisfying [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Liveness flag indicating runtime loop progress, also reported per [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Counters per event class, produced delivered dropped, so ordering guarantees in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) can be audited.
* Per connection utilization, buffer depth, ACK latency histograms to demonstrate compliance with the bounded memory rules in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Rate of subscription failures by reason, including `auth_failed`, `acl_denied`, `filter_invalid`, `buffer_overflow`, `resume_invalid`, `heartbeat_timeout`, all mapped to [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Dependency health and saturation signals, including `system.event_pipeline_degraded`, enabling fail closed transitions per [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* DoS Guard instructions and enforcement outcomes recorded as events so administrators can correlate cause and effect with [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md) directives. 

Telemetry routing:

* Telemetry is routed through [Health Manager](13-health-manager.md) for aggregated status and through [Log Manager](12-log-manager.md) for audit records, matching the observability posture in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Optional verbose samples controlled by `event.telemetry.emit_samples` may include `event_type` and `scope.app_id` but must never include full object bodies or sensitive identifiers outside authorized scope, staying within the access control model in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md). 

## 12. Forbidden behaviors and compliance checklist

The following actions violate this specification:

* Allowing any manager, service, or app to publish events outside [Event Manager](11-event-manager.md), which would violate [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). 
* Embedding mutable graph data, private keys, or secrets in events, contrary to [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md). 
* Delivering events before [Graph Manager](07-graph-manager.md) commits the underlying envelope or before the emitting manager completes its commit point, violating [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). 
* Authorizing subscriptions solely on client provided metadata without consulting [OperationContext](../services-and-apps/05-operation-context.md) and ACL capsules, violating the access control posture in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md). 
* Persisting event history in SQLite or attempting to use [Event Manager](11-event-manager.md) as a durable queue, contrary to the realtime semantics in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). 
* Allowing event filters to span multiple apps or domains unless [App Manager](08-app-manager.md) explicitly registered the cross app subscription and [ACL Manager](06-acl-manager.md) validated visibility, breaking [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md). 
* Calling [ACL Manager](06-acl-manager.md) in the per frame hot path for every delivered event rather than using capsules, which would contradict the capsule reuse requirement in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Allowing resume tokens to be accepted without cryptographic validation and retention window checks, violating [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Growing buffers beyond configured caps instead of failing closed, breaking [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

Implementations must demonstrate that all guarantees, limits, ordering rules, and fail closed behaviors described above are enforced before the [Event Manager](11-event-manager.md) surface is considered complete.
