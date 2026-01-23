



# 03 Serialization and envelopes

## 1. Purpose and scope

This document defines the normative envelope structures and serialization rules used by 2WAY for local graph mutations and for node to node sync packages. It specifies field names, required and optional fields, how operations are represented, what is signed, and what must be rejected.

This specification references:

* [01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)
* [02-object-model.md](02-object-model.md)
* [04-cryptography.md](04-cryptography.md)
* [05-keys-and-identity.md](05-keys-and-identity.md)
* [06-access-control-model.md](06-access-control-model.md)
* [07-sync-and-consistency.md](07-sync-and-consistency.md)
* [08-network-transport-requirements.md](08-network-transport-requirements.md)

This document does not define [object semantics](02-object-model.md), [schema content](../02-architecture/managers/05-schema-manager.md), [ACL logic](06-access-control-model.md), [sync selection rules](07-sync-and-consistency.md), or [storage layout](../03-data/01-sqlite-layout.md). Those are defined elsewhere.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Envelope types and their required fields.
* Operation identifiers and operation record shapes for [Parent](02-object-model.md), [Attribute](02-object-model.md), [Edge](02-object-model.md), [Rating](02-object-model.md).
* Serialization constraints for interoperability, including field naming conventions.
* The signed portion of envelopes that carry signatures.
* Structural validation and rejection conditions for malformed envelopes.

This specification does not cover the following:

* Mapping `type_key` to `type_id`, or validating [schema semantics](../02-architecture/managers/05-schema-manager.md).
* Evaluating [authorization](06-access-control-model.md) and ACL rules.
* Assigning `global_seq` for local writes, or managing [sync state](07-sync-and-consistency.md).
* Defining transport framing, session tokens, or peer discovery (see [08-network-transport-requirements.md](08-network-transport-requirements.md)).

## 3. Invariants and guarantees

### 3.1 Invariants

* All write operations, including local writes, are represented as graph message envelopes.
* Envelope keys use lowercase snake_case.
* Operation identifiers use supervised lowercase naming, for example `parent_create`, `attr_update`.
* An envelope contains one or more operations, and is processed atomically, either all operations apply or none apply.
* Private key material is never serialized into envelopes.

### 3.2 Guarantees

A structurally valid envelope provides these guarantees:

* Deterministic interpretation of fields, because field names and types are fixed.
* Atomic processing boundaries at the [Graph Manager](../02-architecture/managers/07-graph-manager.md) boundary, subject to downstream validation.
* A single declared author context for remote sync packages, carried as metadata and enforced by the receiving node.

This file does not define [authorization](06-access-control-model.md), [schema validity](../02-architecture/managers/05-schema-manager.md), or application semantics, and therefore does not guarantee them.

## 4. Allowed and forbidden behaviors

### 4.1 Explicitly allowed

* Local services, app extension services, and automation jobs may submit graph message envelopes to [Graph Manager](../02-architecture/managers/07-graph-manager.md) using an [OperationContext](../02-architecture/services-and-apps/05-operation-context.md) supplied by the HTTP layer or constructed by the local entrypoint.
* [State Manager](../02-architecture/managers/09-state-manager.md) may submit remote graph message envelopes to [Graph Manager](../02-architecture/managers/07-graph-manager.md) using an [OperationContext](../02-architecture/services-and-apps/05-operation-context.md) that marks the request as remote and binds it to a [sync domain](07-sync-and-consistency.md).
* A graph message envelope may contain a mixture of operation kinds, provided all are for supported object categories and pass validation.
* A sync package may carry additional metadata fields that are required for sync state updates.

### 4.2 Explicitly forbidden

* Any component other than [Graph Manager](../02-architecture/managers/07-graph-manager.md) applies operations to persistent graph state.
* Any write path that bypasses graph message envelopes.
* Any envelope or operation that uses non snake_case keys.
* Any operation identifier outside the supervised set defined in this document.
* Any envelope that includes private keys, raw secrets, or key store material.
* Any envelope that attempts to redefine schema, [ACL semantics](06-access-control-model.md), or manager boundaries via ad hoc fields.

## 5. Naming and serialization conventions

### 5.1 Key naming

* All envelope and operation fields use lowercase snake_case.
* [Sync domain identifiers](07-sync-and-consistency.md) use lowercase with underscores, for example `messages`, `contacts`.
* Operation identifiers use lowercase with underscores and are supervised, for example `edge_create`.

### 5.2 JSON representation

Envelopes and operations are represented as JSON objects in documentation and in the PoC API surfaces. Binary formats are avoided.

Constraints:

* Strings are UTF-8.
* Integers are JSON numbers and must be representable losslessly in the target implementation.
* Objects must not contain duplicate keys.
* Unknown keys are rejected unless explicitly permitted by the envelope type definition in this document.

## 6. Envelope types

2WAY uses one logical envelope format for graph operations. That same format is used for local writes and for remote sync, with additional metadata for sync packages.

Two envelope types are defined:

* Graph message envelope, used for local writes and as the inner payload of sync packages.
* Sync package envelope, used for node to node transmission, which carries a graph message envelope plus sync metadata and a signature.

## 7. Graph message envelope

### 7.1 Purpose

A graph message envelope represents one or more graph operations to be applied atomically by [Graph Manager](../02-architecture/managers/07-graph-manager.md).

### 7.2 Structure

A graph message envelope is a JSON object with these required fields:

* `ops`. An array of one or more operation objects, each conforming to Section 8.
* `trace_id`. An opaque identifier used for logging and correlation. It must be a string.

No other fields are permitted in a graph message envelope.

### 7.3 Processing boundary

* [Graph Manager](../02-architecture/managers/07-graph-manager.md) processes the envelope as a single transaction boundary.
* If any operation is rejected by structural validation, [schema validation](../02-architecture/managers/05-schema-manager.md), [ACL enforcement](06-access-control-model.md), or [graph invariants](02-object-model.md), the entire envelope is rejected.

## 8. Operation records

### 8.1 Common fields

Each operation object MUST contain:

* `op`. The operation identifier, defined in Section 8.2.
* `app_id`. Integer identifier of the app domain for the object ([01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).
* `type_key` or `type_id`. Exactly one MUST be present.

  * `type_key`. A human-readable type key defined by the app schema.
  * `type_id`. An integer type id compiled by [Schema Manager](../02-architecture/managers/05-schema-manager.md).
* `owner_identity`. Integer identity id that owns the object targeted or created by the operation ([05-keys-and-identity.md](05-keys-and-identity.md)).
* `payload`. A JSON object whose shape is defined per operation kind below.

Constraints:

* `app_id` and `owner_identity` are required for all operation kinds.
* An operation MUST NOT contain both `type_key` and `type_id`.
* If `type_key` is present, it MUST be a string.
* If `type_id` is present, it MUST be an integer.

### 8.2 Operation identifiers

The supervised operation identifiers are:

* `parent_create`
* `parent_update`
* `attr_create`
* `attr_update`
* `edge_create`
* `edge_update`
* `rating_create`
* `rating_update`

No other `op` values are permitted.

Deletion operations do not exist in the PoC. Pruning requires complexity outside of the scope of this PoC.

### 8.3 Parent operations

For `parent_create` and `parent_update`, `payload` MUST contain:

* `parent_id`. Required for `parent_update`. Forbidden for `parent_create` unless the object model defines externally supplied identifiers.
* Additional fields required by the Parent object model are defined in [02-object-model.md](02-object-model.md).

### 8.4 Attribute operations

For `attr_create` and `attr_update`, `payload` MUST contain:

* `parent_id`. The Parent the Attribute attaches to.
* `value`. The attribute value.

For `attr_update`, `payload` MAY include:

* `attr_id`. If present, it identifies the specific attribute record being updated. If absent, the update target resolution rules are defined in [02-object-model.md](02-object-model.md).

### 8.5 Edge operations

For `edge_create` and `edge_update`, `payload` MUST contain:

* `src_parent_id`. Source Parent id.
* `dst_parent_id`. Destination Parent id.

For `edge_update`, `payload` MAY include:

* `edge_id`. If present, it identifies the specific edge record being updated. If absent, the update target resolution rules are defined in [02-object-model.md](02-object-model.md).

### 8.6 Rating operations

For `rating_create` and `rating_update`, `payload` MUST contain:

* `subject_parent_id`. The Parent being rated.
* `value`. The rating value.

For `rating_update`, `payload` MAY include:

* `rating_id`. If present, it identifies the specific rating record being updated. If absent, the update target resolution rules are defined in [02-object-model.md](02-object-model.md).

### 8.7 Structural constraints across operations

* Operations MUST NOT include `global_seq`. `global_seq` is assigned during application by [Graph Manager](../02-architecture/managers/07-graph-manager.md) for local writes, and is not a client controlled field.
* Operations MUST NOT include `sync_flags`. `sync_flags` is determined by [schema](../02-architecture/managers/05-schema-manager.md) and [domain membership](07-sync-and-consistency.md) during application.
* Operations MUST NOT include ACL rule material inline. ACL evaluation inputs are defined by the [ACL model](06-access-control-model.md).

## 9. Sync package envelope

### 9.1 Purpose

A sync package envelope is the unit transmitted between nodes for synchronization. It carries sync metadata and a graph message envelope. In the PoC, outbound sync packages are signed using the node key defined in [05-keys-and-identity.md](05-keys-and-identity.md).

### 9.2 Structure

A sync package envelope is a JSON object with these required fields:

* `sender_identity`. Integer identity id of the sending node identity ([05-keys-and-identity.md](05-keys-and-identity.md)).
* `sync_domain`. String domain name, for example `messages` (see [07-sync-and-consistency.md](07-sync-and-consistency.md)).
* `from_seq`. Integer. The first sequence number included, computed as last known sequence plus one.
* `to_seq`. Integer. The highest sequence number included.
* `envelope`. A graph message envelope object as defined in Section 7.
* `signature`. String. A secp256k1 signature over the signed portion defined in Section 9.3 (see [04-cryptography.md](04-cryptography.md)).

No other fields are permitted in a sync package envelope.

### 9.3 Signed portion

The signed portion of a sync package envelope is the JSON serialization of the sync package envelope excluding the `signature` field.

Constraints:

* The sender MUST serialize the signed portion deterministically so that the receiver can reproduce the same byte sequence for verification.
* The receiver MUST verify the signature before applying any enclosed operations.
* Verification uses the sender public key resolved from the sender identity as distributed through identity exchange and stored in the graph (see [05-keys-and-identity.md](05-keys-and-identity.md)).

The cryptographic algorithms and key distribution rules are defined in [04-cryptography.md](04-cryptography.md) and [05-keys-and-identity.md](05-keys-and-identity.md). This section defines only the binding between the signature and the serialized package fields.

### 9.4 Relationship to OperationContext

When a node receives a sync package envelope:

* [State Manager](../02-architecture/managers/09-state-manager.md) constructs an [OperationContext](../02-architecture/services-and-apps/05-operation-context.md) with `is_remote=True`, `sync_domain=sync_domain`, and `remote_node_identity_id` bound to the peer identity.
* [Graph Manager](../02-architecture/managers/07-graph-manager.md) applies the enclosed graph message envelope under that context.

This document does not define OperationContext fields beyond those required to interpret the sync package metadata.

## 10. Validation and rejection

### 10.1 Structural validation

An envelope MUST be rejected before any semantic validation if any of the following occur:

* The top-level JSON is not an object.
* Required fields are missing.
* Unknown fields are present for the envelope type.
* Any field has the wrong JSON type.
* `ops` is empty, or not an array.
* Any operation object is missing required fields, contains unknown fields not defined by this document, or uses an unsupported `op`.
* An operation contains both `type_key` and `type_id`, or contains neither.
* Any operation contains forbidden fields such as `global_seq` or `sync_flags`.

### 10.2 Signature validation for sync packages

A sync package envelope MUST be rejected if:

* [Signature verification](04-cryptography.md) fails.
* The sender identity cannot be resolved to a public key (see [05-keys-and-identity.md](05-keys-and-identity.md)).
* The sender public key is revoked by local policy.

Signature verification failure is terminal for that package. The receiver MUST NOT attempt to partially process the enclosed operations.

### 10.3 Sequence validation for sync packages

A sync package envelope MUST be rejected if:

* `from_seq` is greater than `to_seq`.
* The `(peer_id, sync_domain)` sync_state indicates the package is out of order, replayed, or inconsistent with the expected next sequence.

The specific sync_state rules are defined by [07-sync-and-consistency.md](07-sync-and-consistency.md). This section defines only the required envelope fields and their basic ordering constraints.

### 10.4 Failure handling and side effects

On rejection:

* No enclosed operations are applied.
* No partial writes occur.
* The receiver may record a local log entry as defined by [02-architecture/managers/12-log-manager.md](../02-architecture/managers/12-log-manager.md) and may update local rate limiting or abuse tracking state as defined elsewhere.
* Error information returned to a peer, if any, is constrained to avoid leaking internal state.

## 11. Trust boundaries

* Graph message envelopes received over local APIs are not trusted for [authorization](06-access-control-model.md) or [schema correctness](../02-architecture/managers/05-schema-manager.md). They are trusted only as input data and are validated by [Graph Manager](../02-architecture/managers/07-graph-manager.md), [Schema Manager](../02-architecture/managers/05-schema-manager.md), and [ACL Manager](../02-architecture/managers/06-acl-manager.md).
* Sync package envelopes received from peers are untrusted until [signature verification](04-cryptography.md) and structural validation succeed.
* [Network Manager](../02-architecture/managers/10-network-manager.md) provides transport and cryptography services, but does not interpret graph operations. [Graph Manager](../02-architecture/managers/07-graph-manager.md) remains the authority for mutation correctness, subject to [schema](../02-architecture/managers/05-schema-manager.md) and [ACL enforcement](06-access-control-model.md).
