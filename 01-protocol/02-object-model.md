



# 02 Object model

Defines the canonical graph object categories for 2WAY and their required fields. Specifies object invariants, reference rules, and application-domain isolation constraints. Defines acceptance and rejection conditions for object mutations.

For the meta specifications, see [02-object-model meta](../10-appendix/meta/01-protocol/02-object-model-meta.md).

## 1. Invariants and guarantees

### 1.1 Invariants

The following invariants apply to all graph objects:

* All persistent state is represented exclusively using the canonical object categories defined in this document.
* Every object belongs to exactly one application domain identified by [`app_id`](01-identifiers-and-namespaces.md).
* Every object has a single immutable author identity as defined in [05-keys-and-identity.md](05-keys-and-identity.md).
* Object identifiers, ownership, and provenance metadata are immutable once assigned (see [01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).
* All references between objects are explicit and must resolve within the same `app_id` scope.
* `app_id`, `type_id`, and `owner_identity` must resolve to registered identifiers before acceptance.

### 1.2 Guarantees

When enforced as specified, the object model guarantees:

* Stable authorship and ownership binding for all objects.
* Referential integrity within each application domain.
* Structural isolation between application domains.
* Deterministic rejection of structurally invalid objects.

## 2. Canonical object categories

### 2.1 Categories

2WAY defines five canonical graph object categories:

* [Parent](#6-parent). Entity root for an application domain; anchors other objects.
* [Attribute](#7-attribute). Typed data attached to a source Parent.
* [Edge](#8-edge). Typed relationship from a source Parent to a destination object.
* [Rating](#9-rating). Typed evaluation issued toward a target Parent or Attribute.
* [ACL](#10-acl). Authorization structures modeled as graph data ([06-access-control-model.md](06-access-control-model.md)).

Parent, Attribute, Edge, and Rating are stored as first class object records. ACL is a canonical category at the protocol level and is represented structurally using Parent and Attribute records as defined in [06-access-control-model.md](06-access-control-model.md).

No other persistent object categories are permitted.

### 2.2 Naming constraints

* The category names Parent, Attribute, Edge, Rating, ACL are canonical and fixed.
* Implementations must not alias or redefine these category names in protocol visible behavior.

## 3. Common fields and reference rules

### 3.1 Required metadata fields

All stored object records include the following required metadata fields:

* `app_id`. Integer identifier of the application domain ([01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).
* `id`. Integer identifier of the object within its category and `app_id` scope ([01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).
* `type_id`. Integer identifier of the object type within the `app_id` scope ([01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).
* `owner_identity`. Integer identifier of the authoring identity ([05-keys-and-identity.md](05-keys-and-identity.md)).
* `global_seq`. Integer sequence assigned by the local node at accept time ([07-sync-and-consistency.md](07-sync-and-consistency.md)).
* `sync_flags`. Integer metadata used by the sync subsystem ([07-sync-and-consistency.md](07-sync-and-consistency.md)).

### 3.2 Immutability rules

For any persisted object:

* `app_id` MUST NOT change.
* `id` MUST NOT change.
* `type_id` MUST NOT change.
* `owner_identity` MUST NOT change.
* `global_seq` MUST NOT change.
* `sync_flags` MUST NOT change once persisted.

If updates are supported, only value bearing fields defined for the object category may change, and only under external [validation](../02-architecture/managers/05-schema-manager.md) and [authorization](06-access-control-model.md).

### 3.3 Object reference form

All object references are explicit and consist of:

* `app_id`
* object category
* object `id`

References MUST NOT rely on implicit `app_id` inheritance or contextual assumptions.

### 3.4 Identifier resolution constraints

Before acceptance, the following must be true:

* `app_id` resolves to a registered application ([App Manager](../02-architecture/managers/08-app-manager.md)).
* `type_id` resolves to a schema-defined type for the same `app_id` ([Schema Manager](../02-architecture/managers/05-schema-manager.md)).
* `owner_identity` resolves to an identity Parent in `app_0` ([05-keys-and-identity.md](05-keys-and-identity.md)).

If any of these identifiers fail to resolve, the mutation is rejected.

## 4. Parent

### 4.1 Definition

A Parent represents an entity root within an application domain. All other object categories attach to a Parent directly or indirectly.

### 4.2 Required fields

A Parent record includes:

* Common metadata fields defined in Section 3.1.
* `value_json`. Optional, schema defined payload.

The contents of `value_json` are opaque to this specification.

### 4.3 Structural invariants

* A Parent anchors attachment of Attributes, Edges, Ratings, and ACL structures.
* Ownership of a Parent is permanent.
* A Parent cannot be reassigned to another `app_id`.

### 4.4 Explicitly allowed

* Creation of a Parent with valid metadata fields.
* Attachment of other objects that satisfy the constraints in this document.

### 4.5 Explicitly forbidden

* Deleting a Parent.
* Changing `owner_identity`, `type_id`, or `app_id` of a Parent.
* Referencing a non-existent Parent.

## 5. Attribute

### 5.1 Definition

An Attribute represents typed data attached to a source Parent.

### 5.2 Required fields

An Attribute record includes:

* Common metadata fields defined in Section 3.1.
* `src_parent_id`. Identifier of the Parent the Attribute attaches to.
* `value_json`. Optional, schema defined payload.

### 5.3 Structural invariants

* `src_parent_id` MUST reference an existing Parent within the same `app_id`.
* Attribute ownership is permanent.
* An Attribute MUST NOT reference a Parent in a different `app_id`.

### 5.4 Explicitly allowed

* Creation of an Attribute attached to an existing Parent.
* Updating `value_json` only, if updates are supported and externally authorized.

### 5.5 Explicitly forbidden

* Rebinding an Attribute to a different Parent.
* Changing `owner_identity` or `type_id`.
* Creating an Attribute whose source Parent does not exist.

## 6. Edge

### 6.1 Definition

An Edge represents a typed relationship issued from a source Parent to a destination object.

### 6.2 Required fields

An Edge record includes:

* Common metadata fields defined in Section 3.1.
* `src_parent_id`. Identifier of the source Parent.
* `dst_parent_id` or `dst_attr_id`. Exactly one MUST be present.

### 6.3 Structural invariants

* `src_parent_id` MUST reference an existing Parent in the same `app_id`.
* If present, `dst_parent_id` MUST reference an existing Parent in the same `app_id`.
* If present, `dst_attr_id` MUST reference an existing Attribute in the same `app_id`.
* Exactly one destination selector MUST be set.
* Edge ownership is permanent.

### 6.4 Explicitly allowed

* Creation of an Edge with valid source and destination references.
* Updating destination or value fields, if supported and externally authorized, while preserving invariants.

### 6.5 Explicitly forbidden

* Setting both destination selectors or neither.
* Changing `owner_identity` or `type_id`.
* Creating an Edge with unresolved references.

### 6.6 System group primitives (app_0)

Group membership used by ACL and read filters is represented in `app_0` using the following system types:

* Parent type `system.group` (group definition).
* Edge type `system.group_member` (membership edge from a `system.group` Parent to an identity Parent).

Structural rules:

* `system.group` Parents MUST reside in `app_0` and may only reference identity Parents in `app_0`.
* `system.group_member` Edges MUST use `src_parent_id` pointing to a `system.group` Parent and `dst_parent_id` pointing to an identity Parent.
* Group membership edges are read-only inputs for authorization and read filtering and do not bypass app domain isolation for writes.

## 7. Rating

### 7.1 Definition

A Rating represents a typed evaluation issued by an identity toward a target object.

### 7.2 Required fields

A Rating record includes:

* Common metadata fields defined in Section 3.1.
* `target_parent_id` or `target_attr_id`. Exactly one MUST be present.
* `value_json`. Optional, schema defined payload.

### 7.3 Structural invariants

* Target references MUST resolve within the same `app_id`.
* Exactly one target selector MUST be set.
* Rating ownership is permanent.

### 7.4 Explicitly allowed

* Creation of a Rating targeting a valid object.
* Updating `value_json` only, if updates are supported and externally authorized.

### 7.5 Explicitly forbidden

* Changing `owner_identity` or `type_id`.
* Targeting non-existent objects.
* Cross application targeting.

## 8. ACL

### 8.1 Definition

ACL is a canonical object category used to express authorization structures as graph data.

ACL is represented as:

* A Parent that serves as the ACL root.
* A constrained set of Attributes attached to that Parent.
* Canonical ACL attribute schemas are defined in [06-access-control-model.md](06-access-control-model.md).

### 8.2 Structural invariants

* ACL structures MUST be representable using only Parent and Attribute records.
* All ACL objects MUST reside within a single `app_id` scope, unless explicitly defined as system scope elsewhere.

### 8.3 Explicitly forbidden

* Representing ACL data as a separate storage category.
* Introducing cross application references not permitted by the ACL model.

## 9. Application domain isolation

### 9.1 Isolation invariant

For all object categories:

* All object references MUST resolve within the same `app_id`.

This applies to:

* Attribute source references.
* Edge source and destination references.
* Rating target references.
* ACL related attachments.

### 9.2 Explicitly forbidden

* Accepting objects that reference other application domains.
* Accepting objects that rely on implicit domain inheritance.

## 10. Inputs, outputs, and trust boundaries

### 10.1 Inputs

The object model evaluates proposed object mutations that include:

* Object category and `app_id`.
* Required fields for that category.
* Declared `owner_identity`.

### 10.2 Outputs

The object model produces one of two outcomes:

* Accept. The object satisfies all structural constraints.
* Reject. One or more constraints are violated.

### 10.3 Trust boundaries

* Caller supplied fields are not trusted.
* Object existence checks must be explicit.
* [Structural validation](03-serialization-and-envelopes.md) is mandatory before any [persistence](../03-data/01-sqlite-layout.md).

## 11. Failure and rejection behavior

### 11.1 Rejection conditions

A proposed mutation MUST be rejected if:

* Required fields are missing.
* Destination selector rules are violated.
* Referenced objects do not exist.
* Application domain isolation is violated.
* An immutable field would be modified.
* `app_id`, `type_id`, or `owner_identity` fails to resolve.

### 11.2 Failure handling guarantees

* Rejection produces no partial persistence.
* Rejection is deterministic given the proposed mutation and current graph state.
* Rejection reasons must distinguish structural violations from external [validation](../02-architecture/managers/05-schema-manager.md) failures.

## 12. Guarantees summary

When enforced as specified, this object model guarantees:

* Immutable authorship and provenance metadata.
* Strict structural validity of all graph objects.
* Referential integrity within application domains.
* Canonical representation of ACL structures using graph primitives.
