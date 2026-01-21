



# 02 Object model

## 1. Purpose and scope

This document defines the normative graph object model used by 2WAY. It specifies the canonical object categories, required fields, structural constraints, and invariants that must hold for any object to be accepted into the graph.

This specification references:

* [01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)
* [03-serialization-and-envelopes.md](03-serialization-and-envelopes.md)
* [04-cryptography.md](04-cryptography.md)
* [05-keys-and-identity.md](05-keys-and-identity.md)
* [06-access-control-model.md](06-access-control-model.md)
* [07-sync-and-consistency.md](07-sync-and-consistency.md)

This document does not define [serialization formats](03-serialization-and-envelopes.md), [envelope structures](03-serialization-and-envelopes.md), schema semantics, [ACL evaluation logic](06-access-control-model.md), [persistence layout](../03-data/01-sqlite-layout.md), or [synchronization behavior](07-sync-and-consistency.md). Those concerns are defined in other protocol and architecture documents and are referenced here only where required to establish correctness boundaries.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* The canonical graph object categories.
* Required fields and reference structure for each object category.
* Object level invariants that are enforced independently of schema or ACL logic.
* Cross object and cross category structural constraints.
* Explicit rejection conditions for structurally invalid objects.

This specification does not cover the following:

* [Schema meaning](../02-architecture/managers/05-schema-manager.md), type validation, or value interpretation.
* [Authorization rules](06-access-control-model.md) or ACL evaluation.
* [Envelope formats](03-serialization-and-envelopes.md) or wire serialization.
* [Persistence schemas](../03-data/01-sqlite-layout.md), indexes, or query behavior.
* [Sync ordering](07-sync-and-consistency.md), conflict resolution, or domain selection.

## 3. Invariants and guarantees

### 3.1 Invariants

The following invariants apply to all graph objects:

* All persistent state is represented exclusively using the canonical object categories defined in this document.
* Every object belongs to exactly one application domain identified by [`app_id`](01-identifiers-and-namespaces.md).
* Every object has a single immutable author identity as defined in [05-keys-and-identity.md](05-keys-and-identity.md).
* Object identifiers, ownership, and provenance metadata are immutable once assigned (see [01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).
* All references between objects are explicit and must resolve within the same `app_id` scope.

### 3.2 Guarantees

When enforced as specified, the object model guarantees:

* Stable authorship and ownership binding for all objects.
* Referential integrity within each application domain.
* Structural isolation between application domains.
* Deterministic rejection of structurally invalid objects.

This document does not guarantee schema validity, authorization correctness, or semantic consistency beyond structural constraints.

## 4. Canonical object categories

### 4.1 Categories

2WAY defines five canonical graph object categories:

* Parent
* Attribute
* Edge
* Rating
* [ACL](06-access-control-model.md)

Parent, Attribute, Edge, and Rating are stored as first class object records. ACL is a canonical category at the protocol level and is represented structurally using Parent and Attribute records as defined in [06-access-control-model.md](06-access-control-model.md).

No other persistent object categories are permitted.

### 4.2 Naming constraints

* The category names Parent, Attribute, Edge, Rating, ACL are canonical and fixed.
* Implementations must not alias or redefine these category names in protocol visible behavior.

## 5. Common fields and reference rules

### 5.1 Required metadata fields

All stored object records include the following required metadata fields:

* `app_id`. Integer identifier of the application domain ([01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).
* `id`. Integer identifier of the object within its category and `app_id` scope ([01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).
* `type_id`. Integer identifier of the object type within the `app_id` scope ([01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).
* `owner_identity`. Integer identifier of the authoring identity ([05-keys-and-identity.md](05-keys-and-identity.md)).
* `global_seq`. Integer sequence assigned by the local node at accept time ([07-sync-and-consistency.md](07-sync-and-consistency.md)).
* `sync_flags`. Integer metadata used by the sync subsystem ([07-sync-and-consistency.md](07-sync-and-consistency.md)).

The presence and immutability of these fields are defined here. Their assignment and interpretation are defined elsewhere, including [01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md) and [07-sync-and-consistency.md](07-sync-and-consistency.md).

### 5.2 Immutability rules

For any persisted object:

* `app_id` MUST NOT change.
* `id` MUST NOT change.
* `type_id` MUST NOT change.
* `owner_identity` MUST NOT change.
* `global_seq` MUST NOT change.
* `sync_flags` MUST NOT change once persisted.

If updates are supported, only value bearing fields defined for the object category may change, and only under external validation and authorization.

### 5.3 Object reference form

All object references are explicit and consist of:

* `app_id`
* object category
* object `id`

References MUST NOT rely on implicit `app_id` inheritance or contextual assumptions.

## 6. Parent

### 6.1 Definition

A Parent represents an entity root within an application domain. All other object categories attach to a Parent directly or indirectly.

### 6.2 Required fields

A Parent record includes:

* Common metadata fields defined in Section 5.1.
* `value_json`. Optional, schema defined payload.

The contents of `value_json` are opaque to this specification.

### 6.3 Structural invariants

* A Parent anchors attachment of Attributes, Edges, Ratings, and ACL structures.
* Ownership of a Parent is permanent.
* A Parent cannot be reassigned to another `app_id`.

### 6.4 Explicitly allowed

* Creation of a Parent with valid metadata fields.
* Attachment of other objects that satisfy the constraints in this document.

### 6.5 Explicitly forbidden

* Deleting a Parent.
* Changing `owner_identity`, `type_id`, or `app_id` of a Parent.
* Referencing a non-existent Parent.

## 7. Attribute

### 7.1 Definition

An Attribute represents typed data attached to a source Parent.

### 7.2 Required fields

An Attribute record includes:

* Common metadata fields defined in Section 5.1.
* `src_parent_id`. Identifier of the Parent the Attribute attaches to.
* `value_json`. Optional, schema defined payload.

### 7.3 Structural invariants

* `src_parent_id` MUST reference an existing Parent within the same `app_id`.
* Attribute ownership is permanent.
* An Attribute MUST NOT reference a Parent in a different `app_id`.

### 7.4 Explicitly allowed

* Creation of an Attribute attached to an existing Parent.
* Updating `value_json` only, if updates are supported and externally authorized.

### 7.5 Explicitly forbidden

* Rebinding an Attribute to a different Parent.
* Changing `owner_identity` or `type_id`.
* Creating an Attribute whose source Parent does not exist.

## 8. Edge

### 8.1 Definition

An Edge represents a typed relationship issued from a source Parent to a destination object.

### 8.2 Required fields

An Edge record includes:

* Common metadata fields defined in Section 5.1.
* `src_parent_id`. Identifier of the source Parent.
* `dst_parent_id` or `dst_attr_id`. Exactly one MUST be present.

### 8.3 Structural invariants

* `src_parent_id` MUST reference an existing Parent in the same `app_id`.
* If present, `dst_parent_id` MUST reference an existing Parent in the same `app_id`.
* If present, `dst_attr_id` MUST reference an existing Attribute in the same `app_id`.
* Exactly one destination selector MUST be set.
* Edge ownership is permanent.

### 8.4 Explicitly allowed

* Creation of an Edge with valid source and destination references.
* Updating destination or value fields, if supported and externally authorized, while preserving invariants.

### 8.5 Explicitly forbidden

* Setting both destination selectors or neither.
* Changing `owner_identity` or `type_id`.
* Creating an Edge with unresolved references.

## 9. Rating

### 9.1 Definition

A Rating represents a typed evaluation issued by an identity toward a target object.

### 9.2 Required fields

A Rating record includes:

* Common metadata fields defined in Section 5.1.
* `target_parent_id` or `target_attr_id`. Exactly one MUST be present.
* `value_json`. Optional, schema defined payload.

### 9.3 Structural invariants

* Target references MUST resolve within the same `app_id`.
* Exactly one target selector MUST be set.
* Rating ownership is permanent.

### 9.4 Explicitly allowed

* Creation of a Rating targeting a valid object.
* Updating `value_json` only, if supported and externally authorized.

### 9.5 Explicitly forbidden

* Changing `owner_identity` or `type_id`.
* Targeting non-existent objects.
* Cross application targeting.

## 10. ACL

### 10.1 Definition

ACL is a canonical object category used to express authorization structures as graph data.

ACL is represented as:

* A Parent that serves as the ACL root.
* A constrained set of Attributes attached to that Parent.

### 10.2 Structural invariants

* ACL structures MUST be representable using only Parent and Attribute records.
* All ACL objects MUST reside within a single `app_id` scope, unless explicitly defined as system scope elsewhere.

### 10.3 Explicitly forbidden

* Representing ACL data as a separate storage category.
* Introducing cross application references not permitted by the ACL model.

## 11. Application domain isolation

### 11.1 Isolation invariant

For all object categories:

* All object references MUST resolve within the same `app_id`.

This applies to:

* Attribute source references.
* Edge source and destination references.
* Rating target references.
* ACL related attachments.

### 11.2 Explicitly forbidden

* Accepting objects that reference other application domains.
* Accepting objects that rely on implicit domain inheritance.

## 12. Inputs, outputs, and trust boundaries

### 12.1 Inputs

The object model evaluates proposed object mutations that include:

* Object category and `app_id`.
* Required fields for that category.
* Declared `owner_identity`.

Authentication, [signature verification](04-cryptography.md), schema validation, and [ACL evaluation](06-access-control-model.md) are assumed to occur outside this specification.

### 12.2 Outputs

The object model produces one of two outcomes:

* Accept. The object satisfies all structural constraints.
* Reject. One or more constraints are violated.

### 12.3 Trust boundaries

* Caller supplied fields are not trusted.
* Object existence checks must be explicit.
* Structural validation is mandatory before any persistence.

## 13. Failure and rejection behavior

### 13.1 Rejection conditions

A proposed mutation MUST be rejected if:

* Required fields are missing.
* Destination selector rules are violated.
* Referenced objects do not exist.
* Application domain isolation is violated.
* An immutable field would be modified.

### 13.2 Failure handling guarantees

* Rejection produces no partial persistence.
* Rejection is deterministic given the proposed mutation and current graph state.
* Rejection reasons must distinguish structural violations from external validation failures.

## 14. Guarantees summary

When enforced as specified, this object model guarantees:

* Immutable authorship and provenance metadata.
* Strict structural validity of all graph objects.
* Referential integrity within application domains.
* Canonical representation of ACL structures using graph primitives.
