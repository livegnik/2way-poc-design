



# 08 App Manager

## 1. Purpose and scope

This document specifies the App Manager component. The App Manager owns app registration, app identity binding, per app storage initialization, and controlled wiring of backend extension services. It defines how apps exist as first class system entities and how they are resolved and constrained within the backend.

This specification applies only to backend app lifecycle management and app identity resolution. It does not define frontend behavior, schemas, permissions, APIs, or application logic.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Maintaining the authoritative registry of installed apps.
* Assigning stable numeric app identifiers.
* Binding app slugs to app identities.
* Initializing per app database structures.
* Loading and wiring app specific backend extension services.
* Providing app metadata and resolution services to other backend components.
* Ensuring app identity presence and consistency in the system graph.
* Enforcing strict isolation between apps at the manager wiring level.
* Declaring application identifiers before Graph Manager, Schema Manager, or OperationContext consumers reference them, consistent with the identifier semantics defined by the protocol.

This specification does not cover the following:

* Schema definition or validation.
* Access control decisions.
* Graph mutations.
* HTTP or WebSocket routing.
* Network communication.
* Cryptographic operations beyond delegation to Key Manager.
* Frontend app lifecycle or UI concerns.
* App business logic or domain semantics.

## 3. Conceptual model

An app is a locally registered system entity identified by:

* A unique string slug.
* A locally assigned numeric app_id.
* A dedicated app identity represented in the system graph.
* An optional backend extension service.

Apps are namespaces and authority scopes, and their `app_id` boundaries enforce the cross-object isolation defined in `01-protocol/02-object-model.md`. They are not execution sandboxes and they do not define new protocol behavior.

## 4. App registry

### 4.1 Persistent registry

The App Manager maintains a persistent app registry stored in the backend database. Each registry entry includes:

* app_id
* slug
* title
* version
* creation metadata

The registry is the sole authoritative source for app existence and resolution.

It is the local instantiation of the Application Identifier class defined in `01-protocol/01-identifiers-and-namespaces.md`, and no other component may declare or mutate those identifiers.

### 4.2 Registry invariants

The following invariants apply to the app registry:

* Each slug maps to exactly one app_id.
* app_id values are unique and never reused.
* Registry entries are append only.
* Removal of an app from the registry does not delete graph data.
* An app_id MUST NOT appear in OperationContext, schema records, or envelope metadata until its registry entry exists.
* Lookup of an app_id that is not in the registry is treated as a structural error consistent with `ERR_STRUCT_INVALID_IDENTIFIER` in `01-protocol/09-errors-and-failure-modes.md`.

Violation of these invariants is a fatal configuration error.

## 5. App identity binding

Each app has a corresponding identity represented in the system graph.

The App Manager ensures:

* An app identity Parent exists for every registered app.
* The app identity contains a valid pubkey Attribute.
* The identity Parent resides in `app_0` per the identity specification.
* The app identity is stable across restarts.
* The app identity is uniquely bound to its app_id.

App identities are represented as Parents in `app_0` with at least one bound pubkey Attribute, matching the requirements in `01-protocol/05-keys-and-identity.md`. The App Manager completes registration only after Key Manager persists those graph objects.

App identities are used for:

* App level ACL evaluation.
* App authorship attribution in graph operations.
* Distinguishing user intent from app intent in OperationContext.

## 6. App registration lifecycle

### 6.1 Registration

During app registration, the App Manager performs the following actions:

* Allocate a new app_id.
* Declare the application identifier before Graph Manager, Schema Manager, or the HTTP layer bind any OperationContext to the app, satisfying the explicit declaration rule in `01-protocol/01-identifiers-and-namespaces.md`.
* Insert an entry into the app registry.
* Instruct Storage Manager to create all per app tables.
* Ensure an app identity and keypair exist via Key Manager.
* Ensure the app identity Parent is present in the system graph.

Registration is idempotent per slug. Re registration of an existing slug must resolve to the same app_id.

### 6.2 Resolution and lookup

The App Manager provides lookup facilities for:

* slug to app_id resolution.
* app_id to slug resolution.
* retrieval of immutable app metadata.

Registry backed lookup is the sole mechanism that binds a slug to an `app_id` for routing, OperationContext binding, and schema compilation, satisfying the explicit declaration rule in `01-protocol/01-identifiers-and-namespaces.md`.

Failure to resolve an app is treated as a configuration or routing error.

## 7. Backend extension services

### 7.1 Definition

An app may provide an optional backend extension service. A backend extension service is a backend module bound to exactly one app slug.

### 7.2 Loading and wiring

At backend startup, the App Manager:

* Discovers declared backend extension modules.
* Resolves each module to a registered app slug.
* Instantiates the extension service exactly once.
* Wires the service with explicit references to permitted managers.
* Routes every extension call path through the HTTP layer so that envelopes are submitted only via OperationContext instances, as mandated by `01-protocol/03-serialization-and-envelopes.md`.

Backend extension services are inactive unless explicitly registered.

### 7.3 Permitted interactions

Backend extension services may interact only through:

* Graph Manager.
* Schema Manager.
* ACL Manager.
* Storage Manager for constrained reads.
* Log Manager.
* Event Manager.

Direct database access is forbidden.

Direct key access is forbidden.

Direct network access is forbidden.

### 7.4 Isolation guarantees

The App Manager guarantees:

* Backend extension services cannot access other apps data without ACL approval.
* Backend extension services cannot modify protocol behavior.
* Failure or misbehavior of an extension service cannot corrupt core managers.

## 8. OperationContext integration

For any request originating from an app, the App Manager ensures:

* The correct app_id is attached to the OperationContext.
* The correct app identity is associated with the request.
* App impersonation across slugs is impossible.

The App Manager validates app identity resolution but does not construct OperationContext instances. Per `01-protocol/03-serialization-and-envelopes.md`, OperationContext objects originate in the HTTP layer for both frontend and backend extension services, and the App Manager enforces that wiring so Graph Manager only receives contexts derived through that boundary.

## 9. Interactions with other components

### 9.1 Inputs

The App Manager consumes:

* Persistent registry state via Storage Manager.
* Key material via Key Manager.
* Configuration data required for startup ordering.

### 9.2 Outputs

The App Manager provides:

* app_id resolution to HTTP routing and Auth Manager.
* Backend extension service references to the HTTP layer.
* App identity identifiers to Graph Manager through OperationContext.

### 9.3 Trust boundaries

The App Manager is trusted to:

* Bind app slugs to identities correctly.
* Prevent cross app confusion at the routing and wiring layer.

Backend extension services are not trusted and are sandboxed by design.

## 10. Failure and rejection behavior

The App Manager must reject or fail when:

* An unknown app slug is requested.
* An app_id is referenced that does not exist in the registry (surfacing `ERR_STRUCT_INVALID_IDENTIFIER` as defined in `01-protocol/09-errors-and-failure-modes.md`).
* Registry state is inconsistent or corrupted.
* App identity material is missing or invalid.
* Backend extension wiring violates declared constraints.

Failure handling rules:

* Invariant violations cause hard startup failure.
* Runtime lookup failures result in immediate request rejection.
* Partial or degraded app states are not permitted.

## 11. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* Each app has exactly one stable app_id.
* Each app_id is bound to exactly one app identity.
* App identities are cryptographically anchored.
* App boundaries are enforced independently of caller or execution context.
* Backend extension services cannot bypass managers.
* App registry state is authoritative and local.
* App lifecycle changes do not delete or mutate graph data.

These guarantees must hold regardless of caller, execution context, input source, or peer behavior.

## 12. Explicitly allowed behaviors

The following behaviors are explicitly allowed:

* Local registration of apps by administrative authority.
* Backend extension services performing app scoped queries through managers.
* Apps participating in multiple sync domains if defined elsewhere.
* App identities being referenced in ACL rules.

## 13. Explicitly forbidden behaviors

The following behaviors are explicitly forbidden:

* Dynamic app registration through sync.
* Remote creation or deletion of apps.
* Reuse of app_id values.
* Cross app access without ACL approval.
* App controlled mutation of the app registry.
* Backend extension services accessing raw storage, keys, or network.

Any implementation permitting these behaviors is non compliant.

## 14. Summary

The App Manager is a registry and wiring authority. It defines how apps exist, how they are identified, and how they are isolated. It does not implement protocol logic or app behavior. Its correctness underpins app isolation, ACL semantics, and long term system integrity.
