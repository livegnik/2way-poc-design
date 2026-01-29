



## 1. Purpose and scope

The Event Manager is the authoritative component responsible for the scope described below. The Event Manager is the sole publication and subscription authority for backend events in the 2WAY node. It receives post commit facts from managers, normalizes them into immutable notifications, enforces audience and access constraints, and delivers them to subscribers over the single local WebSocket surface.

This specification defines the event model, internal engines, ordering and delivery guarantees, subscription semantics, configuration surface, and trust boundaries for the Event Manager. It does not redefine schema semantics, persistence rules, network transport encodings, or UI behavior.

This specification consumes the protocol contracts defined in:

* [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md)
* [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md)
* [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md)
* [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md)
* [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md)
* [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md)
* [01-protocol/11-versioning-and-compatibility.md](../../01-protocol/11-versioning-and-compatibility.md)

Those files remain normative for all behaviors described here and for every cross-manager interaction referenced by this document.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Owning all publication surfaces for backend events and enforcing the invariant that all state change notifications flow through [Event Manager](11-event-manager.md), preserving the single ordered write and notification path mandated in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). 
* Accepting normalized event descriptors from [Graph Manager](07-graph-manager.md), [App Manager](08-app-manager.md), [Config Manager](01-config-manager.md), [Network Manager](10-network-manager.md), [Health Manager](13-health-manager.md), [DoS Guard Manager](14-dos-guard-manager.md), and [Log Manager](12-log-manager.md) after those managers complete their own validation and commit phases so sequencing and trust rules from [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) remain intact. 
* Binding event metadata to [OperationContext](../services-and-apps/05-operation-context.md) derived visibility rules so subscribers can only observe events they are authorized to observe under the access control model described in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md) and enforced using the identity guarantees in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md). 
* Maintaining the single WebSocket delivery surface, including admission, subscription filtering, flow control, resume tokens, and delivery telemetry, consistent with the transport and readiness constraints in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md). 
* Providing deterministic classification and routing for domain events, lifecycle events, transport events, and abuse and audit events, while preserving naming, envelope, and compatibility guarantees from [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and [01-protocol/11-versioning-and-compatibility.md](../../01-protocol/11-versioning-and-compatibility.md). 
* Emitting audit signals to [Log Manager](12-log-manager.md) when subscriptions change state, buffers overflow, delivery is suppressed, or component health transitions, matching the failure taxonomy defined in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). 
* Enforcing per connection and global resource limits sourced from `event.*` configuration so hostile subscribers cannot exhaust backend memory, and failing closed when limits from [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md) cannot be honored. 
* Reporting readiness, liveness, and queue depth to [Health Manager](13-health-manager.md), and forwarding repeated abuse signals to [DoS Guard Manager](14-dos-guard-manager.md), so event surfaces participate in fail closed behavior alongside [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md) directives. 
* Providing an internal in process pub sub bus for managers to observe lifecycle transitions and operational signals without introducing additional delivery surfaces, preserving the trust boundaries mandated in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).

This specification does not cover the following:

* Schema validation, ACL evaluation of graph writes, graph mutation sequencing, or sync reconciliation. These remain owned by [Schema Manager](05-schema-manager.md), [ACL Manager](06-acl-manager.md), [Graph Manager](07-graph-manager.md), and [State Manager](09-state-manager.md).
* Definition of HTTP or WebSocket route syntax beyond the existence of a single local upgrade surface. Route naming and HTTP contract details live in [interface specifications](../../04-interfaces/).
* Persistence of historical events, durable replay logs, offline delivery, or guaranteed delivery semantics. [Event Manager](11-event-manager.md) delivers best effort realtime notifications only. 
* Remote sync propagation or peer to peer message routing. [State Manager](09-state-manager.md) and [Network Manager](10-network-manager.md) own remote ingress and egress.
* Any UI behavior, payload interpretation, or client retry policy. Clients must use read APIs to inspect committed state.
