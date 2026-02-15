



# 01 Identifiers and Namespaces

Defines identifier classes and namespace rules for the 2WAY protocol. Specifies identifier invariants, uniqueness, immutability, and resolution rules. Enumerates allowed/forbidden identifier behaviors and failure handling.

For the meta specifications, see [01-identifiers-and-namespaces meta](../10-appendix/meta/01-protocol/01-identifiers-and-namespaces-meta.md).

## 1. Identifier classes

### 1.1 Identity identifiers

An identity identifier represents a principal that can author operations.

Principals include:

* Users.
* Backend services.
* Applications when acting as signing entities.

Properties:

* Each identity identifier corresponds to exactly one [Parent](02-object-model.md) object in [app_0](05-keys-and-identity.md).
* Each identity identifier is anchored to one or more public keys via [Attributes](02-object-model.md).
* Identity identifiers are immutable for the lifetime of the Parent.
* Identity identifiers are unique within a node. They are not assumed to be globally unique across nodes.

Invariants:

* An identity identifier MUST NOT be reassigned.
* An identity identifier MUST NOT be reused.
* An identity identifier MUST always resolve to exactly one owning Parent.
* Any envelope or sync package that references an unknown identity identifier is rejected.

Guarantees:

* Authorship attribution is stable.
* Impersonation through identifier reuse is structurally prevented.

### 1.2 Device identifiers

A device identifier represents a device acting on behalf of an identity.

Properties:

* Device identifiers are represented as [Parents](02-object-model.md) linked to an identity Parent.
* Device identifiers are unique within a node.
* Device identifiers may carry scoped authority defined by typed [Edges](02-object-model.md).
* Device identifiers may be independently revoked.

Invariants:

* A device identifier MUST be linked to exactly one identity identifier.
* A device identifier MUST NOT exist without an owning identity.
* A device identifier MUST NOT exceed the authority explicitly granted to it.

Guarantees:

* Device compromise impact is limited to its granted scope.
* Device authority is explicit and auditable.

### 1.3 Application identifiers

An application identifier represents an application domain.

Properties:

* Application identifiers define namespace boundaries for [schemas](02-object-model.md), [object types](02-object-model.md), [ratings](02-object-model.md), and [domains](07-sync-and-consistency.md).
* `app_id` is a node-local numeric identifier allocated and owned by [App Manager](../02-architecture/managers/08-app-manager.md).
* `app_slug` is the stable string identifier used for routing and configuration ([definitions](../00-scope/03-definitions-and-terminology.md)).
* Application identifiers are declared explicitly before use and are never created via sync.

Invariants:

* Each `app_id` maps to exactly one `app_slug` and is unique within a node.
* `app_id` values MUST NOT be reused or reassigned.
* Objects belonging to one application MUST NOT be interpreted as belonging to another.
* If a sync domain is app-scoped, the `app_id` in a received envelope MUST match the app that owns the declared domain.

Guarantees:

* Cross-application contamination is prevented.
* Schema interpretation is deterministic.

### 1.4 Object identifiers

An object identifier uniquely identifies a graph object.

Object classes include [Parents](02-object-model.md), [Attributes](02-object-model.md), [Edges](02-object-model.md), [Ratings](02-object-model.md), [ACL objects](06-access-control-model.md), [revocation objects](05-keys-and-identity.md), and [recovery objects](05-keys-and-identity.md).

Properties:

* Object identifiers are assigned at creation time.
* Object identifiers are unique within their application namespace and object kind.
* Object identifiers are immutable.

Invariants:

* An object identifier MUST NOT change after creation.
* An object identifier MUST NOT be reused.
* An object identifier MUST be bound to exactly one owning identity.
* References MUST include `app_id`, object kind, and object id (no implicit scope).

Guarantees:

* Object provenance is traceable.
* Ownership enforcement is deterministic.

### 1.5 Domain identifiers

A domain identifier represents a replication and visibility scope.

Properties:

* Domain identifiers constrain [sync participation](07-sync-and-consistency.md).
* Domain identifiers constrain visibility and disclosure.
* Domain identifiers are declared in app-scoped schema and are resolved through [Schema Manager](../02-architecture/managers/05-schema-manager.md).

Invariants:

* Domain identifiers MUST be explicitly declared.
* Domain identifiers are scoped to an `app_id`; duplicate domain names within the same `app_id` are forbidden.
* Objects MUST declare domain membership explicitly.
* Objects outside a domain MUST NOT appear in domain-scoped sync.

Guarantees:

* Selective sync is enforceable.
* Unintended disclosure is prevented.

### 1.6 Type identifiers

Type identifiers bind object records to schema-defined meaning.

Properties:

* `type_key` is a stable string defined by an application's schema.
* `type_id` is a numeric identifier compiled by [Schema Manager](../02-architecture/managers/05-schema-manager.md).
* The `type_key` to `type_id` mapping is scoped to an `app_id` and object kind.

Invariants:

* Exactly one of `type_key` or `type_id` MUST be provided per operation ([03-serialization-and-envelopes.md](03-serialization-and-envelopes.md)).
* Unknown `type_key` or `type_id` values are rejected.
* `type_id` values are immutable for the lifetime of the application.

Guarantees:

* Type resolution is deterministic.
* Cross-application type collisions are impossible.

### 1.7 Sequencing identifiers

Sequencing identifiers order accepted writes and sync state.

Properties:

* `global_seq` is a node-local, strictly monotonic identifier assigned by [Graph Manager](../02-architecture/managers/07-graph-manager.md) at accept time ([07-sync-and-consistency.md](07-sync-and-consistency.md)).
* `domain_seq` is a per-peer, per-domain cursor maintained by [State Manager](../02-architecture/managers/09-state-manager.md) ([07-sync-and-consistency.md](07-sync-and-consistency.md)).
* `from_seq` and `to_seq` are sync window identifiers carried in sync packages ([03-serialization-and-envelopes.md](03-serialization-and-envelopes.md)).

Invariants:

* Sequencing identifiers are not client-supplied for local writes.
* Sequencing identifiers MUST be monotonic within their defined scope.
* Replay or regression of sequencing identifiers is rejected.

Guarantees:

* Ordering is deterministic per node and per domain.
* Partial or out-of-order sync application is prevented.

## 2. Namespace structure

### 2.1 Node namespace

The node namespace contains identifiers that must be interpretable across all local components on a node.

Includes:

* Identity identifiers.
* Device identifiers.
* `app_id` and `app_slug`.
* [Global sequence identifiers](07-sync-and-consistency.md).

Rules:

* Node namespace identifiers MUST be unique within the node.
* Node namespace identifiers MUST be stable over time.

### 2.2 Application namespaces

Each application defines an internal namespace.

Includes:

* Object identifiers.
* [Attribute types](02-object-model.md).
* [Rating types](02-object-model.md).
* [App-specific domains](07-sync-and-consistency.md).
* `type_key` and `type_id` mappings.

Rules:

* Identifiers are unique only within the application scope.
* Interpretation outside the owning application is forbidden unless explicitly defined by [schema linkage](02-object-model.md).

### 2.3 Domain namespaces

Domains define subsets of the graph eligible for sync and visibility.

Rules:

* Domain namespaces MUST NOT overlap implicitly.
* Domain membership MUST be explicit.
* Domain interpretation is local and enforced by policy.

## 3. Identifier resolution and trust boundaries

Resolution rules:

* Identifier resolution is local and deterministic.
* Object identifiers resolve to graph objects through the [Graph Manager](../02-architecture/managers/07-graph-manager.md).
* `app_id` and `app_slug` resolve through [App Manager](../02-architecture/managers/08-app-manager.md).
* `type_key` and `type_id` resolve through [Schema Manager](../02-architecture/managers/05-schema-manager.md).
* Domain identifiers resolve through [Schema Manager](../02-architecture/managers/05-schema-manager.md) and [State Manager](../02-architecture/managers/09-state-manager.md) for sync.
* No external resolution mechanism is permitted.

Trust boundaries:

* Identifiers received from remote peers are untrusted input.
* Resolution occurs only after structural validation and required [signature verification](04-cryptography.md) for remote input.

Failure handling:

* Unknown identifiers MUST cause rejection.
* Ambiguous identifiers MUST cause rejection.
* Identifiers resolving to multiple objects MUST cause rejection.

## 4. Allowed behaviors

The following behaviors are explicitly allowed:

* Independent creation of identifiers on disconnected nodes.
* Creation of new identifiers within declared namespaces.
* Deferred resolution during sync until prerequisites are satisfied.
* Multiple identifiers representing the same real-world entity.

## 5. Forbidden behaviors

The following behaviors are explicitly forbidden:

* Reassignment of an existing identifier.
* Reuse of identifiers after revocation.
* Implicit namespace inference.
* Cross-application interpretation without explicit schema linkage.
* Overloading a single identifier with multiple semantic meanings.
* Use of `app_id` values that are not registered locally.
* Use of domain identifiers that are not declared for the owning `app_id`.
* Use of `type_key` or `type_id` values that are not declared by the owning schema.

Violations MUST result in immediate [rejection](10-errors-and-failure-modes.md).

## 6. Failure and rejection semantics

On invalid identifier usage, the system MUST:

* Reject the operation before persistent storage.
* Record the rejection in the [local log](../02-architecture/managers/12-log-manager.md).
* Apply no partial state changes.

Invalid conditions include:

* Malformed identifier structure.
* Namespace violations.
* Ownership mismatches.
* References to undeclared applications, types, or domains.

Error mapping:

* Structural identifier violations -> `ErrorDetail.code=identifier_invalid` and protocol code `ERR_STRUCT_INVALID_IDENTIFIER`.
* Unknown `type_key` or `type_id` -> `ErrorDetail.code=schema_unknown_type` and protocol code `ERR_SCHEMA_TYPE_NOT_ALLOWED`.
* Domain scope violations in sync -> protocol code `ERR_SYNC_DOMAIN_VIOLATION` (interface mapping follows [04-error-model.md](../04-interfaces/04-error-model.md) and [05-sync-transport.md](../04-interfaces/05-sync-transport.md)).
* Identifier violations detected during authorization still return the identifier error; ACL errors are reserved for valid identifiers that lack permission.

Rejection ownership:

* [Graph Manager](../02-architecture/managers/07-graph-manager.md) rejects malformed, ambiguous, or mismatched object identifiers.
* [App Manager](../02-architecture/managers/08-app-manager.md) rejects unknown `app_id` and `app_slug`.
* [Schema Manager](../02-architecture/managers/05-schema-manager.md) rejects unknown `type_key`, `type_id`, and domain names.
* [State Manager](../02-architecture/managers/09-state-manager.md) rejects sync packages that violate domain scoping or sequencing.

No recovery action is implied by rejection.
