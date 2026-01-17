


# 03 App Backend Extensions

## 1. Purpose and scope

App backend extensions are optional in-process services that belong to a single registered application slug and `app_id`. They let independent app teams expand backend behavior without weakening the trust boundaries enforced by managers, system services, or the interface layer. Extensions never replace managers; they provide app-specific orchestration while remaining inside the platform's fail-closed posture.

This overview defines how extensions are authored, registered, packaged, loaded, observed, and unloaded so they coexist with the 2WAY platform without renegotiating contracts on every release. It codifies lifecycle, configuration, schema, capability, observability, and failure semantics that match the rest of the architecture corpus, enabling reviewers to audit application-owned logic using the same criteria as system-owned logic.

This overview references:

* [01-protocol/**](../../01-protocol/)
* [02-architecture/01-component-model.md](../01-component-model.md)
* [02-architecture/03-trust-boundaries.md](../03-trust-boundaries.md)
* [02-architecture/04-data-flow-overview.md](../04-data-flow-overview.md)
* [02-architecture/managers/**](managers/)
* [02-architecture/managers/00-managers-overview.md](../managers/00-managers-overview.md)
* [02-architecture/services-and-apps/**](./)
* [02-architecture/services-and-apps/01-services-vs-apps.md](01-services-vs-apps.md)
* [02-architecture/services-and-apps/05-operation-context.md](05-operation-context.md)
* [04-interfaces/**](../../04-interfaces/)
* [05-security/**](../../05-security/)

### 1.1 Responsibilities and boundaries

This overview is responsible for the following:

* Defining the mandatory extension model for a conforming node, including the lifecycle, surfaces, dependency requirements, and execution boundaries for every backend extension.
* Defining strict ownership rules between extensions, managers, system services, and the interface layer so app-owned code never weakens the guarantees in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) and [02-architecture/01-component-model.md](../01-component-model.md).
* Defining [OperationContext](05-operation-context.md), capability catalog, configuration, schema, packaging, and observability requirements so extensions integrate with managers using the same posture as system services.
* Defining admission, [DoS Guard Manager](../managers/14-dos-guard-manager.md), and [Health Manager](../managers/13-health-manager.md) expectations that gate extension readiness and resource usage.
* Defining a reusable checklist that implementers can follow to prove an extension meets all contractual obligations before shipment.

This overview does not cover the following:

* Manager internal design, database layout, cryptographic algorithms, or network transport mechanics, which remain owned by protocol managers as detailed in [02-architecture/managers/00-managers-overview.md](../managers/00-managers-overview.md).
* Frontend UI implementations or transport encoding details, which belong to [04-interfaces/**](../../04-interfaces/) unless explicitly called out for missing shapes.
* App-specific product logic that does not cross the backend boundary defined in this document.

### 1.2 Invariants and guarantees

Across all components and execution contexts described in this file, the following invariants hold:

* Extensions never bypass managers. All mutations flow through [Graph Manager](../managers/07-graph-manager.md), preserving the structural -> schema -> ACL -> persistence ordering mandated by [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* All authorization flows through [ACL Manager](../managers/06-acl-manager.md) using the capability posture in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md); extensions never authorize directly.
* Every entry point constructs an immutable [OperationContext](05-operation-context.md) before calling managers, matching [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) and [02-architecture/services-and-apps/05-operation-context.md](05-operation-context.md).
* Namespace isolation follows [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md). Extensions operate only on their owning `app_id` and never impersonate `app_0`.
* All failures are handled fail closed with canonical error classes from [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md). Partial writes, best-effort retries, or out-of-band repairs are forbidden.
* Removal, upgrade, or rollback of an extension never corrupts graph state because [Graph Manager](../managers/07-graph-manager.md) remains the sole write authority under [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).

## 2. Backend extension contract

### 2.1 Architectural role and definitions

App backend extensions sit between frontend applications and protocol managers. They share the service contract defined in [02-architecture/services-and-apps/01-services-vs-apps.md](01-services-vs-apps.md), yet remain optional and app-owned. Key terms:

| Term | Definition |
| --- | --- |
| **Extension manifest** | Metadata describing the extension module (slug, `app_id`, version, capability catalog, dependencies, scheduler jobs, configuration requirements, DoS Guard hints). Stored in [App Manager](../managers/08-app-manager.md)'s registry. |
| **Extension service** | The in-process code module implementing backend logic for the owning app. It invokes managers exclusively via [OperationContext](05-operation-context.md), never through private back channels. |
| **Extension surface** | HTTP, WebSocket, scheduler, or helper RPC entry points registered through the interface layer described in [04-interfaces/**](../../04-interfaces/). |
| **Extension package** | The signed distributable that contains the extension code, manifest, schemas, defaults, and migrations. |

### 2.2 Ownership and namespace rules

* Every extension belongs to exactly one registered `app_id != app_0` and runs wholly inside that application's trust boundary. [App Manager](../managers/08-app-manager.md) enforces slug uniqueness and binds [OperationContext](05-operation-context.md) metadata per [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Extensions may expose APIs, jobs, or events that belong exclusively to their owning app. Cross-app behavior must traverse graph data structures and ACL policy; no direct cross-app RPC is allowed.
* Extensions cannot claim ownership of graph objects outside their app domain unless schema delegation and ACL policy explicitly permit it, mirroring the object rules in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).

### 2.3 Interaction boundaries with managers and system services

* Managers never depend on extensions. Extensions consume manager APIs (Config, Schema, ACL, Graph, Event, Log, Health, DoS Guard, Network, State, App) exactly as documented in [02-architecture/managers/00-managers-overview.md](../managers/00-managers-overview.md).
* Extensions never access SQLite, storage paths, cryptographic keys, sockets, or sync metadata directly. [Graph Manager](../managers/07-graph-manager.md) remains the only write path and Network + State Managers remain the only transport authorities, matching [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md), [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md), and [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).
* Extensions do not implement ad hoc listeners or side channels. All network-facing behavior is routed through interface definitions in [04-interfaces/**](../../04-interfaces/), which in turn use [Network Manager](../managers/10-network-manager.md) and DoS Guard admissions per [01-protocol/11-dos-guard-and-client-puzzles.md](../../01-protocol/11-dos-guard-and-client-puzzles.md).

### 2.4 [OperationContext](05-operation-context.md) and capability encoding

* Every API, helper, or job constructs a complete [OperationContext](05-operation-context.md) before calling managers, using the fields and immutability guarantees in [02-architecture/services-and-apps/05-operation-context.md](05-operation-context.md).
* [OperationContext](05-operation-context.md) always sets `app_id` to the owning application, stamps capability identifiers namespaced under the app (for example, `app.crm.ticket.create`), and records requester identity, device identity, trust posture, correlation IDs, and DoS Guard cost hints.
* Automation jobs run with `actor_type=automation` so [ACL Manager](../managers/06-acl-manager.md) can distinguish them from user traffic. Missing or partial contexts are rejected with canonical errors derived from [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

### 2.5 Interface surfaces

Extensions expose three surface categories and must declare them before activation:

1. **HTTP and WebSocket endpoints** wired through [04-interfaces/**](../../04-interfaces/), documenting URI templates, media types, payload schemas, [OperationContext](05-operation-context.md) prerequisites, and DoS Guard cost classes in line with [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).
2. **Internal helper RPCs** callable only by system services explicitly whitelisted in the manifest. Helpers still take [OperationContext](05-operation-context.md) arguments and call managers; they never bypass ACL or schema enforcement.
3. **Scheduled jobs** registered with the backend scheduler. Manifests specify cadence (`cron`, `fixed_delay`, or event-driven), concurrency caps, capability identifiers, DoS Guard hints, and abort timeouts. Jobs abort automatically when [Health Manager](../managers/13-health-manager.md) reports `not_ready`.

### 2.6 Input handling and validation posture

* All external input is untrusted. Extensions perform local validation (shape, size, cheap semantic checks) before invoking managers, keeping the fail-closed posture defined in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).
* [Schema Manager](../managers/05-schema-manager.md) validates types before [Graph Manager](../managers/07-graph-manager.md) persists any mutation, and [ACL Manager](../managers/06-acl-manager.md) authorizes reads/writes before data leaves the extension, preserving the ordering in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Extensions propagate manager error codes without rewriting them, except to attach human-readable context, so protocol-level rejection classes stay visible to callers.

### 2.7 Mandatory dependencies and resource obligations

* The minimum dependency set for declaring readiness includes App, Config, Schema, Graph, ACL, Log, Event, Health, and DoS Guard Managers, plus Network and State Managers for any remote-aware surface. Extensions never instantiate managers themselves.
* Extensions declare resource budgets (CPU, memory, storage) and DoS Guard hints so [Health Manager](../managers/13-health-manager.md) and DoS Guard can enforce throttles before exhaustion, mirroring [01-protocol/11-dos-guard-and-client-puzzles.md](../../01-protocol/11-dos-guard-and-client-puzzles.md).
* Derived caches are optional, non-authoritative, rebuilt from graph reads, and must recheck authorization on every read.

### 2.8 Allowed responsibilities

Extensions may:

* Expose APIs, jobs, and events that belong exclusively to their owning application, provided every call is scoped to the app namespace defined in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Coordinate workflows using public manager APIs (Config, Schema, ACL, Graph, Event, Log, State, Network, Health, DoS Guard) without bypassing the validation and ordering rules in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Maintain app-specific schemas, capability catalogs, and ACL templates inside their app domain while following the schema guarantees in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) and [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Use scheduler jobs, helper RPCs, and automation helpers to run background work so long as each entry point supplies an immutable [OperationContext](05-operation-context.md) and publishes DoS Guard hints.
* Register observability hooks (logs, events, health signals) through the manager fabric so operators can debug extension-owned logic with the same tooling as system services.

### 2.9 Forbidden responsibilities

Extensions must never:

* Claim `app_0` or operate on behalf of another application unless schema delegation and ACL policy explicitly allow it; namespace isolation in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md) remains absolute.
* Bypass managers by touching SQLite, filesystem storage, sockets, keys, or sync metadata directly; [Graph Manager](../managers/07-graph-manager.md) stays the only write path and Key/Network/State Managers own crypto and transport boundaries.
* Perform manager-grade duties such as ACL enforcement, schema compilation, sync orchestration, or DoS admission decisions—those remain under the manager charter described in [02-architecture/managers/00-managers-overview.md](../managers/00-managers-overview.md).
* Expose new listeners, peer sockets, or transport protocols outside the interface layer; all ingress/egress goes through the HTTP/WebSocket surfaces documented in [04-interfaces/**](../../04-interfaces/) and the admission posture from [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).
* Persist state outside graph-owned storage or rely on mutable local caches that cannot be recomputed deterministically from Graph reads.
* Share runtime state with other extensions or apps via global variables, in-memory message passing, or filesystem side channels; all coordination occurs through manager-governed graph data or documented system service APIs.

## 3. Lifecycle, deployment, and runtime coordination

### 3.1 Lifecycle states and internal execution phases

[App Manager](../managers/08-app-manager.md) enforces the lifecycle states **Registration -> Installation -> Activation -> Ready -> Running -> Quiesce -> Removal**. Within activation, extensions follow deterministic internal phases that mirror legacy engine diagrams:

1. **Initialization**: Dependency injection, configuration snapshot validation, schema availability checks.
2. **Surface registration**: Interface routes and scheduler jobs register with interface and scheduler layers, respecting [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).
3. **Admission**: DoS Guard cost hints and quotas register per [01-protocol/11-dos-guard-and-client-puzzles.md](../../01-protocol/11-dos-guard-and-client-puzzles.md).
4. **Execution**: Requests, jobs, and helper RPCs run while [Health Manager](../managers/13-health-manager.md) reports `ready`.
5. **Drain**: New work is rejected, outstanding jobs complete, backpressure surfaces to [App Manager](../managers/08-app-manager.md).
6. **Shutdown**: Resources release, telemetry flushed, [Health Manager](../managers/13-health-manager.md) marks the extension stopped.

State transitions are observable through [App Manager](../managers/08-app-manager.md) and [Health Manager](../managers/13-health-manager.md) APIs. Any missing dependency forces `ready=false` and blocks activation.

### 3.2 Admission, scheduling, and backpressure

* Extension surfaces register DoS Guard hints (cost classes, identity tokens, max concurrency) to ensure [Network Manager](../managers/10-network-manager.md) throttles before code execution, per [01-protocol/11-dos-guard-and-client-puzzles.md](../../01-protocol/11-dos-guard-and-client-puzzles.md).
* Extensions emit backpressure signals (queue depth, latency, cache pressure) via [Health Manager](../managers/13-health-manager.md) so [App Manager](../managers/08-app-manager.md) and DoS Guard can slow inbound work when budgets approach limits.
* Scheduler jobs declare concurrency limits and budgets. Budget violations trigger throttling or [Health Manager](../managers/13-health-manager.md) degradation, and jobs halt when dependencies are `not_ready`.

### 3.3 Dependency health and readiness

* Extensions monitor [Health Manager](../managers/13-health-manager.md) for dependency readiness. If any dependency transitions to `not_ready`, the extension immediately stops the impacted surfaces and fails closed, following [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).
* Readiness reports (`initializing`, `ready`, `degraded`, `not_ready`, `stopped`) must reflect the ability to handle new work without data loss. Misreporting readiness violates the [OperationContext](05-operation-context.md) guarantees that DoS Guard depends on.

## 4. Packaging, registration, and compatibility

### 4.1 Package contents

Extension packages delivered to [App Manager](../managers/08-app-manager.md) include:

* Manifest file covering slug, `app_id`, semantic version, required platform version, capability catalog, dependency graph, scheduler jobs, configuration defaults, and DoS Guard hints.
* Signed binaries or modules. Signing and verification follow [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md), and unsigned packages are rejected per [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Schema definitions scoped to the owning app plus migration envelopes that respect the sequencing posture in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Interface documentation references pointing to [04-interfaces/**](../../04-interfaces/) entries.

### 4.2 Registration and upgrade policy

* Registration loads the manifest into [App Manager](../managers/08-app-manager.md), validates slug ownership, dependency declarations, scheduler manifests, and capability catalogs.
* Installation stages the package, loads schemas through [Schema Manager](../managers/05-schema-manager.md), validates configuration defaults via [Config Manager](../managers/01-config-manager.md), and runs the security reviews mandated in [05-security/**](../../05-security/). Installation fails closed; nothing runs until all checks succeed.
* Upgrades use prepare/commit semantics. [App Manager](../managers/08-app-manager.md) stages the new version, validates compatibility, swaps modules atomically on success, and replays readiness checks. Rollbacks reinstall the previous signed version and rely on deterministic state reconstruction from [Graph Manager](../managers/07-graph-manager.md).

### 4.3 Compatibility matrix

Manifests declare:

| Field | Description |
| --- | --- |
| `requires.platform.min_version` | Minimum backend platform version required. Loader refuses activation below this value, matching [01-protocol/10-versioning-and-compatibility.md](../../01-protocol/10-versioning-and-compatibility.md). |
| `requires.managers` | Managers and minimum capability sets the extension expects. |
| `requires.permissions` | Capability names that must exist before activation. |
| `supports.frontend.min_version` | Informational hint for frontend coordination, not enforced by the backend. |

Compatibility validation mirrors the negotiation rules in [01-protocol/10-versioning-and-compatibility.md](../../01-protocol/10-versioning-and-compatibility.md).

## 5. Configuration, schema, and storage obligations

### 5.1 Configuration namespace

* Extension configuration keys live under `app.<slug>.*`. [Config Manager](../managers/01-config-manager.md) validates snapshots before exposing them, enforcing the sequencing discipline in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Extensions implement `prepare_config(snapshot)` and `commit_config()` hooks mirroring manager behavior. Rejecting a snapshot keeps the previous version active and marks health degraded.
* Secrets live only as encrypted graph attributes mediated by [Key Manager](../managers/03-key-manager.md). Plaintext secrets in configuration or caches are forbidden.

### 5.2 Schema ownership

* Schemas contributed by an extension are owned by the app domain, versioned, and validated through [Schema Manager](../managers/05-schema-manager.md), preserving the structures defined in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* Migration strategies are expressed as Graph envelopes that run through [Graph Manager](../managers/07-graph-manager.md) and [Schema Manager](../managers/05-schema-manager.md) validation, never via direct SQL.
* Cross-app references require explicit ACL policy and [Schema Manager](../managers/05-schema-manager.md) validation. Extensions cannot create new trust boundaries; they leverage ACL edges defined in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

### 5.3 Storage and caching

* Derived caches rebuild deterministically from Graph reads, recheck ACL policy on every access, and store only references or computed counters.
* Extensions cannot allocate filesystem space outside the sandboxed directories assigned by the runtime. Temporary files declare size limits in the manifest and respect DoS Guard budgets.

## 6. Observability, telemetry, and diagnostics

### 6.1 Logging

* Every action emits structured logs through [Log Manager](../managers/12-log-manager.md), including [OperationContext](05-operation-context.md) identifiers, capability names, manager outcomes, rejection codes, and latency buckets, so incidents map back to [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).
* Sensitive payloads are redacted before logging. Logs include a `redacted=true` flag so downstream tooling understands intentional truncation.

### 6.2 Events

* Extensions publish namespaced events (for example, `app.<slug>.event.*`) via [Event Manager](../managers/11-event-manager.md) after Graph commits. Events reference committed objects, never embed private payloads, and rely on ACL capsules for audience enforcement.
* Event descriptors include capability identifiers and severity so operators can correlate extension behavior with DoS Guard telemetry.

### 6.3 Health and metrics

* Extensions register readiness and liveness probes with [Health Manager](../managers/13-health-manager.md). Metrics include request counts, rejection reasons, queue depth, job runtime, cache rebuild counts, and DoS Guard hint utilization.
* Health transitions drive admission. When an extension reports `not_ready`, [Network Manager](../managers/10-network-manager.md) and frontend routers stop forwarding new work to it in accordance with [01-protocol/11-dos-guard-and-client-puzzles.md](../../01-protocol/11-dos-guard-and-client-puzzles.md).

### 6.4 Diagnostics hooks

* Extensions expose admin diagnostics endpoints (for example, `POST /system/ops/extensions/{slug}/diagnostics`) routed through Operations Console. Dumps include configuration versions, outstanding jobs, dependency health, and DoS telemetry snapshots, with sensitive data redacted.
* Diagnostics adhere to the admin authorization model so only identities with the correct capability edges can trigger them.

## 7. Security and trust boundaries

* Extensions inherit the untrusted caller posture described in [02-architecture/01-component-model.md](../01-component-model.md); managers treat them as any other caller even though they run in-process.
* Mutual authentication is mandatory between the loader and [App Manager](../managers/08-app-manager.md). Only signed packages from the owning app are accepted.
* Extensions never access cryptographic keys directly. [Key Manager](../managers/03-key-manager.md) mediates all signing, encryption, and random number generation per [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md) and [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Authorization always flows through [ACL Manager](../managers/06-acl-manager.md). Cached ACL decisions must be revalidated before reuse, preserving the guarantees in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* External dependencies (for example, outbound webhooks) route through [Network Manager](../managers/10-network-manager.md) so DoS Guard can throttle and so network trust boundaries in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md) stay intact.

## 8. Failure handling and recovery

* Failures reject work atomically with canonical error codes (`ERR_APP_EXTENSION_CONTEXT`, `ERR_APP_EXTENSION_CAPABILITY`, etc.), aligning with [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).
* Background work may retry idempotent operations using bounded exponential backoff. Retries respect the ordering guarantees in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Crash recovery reconstructs state entirely from [Graph Manager](../managers/07-graph-manager.md), [Config Manager](../managers/01-config-manager.md), and other manager-owned stores. Derived caches rebuild deterministically before readiness returns.
* Upgrade or rollback failures trigger [App Manager](../managers/08-app-manager.md) to reinstall the previous signed version, emit health degradation events, and leave graph state untouched.
* Uninstall stops the extension immediately, flushes telemetry, unregisters scheduler jobs and routes, and confirms no background work remains. Graph data persists for archival or reinstall purposes.

## 9. Implementation checklist

1. **Manifest completeness**: Manifest covers slug, `app_id`, dependencies, configuration keys, scheduler jobs, resource budgets, capability catalog, and DoS Guard hints. Validated by [App Manager](../managers/08-app-manager.md).
2. **[OperationContext](05-operation-context.md) discipline**: Every entry point constructs immutable [OperationContext](05-operation-context.md) objects with `app_id=<owning app>`, required capability names, tracing metadata, and trust posture before calling managers.
3. **Manager-only access**: All state mutations flow through Schema, ACL, and Graph Managers in the structural -> schema -> ACL -> persistence order. No raw storage, network, or crypto access exists.
4. **Interface documentation**: HTTP/WebSocket surfaces documented in [04-interfaces/**](../../04-interfaces/), including payload schemas, [OperationContext](05-operation-context.md) requirements, DoS Guard hints, and deterministic error codes.
5. **Configuration and schema validation**: Configuration keys declared in [Config Manager](../managers/01-config-manager.md), schema contributions loaded via [Schema Manager](../managers/05-schema-manager.md), migrations scripted as Graph envelopes.
6. **Observability**: Log, Event, and [Health Manager](../managers/13-health-manager.md) integrations implemented. Diagnostics hooks provide actionable insights without exposing secrets.
7. **Security review**: Extension passed threat modeling and secure code review per [05-security/**](../../05-security/). Secrets stored via [Key Manager](../managers/03-key-manager.md); no plaintext secrets exist in configuration or logs.
8. **Lifecycle hooks**: Start, stop, quiesce, upgrade, rollback, and uninstall hooks implemented. Extension can unload cleanly without affecting other applications.
9. **DoS posture**: Surfaces register DoS hints, respect puzzles, and emit abuse telemetry to DoS Guard. Scheduler jobs publish outbound resource estimates.
10. **Recovery drills**: Extension tested for manager outages, configuration reload failures, schema mismatches, DoS Guard throttling, and uninstall to confirm fail-closed behavior.
