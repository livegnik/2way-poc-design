



# 01 Identifiers and Namespaces

## 1. Purpose and scope

This document defines the identifier classes and namespace rules used by the 2WAY protocol as specified by the PoC design. It establishes how identities, applications, objects, domains, and schemas are named, scoped, and referenced at the protocol level. It specifies invariants, guarantees, allowed behaviors, forbidden behaviors, and failure handling required for correctness and security.

This specification references:

* [02-object-model.md](02-object-model.md)
* [04-cryptography.md](04-cryptography.md)
* [05-keys-and-identity.md](05-keys-and-identity.md)
* [06-access-control-model.md](06-access-control-model.md)
* [07-sync-and-consistency.md](07-sync-and-consistency.md)
* [08-network-transport-requirements.md](08-network-transport-requirements.md)
* [10-errors-and-failure-modes.md](10-errors-and-failure-modes.md)

This document is authoritative only for identifier semantics and namespace isolation. It does not define [cryptographic primitives](04-cryptography.md), [schema content](02-object-model.md), [ACL logic](06-access-control-model.md), [sync mechanics](07-sync-and-consistency.md), [storage layout](../03-data/01-sqlite-layout.md), or [network transport](08-network-transport-requirements.md), except where identifier structure directly constrains those systems. All such behavior is defined elsewhere and referenced implicitly.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining all identifier classes used by the protocol.
* Defining namespace boundaries and isolation rules.
* Defining identifier uniqueness, immutability, and lifetime guarantees.
* Defining how identifiers are interpreted across trust boundaries.
* Defining rejection behavior for invalid, ambiguous, or unauthorized identifier usage.

This specification does not cover the following:

* [Key generation](04-cryptography.md), signing algorithms, or encryption algorithms.
* [Graph object schemas](02-object-model.md) or attribute semantics.
* [Access control](06-access-control-model.md) evaluation rules.
* [Sync ordering](07-sync-and-consistency.md), conflict resolution, or replication mechanics.
* [Physical storage](../03-data/01-sqlite-layout.md), indexing, or persistence strategies.
* [Network addressing](08-network-transport-requirements.md) or peer discovery identifiers.

## 3. Identifier classes

### 3.1 Identity identifiers

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

### 3.2 Device identifiers

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

### 3.3 Application identifiers

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

### 3.4 Object identifiers

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

### 3.5 Domain identifiers

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

## 4. Namespace structure

### 4.1 Global namespace

The global namespace contains identifiers that must be interpretable across all peers.

Includes:

* Identity identifiers.
* Application identifiers.
* Domain identifiers.
* [Global sequence identifiers](07-sync-and-consistency.md).

Rules:

* Global namespace identifiers MUST be globally unique.
* Global namespace identifiers MUST be stable over time.

### 4.2 Application namespaces

Each application defines an internal namespace.

Includes:

* Object identifiers.
* [Attribute types](02-object-model.md).
* [Rating types](02-object-model.md).
* [App-specific domains](07-sync-and-consistency.md).

Rules:

* Identifiers are unique only within the application scope.
* Interpretation outside the owning application is forbidden unless explicitly defined by [schema linkage](02-object-model.md).

### 4.3 Domain namespaces

Domains define subsets of the graph eligible for sync and visibility.

Rules:

* Domain namespaces MUST NOT overlap implicitly.
* Domain membership MUST be explicit.
* Domain interpretation is local and enforced by policy.

## 5. Identifier resolution and trust boundaries

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

## 6. Allowed behaviors

The following behaviors are explicitly allowed:

* Independent creation of identifiers on disconnected nodes.
* Creation of new identifiers within declared namespaces.
* Deferred resolution during sync until prerequisites are satisfied.
* Multiple identifiers representing the same real-world entity.

## 7. Forbidden behaviors

The following behaviors are explicitly forbidden:

* Reassignment of an existing identifier.
* Reuse of identifiers after revocation.
* Implicit namespace inference.
* Cross-application interpretation without explicit schema linkage.
* Overloading a single identifier with multiple semantic meanings.

Violations MUST result in immediate [rejection](10-errors-and-failure-modes.md).

## 8. Failure and rejection semantics

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

## 9. Guarantees summary

This specification guarantees:

* Stable identity anchoring.
* Deterministic object ownership.
* Strict namespace isolation.
* Predictable failure behavior.
* Absence of identifier-based privilege escalation.

No guarantees beyond those explicitly stated are implied.
