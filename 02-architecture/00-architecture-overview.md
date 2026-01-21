


# 00 Architecture overview

## 1. Purpose and scope

This document defines the architectural role and posture of the 2WAY PoC backend. It explains how managers, services, runtime topologies, trust boundaries, and data flows compose into a single node, and it inventories every specification under [02-architecture/**](./). It captures invariants, allowed behaviors, and rejection posture at the architectural level without re-specifying schema, envelope, or transport details already defined elsewhere in the repository. Frontend presentation and UX flows are out of scope except where they cross a trust boundary.

This overview references:

* [01-protocol/**](../01-protocol/)
* [02-architecture/**](./)
* [02-architecture/managers/**](managers/)
* [02-architecture/services-and-apps](services-and-apps/)
* [02-architecture/01-component-model.md](01-component-model.md)
* [02-architecture/02-runtime-topologies.md](02-runtime-topologies.md)
* [02-architecture/03-trust-boundaries.md](03-trust-boundaries.md)
* [02-architecture/04-data-flow-overview.md](04-data-flow-overview.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Documenting the architectural intent and guarantees that bind all managers, services, and runtime arrangements.
* Summarizing the responsibilities of each companion document under [02-architecture](./) and describing how they are consumed together.
* Highlighting the mandatory trust boundaries, sequencing rules, and data flows that all implementations must preserve.

This specification does not cover the following:

* Schema definitions, envelope formats, serialization, or crypto mechanics (see [01-protocol/**](../01-protocol/)).
* [Database layouts](../03-data/01-sqlite-layout.md), query plans, deployment automation, or performance tuning details.
* UI workflows, frontend component structure, or domain semantics beyond architectural constraints.

## 3. Architectural posture and guiding principles

* The backend is a long-lived process composed of singleton managers that guard protocol invariants and services that orchestrate domain workflows ([01-component-model.md](01-component-model.md)).
* [Graph Manager](managers/07-graph-manager.md) remains the only write authority, [Storage Manager](managers/02-storage-manager.md) the only database authority, [Schema Manager](managers/05-schema-manager.md) the only schema interpreter, [ACL Manager](managers/06-acl-manager.md) the only authorization authority, and [Key Manager](managers/03-key-manager.md) the only component allowed to touch private keys.
* Services, frontend apps, and remote peers are untrusted; they must cross [Auth Manager](managers/04-auth-manager.md), [Network Manager](managers/10-network-manager.md), [ACL Manager](managers/06-acl-manager.md), and [Schema Manager](managers/05-schema-manager.md) before any state mutation occurs.
* [OperationContext](services-and-apps/05-operation-context.md) is constructed once per request or sync package and propagated unchanged through managers to ensure deterministic enforcement.
* Runtime topology choices (single-process, split frontend, headless, multi-device, or remote peer) do not dilute the invariants defined by the component model ([02-runtime-topologies.md](02-runtime-topologies.md)).
* Trust boundaries fail closed. Violations never result in best-effort behavior; they result in rejection without state change ([03-trust-boundaries.md](03-trust-boundaries.md)).
* All data movement is intentional, enumerated, and sequenced. Ratings provide suppression semantics instead of delete operations, and derived data never becomes authoritative ([04-data-flow-overview.md](04-data-flow-overview.md)).

## 4. Architectural documents and companion specifications

### 4.1 Core architecture specifications

* [01-component-model.md](01-component-model.md) defines manager and service categories, invariants, and allowed/forbidden interactions for the backend component model.
* [02-runtime-topologies.md](02-runtime-topologies.md) enumerates conforming runtime layouts, the placement of managers, storage, keys, and frontend clients, and the trust posture for each topology.
* [03-trust-boundaries.md](03-trust-boundaries.md) documents every architectural trust boundary, the allowed flows across each boundary, and the rejection behavior when the boundary is violated.
* [04-data-flow-overview.md](04-data-flow-overview.md) details bootstrap, provisioning, read, write, rating, event, sync, and derived-data flows plus the guarantees that bind them.

### 4.2 Manager specifications ([02-architecture/managers](managers/))

Each manager has a dedicated specification file that defines authoritative responsibilities and ownership:

* [managers/00-managers-overview.md](managers/00-managers-overview.md) - landing page for manager responsibilities and dependency posture.
* [managers/01-config-manager.md](managers/01-config-manager.md) - configuration loading, validation, and publication.
* [managers/02-storage-manager.md](managers/02-storage-manager.md) - SQLite access boundaries, transaction guarantees, and persistence APIs.
* [managers/03-key-manager.md](managers/03-key-manager.md) - key lifecycle, storage, signing, decryption, and revocation handling.
* [managers/04-auth-manager.md](managers/04-auth-manager.md) - frontend authentication, session validation, and identity resolution rules.
* [managers/05-schema-manager.md](managers/05-schema-manager.md) - schema definition handling, validation ordering, and namespace enforcement.
* [managers/06-acl-manager.md](managers/06-acl-manager.md) - authorization inputs, evaluation semantics, and enforcement posture.
* [managers/07-graph-manager.md](managers/07-graph-manager.md) - mutation orchestration, sequencing, and envelope application behavior.
* [managers/08-app-manager.md](managers/08-app-manager.md) - app registration, lifecycle, extension loading, and namespace binding.
* [managers/09-state-manager.md](managers/09-state-manager.md) - sync domain definitions, sequencing, reconciliation, and replay protection.
* [managers/10-network-manager.md](managers/10-network-manager.md) - peer communication, transport abstraction, cryptographic binding, and DoS integration.
* [managers/11-event-manager.md](managers/11-event-manager.md) - event emission, subscription semantics, and WebSocket delivery contracts.
* [managers/12-log-manager.md](managers/12-log-manager.md) - audit, diagnostics, structured log formats, and access policies.
* [managers/13-health-manager.md](managers/13-health-manager.md) - liveness checks, readiness signals, and failure reporting.
* [managers/14-dos-guard-manager.md](managers/14-dos-guard-manager.md) - rate limiting, client puzzle enforcement, and abuse containment.

### 4.3 Services and apps specifications ([02-architecture/services-and-apps](services-and-apps/))

These documents define how system services, app extensions, and frontend experiences consume the managers:

* [services-and-apps/00-services-and-apps-overview.md](services-and-apps/00-services-and-apps-overview.md) - scope and shared responsibilities of backend services and frontend apps.
* [services-and-apps/01-services-vs-apps.md](services-and-apps/01-services-vs-apps.md) - differentiates long-lived system services from app-scoped extensions and UI apps.
* [services-and-apps/02-system-services.md](services-and-apps/02-system-services.md) - expectations for built-in services that ship with the node.
* [services-and-apps/03-app-backend-extensions.md](services-and-apps/03-app-backend-extensions.md) - constraints on optional backend extensions authored by apps.
* [services-and-apps/04-frontend-apps.md](services-and-apps/04-frontend-apps.md) - frontend posture, allowed backend interactions, and trust boundaries.
* [services-and-apps/05-operation-context.md](services-and-apps/05-operation-context.md) - definition of OperationContext, required fields, and propagation rules.

## 5. Component model summary

### 5.1 Manager invariants

Managers are singleton authorities. They initialize with the backend process, expose explicit APIs, and never share internal state. [Graph](managers/07-graph-manager.md), [Storage](managers/02-storage-manager.md), [Schema](managers/05-schema-manager.md), [ACL](managers/06-acl-manager.md), [Key](managers/03-key-manager.md), [App](managers/08-app-manager.md), [State](managers/09-state-manager.md), [Network](managers/10-network-manager.md), [Event](managers/11-event-manager.md), [Log](managers/12-log-manager.md), [Health](managers/13-health-manager.md), [DoS Guard](managers/14-dos-guard-manager.md), [Config](managers/01-config-manager.md), and [Auth](managers/04-auth-manager.md) Managers each own a single responsibility domain with no overlap. Managers interact via validated method calls only, never by reaching into each other's state, and circular dependencies are forbidden.

### 5.2 Service responsibilities

Services translate user intent into graph operations, aggregate reads, publish events, and expose backend endpoints. System services are always present and implement shared primitives. App extension services are optional, app-scoped, and must be removable without affecting global correctness. All services must supply a complete [OperationContext](services-and-apps/05-operation-context.md) for every manager invocation and must not attempt to enforce protocol rules independently.

### 5.3 Forbidden interactions

Neither managers nor services may bypass the single write path, the single storage path, or the single authorization path. Services cannot call other services without going through manager APIs. Managers never depend on services. No component touches [SQLite](../03-data/01-sqlite-layout.md), key files, or network sockets directly except the owning manager. Cross-app data mutation is allowed only when ACL policy explicitly permits it. Derived data cannot become a write path.

## 6. Runtime topologies

[02-runtime-topologies.md](02-runtime-topologies.md) defines conforming placements:

* **Integrated single-process** - managers, system services, and app extensions share one process on the same device as frontend apps. Trust boundary between frontend and backend remains strict; backend failure halts all backend work.
* **Split frontend-backend** - backend runs as a local service with separate frontend processes or devices. Backend treats frontend input as untrusted, and backend restarts invalidate frontend sessions.
* **Headless backend** - backend runs without an attached frontend, continues to sync and enforce policy, and assumes all inbound data originates from untrusted peers.
* **Multi-device** - multiple devices host independent backends for the same identity. No implicit trust exists between devices, and they synchronize solely through [State Manager](managers/09-state-manager.md) rules.
* **Remote peer** - independent nodes exchange [envelopes](../01-protocol/03-serialization-and-envelopes.md) over adversarial transports. [Cryptographic verification](../01-protocol/04-cryptography.md), ordering enforcement, and replay protection are mandatory.

All topologies preserve singular ownership of managers, local-only storage and key custody, and fail-closed ordering. Any topology that weakens these guarantees is non-conforming.

## 7. Trust boundaries

Trust boundaries defined in [03-trust-boundaries.md](03-trust-boundaries.md) include:

* **Frontend to backend** - frontend input (HTTP, WebSocket, [envelopes](../01-protocol/03-serialization-and-envelopes.md), tokens) is untrusted until verified by [Auth Manager](managers/04-auth-manager.md) and validated through [Schema](managers/05-schema-manager.md) and [ACL](managers/06-acl-manager.md) enforcement. No direct storage or key access is permitted.
* **Apps to backend** - apps, including those with backend extensions, cannot modify protocol behavior, bypass [ACL evaluation](managers/06-acl-manager.md), or touch database connections. Violations are rejected within the app scope.
* **Services to managers** - managers do not trust services. Services invoke managers via [OperationContext](services-and-apps/05-operation-context.md); managers enforce invariants and reject on violation.
* **Manager to storage** - storage is untrusted. Managers rely on [Storage Manager](managers/02-storage-manager.md) for transactional integrity but never expect storage to enforce ACLs or schemas.
* **Local node to remote node** - peers are untrusted. All inbound data is validated [cryptographically](../01-protocol/04-cryptography.md) and semantically before persistence; replay or ordering violations are rejected.
* **Network transport** - transport is treated as hostile. [Network Manager](managers/10-network-manager.md) plus [DoS Guard Manager](managers/14-dos-guard-manager.md) enforce admission control, [signature verification](../01-protocol/04-cryptography.md), [encryption](../01-protocol/04-cryptography.md), and throttling before any data reaches [Graph Manager](managers/07-graph-manager.md).

Every boundary fails closed: invalid input is rejected without partial writes, and trust is never inferred from transport metadata or topology.

## 8. Data flow lifecycle

[04-data-flow-overview.md](04-data-flow-overview.md) enumerates the only permitted data flows:

### 8.1 Node bootstrap and Server Graph initialization

First-run execution generates node/server key material, creates Server Graph roots via [Graph Manager](managers/07-graph-manager.md), validates them through [Schema](managers/05-schema-manager.md) and [ACL Manager](managers/06-acl-manager.md), persists atomically through [Storage Manager](managers/02-storage-manager.md), and anchors the global sequence. It runs exactly once per node and fails closed. Bootstrap also initializes boot-critical configuration, ensures [Key Manager](managers/03-key-manager.md) has durable custody, and records audit events for the initial identity and graph roots. If any step fails, no partial state remains and the node does not proceed to serve requests.

### 8.2 User provisioning and User Graph creation

Authorized admin requests trigger [Auth Manager](managers/04-auth-manager.md) to build [OperationContext](services-and-apps/05-operation-context.md), [Key Manager](managers/03-key-manager.md) to mint user keys, [Graph Manager](managers/07-graph-manager.md) to create identity and User Graph roots, [Schema](managers/05-schema-manager.md) and [ACL Managers](managers/06-acl-manager.md) to validate and bind ownership, [Storage Manager](managers/02-storage-manager.md) to persist atomically, and [Event Manager](managers/11-event-manager.md) to emit post-commit events. Failures roll back completely. Provisioning writes are monotonic and single-app scoped, and the resulting identities are immediately available for authorization decisions without separate activation steps. [Log Manager](managers/12-log-manager.md) records audit and security entries for each provisioning attempt.

### 8.3 Local read flow

Reads begin at the API layer, construct [OperationContext](services-and-apps/05-operation-context.md), pass through [ACL Manager](managers/06-acl-manager.md) for authorization, invoke [Storage Manager](managers/02-storage-manager.md) for constrained queries, optionally apply deterministic visibility suppression using Ratings, and return results. Unauthorized or cross-domain reads are rejected without side effects. Reads never mutate state, never bypass ACL capsules, and always reflect the most recent committed graph state in order. Cache layers may be used for performance but must be invalidated on commits and must never widen visibility.

### 8.4 Local write flow

Write requests submit [envelopes](../01-protocol/03-serialization-and-envelopes.md) that undergo [Schema](managers/05-schema-manager.md) validation, [ACL](managers/06-acl-manager.md) evaluation, exclusive sequencing by [Graph Manager](managers/07-graph-manager.md), atomic persistence via [Storage Manager](managers/02-storage-manager.md), and post-commit notifications through [Event Manager](managers/11-event-manager.md). Writes outside this pipeline, cross-domain writes, or partial writes are forbidden. Each accepted write advances `global_seq` exactly once, generates deterministic audit records, and becomes visible to reads only after commit. Rejections surface precise error codes and never emit events or log entries that imply a commit.

### 8.5 Visibility suppression via Ratings

Ratings act as immutable suppression signals. They follow the standard write flow, never delete objects, and are interpreted deterministically at read time according to app policy. Suppression requires an explicit [Rating](../01-protocol/02-object-model.md); no implicit delete semantics exist. Ratings are scoped to the owning app and never alter the canonical object state, only its visibility. Any suppression decision must remain explainable from the recorded Rating objects and [ACL rules](../01-protocol/06-access-control-model.md).

### 8.6 Event emission flow

Committed graph mutations emit domain events routed by [Event Manager](managers/11-event-manager.md) to subscribers over WebSocket. Events never mutate state, and delivery failures do not affect persistence or sequencing. [Event envelopes](../01-protocol/03-serialization-and-envelopes.md) include stable identifiers and ordering anchors derived from the commit, and authorization is enforced per subscriber using cached ACL capsules. Clients treat events as best-effort hints and must recover via read APIs when gaps occur.

### 8.7 Remote ingress flow

Remote packages enter through [Network Manager](managers/10-network-manager.md), pass [DoS Guard Manager](managers/14-dos-guard-manager.md) admission control, are verified and decrypted by [Key Manager](managers/03-key-manager.md), are validated by [State Manager](managers/09-state-manager.md) for domain and ordering, derive a remote [OperationContext](services-and-apps/05-operation-context.md), and finally enter the standard envelope pipeline. Invalid signatures, revoked keys, or ordering violations cause rejection without advancing sync state. State Manager enforces monotonic per-peer and per-domain sequencing and rejects out-of-order or replayed envelopes. All remote writes are treated as untrusted until the same schema and ACL gates applied to local writes are satisfied.

### 8.8 Remote egress flow

[State Manager](managers/09-state-manager.md) selects eligible graph changes, constructs [envelopes](../01-protocol/03-serialization-and-envelopes.md), [Key Manager](managers/03-key-manager.md) signs headers and encrypts payloads, [Network Manager](managers/10-network-manager.md) transmits them, and State Manager tracks per-peer sequencing. Only committed, in-domain data is transmitted. Outbound packaging preserves ordering guarantees and never includes suppressed or unauthorized objects for the receiving peer. Delivery is best-effort and does not mutate local state beyond per-peer sync metadata.

### 8.9 Derived and cached data flow

Derived indices and caches exist solely for performance. They rebuild from authoritative graph state, are never synced, and can be discarded without affecting correctness. Derived data must not introduce new write paths or authorization decisions and must be invalidated on source changes. Any cache miss or corruption falls back to authoritative reads.

### 8.10 Rejection propagation and observability

All rejections propagate to the originator (local caller or peer). [Log Manager](managers/12-log-manager.md) captures failures, [State Manager](managers/09-state-manager.md) records peer rejections, and no hidden fallback paths exist. Rejection codes are deterministic and map to protocol failure categories, enabling audit and debugging without leaking sensitive data. Rejections never advance sequencing or change readiness by themselves unless they indicate systemic failure.

### 8.11 Configuration and policy reload flow

Administrative configuration changes enter through [Config Manager](managers/01-config-manager.md), are validated against the [schema registry](managers/05-schema-manager.md), and are published as immutable snapshots only after prepare/commit acknowledgements from dependent managers. Any veto or validation failure leaves the prior snapshot intact and forces a fail-closed posture until remediation. Reloads are atomic at the namespace level and never expose partial updates to any manager. Successful reloads emit audit records and readiness transitions so operators can correlate behavior with applied policy.

### 8.12 Health signal and readiness flow

Managers emit heartbeat and threshold signals to [Health Manager](managers/13-health-manager.md), which aggregates readiness and liveness, publishes transitions to [Log Manager](managers/12-log-manager.md) and [Event Manager](managers/11-event-manager.md), and gates admissions through [DoS Guard](managers/14-dos-guard-manager.md) policy. Missing or invalid signals degrade readiness without mutating state. Readiness changes are monotonic per transition and never suppressed; consumers must react immediately. Health signals do not carry application data and are bounded in size and rate.

### 8.13 Audit and diagnostics flow

Operational, audit, and security records are emitted through [Log Manager](managers/12-log-manager.md), optionally bridged as high-level events. Audit and security records never bypass ACL controls, and failures in mandatory sinks surface as explicit readiness degradation rather than silent loss. Log records include [OperationContext](services-and-apps/05-operation-context.md) when available and preserve ordering relative to the committed operation they describe. Operators must use read-only query interfaces for inspection; no log stream is writable by clients or apps.

## 9. Guarantees and invariants

* All persistent state is representable as [graph objects](../01-protocol/02-object-model.md) governed by schema and ACL rules.
* All accepted writes are validated structurally, authorized, sequenced monotonically, and applied atomically via [Graph](managers/07-graph-manager.md) and [Storage Managers](managers/02-storage-manager.md).
* Sync ordering is monotonic per peer and per domain; no state advances on rejection.
* Private keys never leave [Key Manager](managers/03-key-manager.md) custody, and [cryptographic verification](../01-protocol/04-cryptography.md) precedes semantic processing.
* [OperationContext](services-and-apps/05-operation-context.md) is immutable once created and drives every authorization and logging decision.
* Ratings provide the only suppression mechanism; there is no delete path.
* Derived data and events are non-authoritative and cannot repair or bypass failed operations.

## 10. Allowed and forbidden behaviors

### 10.1 Allowed

* Local writes via HTTP using [graph envelopes](../01-protocol/03-serialization-and-envelopes.md) with validated [OperationContext](services-and-apps/05-operation-context.md).
* Remote sync via signed and optionally encrypted packages that [State Manager](managers/09-state-manager.md) sequences and [Graph Manager](managers/07-graph-manager.md) applies.
* Multiple devices per identity, each operating independently while respecting sync and ACL rules.
* Silent rejection of hostile remote input while continuing to serve other peers.

### 10.2 Forbidden

* Any mutation path bypassing [Graph Manager](managers/07-graph-manager.md), [Storage Manager](managers/02-storage-manager.md), [Schema Manager](managers/05-schema-manager.md), or [ACL Manager](managers/06-acl-manager.md).
* Direct database, filesystem, or network access by services, apps, or extensions.
* Authorization decisions derived from transport metadata or inferred identity.
* Partial envelope application, implicit retries that break ordering, or advancing [sync state](managers/09-state-manager.md) after a failure.
* Accepting remote packages without full [cryptographic verification](../01-protocol/04-cryptography.md) or by guessing missing metadata.

## 11. Failure posture and observability

* Rejections are atomic and leave no residual state; failures are classified by the earliest stage that detects them (structural, cryptographic, schema, ACL, sync ordering, storage, or resource).
* Storage failures trigger full rollbacks; network failures isolate to [Network Manager](managers/10-network-manager.md); derived-data failures degrade performance only.
* Crashes are contained to the failing component; recovery occurs through process restart leveraging authoritative persistent state.
* Debugging, logging, health, and event inspection surfaces remain read-only and require administrative authorization.
* [DoS Guard Manager](managers/14-dos-guard-manager.md) enforces rate limits and client puzzles on peer ingress to prevent resource exhaustion before envelopes are verified.

This overview, together with the referenced specifications in [02-architecture/**](./), defines the authoritative architecture contract for the PoC. All future changes to managers, services, runtime topologies, or data flows must preserve these guarantees or amend the relevant companion documents alongside this overview.
