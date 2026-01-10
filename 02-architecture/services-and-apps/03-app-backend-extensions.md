# 03 App Backend Extensions

## 1. Purpose and scope

App backend extensions are optional in-process services that belong to a single registered application slug and `app_id`. They expand an application's backend behavior without weakening the trust boundaries enforced by managers, system services, or interface layers. This specification defines how extensions are authored, packaged, registered, loaded, observed, and unloaded so independent teams can deliver backend code that coexists with the 2WAY platform without renegotiating contracts with every release.

This document sets the implementation requirements for extension lifecycle, OperationContext discipline, capability catalogs, scheduler integration, configuration exchange, schema contributions, and observability. It also defines how extensions interact with App Manager, system services, and protocol managers while maintaining fail-closed behavior. App extensions must follow all guarantees in the component model and protocol specifications; this document clarifies the additional rules that apply because extensions are application owned rather than platform owned.

This specification references the following documents:

* `01-protocol/00-protocol-overview.md`
* `01-protocol/02-object-model.md`
* `01-protocol/03-serialization-and-envelopes.md`
* `01-protocol/04-cryptography.md`
* `01-protocol/05-keys-and-identity.md`
* `01-protocol/06-access-control-model.md`
* `01-protocol/07-sync-and-consistency.md`
* `01-protocol/08-network-transport-requirements.md`
* `01-protocol/09-errors-and-failure-modes.md`
* `01-protocol/11-dos-guard-and-client-puzzles.md`
* `02-architecture/01-component-model.md`
* `02-architecture/services-and-apps/01-services-vs-apps.md`
* `02-architecture/services-and-apps/02-system-services.md`
* `02-architecture/services-and-apps/05-operation-context.md`
* `02-architecture/managers/00-managers-overview.md`
* `04-interfaces/**`
* `05-security/**`

## 2. Architectural role and definitions

App backend extensions occupy the middle layer between frontend applications and protocol managers. They inherit the service contract defined in `02-architecture/services-and-apps/01-services-vs-apps.md`, but unlike system services they:

* Are owned, versioned, and distributed by a single application (`app_id != app_0`).
* Are optional. An app may supply zero or one backend extension service. Removing the app removes the extension.
* Must run entirely within the application's trust boundary. App Manager enforces a one-to-one mapping between an extension and its owning app slug.

Key terms used in this specification:

| Term | Definition |
| --- | --- |
| **Extension manifest** | The metadata describing the extension module (slug, `app_id`, version, capabilities, dependencies, scheduler jobs, storage needs). Stored in App Manager's registry. |
| **Extension service** | The in-process code module implementing backend logic for the owning app. Invokes managers via OperationContext just like system services. |
| **Extension surface** | The HTTP/WebSocket endpoints, RPC helpers, or scheduled jobs exposed by the extension through the interface layer in `04-interfaces/**`. |
| **Extension package** | The signed bundle that contains the extension binary, schemas, configuration defaults, and manifest. Delivered to App Manager during installation or update. |

Extensions are never authoritative for protocol invariants. Managers own data integrity, cryptography, ACLs, and transport. Extensions orchestrate workflows on behalf of their app using only public manager APIs and published system service helpers.

## 3. Responsibilities and boundaries

### 3.1 Allowed responsibilities

Extensions may:

* Expose APIs that belong exclusively to their owning application (for example, `/apps/{slug}/vault/*`).
* Run scheduled jobs that mutate or read the owning app's graph domain, provided all work flows through OperationContext and Graph Manager.
* Consume platform services (Config, Storage, Log, Event, Health, DoS Guard, Network, State) through their published APIs.
* Register capability catalogs, ACL templates, or derived data models that live inside the owning app domain.
* Reuse system service helper APIs when explicitly documented (for example, Feed Service helper RPCs).

### 3.2 Forbidden responsibilities

Extensions must never:

* Claim `app_0` or any other app's identifier.
* Provide manager-like functions (key storage, ACL enforcement, schema compilation, sync orchestration) outside their app domain.
* Read or write SQLite, key files, sockets, or sync metadata directly.
* Bypass DoS Guard, Health Manager, or the interface layer to expose custom sockets or listeners.
* Invoke other extensions directly. All cross-app collaboration goes through manager-enforced graph objects or published system services.
* Install background daemons, OS services, or tasks outside the backend process.

Any attempt to cross these boundaries must be rejected before code runs. App Manager, Config Manager, and the runtime loader enforce these prohibitions.

## 4. Lifecycle and state machine

Extensions follow a deterministic lifecycle managed by App Manager:

1. **Registration**: The app submits an extension manifest via App Manager. Manifest validation checks slug ownership, semantic versioning, dependency declarations, and capability catalog completeness.
2. **Installation**: App Manager stages the extension package, uses Schema Manager to load declared types, validates configuration defaults with Config Manager, and performs security scans referenced in `05-security/**`. Installation fails closed; nothing is loaded until all checks succeed.
3. **Activation**: App Manager loads the extension module into the backend process, injects dependency handles, and registers surfaces with the interface layer and scheduler. Health Manager marks the extension `initializing`.
4. **Ready**: The extension reports readiness after configuration is applied, schemas are confirmed, OperationContext templates exist, and scheduler registrations succeed.
5. **Running**: Extension handles API calls, jobs, and internal requests. Health Manager monitors readiness/liveness. App Manager can request `quiesce`, `stop`, or `restart`.
6. **Quiesce/Stop**: During uninstall, upgrade, or failure, App Manager instructs the extension to stop accepting new work, drain outstanding jobs, flush logs, and release resources.
7. **Removal**: App uninstall removes its extension by unregistering surfaces, removing scheduler jobs, deleting configuration keys, and marking schema contributions as inactive if no longer needed (Graph objects remain intact).

State transitions are observable through App Manager and Health Manager APIs so tooling can orchestrate upgrades without race conditions.

## 5. OperationContext and capability requirements

Extensions obey the same OperationContext contract as system services, with additional app-specific rules:

* Every entry point (HTTP, WebSocket, RPC helper, scheduler job) constructs an immutable OperationContext that sets `app_id` to the owning application. Context includes user identity, device identity, capability intent, trust posture, correlation IDs, and cost hints per `02-architecture/services-and-apps/05-operation-context.md`.
* Capability names must be namespaced under the owning app (for example, `capability=app.crm.ticket.create`). Capability catalogs are published via Graph Manager and guarded by ACL Manager according to `01-protocol/06-access-control-model.md`.
* Extension jobs acting as automation mark `actor_type=app_service` and include the app slug in OperationContext metadata so audit trails distinguish app automation from user requests.
* Extensions reject any request lacking a valid OperationContext even if the call originates from the same device. Partial contexts are logged as `ERR_APP_EXTENSION_CONTEXT`, referencing the rejection semantics in `01-protocol/09-errors-and-failure-modes.md`.
* Extensions are prohibited from mutating OperationContext mid flight. If additional metadata is needed (for example, feeder hints), it must be attached before manager calls or passed as separate arguments.

## 6. Interface surfaces

Extensions expose three surface categories:

1. **HTTP/WebSocket endpoints** routed through the interface layer defined in `04-interfaces/**`. Each endpoint documents:
   * URI template, verb, media types, payload schema references, and maximum payload size.
   * Required OperationContext fields and capability names.
   * Expected DoS Guard cost class (`light`, `medium`, `heavy`) plus any advisory tokens (for example, maximum rate per identity).
   * Deterministic responses and protocol error codes (`01-protocol/09-errors-and-failure-modes.md`).

2. **Internal RPC helpers** callable only by system services explicitly whitelisted in the extension manifest. RPC helpers never bypass ACL checks and always accept an OperationContext argument.

3. **Scheduled jobs** registered with the backend scheduler. Job manifests include cadence (`cron` or fixed delay), concurrency cap, capability name, resource cost, DoS Guard hints, and abort timeout. Jobs stop automatically when Health Manager marks the node `not_ready`.

All surfaces must be defined before activation so interface documentation, DoS Guard quotas, and Health Manager readiness gating can be configured ahead of time.

## 7. Inputs, outputs, and dependencies

### 7.1 Inputs

Extensions consume the following inputs:

* Requests routed through the interface layer after Auth Manager builds an OperationContext skeleton.
* App-specific configuration namespaces (`app.<slug>.*`) supplied by Config Manager.
* Owning app schemas and ACL templates validated by Schema Manager and ACL Manager.
* Manager handles (Graph, Storage, Event, Log, State, Network, Health, DoS Guard, Config, App, Key) injected by the runtime. Extensions never instantiate managers.
* Telemetry from system services (for example, Feed Service helper results) when such services publish extension-safe APIs.

### 7.2 Outputs

Extensions produce:

* Graph envelopes for objects belonging to their app domain, serialized via `01-protocol/03-serialization-and-envelopes.md`.
* Events published through Event Manager with namespaced identifiers (`app.<slug>.event.*`). Events only reference objects, never embed private payloads.
* Structured logs via Log Manager, containing OperationContext identifiers, capability names, and rejection codes.
* Health Manager readiness and liveness signals scoped to the extension.
* DoS Guard telemetry events when the extension detects abusive patterns tied to its app domain.

### 7.3 Mandatory dependencies

The following minimum set of managers must be available for an extension to declare readiness:

* App Manager (identity binding, lifecycle control).
* Config Manager (configuration snapshot validation).
* Schema Manager and Graph Manager (schema enforcement and persistence).
* ACL Manager (authorization).
* Log, Event, and Health Managers (observability).
* DoS Guard Manager (admission enforcement hints).
* Network and State Managers for any remote or sync-aware flows.

Extensions may depend on additional system services; dependencies are declared in the manifest, and App Manager enforces ordering during activation.

## 8. Packaging, upgrades, and compatibility

### 8.1 Package contents

An extension package delivered to App Manager must include:

* Manifest file (slug, `app_id`, semantic version, required platform version, capability catalog, dependency graph, scheduler job table, configuration defaults, DoS Guard hints).
* Extension binaries or modules (signed, reproducible build artifacts).
* Schema definitions (if any) scoped to the owning app and versioned.
* Interface documentation references (links to `04-interfaces/**` entries or embedded drafts if not yet published).
* Migration scripts expressed as Graph envelopes (never raw SQL).

Packages are signed using the owning app's release keys managed by Key Manager per `01-protocol/04-cryptography.md`. Unsigned or tampered packages are rejected.

### 8.2 Upgrade policy

* Upgrades follow prepare/commit semantics. App Manager stages the new version, validates compatibility (schema diffs, capability catalog evolution, configuration migrations), then swaps modules atomically.
* Rolling back is only supported by reinstalling a previous signed version. Extensions must be stateless or capable of replaying derived state from Graph Manager so rollbacks do not corrupt data.
* Version compatibility rules:
  * `major` bumps may introduce breaking schema or API changes and require explicit admin confirmation.
  * `minor` bumps add backward compatible capabilities or surfaces.
  * `patch` bumps contain bug fixes only.
* Extensions must publish migration hooks that translate stored configuration and scheduler manifests during upgrade.

### 8.3 Compatibility matrix

Manifest declares:

| Field | Description |
| --- | --- |
| `requires.platform.min_version` | Minimum backend platform version required. Loader refuses activation below this version. |
| `requires.managers` | List of managers or system services and the minimum capabilities they must expose. |
| `requires.permissions` | Capability names that must exist before extension can run (for example, `system.feed.publish`). |
| `supports.frontend.min_version` | Minimum frontend app version supported. Used for interface validation, not enforced by the backend. |

App Manager persists the matrix and surfaces incompatible extensions via Health Manager.

## 9. Configuration, schema, and storage obligations

### 9.1 Configuration namespace

* Extension configuration keys live under `app.<slug>.*`. Keys must define type, default, min/max, reload semantics, and whether dynamic reload is supported.
* Config Manager validates snapshots before exposing them. Extensions implement `prepare_config(snapshot)` and `commit_config()` hooks mirroring manager behavior. Rejecting a snapshot keeps the previous version active.
* Sensitive configuration (secrets) must be stored as encrypted graph attributes managed via Key Manager, never as plaintext configuration values.

### 9.2 Schema ownership

* Schemas contributed by an extension are owned by the app domain and versioned using semantic identifiers (`app.<slug>.object.v1`). Schema Manager enforces compatibility.
* Extensions declare migration strategies (automatic envelope replay, manual job) and register capabilities required to run migrations.
* Cross-app references require explicit ACL policy and Schema Manager validation. Extensions cannot create new trust boundaries; they must leverage ACL Manager edges defined in `01-protocol/06-access-control-model.md`.

### 9.3 Storage and caching

* Derived caches must rebuild from Graph Manager reads. Caches are optional and cannot store secrets or ACL protected payloads without rechecking authorization on every read.
* Extensions cannot allocate filesystem space outside the sandboxed directories assigned by the runtime. Temporary files must be declared in the manifest with size limits.

## 10. Runtime coordination and resource management

### 10.1 Admission and quotas

* Extension surfaces register DoS Guard hints (cost class, stateful tokens, max outstanding requests). DoS Guard enforces puzzles or throttles before the extension code runs, aligning with `01-protocol/11-dos-guard-and-client-puzzles.md`.
* Extensions must expose backpressure signals to App Manager (for example, queue depth). When pressure exceeds declared thresholds, App Manager may instruct the extension to respond with `429 Too Many Requests` or escalate DoS difficulty.
* Scheduler jobs declare concurrency limits and budgets. Job overruns cause Health Manager to mark the extension degraded and may result in automatic pause.

### 10.2 Dependency health

* Extensions watch Health Manager for dependency readiness. If any declared dependency goes `not_ready`, the extension must stop the corresponding surface and fail closed.
* Extensions publish readiness states: `initializing`, `ready`, `degraded`, `not_ready`, `stopped`. Readiness must reflect the ability to handle new work without data loss.

### 10.3 Resource budgets

* CPU, memory, and storage budgets declared in the manifest allow the runtime to isolate extensions. Exceeding budgets triggers throttling or shutdown.
* Extensions cannot spawn threads outside the runtime pool. Long running work must use asynchronous jobs scheduled through the backend scheduler.

## 11. Observability and diagnostics

* **Logging**: All actions produce structured logs with OperationContext identifiers, capability names, request IDs, execution latency, and manager outcomes. Logs must be emitted via Log Manager and tagged with `app=<slug>`.
* **Events**: Extensions emit events through Event Manager for domain specific notifications. Event descriptors include object references, capability used, and severity.
* **Metrics/Health**: Extensions register readiness and liveness probes with Health Manager (for example, `app.<slug>.extension`). Metrics include request counts, success/failure ratios, DoS hints consumed, job runtimes, queue depths, and cache rebuild counts.
* **Diagnostics hooks**: Extensions support admin-triggered diagnostics endpoints (e.g., `POST /system/ops/extensions/{slug}/diagnostics`). Diagnostics dumps include current configuration version, outstanding jobs, dependency health, last error summary, and DoS telemetry snapshots. Sensitive payloads must be redacted.

Observability requirements ensure that operators can debug extensions using the same tooling as system services.

## 12. Security and trust boundaries

* Extensions inherit the untrusted caller posture described in `02-architecture/01-component-model.md`. Managers validate every request before acting.
* Mutual authentication is mandatory between the extension loader and App Manager. Only signed packages from the owning app are accepted.
* Extensions never access cryptographic keys directly. Key Manager mediates all crypto operations, including signature, encryption, and random number generation.
* Authorization always flows through ACL Manager. Extensions cannot cache ACL decisions without revalidation.
* Secrets (tokens, credentials) are stored only as encrypted graph attributes with ACL protections. Logs or events never contain raw secrets.
* Extensions must document every external dependency (for example, remote API) and run them through Network Manager so DoS Guard can apply outbound throttles.
* Extensions participate in security reviews defined in `05-security/**`, including threat modeling, secure coding checklists, and penetration tests before release.

## 13. Failure handling and recovery

* **Fail closed**: On ambiguous conditions (missing dependency, invalid configuration, schema mismatch), extensions reject the request with a specific protocol error (for example, `ERR_APP_EXTENSION_CONFIG`) and log the cause.
* **Automatic retries**: Background jobs may retry idempotent work using bounded exponential backoff. Retries must respect operation ordering to preserve `01-protocol/07-sync-and-consistency.md`.
* **Crash recovery**: After a crash, the extension must reconstruct state exclusively from Graph Manager, Config Manager, and manager owned stores. Derived caches rebuild deterministically.
* **Dependency failure**: If a dependency goes offline, the extension notes degraded state and halts affected surfaces. It may expose read-only functionality if safe and documented, but write paths must remain disabled until dependencies recover.
* **Upgrade failure**: If activation of a new version fails, App Manager rolls back to the previous signed version and emits `app.<slug>.extension.rollback`. The extension must keep backward compatible data formats to support this scenario.
* **Removal**: Uninstalling an app stops the extension immediately. The extension must flush telemetry, stop scheduler jobs, invalidate outstanding invites or tokens, and confirm no background threads remain. Graph data persists for archival or reinstall purposes.

## 14. Compliance checklist

Before publishing or upgrading an extension, the owning app must prove the following:

1. **Manifest completeness**: Manifest describes version, dependencies, configuration keys, scheduler jobs, resource budgets, capability catalog, and DoS Guard hints. Validated by App Manager.
2. **OperationContext discipline**: Every entry point constructs immutable OperationContext objects with `app_id=<owning app>`, capability names, tracing metadata, and trust posture, per `02-architecture/services-and-apps/05-operation-context.md`.
3. **Manager-only access**: All state mutations flow through Schema, ACL, and Graph Manager in the required order. No direct storage, network, or crypto access exists.
4. **Interface documentation**: HTTP/WebSocket surfaces documented in `04-interfaces/**`, including payload schemas, media types, OperationContext requirements, DoS Guard hints, and deterministic error codes.
5. **Configuration and schema validation**: Configuration keys declared in Config Manager, schema contributions loaded via Schema Manager, migrations scripted as Graph envelopes.
6. **Observability**: Log, Event, and Health Manager integrations implemented. Diagnostics hooks provide actionable insights without exposing secrets.
7. **Security review**: Extension passed threat modeling and secure code review per `05-security/**`. All secrets stored via Key Manager, no plaintext secrets in configuration or logs.
8. **Lifecycle hooks**: Start, stop, quiesce, upgrade, and rollback hooks implemented. Extension can unload cleanly without affecting other applications.
9. **DoS posture**: Surfaces register DoS hints, respect puzzles, and emit abuse telemetry to DoS Guard. Scheduler jobs publish outbound resource estimates.
10. **Recovery drills**: Tested crash recovery, configuration reload failure, schema mismatch, dependency outage, and uninstall flows to confirm fail-closed behavior.

Meeting this checklist demonstrates that the extension behaves like a first-class citizen inside the 2WAY backend while preserving the platform's security and isolation guarantees.
