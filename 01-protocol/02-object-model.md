



## 1. Purpose and scope

This document defines the 2WAY object model. It specifies the set of object types that constitute the graph, their structural properties, invariants, and permitted relationships. It defines what an object is, how objects relate, and which properties are enforced at the model level.

This document does not define storage layout, serialization formats, validation pipelines, access control logic, or synchronization behavior. Those are specified elsewhere and are only referenced here where required to define object correctness or trust boundaries.

## 2. Responsibilities

The object model is responsible for:

* Defining the canonical object types used by the 2WAY graph.
* Defining mandatory and optional fields for each object type.
* Defining ownership, authorship, and immutability rules at the object level.
* Defining allowed relationships between object types.
* Defining invariants that must hold for all valid objects.

The object model is not responsible for:

* Enforcing access control decisions.
* Performing schema or application-level semantic validation.
* Managing persistence, indexing, or storage optimization.
* Resolving conflicts or ordering operations.
* Network transport, encryption, or synchronization.

## 3. Object taxonomy

All persistent state in 2WAY is represented as graph objects. There are exactly four first-class object types:

1. Parent
2. Attribute
3. Edge
4. Rating

No other persistent object types are permitted.

Each object belongs to exactly one application domain, identified by an app identifier. System-level objects belong to app_0.

## 4. Common object properties

All object types share the following mandatory properties:

* Object identifier. Globally unique within the local graph.
* App identifier. Identifies the application domain that defines the object semantics.
* Owner identity. Cryptographic identity that authored the object.
* Global sequence number. Assigned at acceptance time by the local node.
* Creation timestamp. Local node time at acceptance.

The following properties are invariant once assigned:

* Object identifier.
* App identifier.
* Owner identity.
* Global sequence number.

Objects are immutable unless explicitly defined otherwise in this specification.

## 5. Parent objects

### 5.1 Definition

A Parent represents a durable entity in the graph. It is the root to which other objects attach.

### 5.2 Properties

A Parent object has:

* A unique object identifier.
* An owner identity.
* An app identifier.
* Zero or more associated Attributes.
* Zero or more incoming and outgoing Edges.
* Zero or more associated Ratings.

### 5.3 Invariants

* A Parent is immutable after creation.
* Ownership of a Parent cannot change.
* A Parent cannot be deleted.
* A Parent cannot be retyped or reassigned to another app.

### 5.4 Guarantees

* A Parent uniquely anchors authorship for all objects attached to it.
* A Parent provides a stable reference point for ACL and schema evaluation.

### 5.5 Forbidden behaviors

* Modifying a Parent after creation.
* Deleting a Parent.
* Creating a Parent without a valid owner identity.

## 6. Attribute objects

### 6.1 Definition

An Attribute represents typed data attached to exactly one Parent.

### 6.2 Properties

An Attribute has:

* A unique object identifier.
* A target Parent identifier.
* A declared type identifier.
* A value representation.
* An owner identity.

### 6.3 Invariants

* An Attribute must reference exactly one existing Parent.
* The referenced Parent must belong to the same app.
* Attribute ownership must match the Parent owner unless explicitly permitted by ACL rules.
* Attribute type and representation must conform to the schema of the app.

### 6.4 Mutability rules

* Attributes may be mutable or immutable as defined by schema.
* Mutable Attributes may only be modified by their owner or explicitly authorized identities.
* Immutable Attributes cannot be modified after creation.

### 6.5 Forbidden behaviors

* Attributes referencing non-existent Parents.
* Attributes crossing app boundaries.
* Reassigning an Attribute to a different Parent.

## 7. Edge objects

### 7.1 Definition

An Edge represents a typed relationship between two Parents.

### 7.2 Properties

An Edge has:

* A unique object identifier.
* A source Parent identifier.
* A target Parent identifier.
* A declared edge type.
* An owner identity.

### 7.3 Invariants

* Source and target Parents must exist.
* Source and target Parents must belong to the same app.
* Edge type must be defined by the app schema.
* Edge direction is fixed at creation.

### 7.4 Semantics

* Edges may represent relationships such as membership, trust, delegation, or containment.
* Edge semantics are defined entirely by the consuming app and schema.

### 7.5 Forbidden behaviors

* Edges across app boundaries.
* Retargeting an Edge after creation.
* Modifying Edge type after creation.

## 8. Rating objects

### 8.1 Definition

A Rating represents a typed evaluation issued by one identity toward a Parent.

### 8.2 Properties

A Rating has:

* A unique object identifier.
* A subject Parent identifier.
* A declared rating type.
* A value representation.
* An issuing identity.

### 8.3 Invariants

* The subject Parent must exist.
* Rating types are app-scoped.
* A Rating is immutable after creation.
* Ratings do not imply global reputation.

### 8.4 Semantics

* Ratings are interpreted only by the app that defines them.
* Ratings have no cross-app meaning.
* Aggregation rules are outside the scope of this document.

### 8.5 Forbidden behaviors

* Modifying or deleting Ratings.
* Using Ratings outside their app context.

## 9. Ownership and authorship rules

* Every object has exactly one owner identity.
* Ownership is determined at creation and never changes.
* All write operations must be signed by the owner or an authorized delegate.
* Objects cannot be forged because ownership is cryptographically verifiable.

Ownership rules are enforced structurally by the object model and procedurally by the validation pipeline defined elsewhere.

## 10. Cross-object constraints

The following constraints apply globally:

* All objects must belong to exactly one app.
* Objects may only reference other objects within the same app.
* Cycles are permitted unless forbidden by app schema.
* Referential integrity must be satisfied at creation time.

## 11. Interaction with other components

### 11.1 Inputs

* Signed operation envelopes proposing object creation or modification.

### 11.2 Outputs

* Accepted objects committed to the graph.
* Rejection signals indicating object model violations.

### 11.3 Trust boundaries

* The object model does not trust callers.
* All object correctness assumptions rely on prior signature verification.
* Access control decisions are external to this specification.

## 12. Failure and rejection behavior

Operations are rejected if any of the following occur:

* Required properties are missing.
* Object references are invalid.
* Invariants defined in this document are violated.
* App boundary constraints are violated.

Rejected operations produce no partial state and have no side effects. Rejection reasons must be explicit and deterministic.

## 13. Guarantees summary

The object model guarantees:

* Stable authorship and ownership.
* Immutable history anchors.
* Strict app-level isolation.
* Referential integrity within the graph.

No other guarantees are provided by this specification.
