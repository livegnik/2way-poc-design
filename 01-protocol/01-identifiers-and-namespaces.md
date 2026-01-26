



# 01 Identifiers and Namespaces

Defines identifier classes and namespace rules for the 2WAY protocol.
Specifies identifier invariants, uniqueness, immutability, and resolution rules.
Enumerates allowed/forbidden identifier behaviors and failure handling.

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
* Identity identifiers are globally unique within the node and across sync.

Invariants:

* An identity identifier MUST NOT be reassigned.
* An identity identifier MUST NOT be reused.
* An identity identifier MUST always resolve to exactly one owning Parent.

Guarantees:

* Authorship attribution is stable.
* Impersonation through identifier reuse is structurally prevented.

### 1.2 Device identifiers

A device identifier represents a device acting on behalf of an identity.

Properties:

* Device identifiers are represented as [Parents](02-object-model.md) linked to an identity Parent.
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
* Application identifiers are declared explicitly before use.
* Application identifiers are stable across sync.

Invariants:

* Application identifiers MUST be globally unique.
* Application identifiers MUST NOT overlap.
* Objects belonging to one application MUST NOT be interpreted as belonging to another.

Guarantees:

* Cross-application contamination is prevented.
* Schema interpretation is deterministic.

### 1.4 Object identifiers

An object identifier uniquely identifies a graph object.

Object classes include [Parents](02-object-model.md), [Attributes](02-object-model.md), [Edges](02-object-model.md), [Ratings](02-object-model.md), [ACL objects](06-access-control-model.md), [revocation objects](05-keys-and-identity.md), and [recovery objects](05-keys-and-identity.md).

Properties:

* Object identifiers are assigned at creation time.
* Object identifiers are unique within their application namespace.
* Object identifiers are immutable.

Invariants:

* An object identifier MUST NOT change after creation.
* An object identifier MUST NOT be reused.
* An object identifier MUST be bound to exactly one owning identity.

Guarantees:

* Object provenance is traceable.
* Ownership enforcement is deterministic.

### 1.5 Domain identifiers

A domain identifier represents a replication and visibility scope.

Properties:

* Domain identifiers constrain [sync participation](07-sync-and-consistency.md).
* Domain identifiers constrain visibility and disclosure.

Invariants:

* Domain identifiers MUST be explicitly declared.
* Objects MUST declare domain membership explicitly.
* Objects outside a domain MUST NOT appear in domain-scoped sync.

Guarantees:

* Selective sync is enforceable.
* Unintended disclosure is prevented.

## 2. Namespace structure

### 2.1 Global namespace

The global namespace contains identifiers that must be interpretable across all peers.

Includes:

* Identity identifiers.
* Application identifiers.
* Domain identifiers.
* [Global sequence identifiers](07-sync-and-consistency.md).

Rules:

* Global namespace identifiers MUST be globally unique.
* Global namespace identifiers MUST be stable over time.

### 2.2 Application namespaces

Each application defines an internal namespace.

Includes:

* Object identifiers.
* [Attribute types](02-object-model.md).
* [Rating types](02-object-model.md).
* [App-specific domains](07-sync-and-consistency.md).

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
* Identifiers resolve to graph objects through the [Graph Manager](../02-architecture/managers/07-graph-manager.md).
* No external resolution mechanism is permitted.

Trust boundaries:

* Identifiers received from remote peers are untrusted input.
* Resolution occurs only after [signature verification](04-cryptography.md) and [schema validation](02-object-model.md).

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
* References to undeclared applications or domains.

No recovery action is implied by rejection.
