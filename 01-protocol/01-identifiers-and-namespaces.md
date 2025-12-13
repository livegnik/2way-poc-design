



# 01 Identifiers and Namespaces

## 1. Purpose and scope

This document defines the identifier types and namespace rules used by the 2WAY protocol. It specifies how identities, objects, applications, domains, and schemas are named, scoped, and referenced at the protocol level. It establishes invariants and guarantees required for correctness, security, and interoperability.

This document does not define storage layout, cryptographic primitives, access control semantics, or sync behavior, except where identifier structure directly constrains those systems. Those aspects are defined elsewhere in the repository.

## 2. Responsibilities

This specification is responsible for the following:

* Defining canonical identifier forms used by the protocol.
* Defining namespace boundaries and isolation rules.
* Defining uniqueness and immutability guarantees for identifiers.
* Defining how identifiers are interpreted across trust boundaries.
* Defining rejection conditions for invalid or ambiguous identifiers.

## 3. Non-responsibilities

This specification does not define:

* Key generation or cryptographic algorithms.
* Object schemas or attribute semantics.
* ACL evaluation rules.
* Storage or indexing strategies.
* Network addressing or transport identifiers.

## 4. Identifier classes

### 4.1 Identity identifiers

An identity identifier uniquely represents an actor in the system.

Actors include:

* Users.
* Devices.
* Backend services.
* Applications when acting as signing entities.

Properties:

* Each identity identifier corresponds to exactly one Parent object.
* Each identity identifier is anchored to at least one public key.
* Identity identifiers are immutable for the lifetime of the Parent.
* Identity identifiers are globally unique within a node and across sync domains.

Invariants:

* An identity identifier MUST NOT be reassigned.
* An identity identifier MUST NOT be reused, even after revocation.
* An identity identifier MUST resolve to exactly one cryptographic authority at any given time.

Guarantees:

* Authorship attribution is stable and verifiable.
* Identity collision is structurally prevented.

### 4.2 Object identifiers

An object identifier uniquely identifies a graph object.

Object classes include:

* Parents.
* Attributes.
* Edges.
* Ratings.
* ACL objects.
* Revocation and recovery objects.

Properties:

* Object identifiers are assigned at creation time.
* Object identifiers are unique within their app namespace.
* Object identifiers are immutable.

Invariants:

* An object identifier MUST NOT change after creation.
* An object identifier MUST NOT be reused.
* An object identifier MUST be bound to exactly one owning identity.

Guarantees:

* Object lineage is traceable.
* Ownership enforcement is deterministic.

### 4.3 Application identifiers

An application identifier uniquely identifies an application domain.

Properties:

* Application identifiers define namespace boundaries.
* Application identifiers scope schemas, object types, and ratings.
* Application identifiers are stable across sync.

Invariants:

* An application identifier MUST NOT overlap with another application identifier.
* An application identifier MUST be explicitly declared before use.
* Objects belonging to one application MUST NOT be interpreted as belonging to another.

Guarantees:

* Cross-application contamination is prevented.
* Schema interpretation is unambiguous.

### 4.4 Device identifiers

A device identifier represents a specific device acting on behalf of an identity.

Properties:

* Device identifiers are subordinate to an identity identifier.
* Device identifiers may carry scoped authority.
* Device identifiers may be revoked independently.

Invariants:

* A device identifier MUST be linked to exactly one identity.
* A device identifier MUST NOT exist without an owning identity.

Guarantees:

* Device compromise impact is limited.
* Authority delegation is explicit and auditable.

## 5. Namespace structure

### 5.1 Global namespace

The global namespace contains identifiers that must be interpretable across all sync domains.

Includes:

* Identity identifiers.
* Application identifiers.
* Global sequence identifiers.

Rules:

* Global namespace identifiers MUST be globally unique.
* Global namespace identifiers MUST be stable across time.

### 5.2 Application namespaces

Each application defines its own internal namespace.

Includes:

* Object identifiers.
* Attribute types.
* Rating types.
* App-specific domains.

Rules:

* Identifiers are unique only within the application scope.
* Interpretation outside the owning application is forbidden unless explicitly defined.

### 5.3 Domain namespaces

Domains define subsets of the graph that participate in sync and visibility rules.

Properties:

* Domain identifiers scope replication.
* Domain identifiers constrain visibility and disclosure.

Rules:

* An object MUST belong to zero or more explicitly declared domains.
* An object outside a domain MUST NOT be included in domain-scoped sync.

## 6. Identifier resolution

Resolution rules:

* Identifier resolution is local and deterministic.
* Identifiers resolve to graph objects through the Graph Manager.
* No external resolution mechanism is permitted.

Trust boundaries:

* Incoming identifiers from remote peers are treated as untrusted input.
* Resolution occurs only after signature verification and schema validation.

Failure handling:

* Unknown identifiers result in rejection.
* Ambiguous identifiers result in rejection.
* Identifiers resolving to multiple objects result in rejection.

## 7. Allowed behaviors

The following behaviors are explicitly allowed:

* Creation of new identifiers within declared namespaces.
* Independent identifier creation across disconnected nodes.
* Deferred resolution during sync until prerequisites are satisfied.
* Coexistence of multiple identifiers referring to the same real-world entity.

## 8. Forbidden behaviors

The following behaviors are explicitly forbidden:

* Reassignment of an existing identifier.
* Cross-application interpretation without explicit schema linkage.
* Implicit namespace inference.
* Identifier reuse after revocation.
* Overloading identifiers with multiple semantic meanings.

Violations MUST result in immediate rejection.

## 9. Failure and rejection semantics

On invalid identifier input, the system MUST:

* Reject the operation before persistent storage.
* Record the rejection in the local log.
* Avoid partial application of related operations.

Invalid conditions include:

* Malformed identifier structure.
* Namespace violation.
* Ownership mismatch.
* Undeclared application or domain reference.

No recovery action is implied by rejection.

## 10. Guarantees summary

This specification guarantees:

* Stable identity anchoring.
* Deterministic object ownership.
* Strict namespace isolation.
* Predictable failure behavior.
* Absence of identifier-based privilege escalation.

No additional guarantees are implied beyond those explicitly stated.
