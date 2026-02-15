



# 02 System Services

Defines the mandatory system services and their required behaviors in the 2WAY backend. Specifies capability, OperationContext, and manager interaction requirements for system services. Defines lifecycle sequencing, configuration obligations, and fail-closed handling for service workflows.

For the meta specifications, see [02-system-services meta](../../10-appendix/meta/02-architecture/services-and-apps/02-system-services-meta.md).

## 1. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* Managers never depend on system services.
* System services never read or write SQLite directly, never touch key files directly, never manage sockets directly, and never mutate sync metadata directly.
* Every system service invocation requires a complete [OperationContext](05-operation-context.md), including requester identity, device identity, app_id, capability intent, and tracing metadata.
* System services never authorize directly, they declare capability intent and rely on [ACL Manager](../managers/06-acl-manager.md) enforcement.
* All external input is treated as untrusted and is validated before reaching managers.
* Schema validation occurs before graph mutation for schema dependent writes.
* ACL evaluation occurs before any read or write that requires authorization, including reads of ACL protected data.
* Failures are handled fail closed, with no best-effort fallback behavior that would weaken correctness or security.
* Admission is gated by [Health Manager](../managers/13-health-manager.md) readiness and [DoS Guard Manager](../managers/14-dos-guard-manager.md) posture, regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.
* DoS Guard challenges (`dos_challenge_required`) are issued only for network transport surfaces; local HTTP system service endpoints do not emit challenges and instead return `network_rejected` when admission is not permitted.

These guarantees must hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 2. System service contract

All system services adhere to a single contract. Deviating from these rules voids conformance even if the service appears to function.

### 2.1 Ownership and namespace rules

* Every system service runs under the system application namespace (`app_0`). [App Manager](../managers/08-app-manager.md) registers the service so the node can bind deterministic `app_id`, capability manifests, and health entries.
* Services publish their schema contributions (if any) through [Schema Manager](../managers/05-schema-manager.md) during installation. Schemas are immutable once loaded, migrations use the manager pipeline described in [02-architecture/04-data-flow-overview.md](../04-data-flow-overview.md), and all graph operations stay within the object invariants defined in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) plus the envelope guarantees in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Services cannot claim ownership of graph objects outside `app_0` unless ACL policy and schema delegation explicitly permit it. Cross-app mutations always carry the requesting app's [OperationContext](05-operation-context.md), stay within the access semantics defined by [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md), and are authorized by [ACL Manager](../managers/06-acl-manager.md).

### 2.2 Interaction boundaries with managers and apps

* Managers never depend on system services. Services may depend on managers or on other services only through published APIs that themselves rely on managers. Hidden shared state is forbidden because [Graph Manager](../managers/07-graph-manager.md) is the only write path per [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) and [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Services never read or write SQLite, key files, sockets, or sync metadata directly. [Graph Manager](../managers/07-graph-manager.md), [Storage Manager](../managers/02-storage-manager.md), [Key Manager](../managers/03-key-manager.md), [Network Manager](../managers/10-network-manager.md), [State Manager](../managers/09-state-manager.md), [Config Manager](../managers/01-config-manager.md), [Event Manager](../managers/11-event-manager.md), [Log Manager](../managers/12-log-manager.md), [Health Manager](../managers/13-health-manager.md), [App Manager](../managers/08-app-manager.md), and [DoS Guard Manager](../managers/14-dos-guard-manager.md) managers remain the sole authorities over their respective domains ([02-architecture/managers/00-managers-overview.md](../managers/00-managers-overview.md)), matching the trust boundaries stated in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md).
* Services never create, manage, or accept network listeners, onion services, or peer sockets. Any network facing behavior is mediated by [Network Manager](../managers/10-network-manager.md) and [State Manager](../managers/09-state-manager.md), and invoked only through their published APIs in alignment with [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md) and the DoS admission model from [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Services must be callable by frontend apps, automation jobs, or remote peers exclusively through surfaces defined in [04-interfaces/**](../../04-interfaces/). If an interface does not exist yet, the service specification must declare the HTTP or WebSocket shape, expected authentication mode, and [OperationContext](05-operation-context.md) fields so the interface document can be authored before implementation and so requests satisfy the [OperationContext](05-operation-context.md) rules enumerated in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).

### 2.3 [OperationContext](05-operation-context.md) and capability encoding

* Every request or scheduled job constructs a complete [OperationContext](05-operation-context.md) as defined in [02-architecture/services-and-apps/05-operation-context.md](05-operation-context.md) and [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md). System services default to `app_id=app_0` and stamp granular capability strings (for example, `capability=system.bootstrap.install`), matching how [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) ties [OperationContext](05-operation-context.md) to envelope submission.
* Services must reject requests missing `app_id`, requester identity, device identity, capability intent, or tracing metadata. Partial contexts are invalid even if the service could infer identity from other data because ACL evaluation defined in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md) requires those inputs.
* Missing required [OperationContext](05-operation-context.md) fields MUST return `ErrorDetail.code=envelope_invalid` and be surfaced to interfaces as HTTP `400` (or WebSocket error event) before any manager invocation.
* Capabilities are documented and versioned. [ACL Manager](../managers/06-acl-manager.md) enforces them via capability edges anchored in the graph, as mandated by [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md). Services never authorize directly, they only declare the capability they are attempting to exercise.

### 2.4 Interface surfaces

System services expose three kinds of surfaces:

1. **API endpoints** (HTTP and WebSocket) wired through the interface layer in [04-interfaces/**](../../04-interfaces/). Endpoints must document accepted media types, payload schemas, [OperationContext](05-operation-context.md) prerequisites, and [DoS Guard Manager](../managers/14-dos-guard-manager.md) hints (expected cost, resource class).
2. **Internal command channels** used only by other system services through typed RPC helpers. These helpers still take [OperationContext](05-operation-context.md) arguments and call managers. They cannot bypass ACL or Schema enforcement.
3. **Scheduled jobs** run by the backend scheduler. Each job registers a manifest describing cadence, maximum concurrency, capability identity, and resource cost. Jobs abort when [Health Manager](../managers/13-health-manager.md) reports `not_ready` or when required managers are degraded.

### 2.5 Input handling and validation posture

* All external input is untrusted. Services perform local validation (shape, size, obvious semantic checks) before handing data to managers so the fail-closed posture described in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md) can be enforced deterministically. Hostile inputs die at the boundary and emit structured logs.
* Services rely on [Schema Manager](../managers/05-schema-manager.md) validation before [Graph Manager](../managers/07-graph-manager.md) persists any mutation and on [ACL Manager](../managers/06-acl-manager.md) checks before serving read or write results, mirroring the ordering defined in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md). They never bypass [Graph Manager](../managers/07-graph-manager.md) or attempt ad hoc persistence.
* Services propagate manager error codes without rewriting them, except to attach human readable context, so protocol level error classes from [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md) remain visible. They do not introduce best-effort fallbacks.

### 2.6 Resource and capacity obligations

* Each service declares `service.*` configuration keys (Section 4) describing per endpoint limits, batch sizes, derived cache limits, and background job budgets.
* Services register [DoS Guard Manager](../managers/14-dos-guard-manager.md) hints (`dos.cost_class`, expected execution time, identity tokens) so [DoS Guard Manager](../managers/14-dos-guard-manager.md) can throttle before resource exhaustion occurs, matching the admission behavior described in [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Derived caches are optional, non authoritative, and rebuild from graph reads after restart. Caches may not contain secrets or ACL protected data unless access is rechecked at read time.

## 3. Lifecycle, deployment, and upgrades

### 3.1 Startup sequencing and readiness

* System services start only after all critical managers report `healthy` and [App Manager](../managers/08-app-manager.md) has registered `app_0` plus the service descriptors.
* Services declare dependencies on other system services explicitly (for example, Sync Service depends on Identity Service for peer and identity lookups). The runtime starts services according to this dependency DAG and enforces timeouts.
* Readiness is reported to [Health Manager](../managers/13-health-manager.md) only after the service validates configuration, loads required schemas, restores derived caches (if any), and registers endpoints and jobs. Any missing dependency forces `ready=false`.
* Services that expose network visible effects must also respect [Network Manager](../managers/10-network-manager.md) admission gates. If [Network Manager](../managers/10-network-manager.md) is not ready, services must reject network coupled work, even if the service itself is ready, matching the sequencing described in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md) and [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* When [Network Manager](../managers/10-network-manager.md) is not ready, network coupled requests MUST return `ErrorDetail.code=network_rejected` and avoid any manager mutations.

### 3.2 Shutdown and fail-closed posture

* During shutdown or degraded health, services stop accepting new work, mark outstanding jobs as `aborted`, and provide [Health Manager](../managers/13-health-manager.md) with a degraded reason. They flush logs and events before releasing dependencies.
* Services do not attempt to run graceful fallbacks when managers are unavailable. They reject work with the relevant error classification so [DoS Guard Manager](../managers/14-dos-guard-manager.md) and frontend callers can back off, in line with the rejection semantics called out in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* When a system service is registered but unavailable, requests MUST fail with one of the following availability codes (HTTP `503` on HTTP interfaces): `ERR_SVC_SYS_NOT_READY`, `ERR_SVC_SYS_DISABLED`, `ERR_SVC_SYS_DEPENDENCY_UNAVAILABLE`, `ERR_SVC_SYS_DRAINING`, or `ERR_SVC_SYS_LOAD_FAILED`.
* Services must not attempt to drain or reconcile partially completed workflows by bypassing managers. Recovery is performed only through the normal manager pipeline after restart, preserving the envelope ordering rules in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).

### 3.3 Upgrade and migration requirements

* Upgrades follow the same prepare and commit configuration flow managers use. A service may refuse to upgrade if schemas are outdated or if [Graph Manager](../managers/07-graph-manager.md) indicates pending migrations.
* Schema migrations are orchestrated via [Graph Manager](../managers/07-graph-manager.md), not ad hoc SQL. Services submit migration envelopes tagged with `capability=system.schema.migrate`, rely on [Schema Manager](../managers/05-schema-manager.md) for validation, and preserve the type invariants defined in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).

### 3.4 Background work scheduling

* Scheduled tasks declare their cadence (`cron`, `fixed_delay`, or on demand), concurrency limit, [OperationContext](05-operation-context.md) capability, and abort timeout. The scheduler ensures only one instance per capability runs simultaneously unless explicitly allowed.
* Jobs that enqueue network work must coordinate with [DoS Guard Manager](../managers/14-dos-guard-manager.md) by publishing expected outbound volume and verifying [Health Manager](../managers/13-health-manager.md) readiness, reflecting the admission obligations in [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).

## 4. Configuration and schema obligations

### 4.1 Configuration namespace

System service configuration keys live under `service.<service_name>.*`. Typical keys include:

| Key                                          | Description                                                                             | Owner              |
| -------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------ |
| `service.bootstrap.install_window_ms`        | Maximum allowed duration for installation sessions before they expire and must restart. | Bootstrap Service  |
| `service.bootstrap.max_pending_invites`      | Cap on concurrent bootstrap invitations before new requests are denied.                 | Bootstrap Service  |
| `service.identity.max_contacts_per_identity` | Soft limit enforced by ACL policy for the Identity Service.              | Identity Service   |
| `service.sync.max_parallel_peers`            | Number of peer sync plans the Sync Service may run.                       | Sync Service       |
| `service.ops.admin_routes_enabled`           | Flag gating whether Admin Service routes are exposed.                              | Operations Service |

[Config Manager](../managers/01-config-manager.md) owns validation and reload semantics. Services may listen for reload events and re validate inputs before applying them. Failure to validate keeps the previous snapshot active and marks health degraded.

### 4.2 Schema ownership and migrations

* Each service documents the schema types it owns inside `app_0`, including parent types, attribute keys, edges, ratings, and ACL templates, preserving the structures defined in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md). Types are versioned. The service declares compatibility ranges.
* Schema additions follow the manager pipeline. Author schema, stage through [Schema Manager](../managers/05-schema-manager.md), commit after validation, and ensure [Graph Manager](../managers/07-graph-manager.md) sequences all resulting objects as graph message envelopes per [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Services never mutate schemas owned by apps directly. If an app needs service assistance (for example, bootstrap provisioning), the service supplies helper objects inside `app_0` that reference the app domain through ACL controlled edges, staying within [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

### 4.3 Capability and ACL templates

* Services publish capability catalogs in the graph (for example, `system.capability.sync.manage`). [ACL Manager](../managers/06-acl-manager.md) consumes these when evaluating requests, as defined in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Default ACL templates for system services are stored in `app_0` during installation. Bootstrap Service initializes admin identities with the minimum capabilities needed to operate other services, including `system.admin`, so [OperationContext](05-operation-context.md) decisions stay deterministic per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

## 5. Observability, telemetry, and policy hooks

### 5.1 Logging

* All actions produce structured logs through [Log Manager](../managers/12-log-manager.md), including [OperationContext](05-operation-context.md), capability attempted, target objects, manager error codes, and execution latency buckets, so rejection data can be traced back to the classifications in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Sensitive payloads (for example, bootstrap secrets) must be redacted before logging. Logs include a boolean flag (`redacted=true`) so downstream tools know the record is intentionally truncated.

### 5.2 Events

* Services emit events through [Event Manager](../managers/11-event-manager.md) per [04-interfaces/events/**](../../04-interfaces/14-events-interface.md). Event descriptors include event family (`system.bootstrap.completed`, `system.identity.invite.accepted`, `system.sync.plan.failed`, `system.ops.health_toggle`), referencing committed graph objects.
* Subscribers must revalidate authorization via ACL capsules attached to the event. Services never include raw object payloads. They only reference objects for callers to fetch through authorized reads.

### 5.3 Metrics and health

* Each service reports readiness, liveness, and degraded modes to [Health Manager](../managers/13-health-manager.md). Metrics include request counts, rejection reasons, cache hit ratios, job runtimes, and [DoS Guard Manager](../managers/14-dos-guard-manager.md) hint utilization.
* Health signals drive admission. If a service is `not_ready`, [Network Manager](../managers/10-network-manager.md) and frontend routers stop forwarding new requests to it, consistent with [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).

### 5.4 [DoS Guard Manager](../managers/14-dos-guard-manager.md) integration

* Services classify endpoints into cost tiers (light, medium, heavy) with deterministic descriptions so [DoS Guard Manager](../managers/14-dos-guard-manager.md) can assign puzzles and throttles in line with [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Services feed telemetry into [DoS Guard Manager](../managers/14-dos-guard-manager.md) when they detect abusive patterns (for example, repeated bootstrap attempts from one peer). Telemetry includes [OperationContext](05-operation-context.md) identifiers, resource usage, and recommended throttle levels and must follow the signaling rules in [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).

## 6. Canonical system service catalog

The proof of concept ships with five mandatory system services. Each one is described in later sections. The table below summarizes their remit.

PoC app domains (contacts, messaging, social, market) are not system services. They are app domains shipped by default for validation and can be swapped for other apps without changing system service contracts or manager boundaries.

| Service                                        | Responsibilities                                                                                                                                     | Primary surfaces                                                             | Mandatory dependencies                                    |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------- |
| Setup Service | Node installation, admin creation, device enrollment, bootstrap invites, recovery keys, installation auditing.                                       | HTTP install APIs, local CLI integration, scheduled cleanup job.             | Config, Graph, Schema, ACL, App, Key, Log, Event, Health. |
| Identity Service          | Identity lifecycle, device linking, contact management, invitation issuance, trust edges, capability delegation, baseline directory queries.         | HTTP APIs, WebSocket notifications, scheduled integrity sweeps.              | Graph, Schema, ACL, App, Log, Event.                      |
| Sync Service               | Peer sync planning, outbound schedule hints, local sync health reporting, manual resync controls, schema aware reconciliation policies.              | HTTP APIs, admin automation hooks, scheduler cooperating with [State Manager](../managers/09-state-manager.md). | State, Graph, Network, [DoS Guard Manager](../managers/14-dos-guard-manager.md), Health, Log, Event.     |
| Admin Service               | Administrative controls, configuration export, health dashboards, audit log queries, service toggles, capability assignment UI glue.                 | HTTP admin APIs, WebSocket dashboards, scheduled policy audits.              | Config, Health, Log, Event, Graph, ACL, Identity Service. |

Each service specification below elaborates required data flows, [OperationContext](05-operation-context.md) expectations, and failure modes.

## 7. Setup Service

### 7.1 Responsibilities

Setup Service is the only authority allowed to transition a node from uninitialized to operational. Its duties include, while preserving the identity and key invariants documented in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md) and the envelope processing rules from [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md):

* Running the installation wizard that provisions the Server Graph roots described in [02-architecture/04-data-flow-overview.md](../04-data-flow-overview.md) and verifying that all bootstrap envelopes commit successfully, following the sequencing from [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Creating the first administrator identity, device, and [OperationContext](05-operation-context.md) bindings, including minimal capabilities needed to operate other services, and binding keys exactly as defined in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Managing bootstrap invitations (time limited capability tokens) so additional devices or administrators can be enrolled without exposing private keys directly.
* Orchestrating device enrollment flows. Verifying device attestations, binding devices to identities, and ensuring [Key Manager](../managers/03-key-manager.md) stores the required key pairs without violating the cryptographic boundaries in [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md).
* Handling bootstrap recovery (revoking stale install tokens, rotating bootstrap secrets, reconstructing default ACLs if they drift).
* Coordinating readiness gating so network coupled surfaces remain closed until bootstrap has completed and [Health Manager](../managers/13-health-manager.md) marks the node ready.

### 7.2 Inputs and outputs

**Inputs**
* Installation payloads carrying node name, storage path confirmation, admin identity metadata, and optional recovery contact information. Payloads are signed locally and never sent over the network.
* Device attestation bundles referencing physical device fingerprints, key fingerprints, and intended identity association.
* Bootstrap invite acceptance payloads containing invite tokens, proof of possession for the identity key, and capability selections.
**Outputs**
* Graph envelopes that create or mutate bootstrap objects (`app_0` parents for node, admin identity, devices, capability edges) per [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* [Event Manager](../managers/11-event-manager.md) descriptors announcing installation milestones (`system.bootstrap.installation_started`, `system.bootstrap.first_admin_created`, `system.bootstrap.device_enrolled`).
* [Log Manager](../managers/12-log-manager.md) records for every bootstrap step, including structured error logs when schema or ACL validation fails.

### 7.2.1 Bootstrap install payload schemas (app_0)

Setup Service owns the `admin.identity`, `admin.device`, and `admin.recovery` schemas in `app_0`. Unknown fields are rejected.

`admin.identity` (object):

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `handle` | Yes | string | 1-64 chars, lowercase `[a-z0-9_]+`. |
| `display_name` | No | string | 1-128 chars. |
| `public_key` | Yes | string | base64, 32-512 bytes decoded. |

`admin.device` (object):

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `device_name` | Yes | string | 1-64 chars. |
| `device_fingerprint` | Yes | string | hex string, 16-128 chars. |
| `key_fingerprint` | Yes | string | hex string, 16-128 chars. |
| `device_type` | No | string | 1-32 chars. |

`admin.recovery` (object):

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `recovery_key_fingerprint` | Yes | string | hex string, 16-128 chars. |
| `recovery_public_key` | Yes | string | base64, 32-512 bytes decoded. |
| `recovery_hint` | No | string | 1-128 chars. |

### 7.3 Critical flows

1. **Installation**
   * Interface layer calls Setup Service `POST /system/bootstrap/install`.
   * Setup Service validates payload, ensures node is not already installed, and constructs an [OperationContext](05-operation-context.md) with `capability=system.bootstrap.install`.
   * If the node is already installed, Setup Service rejects the request with `ERR_SVC_SYS_SETUP_ACL`.
   * Setup Service orchestrates [Graph Manager](../managers/07-graph-manager.md) writes to create node parents, admin identity, admin device, default ACL templates, and capability edges, packaged per [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and authorized per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
   * Upon success, [Event Manager](../managers/11-event-manager.md) receives `system.bootstrap.completed`, [Health Manager](../managers/13-health-manager.md) marks the node ready, and [DoS Guard Manager](../managers/14-dos-guard-manager.md) unlocks public surfaces in line with [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
   * If network transport services exist, Setup Service ensures [Network Manager](../managers/10-network-manager.md) does not accept inbound peer work until [Health Manager](../managers/13-health-manager.md) is ready so the ordering in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md) is respected.
2. **Device enrollment**
   * Device runs local CLI or UI to request an invite. Admin obtains invite token via Setup Service `POST /system/bootstrap/invites`.
   * Device presents token plus key proof to `POST /system/bootstrap/devices`. Setup Service validates, binds device to identity via [Graph Manager](../managers/07-graph-manager.md) per [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md), and destroys the invite token.
   * [Event Manager](../managers/11-event-manager.md) emits `system.bootstrap.device_enrolled`. [Log Manager](../managers/12-log-manager.md) records the enrollment, including device metadata.
3. **Recovery**
   * Admin uses `POST /system/bootstrap/recover` to rotate bootstrap secrets or reset capability assignments.
   * Setup Service ensures [Graph Manager](../managers/07-graph-manager.md) replays schema compliant ACL edges per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md) and revokes stale invites.

### 7.4 Failure handling

* If any Graph or Schema operation fails, Setup Service aborts the entire operation, rolls back, and records the failure reason (`ERR_SVC_SYS_SETUP_SCHEMA`, `ERR_SVC_SYS_SETUP_ACL`) in accordance with [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). No partial installs exist.
* Expired invites result in `HTTP 410 Gone` responses with DoS telemetry increments so repeated misuse pushes puzzle difficulty upward.
* Device attestations that cannot be verified result in `ERR_SVC_SYS_SETUP_DEVICE_ATTESTATION`. Setup Service logs the fingerprint for audit.

## 8. Identity Service

### 8.1 Responsibilities

Identity Service owns the authoritative identity directory within `app_0` and must uphold the identity bindings described in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md). It:

* Creates, updates, and retires identities and associated devices after bootstrap.
* Issues and tracks invitations for contacts (local or remote) and attaches trust edges per ACL policy.
* Manages capability delegation between identities, ensuring capability edges align with service catalogs per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Provides read surfaces for directory queries (by handle, capability, trust state, device status) and exposes filters for frontend apps.
* Triggers periodic integrity sweeps that verify ACL and schema compliance across identity edges.
* Emits signals that allow other components to react to identity and trust changes, without performing network operations directly.

### 8.2 Inputs and outputs

* **Inputs**:
  * Authenticated HTTP requests from admins or app automation ([OperationContext](05-operation-context.md) includes requesting identity, capability such as `system.identity.manage`).
  * Scheduled jobs that scan for stale invitations or orphaned devices.
* **Outputs**:
  * Graph envelopes for identity updates, capability edges, contact relationships, authored per [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
  * Events `system.identity.identity_created`, `system.identity.capability_delegated`, `system.identity.contact_revoked`.
  * Log entries for every identity lifecycle step with ACL decisions.

### 8.2.1 Identity and group schemas (app_0)

Identity Service owns the following schema types in `app_0`. Unknown fields are rejected.

`system.group` (Parent payload):

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `name` | Yes | string | 1-64 chars, lowercase `[a-z0-9_]+`. |
| `description` | No | string | 0-256 chars. |
| `created_at` | Yes | string | RFC3339 timestamp. |
| `updated_at` | No | string | RFC3339 timestamp. |

`system.group_member` (Edge payload):

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `role` | No | string | `member` or `admin`. |
| `created_at` | Yes | string | RFC3339 timestamp. |

### 8.3 Workflow specifics

* Identity creation requires [Schema Manager](../managers/05-schema-manager.md) validation (`identity.parent`, `device.parent`, `capability.edge` types). Identity Service ensures [Graph Manager](../managers/07-graph-manager.md) writes objects in the order defined in [02-architecture/04-data-flow-overview.md](../04-data-flow-overview.md) and within the ownership rules of [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Device linking uses a double opt in. Device owner signs a request, admin approves, Identity Service records the association and notifies [Event Manager](../managers/11-event-manager.md).
* Contact invitations track acceptance state. Identity Service enforces `service.identity.max_contacts_per_identity` by counting accepted edges, and every mutation honors the ACL semantics in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md). Exceeding the limit returns `ERR_SVC_SYS_IDENTITY_CONTACT_LIMIT`.

### 8.4 Failure handling

* Unknown capability results in immediate rejection with `ERR_SVC_SYS_IDENTITY_CAPABILITY`, preserving the deterministic failure posture described in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Integrity sweep failures (for example, orphaned capability edges) trigger alerts via [Event Manager](../managers/11-event-manager.md) (`severity=warning` or `critical`). Identity Service attempts to repair by submitting Graph envelopes. Repeated failure marks the service degraded.

## 9. Sync Service

### 9.1 Responsibilities

Sync Service bridges admin intent with [State Manager](../managers/09-state-manager.md)'s sync engines while adhering to the sync guarantees in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) and the network trust boundaries in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md). It:

* Provides APIs to inspect peer sync health, outstanding envelopes, last successful exchange, and per domain progression.
* Generates sync plans (peer plus domain plus range) and submits them to [State Manager](../managers/09-state-manager.md) following the ordering requirements in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Enforces policy for which peers may sync which app domains, consulting ACL and [App Manager](../managers/08-app-manager.md) metadata.
* Surfaces manual controls (pause peer, resume, force rescan, clear backlog) for administrators via Admin Service.
* Collects telemetry on sync successes and failures, publishes them as events, and feeds [DoS Guard Manager](../managers/14-dos-guard-manager.md) with abusive peer signals (for example, repeated invalid envelopes) in accordance with [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).

### 9.2 Interfaces and jobs

* HTTP APIs:
  * `GET /system/sync/peers`, List peers with sync status.
  * `POST /system/sync/plans`, Submit or adjust sync plans.
  * `POST /system/sync/peers/{peer_id}/pause|resume`.
  * `POST /system/sync/diagnostics`, Trigger diagnostics package.
* Background jobs coordinate with [State Manager](../managers/09-state-manager.md) to refresh sync plans, enforce `service.sync.max_parallel_peers`, and compute remote health indicators.

### 9.3 Data flow and validation

* Sync Service never mutates sync metadata directly. It calls [State Manager](../managers/09-state-manager.md) APIs that in turn talk to Graph and Storage, mirroring the sequencing from [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Sync Service ensures [OperationContext](05-operation-context.md) includes admin identity and capability `system.sync.manage`. Requests without this capability fail under [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* When generating plans, Sync Service consults [Config Manager](../managers/01-config-manager.md) for network scheduling limits, [DoS Guard Manager](../managers/14-dos-guard-manager.md) for throttle hints, and [Health Manager](../managers/13-health-manager.md) to ensure the node can handle additional sync load, matching the admission controls specified in [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Any network coupled behavior remains mediated through the manager layer. Sync Service does not open connections, does not create network listeners, and does not handle transport encryption, preserving the Network/State division from [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md) and [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).

### 9.4 Failure handling

* [State Manager](../managers/09-state-manager.md) rejections are mapped when surfaced to interfaces as follows: ordering violations return `sequence_error`, unknown peer returns `object_invalid`, ACL denial returns `acl_denied`, and remaining plan validation failures return `ERR_SVC_SYS_SYNC_PLAN_INVALID`. Sync Service logs the original reason and marks the plan `failed`.
* If [DoS Guard Manager](../managers/14-dos-guard-manager.md) indicates a peer is abusive, Sync Service automatically pauses the peer and emits `system.sync.peer_paused` with severity `warning`, aligning with [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).

## 10. Admin Service

### 10.1 Responsibilities

Admin Service provides administrative surfaces needed to operate a node safely:

* Aggregates [Health Manager](../managers/13-health-manager.md) signals, service readiness, [DoS Guard Manager](../managers/14-dos-guard-manager.md) posture, and configuration snapshots into HTTP and WebSocket dashboards.
* Offers controlled APIs for configuration export and import, limited to read only or pre approved namespaces per [Config Manager](../managers/01-config-manager.md) policy.
* Provides audit log query helpers that read from [Log Manager](../managers/12-log-manager.md) using [OperationContext](05-operation-context.md) driven filters.
* Manages capability assignments by invoking Identity Service workflows (Admin Service never mutates capability edges directly).
* Hosts toggles for enabling and disabling services, pausing network surfaces, or draining sync pipelines, all implemented via manager APIs.

### 10.2 Interfaces

* HTTP APIs under `/system/ops/*` requiring admin [OperationContext](05-operation-context.md):
  * `GET /system/ops/health`, Aggregated readiness and liveness snapshot.
  * `GET /system/ops/config`, Export sanitized configuration.
  * `POST /system/ops/service-toggles`, Enable and disable services with `system.ops.manage` capability.
  * `POST /system/ops/capabilities`, Request capability grant and revoke (delegates to Identity Service).
  * `GET /system/ops/audit/logs`, Query structured logs with ACL enforced filters.
* WebSocket dashboards streaming health and event summaries.
* Scheduled policy audits verifying configuration drift (`service.ops.policy_audit_interval_ms`).

### 10.3 Security posture

* All endpoints require `system.ops.manage` capability plus admin identity classification (`system.admin`). [ACL Manager](../managers/06-acl-manager.md) verifies both identity and capability edges in accordance with [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md). Admin Service does not implement shortcuts.
* Configuration exports redact sensitive keys (`log.*` secrets, encryption salts). Redaction is deterministic and logged.
* Service toggles result in [Graph Manager](../managers/07-graph-manager.md) events that record who toggled what, preserving auditability.

### 10.4 Failure handling

* Missing capability, `ERR_SVC_SYS_OPS_CAPABILITY`, preserving the rejection semantics from [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Config export failure due to ACL or [Config Manager](../managers/01-config-manager.md) rejection, `ERR_SVC_SYS_OPS_CONFIG_ACCESS`.
* Service is unavailable, disabled, or not ready, one of: `ERR_SVC_SYS_NOT_READY`, `ERR_SVC_SYS_DISABLED`, `ERR_SVC_SYS_DEPENDENCY_UNAVAILABLE`, `ERR_SVC_SYS_DRAINING`, `ERR_SVC_SYS_LOAD_FAILED` (`503` on HTTP surfaces).
* When Admin Service cannot reach [Health Manager](../managers/13-health-manager.md), it marks itself degraded and refuses to serve stale data by returning `internal_error`, so callers never rely on outdated readiness information per [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

## 11. Shared security considerations

* **No implicit trust**: Even though system services live inside the backend, managers treat them as untrusted callers. Services must never assume elevated privilege beyond what [ACL Manager](../managers/06-acl-manager.md) grants via capability edges, matching the boundaries in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* **Immutable audit trail**: Every service action must leave a trace in [Log Manager](../managers/12-log-manager.md) referencing [OperationContext](05-operation-context.md), capability, and object IDs, satisfying the traceability expectations in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* **Secret handling**: Bootstrap secrets, invitation tokens, and admin toggles are stored as encrypted attributes governed by ACL rules so Key and [Network Manager](../managers/10-network-manager.md) boundaries from [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md) and identity bindings from [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md) remain intact. Services never store secrets in configuration or derived caches.
* **DoS response**: Services integrate with [DoS Guard Manager](../managers/14-dos-guard-manager.md) by submitting telemetry events when abusive patterns appear, ensuring the admission layer can intervene before resources are exhausted, consistent with [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).

## 12. Implementation checklist

1. **Registration**: Service descriptor registered with [App Manager](../managers/08-app-manager.md) under `app_0`, including capability catalog, configuration keys, dependency graph, and readiness hooks, consistent with the boundaries in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
2. **[OperationContext](05-operation-context.md) discipline**: Every endpoint, job, or RPC helper constructs the immutable [OperationContext](05-operation-context.md) defined in [02-architecture/services-and-apps/05-operation-context.md](05-operation-context.md) and [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) before touching managers.
3. **Manager usage**: All mutations go through [Graph Manager](../managers/07-graph-manager.md) (schema to ACL to persistence ordering), all reads respect ACL checks, and no raw SQLite or filesystem access exists, per [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
4. **Configuration**: Service specific `service.*` keys registered with [Config Manager](../managers/01-config-manager.md), validation functions implemented, reload behavior documented.
5. **Schema**: All required schema types defined inside `app_0`, versioned, and validated through [Schema Manager](../managers/05-schema-manager.md), preserving [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md). Migrations planned as Graph envelopes with capability gating.
6. **Interfaces**: HTTP and WebSocket routes documented in [04-interfaces/**](../../04-interfaces/), including payload schema, [OperationContext](05-operation-context.md) requirements, and [DoS Guard Manager](../managers/14-dos-guard-manager.md) hints, and the resulting writes conform to [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md). Interface tests cover success and fail closed paths.
7. **Jobs**: Scheduler manifests declare cadence, capability, resource cost, and abort semantics. Jobs can resume idempotently after crash.
8. **Observability**: Logs, events, and health signals wired through [Log Manager](../managers/12-log-manager.md), [Event Manager](../managers/11-event-manager.md), and [Health Manager](../managers/13-health-manager.md) with deterministic severity levels.
9. **Security**: Secrets stored only via [Graph Manager](../managers/07-graph-manager.md) with ACL protection so [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md) remains authoritative. [DoS Guard Manager](../managers/14-dos-guard-manager.md) telemetry integrated per [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md). Capability delegation enforced exclusively by [ACL Manager](../managers/06-acl-manager.md).
10. **Failure drills**: Service tested for manager outages, configuration reload failures, schema mismatches, and [DoS Guard Manager](../managers/14-dos-guard-manager.md) throttling to confirm fail closed behavior, mirroring the failure posture in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

Following this specification ensures all system services deliver consistent behavior, align with the manager fabric, and remain safe to reuse by every application targeting the 2WAY substrate.

