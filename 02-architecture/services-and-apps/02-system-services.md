



# 02 System Services

## 1. Purpose and scope

System services are the mandatory backend orchestration layers that translate baseline 2WAY capabilities into concrete APIs, scheduled jobs, and automation that every conforming node must expose. They provide provisioning, registry, feed, sync, and operational workflows that all applications rely on regardless of custom code. This document defines the implementation contract for those services so independent teams can ship compatible runtimes without renegotiating behaviors on a per deployment basis.

The specification establishes the ownership boundaries between system services and protocol managers, codifies the OperationContext and capability requirements that every service invocation must satisfy, prescribes lifecycle sequencing, and provides an implementation-ready catalog for the default service lineup that ships with the proof of concept. It treats inputs, configuration, observability, and failure handling with the same fail-closed posture mandated elsewhere in the architecture corpus, ensuring these services can never weaken protocol guarantees.

This specification references the following documents:

* `02-architecture/01-component-model.md`
* `02-architecture/services-and-apps/01-services-vs-apps.md`
* `02-architecture/services-and-apps/05-operation-context.md`
* `02-architecture/04-data-flow-overview.md`
* `02-architecture/managers/00-managers-overview.md`
* `04-interfaces/**`
* `05-security/**`

### 1.1 Responsibilities and boundaries

This specification is responsible for the following:

* Defining the mandatory system service model for a conforming node, including required services, their responsibilities, and their interface surfaces.
* Defining strict ownership boundaries between system services, managers, apps, and interface layers.
* Defining OperationContext requirements, capability encoding requirements, and fail-closed behavior for every system service invocation.
* Defining lifecycle sequencing for service startup, readiness gating, shutdown, and upgrades.
* Defining configuration namespaces, schema obligations, capability catalogs, ACL templates, and observability requirements for system services.
* Defining service to manager integration contracts in terms of inputs, outputs, and trust boundaries, including DoS Guard and Health admission behavior.
* Defining the canonical mandatory system service catalog for the proof of concept, with implementable flows, failure handling, and surface shapes.

This specification does not cover the following:

* Manager internal design, database schemas, or implementation details beyond what system services must rely on via manager APIs.
* App specific business logic beyond the optional app extension service model.
* Network transport implementation, peer discovery implementation, or handshake protocol details, which are owned by Network Manager and State Manager.
* Cryptographic primitive implementation, key storage formats, or signing and encryption algorithms, which are owned by Key Manager and the relevant manager pipelines.
* Full HTTP and WebSocket interface documentation, which is owned by `04-interfaces/**`, except where this file must declare missing shapes to keep implementation unblocked.
* Any future or speculative services not listed in the proof of concept catalog.

### 1.2 Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* Managers never depend on system services.
* System services never read or write SQLite directly, never touch key files directly, never manage sockets directly, and never mutate sync metadata directly.
* Every system service invocation requires a complete OperationContext, including requester identity, device identity, app_id, capability intent, and tracing metadata.
* System services never authorize directly, they declare capability intent and rely on ACL Manager enforcement.
* All external input is treated as untrusted and is validated before reaching managers.
* Schema validation occurs before graph mutation for schema dependent writes.
* ACL evaluation occurs before any read or write that requires authorization, including reads of ACL protected data.
* Failures are handled fail closed, with no best-effort fallback behavior that would weaken correctness or security.
* Admission is gated by Health Manager readiness and DoS Guard posture, regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

These guarantees must hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 2. System service contract

All system services adhere to a single contract. Deviating from these rules voids conformance even if the service appears to function.

### 2.1 Ownership and namespace rules

* Every system service runs under the system application namespace (`app_0`). App Manager registers the service so the node can bind deterministic `app_id`, capability manifests, and health entries.
* Services publish their schema contributions (if any) through Schema Manager during installation. Schemas are immutable once loaded, migrations use the manager pipeline described in `02-architecture/04-data-flow-overview.md`.
* Services cannot claim ownership of graph objects outside `app_0` unless ACL policy and schema delegation explicitly permit it. Cross-app mutations always carry the requesting app’s OperationContext and are authorized by ACL Manager.

### 2.2 Interaction boundaries with managers and apps

* Managers never depend on system services. Services may depend on managers or on other services only through published APIs that themselves rely on managers. Hidden shared state is forbidden.
* Services never read or write SQLite, key files, sockets, or sync metadata directly. Graph, Storage, Key, Network, State, Config, Event, Log, Health, App, and DoS Guard Managers remain the sole authorities over their respective domains (`02-architecture/managers/00-managers-overview.md`).
* Services never create, manage, or accept network listeners, onion services, or peer sockets. Any network facing behavior is mediated by Network Manager and State Manager, and invoked only through their published APIs.
* Services must be callable by frontend apps, automation jobs, or remote peers exclusively through surfaces defined in `04-interfaces/**`. If an interface does not exist yet, the service specification must declare the HTTP or WebSocket shape, expected authentication mode, and OperationContext fields so the interface document can be authored before implementation.

### 2.3 OperationContext and capability encoding

* Every request or scheduled job constructs a complete OperationContext as defined in `02-architecture/services-and-apps/05-operation-context.md`. System services default to `app_id=app_0` and stamp granular capability strings (for example, `capability=system.bootstrap.install`).
* Services must reject requests missing `app_id`, requester identity, device identity, capability intent, or tracing metadata. Partial contexts are invalid even if the service could infer identity from other data.
* Capabilities are documented and versioned. ACL Manager enforces them via capability edges anchored in the graph. Services never authorize directly, they only declare the capability they are attempting to exercise.

### 2.4 Interface surfaces

System services expose three kinds of surfaces:

1. **API endpoints** (HTTP and WebSocket) wired through the interface layer in `04-interfaces/**`. Endpoints must document accepted media types, payload schemas, OperationContext prerequisites, and DoS Guard hints (expected cost, resource class).
2. **Internal command channels** used only by other system services through typed RPC helpers. These helpers still take OperationContext arguments and call managers. They cannot bypass ACL or Schema enforcement.
3. **Scheduled jobs** run by the backend scheduler. Each job registers a manifest describing cadence, maximum concurrency, capability identity, and resource cost. Jobs abort when Health Manager reports `not_ready` or when required managers are degraded.

### 2.5 Input handling and validation posture

* All external input is untrusted. Services perform local validation (shape, size, obvious semantic checks) before handing data to managers. Hostile inputs die at the boundary and emit structured logs.
* Services must call Schema Manager before Graph Manager for any mutation that depends on schema defined invariants. They must call ACL Manager before performing even read only operations that require permission.
* Services propagate manager error codes without rewriting them, except to attach human readable context. They do not introduce best-effort fallbacks.

### 2.6 Resource and capacity obligations

* Each service declares `service.*` configuration keys (Section 4) describing per endpoint limits, batch sizes, derived cache limits, and background job budgets.
* Services register DoS Guard hints (`dos.cost_class`, expected execution time, identity tokens) so DoS Guard can throttle before resource exhaustion occurs.
* Derived caches are optional, non authoritative, and rebuild from graph reads after restart. Caches may not contain secrets or ACL protected data unless access is rechecked at read time.

## 3. Lifecycle, deployment, and upgrades

### 3.1 Startup sequencing and readiness

* System services start only after all critical managers report `healthy` and App Manager has registered `app_0` plus the service descriptors.
* Services declare dependencies on other system services explicitly (for example, Feed Service depends on Identity Service for membership expansion). The runtime starts services according to this dependency DAG and enforces timeouts.
* Readiness is reported to Health Manager only after the service validates configuration, loads required schemas, restores derived caches (if any), and registers endpoints and jobs. Any missing dependency forces `ready=false`.
* Services that expose network visible effects must also respect Network Manager admission gates. If Network Manager is not ready, services must reject network coupled work, even if the service itself is ready.

### 3.2 Shutdown and fail-closed posture

* During shutdown or degraded health, services stop accepting new work, mark outstanding jobs as `aborted`, and provide Health Manager with a degraded reason. They flush logs and events before releasing dependencies.
* Services do not attempt to run graceful fallbacks when managers are unavailable. They reject work with the relevant error classification so DoS Guard and frontend callers can back off.
* Services must not attempt to drain or reconcile partially completed workflows by bypassing managers. Recovery is performed only through the normal manager pipeline after restart.

### 3.3 Upgrade and migration requirements

* Upgrades follow the same prepare and commit configuration flow managers use. A service may refuse to upgrade if schemas are outdated or if Graph Manager indicates pending migrations.
* Schema migrations are orchestrated via Graph Manager, not ad hoc SQL. Services submit migration envelopes tagged with `capability=system.schema.migrate` and rely on Schema Manager for validation.

### 3.4 Background work scheduling

* Scheduled tasks declare their cadence (`cron`, `fixed_delay`, or on demand), concurrency limit, OperationContext capability, and abort timeout. The scheduler ensures only one instance per capability runs simultaneously unless explicitly allowed.
* Jobs that enqueue network work must coordinate with DoS Guard by publishing expected outbound volume and verifying Health Manager readiness.

## 4. Configuration and schema obligations

### 4.1 Configuration namespace

System service configuration keys live under `service.<service_name>.*`. Typical keys include:

| Key                                          | Description                                                                             | Owner              |
| -------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------ |
| `service.bootstrap.install_window_ms`        | Maximum allowed duration for installation sessions before they expire and must restart. | Bootstrap Service  |
| `service.bootstrap.max_pending_invites`      | Cap on concurrent bootstrap invitations before new requests are denied.                 | Bootstrap Service  |
| `service.identity.max_contacts_per_identity` | Soft limit enforced by ACL policy for the Identity & Relationship Service.              | Identity Service   |
| `service.feed.max_threads_per_app`           | Hard limit for feed aggregation fan out per app namespace.                              | Feed Service       |
| `service.sync.max_parallel_peers`            | Number of peer sync plans the Sync Orchestration Service may run.                       | Sync Service       |
| `service.ops.admin_routes_enabled`           | Flag gating whether Operations Console routes are exposed.                              | Operations Service |

Config Manager owns validation and reload semantics. Services may listen for reload events and re validate inputs before applying them. Failure to validate keeps the previous snapshot active and marks health degraded.

### 4.2 Schema ownership and migrations

* Each service documents the schema types it owns inside `app_0`, including parent types, attribute keys, edges, ratings, and ACL templates. Types are versioned. The service declares compatibility ranges.
* Schema additions follow the manager pipeline. Author schema, stage through Schema Manager, commit after validation, and ensure Graph Manager sequences all resulting objects.
* Services never mutate schemas owned by apps directly. If an app needs service assistance (for example, feed ingestion), the service supplies helper objects inside `app_0` that reference the app domain through ACL controlled edges.

### 4.3 Capability and ACL templates

* Services publish capability catalogs in the graph (for example, `system.capability.feed.publish`). ACL Manager consumes these when evaluating requests.
* Default ACL templates for system services are stored in `app_0` during installation. Bootstrap Service initializes admin identities with the minimum capabilities needed to operate other services.

## 5. Observability, telemetry, and policy hooks

### 5.1 Logging

* All actions produce structured logs through Log Manager, including OperationContext, capability attempted, target objects, manager error codes, and execution latency buckets.
* Sensitive payloads (for example, bootstrap secrets) must be redacted before logging. Logs include a boolean flag (`redacted=true`) so downstream tools know the record is intentionally truncated.

### 5.2 Events

* Services emit events through Event Manager per `04-interfaces/events/**`. Event descriptors include event family (`system.bootstrap.completed`, `system.identity.invite.accepted`, `system.feed.thread.updated`, `system.sync.plan.failed`, `system.ops.health_toggle`), referencing committed graph objects.
* Subscribers must revalidate authorization via ACL capsules attached to the event. Services never include raw object payloads. They only reference objects for callers to fetch through authorized reads.

### 5.3 Metrics and health

* Each service reports readiness, liveness, and degraded modes to Health Manager. Metrics include request counts, rejection reasons, cache hit ratios, job runtimes, and DoS Guard hint utilization.
* Health signals drive admission. If a service is `not_ready`, Network Manager and frontend routers stop forwarding new requests to it.

### 5.4 DoS Guard integration

* Services classify endpoints into cost tiers (light, medium, heavy) with deterministic descriptions so DoS Guard can assign puzzles and throttles.
* Services feed telemetry into DoS Guard when they detect abusive patterns (for example, repeated bootstrap attempts from one peer). Telemetry includes OperationContext identifiers, resource usage, and recommended throttle levels.

## 6. Canonical system service catalog

The proof of concept ships with five mandatory system services. Each one is described in later sections. The table below summarizes their remit.

| Service                                        | Responsibilities                                                                                                                                     | Primary surfaces                                                             | Mandatory dependencies                                    |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------- |
| System Bootstrap & Provisioning Service (SBPS) | Node installation, admin creation, device enrollment, bootstrap invites, recovery keys, installation auditing.                                       | HTTP install APIs, local CLI integration, scheduled cleanup job.             | Config, Graph, Schema, ACL, App, Key, Log, Event, Health. |
| Identity & Relationship Service (IRS)          | Identity lifecycle, device linking, contact management, invitation issuance, trust edges, capability delegation, baseline directory queries.         | HTTP APIs, WebSocket notifications, scheduled integrity sweeps.              | Graph, Schema, ACL, App, Log, Event.                      |
| Base Feed Service (BFS)                        | Aggregated timeline assembly, thread creation helpers, rating fan out, derived index maintenance, capability enforcement for publish and read flows. | HTTP APIs, WebSocket feeds, worker jobs for aggregation.                     | Graph, Schema, ACL, Event, Log, Config, Identity Service. |
| Sync Orchestration Service (SOS)               | Peer sync planning, outbound schedule hints, local sync health reporting, manual resync controls, schema aware reconciliation policies.              | HTTP APIs, admin automation hooks, scheduler cooperating with State Manager. | State, Graph, Network, DoS Guard, Health, Log, Event.     |
| Operations Console Service (OCS)               | Administrative controls, configuration export, health dashboards, audit log queries, service toggles, capability assignment UI glue.                 | HTTP admin APIs, WebSocket dashboards, scheduled policy audits.              | Config, Health, Log, Event, Graph, ACL, Identity Service. |

Each service specification below elaborates required data flows, OperationContext expectations, and failure modes.

## 7. System Bootstrap & Provisioning Service (SBPS)

### 7.1 Responsibilities

SBPS is the only authority allowed to transition a node from uninitialized to operational. Its duties include:

* Running the installation wizard that provisions the Server Graph roots described in `02-architecture/04-data-flow-overview.md` and verifying that all bootstrap envelopes commit successfully.
* Creating the first administrator identity, device, and OperationContext bindings, including minimal capabilities needed to operate other services.
* Managing bootstrap invitations (time limited capability tokens) so additional devices or administrators can be enrolled without exposing private keys directly.
* Orchestrating device enrollment flows. Verifying device attestations, binding devices to identities, and ensuring Key Manager stores the required key pairs.
* Handling bootstrap recovery (revoking stale install tokens, rotating bootstrap secrets, reconstructing default ACLs if they drift).
* Coordinating readiness gating so network coupled surfaces remain closed until bootstrap has completed and Health Manager marks the node ready.

### 7.2 Inputs and outputs

**Inputs**

* Installation payloads carrying node name, storage path confirmation, admin identity metadata, and optional recovery contact information. Payloads are signed locally and never sent over the network.
* Device attestation bundles referencing physical device fingerprints, key fingerprints, and intended identity association.
* Bootstrap invite acceptance payloads containing invite tokens, proof of possession for the identity key, and capability selections.

**Outputs**

* Graph envelopes that create or mutate bootstrap objects (`app_0` parents for node, admin identity, devices, capability edges).
* Event Manager descriptors announcing installation milestones (`system.bootstrap.installation_started`, `system.bootstrap.first_admin_created`, `system.bootstrap.device_enrolled`).
* Log Manager records for every bootstrap step, including structured error logs when schema or ACL validation fails.

### 7.3 Critical flows

1. **Installation**

   * Interface layer calls SBPS `POST /system/bootstrap/install`.
   * SBPS validates payload, ensures node is not already installed, and constructs an OperationContext with `capability=system.bootstrap.install`.
   * SBPS orchestrates Graph Manager writes to create node parents, admin identity, admin device, default ACL templates, and capability edges.
   * Upon success, Event Manager receives `system.bootstrap.completed`, Health Manager marks the node ready, and DoS Guard unlocks public surfaces.
   * If network transport services exist, SBPS ensures Network Manager does not accept inbound peer work until Health Manager is ready.

2. **Device enrollment**

   * Device runs local CLI or UI to request an invite. Admin obtains invite token via SBPS `POST /system/bootstrap/invites`.
   * Device presents token plus key proof to `POST /system/bootstrap/devices`. SBPS validates, binds device to identity via Graph Manager, and destroys the invite token.
   * Event Manager emits `system.bootstrap.device_enrolled`. Log Manager records the enrollment, including device metadata.

3. **Recovery**

   * Admin uses `POST /system/bootstrap/recover` to rotate bootstrap secrets or reset capability assignments.
   * SBPS ensures Graph Manager replays schema compliant ACL edges and revokes stale invites.

### 7.4 Failure handling

* If any Graph or Schema operation fails, SBPS aborts the entire operation, rolls back, and records the failure reason (`ERR_BOOTSTRAP_SCHEMA`, `ERR_BOOTSTRAP_ACL`). No partial installs exist.
* Expired invites result in `HTTP 410 Gone` responses with DoS telemetry increments so repeated misuse pushes puzzle difficulty upward.
* Device attestations that cannot be verified result in `ERR_BOOTSTRAP_DEVICE_ATTESTATION`. SBPS logs the fingerprint for audit.

## 8. Identity & Relationship Service (IRS)

### 8.1 Responsibilities

IRS owns the authoritative identity directory within `app_0`. It:

* Creates, updates, and retires identities and associated devices after bootstrap.
* Issues and tracks invitations for contacts (local or remote) and attaches trust edges per ACL policy.
* Manages capability delegation between identities, ensuring capability edges align with service catalogs.
* Provides read surfaces for directory queries (by handle, capability, trust state, device status) and exposes filters for frontend apps.
* Triggers periodic integrity sweeps that verify ACL and schema compliance across identity edges.
* Emits signals that allow other components to react to identity and trust changes, without performing network operations directly.

### 8.2 Inputs and outputs

* **Inputs**:

  * Authenticated HTTP requests from admins or app automation (OperationContext includes requesting identity, capability such as `system.identity.manage`).
  * Scheduled jobs that scan for stale invitations or orphaned devices.
* **Outputs**:

  * Graph envelopes for identity updates, capability edges, contact relationships.
  * Events `system.identity.identity_created`, `system.identity.capability_delegated`, `system.identity.contact_revoked`.
  * Log entries for every identity lifecycle step with ACL decisions.

### 8.3 Workflow specifics

* Identity creation requires Schema Manager validation (`identity.parent`, `device.parent`, `capability.edge` types). IRS ensures Graph Manager writes objects in the order defined in `02-architecture/04-data-flow-overview.md`.
* Device linking uses a double opt in. Device owner signs a request, admin approves, IRS records the association and notifies Event Manager.
* Contact invitations track acceptance state. IRS enforces `service.identity.max_contacts_per_identity` by counting accepted edges. Exceeding the limit returns `ERR_IDENTITY_CONTACT_LIMIT`.

### 8.4 Failure handling

* Unknown capability results in immediate rejection with `ERR_IDENTITY_CAPABILITY`.
* Integrity sweep failures (for example, orphaned capability edges) trigger alerts via Event Manager (`severity=warning` or `critical`). IRS attempts to repair by submitting Graph envelopes. Repeated failure marks the service degraded.

## 9. Base Feed Service (BFS)

### 9.1 Responsibilities

The Base Feed Service provides a canonical social timeline abstraction every app can reuse. Responsibilities include:

* Authoring feed thread parents, message attributes, reaction ratings, and reply edges within `app_0`, while permitting other apps to reference or embed feed entries through ACL governed edges.
* Aggregating cross app inputs by running read queries against Graph Manager scoped to authorized app domains, respecting OperationContext capability tags (`system.feed.publish`, `system.feed.read`, `system.feed.moderate`).
* Maintaining derived indices (per app thread lists, unread counters) stored as cache tables managed through Storage Manager read only helpers.
* Emitting WebSocket events for new feed items, reactions, and moderation actions via Event Manager.
* Enforcing moderation primitives. Rating objects, capability toggles, and derived hide lists applied at read time.

### 9.2 Interfaces and jobs

* HTTP APIs:

  * `POST /system/feed/threads`, Create a new thread, requires capability `system.feed.publish`.
  * `POST /system/feed/messages`, Append to thread.
  * `POST /system/feed/reactions`, Create rating.
  * `GET /system/feed/threads`, Read aggregated feed, enforces ACL filters.
  * `POST /system/feed/moderations`, Submit moderation ratings.
* WebSocket channel `system.feed.stream` delivering normalized event descriptors.
* Background jobs:

  * Aggregation sweeps building derived indices.
  * Moderation policy enforcement that recalculates hide lists when a rating threshold is crossed.

### 9.3 Data and validation flow

* BFS constructs OperationContext, validates payloads locally, verifies schema types with Schema Manager, authorizes with ACL Manager, then calls Graph Manager to commit.
* Derived caches store only object references and computed counters. They rebuild by replaying Graph reads. Cache corruption forces BFS to drop caches and rebuild (logged via `system.feed.cache_reset` event).
* BFS respects per app fan out limits defined by `service.feed.max_threads_per_app` and `service.feed.max_replies_per_thread`. Exceeding limits yields deterministic errors.

### 9.4 Failure modes

* Missing OperationContext capability, `ERR_FEED_CAPABILITY`.
* Attempting to reference another app’s objects without delegation, ACL denial.
* Derived cache rebuild failure, BFS marks itself degraded and raises `system.feed.cache_failure`.

## 10. Sync Orchestration Service (SOS)

### 10.1 Responsibilities

SOS bridges admin intent with State Manager’s sync engines. It:

* Provides APIs to inspect peer sync health, outstanding envelopes, last successful exchange, and per domain progression.
* Generates sync plans (peer plus domain plus range) and submits them to State Manager following the ordering requirements in `01-protocol/07-sync-and-consistency.md`.
* Enforces policy for which peers may sync which app domains, consulting ACL and App Manager metadata.
* Surfaces manual controls (pause peer, resume, force rescan, clear backlog) for administrators via Operations Console.
* Collects telemetry on sync successes and failures, publishes them as events, and feeds DoS Guard with abusive peer signals (for example, repeated invalid envelopes).

### 10.2 Interfaces and jobs

* HTTP APIs:

  * `GET /system/sync/peers`, List peers with sync status.
  * `POST /system/sync/plans`, Submit or adjust sync plans.
  * `POST /system/sync/peers/{peer_id}/pause|resume`.
  * `POST /system/sync/diagnostics`, Trigger diagnostics package.
* Background jobs coordinate with State Manager to refresh sync plans, enforce `service.sync.max_parallel_peers`, and compute remote health indicators.

### 10.3 Data flow and validation

* SOS never mutates sync metadata directly. It calls State Manager APIs that in turn talk to Graph and Storage.
* SOS ensures OperationContext includes admin identity and capability `system.sync.manage`. Requests without this capability fail.
* When generating plans, SOS consults Config Manager for network scheduling limits, DoS Guard for throttle hints, and Health Manager to ensure the node can handle additional sync load.
* Any network coupled behavior remains mediated through the manager layer. SOS does not open connections, does not create network listeners, and does not handle transport encryption.

### 10.4 Failure handling

* State Manager rejection leads to `ERR_SYNC_PLAN_INVALID`, logged with reason (ordering violation, unknown peer, ACL denial). SOS propagates the error and marks the plan `failed`.
* If DoS Guard indicates a peer is abusive, SOS automatically pauses the peer and emits `system.sync.peer_paused` with severity `warning`.

## 11. Operations Console Service (OCS)

### 11.1 Responsibilities

OCS provides administrative surfaces needed to operate a node safely:

* Aggregates Health Manager signals, service readiness, DoS Guard posture, and configuration snapshots into HTTP and WebSocket dashboards.
* Offers controlled APIs for configuration export and import, limited to read only or pre approved namespaces per Config Manager policy.
* Provides audit log query helpers that read from Log Manager using OperationContext driven filters.
* Manages capability assignments by invoking Identity Service workflows (OCS never mutates capability edges directly).
* Hosts toggles for enabling and disabling services, pausing network surfaces, or draining sync pipelines, all implemented via manager APIs.

### 11.2 Interfaces

* HTTP APIs under `/system/ops/*` requiring admin OperationContext:

  * `GET /system/ops/health`, Aggregated readiness and liveness snapshot.
  * `GET /system/ops/config`, Export sanitized configuration.
  * `POST /system/ops/service-toggles`, Enable and disable services with `system.ops.manage` capability.
  * `POST /system/ops/capabilities`, Request capability grant and revoke (delegates to Identity Service).
  * `GET /system/ops/audit/logs`, Query structured logs with ACL enforced filters.
* WebSocket dashboards streaming health and event summaries.
* Scheduled policy audits verifying configuration drift (`service.ops.policy_audit_interval_ms`).

### 11.3 Security posture

* All endpoints require `system.ops.manage` capability plus admin identity classification. ACL Manager verifies both identity and capability edges. OCS does not implement shortcuts.
* Configuration exports redact sensitive keys (`log.*` secrets, encryption salts). Redaction is deterministic and logged.
* Service toggles result in Graph Manager events that record who toggled what, preserving auditability.

### 11.4 Failure handling

* Missing capability, `ERR_OPS_CAPABILITY`.
* Config export failure due to ACL or Config Manager rejection, `ERR_OPS_CONFIG_ACCESS`.
* When OCS cannot reach Health Manager, it marks itself degraded and refuses to serve stale data.

## 12. Shared security considerations

* **No implicit trust**: Even though system services live inside the backend, managers treat them as untrusted callers. Services must never assume elevated privilege beyond what ACL Manager grants via capability edges.
* **Immutable audit trail**: Every service action must leave a trace in Log Manager referencing OperationContext, capability, and object IDs. This enables forensic reconstruction of misuse or bugs.
* **Secret handling**: Bootstrap secrets, invitation tokens, and admin toggles are stored as encrypted attributes governed by ACL rules. Services never store secrets in configuration or derived caches.
* **DoS response**: Services integrate with DoS Guard by submitting telemetry events when abusive patterns appear, ensuring the admission layer can intervene before resources are exhausted.

## 13. Implementation checklist

1. **Registration**: Service descriptor registered with App Manager under `app_0`, including capability catalog, configuration keys, dependency graph, and readiness hooks.
2. **OperationContext discipline**: Every endpoint, job, or RPC helper constructs the immutable OperationContext defined in `02-architecture/services-and-apps/05-operation-context.md` before touching managers.
3. **Manager usage**: All mutations go through Graph Manager (schema to ACL to persistence ordering), all reads respect ACL checks, and no raw SQLite or filesystem access exists.
4. **Configuration**: Service specific `service.*` keys registered with Config Manager, validation functions implemented, reload behavior documented.
5. **Schema**: All required schema types defined inside `app_0`, versioned, and validated through Schema Manager. Migrations planned as Graph envelopes with capability gating.
6. **Interfaces**: HTTP and WebSocket routes documented in `04-interfaces/**`, including payload schema, OperationContext requirements, and DoS Guard hints. Interface tests cover success and fail closed paths.
7. **Jobs**: Scheduler manifests declare cadence, capability, resource cost, and abort semantics. Jobs can resume idempotently after crash.
8. **Observability**: Logs, events, and health signals wired through Log Manager, Event Manager, and Health Manager with deterministic severity levels.
9. **Security**: Secrets stored only via Graph Manager with ACL protection. DoS Guard telemetry integrated. Capability delegation enforced exclusively by ACL Manager.
10. **Failure drills**: Service tested for manager outages, configuration reload failures, schema mismatches, and DoS Guard throttling to confirm fail closed behavior.

Following this specification ensures all system services deliver consistent behavior, align with the manager fabric, and remain safe to reuse by every application targeting the 2WAY substrate.
