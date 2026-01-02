
# 01 Services vs Apps

## 1. Purpose and scope

This specification defines how backend services and applications relate inside the 2WAY PoC architecture. It explains why services and applications are separate architectural constructs, enumerates the invariants that keep them isolated, and provides implementation rules that every conforming backend must follow. It binds the component model, manager responsibilities, and OperationContext requirements into a single consumable contract that backend implementers must follow when writing system services, optional app extensions, or frontend applications that target this backend.

This document does not redefine schemas, ACL policy, serialization, cryptography, or other protocol-level mechanics. Those topics remain governed by their dedicated specifications, and this document consumes them without restating their guarantees.

This specification references the following documents:

* `01-protocol/**`
* `02-architecture/01-component-model.md`
* `02-architecture/managers/00-managers-overview.md`
* `02-architecture/managers/**`
* `02-architecture/services-and-apps/05-operation-context.md`

Those documents remain normative for their respective domains.

## 2. Terminology and classification

* **Service** : A backend module that executes inside the node process, translates high level intent into manager calls, and never owns protocol invariants. Two classes exist: system services and app extension services.
* **System service** : A mandatory service that ships with every node. System services implement shared functionality (bootstrap, provisioning, feeds, sync helpers, etc.). They have no owner app and cannot be removed by app uninstallations.
* **App extension service** : An optional backend service bound to exactly one registered application slug and `app_id`. These services only exist if an application declares backend code. They must be unloadable without affecting other applications or the core platform.
* **Application (app)** : A namespace and identity registered through App Manager. Every app owns schemas, ACL policy, and UI/UX semantics within its domain. An app may have zero or one backend extension service plus any number of frontend experiences.
* **Frontend app** : Presentation layer code that uses backend APIs or sync flows. Frontend apps execute outside the backend process, are always untrusted, and must cross Network, Auth, ACL, and Schema Manager before affecting state.
* **OperationContext** : The per request structure that carries user identity, device identity, app identity, trust posture, requested capability, and logging metadata (detailed in `02-architecture/services-and-apps/05-operation-context.md`). All services and apps must construct or consume OperationContext faithfully.

The following table summarizes the primary distinctions:

| Dimension | System service | App extension service | Application / Frontend |
| --- | --- | --- | --- |
| Trust level | Runs inside backend but untrusted by managers | Same as system service | Fully untrusted by backend |
| Ownership | Platform | Single app | Single app |
| Lifecycle | Always present | Optional, installed with app | Optional, user installed |
| State authority | None (delegates to managers) | None | None |
| Isolation boundary | Service boundary only | App domain boundary | App domain boundary plus frontend trust boundary |
| Removal impact | Requires migration or replacement | Must be removable without global impact | User choice |

## 3. Architectural positioning

1. Managers enforce protocol invariants. Services, regardless of class, are orchestration layers that assemble manager calls. Apps own UX and policy semantics but never mutate manager state directly.
2. Apps define namespaces, ACL policy, schemas, and UI semantics. A backend service may exist without an app (system service) or be tethered to exactly one app (extension), but an app may also live without any backend code (frontend only experience).
3. The separation is structural: services run in process but are still treated as untrusted by managers. Apps, including backend extensions, never get privileged access to storage, crypto keys, or network sockets. Violations fail closed and are observable.
4. OperationContext ties apps, services, and managers together. Every service invocation must name an application domain (often `app_0` for system work) even when the caller is a system service. Frontend apps must provide enough context for the backend to bind an OperationContext before invoking services.
5. Deployments must ensure services and apps evolve independently. A service upgrade cannot assume frontend behavior, and frontend updates cannot change backend invariants.

## 4. Service classes and invariants

### 4.1 System services

System services implement functionality that is required for every conforming node, such as account provisioning, identity graph helpers, base feeds, sync planners, or administrative APIs. Architectural requirements include:

* **Ownership** : System services live in the system application namespace (`app_0`). App Manager still registers them so that OperationContext binding and logging provide deterministic app identifiers.
* **Initialization** : They start immediately after managers finish initialization (`02-architecture/managers/00-managers-overview.md`). Services block readiness until their dependencies declare readiness. Failure to start is fatal.
* **Dependency rules** : System services may depend on managers and other system services, but circular service dependencies are forbidden. If one system service needs data from another, the data must be exposed via manager read APIs or OperationContext-driven calls to avoid hidden channels.
* **API exposure** : System services expose HTTP/WebSocket endpoints or internal RPC endpoints only through the interface layer defined in `04-interfaces/**`. They cannot open sockets or background threads that bypass Network Manager.
* **Observability** : They must emit structured logs through Log Manager and register health checks through Health Manager so that backend supervisors can determine readiness and liveness.
* **Upgrade path** : Since they are mandatory, system services must support rolling schema or ACL migrations by coordinating with Schema Manager and Graph Manager explicitly.

### 4.2 App extension services

App extension services extend backend behavior for a specific application. Requirements:

* **Binding** : Each extension is bound to a slug/app_id pair resolved by App Manager. The binding is immutable for the lifetime of the node.
* **Loading** : App Manager is the only component allowed to instantiate extension services. Modules declare metadata (slug, version, capabilities, minimum manager set) and App Manager wires them after verifying registration and dependencies.
* **Isolation** : Extension services run within their app's domain. All OperationContext instances created by extension services must name the owning `app_id`. They cannot use other app identifiers unless ACL policy explicitly grants cross-app rights and Graph Manager enforces them.
* **Removability** : Uninstalling an app unloads its extension service. Extensions must tolerate being stopped between requests and may not hold global locks that block the backend.
* **Fault containment** : App Manager must be able to disable a faulty extension while leaving the rest of the backend operational. Extensions must therefore expose a stop hook and avoid shared memory outside their module.
* **Capability limits** : Extension services cannot: register system services, claim system app identifiers, call other extensions directly, or declare their own trust boundaries.

### 4.3 Shared service requirements

Regardless of class, every service must comply with the following rules (restating the component model and manager specifications):

1. **OperationContext discipline** : Services must construct a complete OperationContext for every manager invocation, including caller identity, device identity, app identity, capability intent, and request correlation metadata. Missing or malformed context is a rejection reason.
2. **Manager-only state access** : Services never access SQLite, key files, or network sockets; only Storage Manager, Key Manager, and Network Manager may do so. Services call the managers’ public methods.
3. **Fail-closed posture** : Ambiguous conditions result in rejection, not default success. Services must bubble up manager rejections unchanged so that frontend apps see authoritative failures.
4. **Concurrency** : Services may spawn worker tasks but must never bypass the serialized write path. Any background task that mutates state must funnel its work through Graph Manager under a fresh OperationContext.
5. **Configuration** : Services read configuration solely via Config Manager. The configuration contract must be declared so deployment tooling knows which values are required.
6. **Observability** : Log Manager is mandatory for audit trails; Health Manager is mandatory for component liveness; Event Manager is optional but recommended for emitting domain events.

### 4.4 Forbidden service behaviors

* Defining new trust boundaries or authorization shortcuts outside ACL Manager.
* Acting on partially validated envelopes or OperationContext data.
* Persisting shadow copies of graph state or caching derived data without replaying on restart (see `02-architecture/04-data-flow-overview.md` for derived data rules).
* Calling into frontend code or relying on UI state to preserve correctness.
* Invoking remote peers directly or opening sockets; all outbound or inbound network I/O must flow through Network Manager and DoS Guard Manager.

## 5. Application layers and responsibilities

### 5.1 Application identity and namespace

Applications exist independently of services. Registration, slug assignment, `app_id` allocation, and identity binding are the sole domain of App Manager (`02-architecture/managers/08-app-manager.md`). Applications provide:

* A namespace for graph objects, schema identifiers, and ACL policies.
* Authorship attribution that distinguishes user intent from app automated work.
* Policy hooks that services may invoke but not redefine.
* A mapping between frontend bundles and backend capabilities.

Applications are authoritative for their own schemas and ACL rules but must obey system constraints (e.g., no schema that bypasses required auditing fields). Schemas must be compiled and loaded through Schema Manager even when authored by apps.

### 5.2 Backend extension binding

If an application declares backend logic, it ships an extension module that App Manager wires into the backend. Implementation rules:

* Extension modules declare dependency metadata, including manager APIs they require. Missing dependencies are a fatal wiring error.
* Extension modules must be versioned. Upgrades require compatibility shims or explicit data migration steps executed through Graph Manager.
* Module initialization occurs after the owning application schema loads but before the backend advertises readiness. Initialization may enqueue background work but cannot mutate graph state until OperationContext creation is possible.

### 5.3 Frontend applications

Frontend apps (native, mobile, CLI, or web) consume backend APIs or sync flows defined by system or extension services. Requirements:

* Frontend apps never run inside the backend process and are treated as fully untrusted clients. They must authenticate through Auth Manager, solve DoS puzzles when required, and present signed envelopes when acting on behalf of a remote node.
* Frontend apps operate strictly through published APIs or through sync packages defined by State Manager. Any attempt to open privileged channels is rejected.
* Frontend apps must track the `app_id` they belong to and send it with every request, enabling the backend to bind OperationContext and enforce ACL rules.
* Frontend apps may be multi-surface (e.g., local UI + remote automation) but all surfaces share the same app identity and backend permissions.

### 5.4 App-service coordination

* Apps specify which services handle their backend requests. System services may refuse app traffic if schemas or ACLs are misconfigured.
* Services expose explicit APIs that name the app domains they are willing to serve. For example, a social feed system service may accept requests from any app that adheres to a given schema contract, whereas a ledger extension service only accepts requests from its own app.
* Apps must not assume that a service exists. Frontend apps must handle `503 Service Unavailable` or explicit rejection responses when a required extension is missing.

## 6. Interaction model

### 6.1 Local frontend to backend request flow

1. Frontend app issues a request to an HTTP/WebSocket endpoint owned by a service.
2. Interface layer authenticates the caller via Auth Manager, building an initial OperationContext skeleton (user, device, session, app identifier).
3. Service-specific middleware enriches the OperationContext with capability descriptors (requested action, schema references, rate-limit tokens).
4. Service runs domain validation. Failures at this stage do not hit managers.
5. Service invokes managers in the required order (Schema -> ACL -> Graph -> Storage -> Event) per the data flow rules in `02-architecture/04-data-flow-overview.md`.
6. Manager responses propagate back to the frontend app unchanged, with logging and metrics recorded through Log Manager and Health Manager.

### 6.2 Backend extension initiated work

Extensions may run scheduled work (e.g., a digest generator). Requirements:

* Work must be triggered by timers owned by the backend scheduler, not by ad hoc threads that bypass Health Manager visibility.
* Each job constructs a synthetic OperationContext that clearly states it is automation (e.g., `actor_type=app_service`). ACL Manager must see the owning app identity and enforce policy accordingly.
* Jobs must respect DoS Guard quotas when enqueueing tasks that will result in outbound network traffic via Network Manager.

### 6.3 Remote peer interactions

When remote nodes send sync packages tied to a particular application:

* State Manager validates sync metadata, then hands OperationContext construction off to the receiving service or extension.
* Services must not assume remote peers share the same schema versions. Schema Manager and ACL Manager enforce compatibility and access rules, and the service either rejects the package or invokes Graph Manager for permissible mutations.
* Services cannot respond directly; Network Manager owns transmission. Services hand responses to State Manager or Event Manager depending on the flow.

## 7. OperationContext authorship rules

OperationContext unifies services and apps. Mandatory rules (expanding on `02-architecture/services-and-apps/05-operation-context.md` once implemented):

1. **App identity presence** : Every OperationContext must include `app_id`. System services use `app_0`. Extension services use their owning `app_id`. Frontend requests must supply the app identifier before any other processing.
2. **Caller identity** : OperationContext distinguishes between the user/device making the request and the app/service assisting. Even automated jobs record the app identity to preserve authorship.
3. **Capability stamping** : OperationContext includes the specific capability or verb the service is attempting (e.g., `capability=feed.publish`). ACL Manager evaluates capabilities alongside graph relationships to determine access.
4. **Traceability** : Correlation IDs, timestamps, and service identifiers are required so Log Manager can reconstruct flows. Lack of traceability is a structural error.
5. **Immutability** : Once constructed, OperationContext is immutable. Services pass it verbatim to managers. Any attempt to mutate mid-flight is rejected by instrumentation wrappers.

## 8. Data ownership and cross-app behavior

* Graph data belongs to the app domain where it was created, even when a system service orchestrated the mutation. Cross-app reads or writes require explicit ACL policy and Schema Manager validation. This enforces the isolation rules in `01-protocol/02-object-model.md`.
* Services may offer shared functionality that spans apps (e.g., a messaging service) but the data always resides in a concrete app domain chosen at object creation. Shared services must not create hidden global namespaces.
* When services aggregate data across apps, they must ensure OperationContext expresses the requesting app so ACL Manager can mask unauthorized rows.
* Ratings and suppression signals remain app scoped. Services cannot delete or mutate another app's objects; they can only request Ratings or new objects that reference targeted objects per the data flow spec.

## 9. Lifecycle and deployment ordering

### 9.1 Startup sequence

1. Managers initialize and declare readiness (Config, Storage, Key, Schema, ACL, Graph, App, etc.).
2. App Manager loads application registry, binds identities, and prepares backend extension metadata.
3. System services start in a deterministic order agreed upon by the deployment (e.g., Auth-facing services before sync services). Each service must declare dependencies explicitly.
4. App extension services load only after their owning application schema passes validation. Any failure aborts backend startup or results in the extension being skipped with an audit log entry.
5. Frontend endpoints are registered only after the owning service declares readiness. Partially initialized services must not receive traffic.

### 9.2 Shutdown sequence

* Services receive a stop signal and must quiesce, rejecting new work while completing in-flight operations within a bounded timeout.
* Extension services must flush derived caches and persist checkpoint metadata via Storage Manager if they need fast resume.
* App Manager marks extensions as stopped before managers shut down so no background job attempts to run without manager support.

### 9.3 Installation and upgrade

* Installing an app registers schemas and ACL policies first, then loads backend code. Any schema error halts installation before code executes.
* Upgrades must be explicitly versioned. Services must support coexistence of requests from older frontend versions by handling backwards-compatible payloads or rejecting unsupported versions with actionable errors.
* Removing an app unloads its extension service, revokes scheduled jobs, and leaves graph data intact. No other app or service may reuse the freed `app_id`.

## 10. Security posture and failure handling

* All services treat frontend input as hostile even when called from the same device. Validation occurs before manager invocation, and failures propagate unchanged.
* App extension services have no implicit elevation. They must pass through the same ACL and schema gates as system services.
* DoS Guard Manager protects services from abusive clients. Services publish cost hints (e.g., read heavy vs write heavy) so the DoS layer can enforce quotas per app and per user.
* Any attempt by an app or service to bypass manager APIs is a fatal configuration error and must stop the backend from accepting traffic until corrected.
* Services must clearly categorize failures: structural (schema), authorization (ACL), sequencing (Graph), storage, or resource limits. This classification is surfaced in OperationContext for observability.

## 11. Observability, configuration, and policy inputs

* Services declare required configuration keys, default values, and dynamic reload behavior through Config Manager. Hot reload is optional but, when supported, services must revalidate inputs before applying them.
* Every service registers a health endpoint with Health Manager, exposing: readiness (dependencies satisfied), liveness (event loop responsive), and degraded modes (e.g., running without optional peer connections).
* Structured logs must include `app_id`, service name, OperationContext correlation ID, and failure classification. Logs never contain private keys or raw secrets.
* Services emitting domain events must document schemas for those events so downstream subscribers (often frontend apps) can parse them deterministically.
* Policy inputs (feature flags, ACL templates, schema migrations) are delivered as graph data governed by Schema and ACL rules. Services read them using Storage Manager rather than ad hoc configuration files.

## 12. Implementation checklist

Before shipping a service or app, verify the following:

1. **Registration** : App exists in App Manager registry (`app_id` assigned, identity persisted). System services declare themselves under `app_0`.
2. **OperationContext** : Every code path constructs immutable OperationContext objects with user/device/app identity, capability, trace metadata, and trust posture.
3. **Manager usage** : All state mutations enter Graph Manager, all reads go through Storage Manager with ACL enforcement, and no direct database or filesystem access exists.
4. **Schema/ACL alignment** : Required schemas are loaded through Schema Manager and ACL rules are declared so ACL Manager can authorize service actions.
5. **API surface** : HTTP/WebSocket routes list accepted payload schemas, capability names, and expected responses. Remote peers receive equivalent documentation for sync endpoints.
6. **Observability** : Health checks, structured logs, and metrics exist; failure modes are categorized and documented.
7. **Lifecycle hooks** : Start/stop hooks exist, extension services can be unloaded cleanly, and system services cooperate with rolling upgrades.
8. **DoS posture** : Rate limits or client puzzles are registered with DoS Guard Manager where appropriate, and services refuse to run expensive operations without quotas.
9. **Removability** : App extension services can be removed without affecting other applications, leaving graph data intact for archival or reinstall purposes.
10. **Documentation** : The service or app declares how frontend apps should integrate, including required scopes, OperationContext expectations, and recovery semantics.

Adhering to this specification ensures that services and applications remain decoupled yet interoperable, enforcing the structural guarantees that make 2WAY resilient, local-first, and fail-closed by construction.
