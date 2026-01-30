



# 08 App Manager

Defines application registration, identity binding, and backend extension wiring. Specifies app registry invariants, lifecycle ordering, and isolation constraints. Defines startup/shutdown behavior and manager interactions for applications.

For the meta specifications, see [08-app-manager meta](../09-appendix/meta/02-architecture/managers/08-app-manager-meta.md).


## 1. Conceptual model

An application is a locally registered system entity that defines a namespace, authorship scope, and isolation boundary. An application is identified by:

* A unique, stable string slug.
* A locally assigned numeric app_id.
* A dedicated application identity represented in the system graph.
* Zero or one backend extension service module.

Applications are namespaces and authority scopes only. They do not define protocol behavior, do not modify core manager semantics, and do not act as execution sandboxes. These properties instantiate the application identifier semantics defined in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).

Application boundaries enforce the cross object isolation defined by the protocol object model. No application may implicitly access or mutate another application's data per the application domain isolation rules in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).

## 2. App registry

### 2.1 Persistent registry

The [App Manager](08-app-manager.md) maintains a persistent registry stored in the backend database. Each registry entry includes:

* app_id
* slug
* title
* version
* creation timestamp

The registry is the sole authoritative source of application existence and identity. No other manager may declare, mutate, or infer application identifiers.

The registry represents the local instantiation of the Application Identifier concept defined by the protocol identifier and namespace rules in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).

### 2.2 Registry invariants

The following invariants apply to the application registry:

* Each slug maps to exactly one app_id.
* Each app_id maps to exactly one slug.
* app_id values are unique and never reused.
* Registry entries are append only.
* Removal or deactivation of an application does not delete graph data.
* An app_id must not appear in [OperationContext](../services-and-apps/05-operation-context.md) instances, schemas, or envelopes until its registry entry exists.
* Lookup of a non existent app_id is a structural error.

Violation of these invariants is a fatal configuration error. These guarantees restate the declaration-before-use, uniqueness, and isolation rules from [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md) and ensure that every `app_id` referenced by envelopes in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and by objects in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) refers to a registered application.

## 3. Application identity binding

Each application has a corresponding identity represented in the system graph.

The [App Manager](08-app-manager.md) ensures:

* An application identity Parent exists for every registered application.
* The application identity contains a valid pubkey Attribute.
* The identity Parent resides in `app_0`, the system application namespace defined by [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* The application identity is stable across restarts.
* The application identity is uniquely bound to its app_id.

Application identities are represented as Parents with cryptographic pubkey Attributes and follow the same identity rules as node and user identities per [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).

Application identities are used for:

* Application scoped ACL evaluation.
* Authorship attribution in graph operations.
* Distinguishing user intent from application intent in [OperationContext](../services-and-apps/05-operation-context.md) instances.
* App level signing and verification when required by other managers.

Registration is not complete until the identity Parent and pubkey Attribute are persisted.

## 4. Application registration lifecycle

### 4.1 Registration

During application registration, the [App Manager](08-app-manager.md) performs the following actions in strict order:

* Allocate a new `app_id` per the uniqueness and monotonicity constraints in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Persist the registry entry so declaration-before-use rules in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md) are upheld.
* Declare the application identifier as globally valid within the backend per [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Instruct the [Storage Manager](02-storage-manager.md) to create all per application tables so the per-app data isolation invariants in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) are satisfied.
* Ensure an application keypair exists via the [Key Manager](03-key-manager.md) per [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Ensure the application identity Parent and pubkey Attribute exist in the system graph, satisfying [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Make the application available for schema loading and [OperationContext](../services-and-apps/05-operation-context.md) binding so that [OperationContext](../services-and-apps/05-operation-context.md) construction described in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) and the `app_id` field requirements in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) have a registered target.

Registration is idempotent per slug. Re registration of an existing slug must resolve to the same app_id and identity.

### 4.2 Resolution and lookup

The [App Manager](08-app-manager.md) provides lookup facilities for:

* slug to app_id resolution.
* app_id to slug resolution.
* retrieval of immutable application metadata.

Registry backed lookup is the only valid mechanism for binding slugs to app_id values for routing, [OperationContext](../services-and-apps/05-operation-context.md) construction, schema compilation, and sync metadata. This ensures that the `app_id` field required in operation records by [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and the application scoped object guarantees in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) are interpreted only through registered identifiers.

Failure to resolve an application is treated as a configuration or routing error and must fail closed.

## 5. Backend extension services

### 5.1 Definition

An application may provide an optional backend extension service. A backend extension service is a backend module bound to exactly one application slug and app_id.

Backend extension services exist to perform backend only tasks such as indexing, heavy computation, or secure validation. They do not define protocol behavior.

### 5.2 Loading and wiring

At backend startup, the [App Manager](08-app-manager.md) performs the following steps:

* Discover declared backend extension modules.
* Resolve each module to a registered application slug.
* Reject any extension whose slug is not registered.
* Instantiate each extension service exactly once.
* Wire each extension with explicit references to permitted managers so that authorization enforcement remains confined to the managers defined in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Register extension service endpoints with the HTTP layer.
* Ensure all extension calls originate through [OperationContext](../services-and-apps/05-operation-context.md) instances, consistent with the [OperationContext](../services-and-apps/05-operation-context.md) usage defined in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) and [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).

Backend extension services are inactive unless explicitly registered and wired.

### 5.3 Permitted interactions

Backend extension services may interact only through the following managers:

* [Graph Manager](07-graph-manager.md).
* [Schema Manager](05-schema-manager.md).
* [ACL Manager](06-acl-manager.md).
* [Storage Manager](02-storage-manager.md) for constrained reads.
* [Log Manager](12-log-manager.md).
* [Event Manager](11-event-manager.md).

The following interactions are explicitly forbidden:

* Direct database access.
* Direct key access.
* Direct network access.
* Direct inter extension communication.
* Invocation outside an [OperationContext](../services-and-apps/05-operation-context.md).

These boundaries preserve the authorization layering rules in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

### 5.4 Isolation guarantees

The [App Manager](08-app-manager.md) guarantees:

* Extension services cannot access data belonging to other applications without ACL approval.
* Extension services cannot modify protocol behavior or core manager invariants.
* Failure or misbehavior of an extension service cannot corrupt core managers.
* Extension services cannot impersonate other applications.

These guarantees restate the app domain and isolation rules defined in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md), [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md), and the authorization posture in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

## 6. OperationContext integration

For any request originating from an application, the [App Manager](08-app-manager.md) ensures:

* The correct app_id is attached to the [OperationContext](../services-and-apps/05-operation-context.md).
* The correct application identity is associated with the request.
* Application impersonation across slugs is impossible.

The [App Manager](08-app-manager.md) does not construct [OperationContext](../services-and-apps/05-operation-context.md) instances. [OperationContext](../services-and-apps/05-operation-context.md) creation occurs in the HTTP layer per [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) and [04-interfaces/**](../../04-interfaces/). The [App Manager](08-app-manager.md) validates and enforces correct application binding before the context defined in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) is consumed by other managers.

## 7. Startup and shutdown behavior

### 7.1 Startup ordering

The [App Manager](08-app-manager.md) must initialize before:

* [Schema Manager](05-schema-manager.md) loads application schemas.
* [Auth Manager](04-auth-manager.md) resolves application scoped requests.
* [Graph Manager](07-graph-manager.md) accepts application authored operations.

The [App Manager](08-app-manager.md) must initialize after:

* [Storage Manager](02-storage-manager.md) is ready.
* [Key Manager](03-key-manager.md) is ready.

### 7.2 Shutdown behavior

During shutdown, the [App Manager](08-app-manager.md):

* Stops routing requests to backend extension services.
* Releases references to extension service instances.
* Performs no graph mutation.
* Requires no persistence actions.

Shutdown must not delete registry entries or application data.

## 8. Interactions with other components

### 8.1 Inputs

The [App Manager](08-app-manager.md) consumes:

* Persistent registry state via [Storage Manager](02-storage-manager.md).
* Key material via [Key Manager](03-key-manager.md).
* Configuration data required for startup ordering.

These inputs allow the [App Manager](08-app-manager.md) to satisfy the identifier guarantees in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md) and the identity requirements in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).

### 8.2 Outputs

The [App Manager](08-app-manager.md) provides:

* app_id resolution to HTTP routing and [Auth Manager](04-auth-manager.md).
* Backend extension service references to the HTTP layer ([04-interfaces/**](../../04-interfaces/)).
* Application identity identifiers to [OperationContext](../services-and-apps/05-operation-context.md) consumers.

These outputs satisfy the envelope construction requirements in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and the authorization inputs that rely on `app_id` and identity context defined in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

### 8.3 Trust boundaries

The [App Manager](08-app-manager.md) is trusted to:

* Bind application slugs to identities correctly.
* Enforce application isolation at wiring boundaries.

Backend extension services are untrusted and sandboxed.

These trust boundaries mirror the authorization posture documented in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

## 9. Failure and rejection behavior

The [App Manager](08-app-manager.md) must reject or fail when:

* An unknown application slug is requested.
* An app_id is referenced that does not exist in the registry.
* Registry state is inconsistent or corrupted.
* Application identity material is missing or invalid.
* Backend extension wiring violates declared constraints.

Failure handling rules:

* Invariant violations cause hard startup failure.
* Runtime lookup failures result in immediate request rejection.
* Partial or degraded application states are not permitted.

  All failures must fail closed, consistent with the error handling posture mandated by [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

## 10. Invariants and guarantees

Across all components and boundaries defined in this file, the following invariants and rememberable guarantees hold:

* Each application has exactly one stable `app_id`, satisfying the namespace guarantees in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Each `app_id` is bound to exactly one application identity as required by [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Application identities are cryptographically anchored per [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Application boundaries are enforced regardless of caller or execution context, matching the requirements in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md) and [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* Backend extension services cannot bypass managers, preserving the authorization ordering in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Application registry state is authoritative and local so that declaration rules in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md) remain satisfied.
* Application lifecycle changes do not delete or mutate graph data, upholding the structural persistence rules in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).

These guarantees hold regardless of caller, execution context, input source, or peer behavior.

## 11. Explicitly allowed behaviors

The following behaviors are explicitly allowed:

* Local registration of applications by administrative authority, consistent with the declaration rules in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Backend extension services performing application scoped queries through managers while respecting the authorization boundaries in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Applications participating in multiple sync domains when defined elsewhere, provided the sync semantics in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) are followed.
* Application identities being referenced in ACL rules, honoring the identity guarantees in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md) and the ACL semantics in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

## 12. Explicitly forbidden behaviors

The following behaviors are explicitly forbidden:

* Dynamic application registration through sync, which would violate [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) and the declaration rules in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Remote creation, modification, or deletion of applications, because application authority stays local per [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Reuse of `app_id` values, forbidden by [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Cross application access without ACL approval, which breaks the isolation requirements in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Application controlled mutation of the registry, which would bypass the guarantees in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Backend extension services accessing raw storage, keys, or network directly, which would circumvent the trust boundaries enforced by [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md) and [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).

Any implementation permitting these behaviors is non compliant.
