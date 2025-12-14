



# 03. Definitions and terminology

## 1. Purpose and scope

This file defines the normative terminology used across the 2WAY PoC design repository. It standardizes names for core entities, graph object types, schema concepts, sync concepts, and security concepts so that other documents can be read and reviewed without ambiguity.

This file does not define APIs, wire formats, database schemas, or protocol flows. Where a term depends on a formal structure, this file references the owning specification and constrains meaning only.

## 2. Responsibilities

### 2.1 Responsibilities

This file is responsible for:

1. Defining canonical meanings for repository level terms.
2. Fixing canonical names for the fundamental graph object types and their related concepts.
3. Defining the naming and scoping terms used for apps, types, and domains.
4. Defining security vocabulary needed to interpret authorization, signing, and revocation rules.

### 2.2 Non responsibilities

This file is not responsible for:

1. Describing how managers execute validation or persistence.
2. Defining the database schema, table layouts, or indexes.
3. Defining envelope fields, request formats, or network message layouts.
4. Defining app specific schemas or object types.

## 3. Invariants and guarantees

### 3.1 Terminology invariants

1. Terms defined in this file have a single authoritative meaning across the repository.
2. The canonical graph object type names are Parent, Attribute, Edge, Rating, ACL.
3. Canonical names must not be aliased, abbreviated, or replaced with synonyms in normative text.
4. If a document introduces a new term, it must define it locally or reference a file that defines it.

### 3.2 Repository guarantees

1. Any normative use of a term defined here is interpreted as the definition in this file.
2. Any conflicting definition elsewhere is treated as a specification error and must be corrected to match this file.

## 4. Allowed and forbidden terminology usage

### 4.1 Allowed usage

1. Using these terms verbatim as headings, identifiers, or normative labels.
2. Narrowing a term within a specific file if the file explicitly states the narrower scope and does not conflict with this file.
3. Referencing a different file for formal structure while keeping the term meaning consistent.

### 4.2 Forbidden usage

1. Redefining a term in a different document without an explicit override statement and scope.
2. Using synonyms in place of canonical object type names in normative requirements.
3. Using the same word to refer to two different concepts, even if context appears clear.

## 5. System and runtime terms

### 5.1 Node

A node is a single running 2WAY backend instance with its own local persistent state.

Properties:
1. A node assigns and maintains its own monotonic ordering for local writes.
2. A node enforces validation and authorization for all accepted mutations.
3. A node may participate in sync with peers.

A node is not defined as a cluster, shard, or externally managed service.

### 5.2 Backend

The backend is the trusted local execution environment that hosts managers and services and exposes interfaces to frontend apps.

Trust boundary:
1. The backend is trusted to enforce all validation and access control rules defined by this repository.
2. Frontend apps are not trusted by default.

### 5.3 Frontend app

A frontend app is a user facing application that interacts with the backend only through the backend’s exposed interfaces.

Constraints:
1. A frontend app does not directly invoke managers.
2. A frontend app does not bypass backend validation or authorization.

### 5.4 Manager

A manager is a backend component that owns a narrow, explicit responsibility and exposes a stable interface for that responsibility.

Constraints:
1. Managers are the only components permitted to perform their responsibility.
2. Write paths that mutate persisted graph state are mediated by the backend’s write pipeline as defined in the architecture and build guide documents.

This file does not define manager APIs.

### 5.5 Service

A service is backend resident logic that operates within a specific app or system scope using managers.

Constraints:
1. A service does not bypass manager enforced rules.
2. A service is constrained by schema and ACL enforcement for the objects it attempts to create or mutate.

## 6. App and type system terms

### 6.1 App

An app is a logical domain that defines its own schema scoped object types and semantics.

Properties:
1. App semantics are isolated. Objects and type meanings are app scoped.
2. App boundaries are enforced by schema validation and authorization rules.

### 6.2 app_id and app_slug

An app_id is the numeric identifier used to bind storage and types to an app. An app_slug is the stable string name used for human readable identification and routing.

Constraints:
1. app_id determines the per app table set in storage.
2. app_slug identifies the app in configuration and higher level interfaces.

This file does not define allocation rules for app_id.

### 6.3 Type

A type is an app scoped identifier for a specific Parent type, Attribute type, Edge type, Rating type, or ACL type.

Two representations are used across the design:
1. type_key. A stable string key used in schema definitions and documentation.
2. type_id. A numeric identifier used in persisted storage.

Constraint:
1. type_key and type_id mapping is app scoped.

### 6.4 Schema

A schema is an app scoped declaration of allowed types and allowed relationships among types.

Constraint:
1. Schema validation uses schema declared constraints to accept or reject operations.

This file does not define schema file formats, value representations, or validation algorithms. Those are defined in the schema and data model specifications.

### 6.5 Value kind

A value kind is the schema level classification used to validate the representation of an Attribute value.

In the PoC build guide schema examples, value_kind includes:
1. text.
2. number.
3. json.

This file does not define encoding rules beyond these labels.

## 7. Graph model terms

### 7.1 Graph

The graph is the set of persisted objects stored by a node across all apps.

Constraints:
1. The graph is local to a node.
2. The graph is the authoritative record for the node’s accepted operations.

### 7.2 Graph object

A graph object is a persisted record of one of the fundamental object types.

The fundamental object types are:
1. Parent.
2. Attribute.
3. Edge.
4. Rating.
5. ACL.

### 7.3 Parent

A Parent is a top level graph object that anchors ownership and is the root for related objects.

Constraints:
1. A Parent has an owning identity.
2. A Parent is used as the anchor for Attributes and as the endpoint for Edges.

This file does not define Parent fields.

### 7.4 Attribute

An Attribute is a typed value associated with a Parent.

Constraints:
1. Attribute meaning is defined by the app schema.
2. Attribute representation is validated against value kind constraints.

This file does not define Attribute fields.

### 7.5 Edge

An Edge is a typed directed relationship between two Parents.

Constraints:
1. Edge meaning is defined by the app schema.
2. Edge validity is constrained by schema allowed relations.

This file does not define Edge fields.

### 7.6 Rating

A Rating is a typed evaluative object with app scoped semantics.

Constraints:
1. Rating meaning is interpreted only within the app that defines the rating type.
2. Ratings do not imply a global reputation model.

This file does not define Rating fields.

### 7.7 ACL

An ACL is a graph object that defines visibility and mutation permissions for target objects within a defined scope.

Constraints:
1. ACL interpretation is defined by the authorization model.
2. ACL evaluation is applied to read and write decisions according to the access control specification.

This file does not define ACL fields or evaluation rules.

## 8. Operation and validation terms

### 8.1 Operation

An operation is a request to create, update, or relate graph objects.

Constraints:
1. An operation is subject to validation and authorization.
2. An operation may be rejected and therefore not persisted.

This file does not define the operation vocabulary.

### 8.2 Envelope

An envelope is a signed container used to carry one or more operations for local processing or network sync.

Constraints:
1. An envelope includes an explicit author identity reference.
2. An envelope is not trusted until verified and validated.

This file does not define envelope fields, signing formats, or encryption formats.

### 8.3 OperationContext

An OperationContext is the backend derived context used to evaluate an operation.

Constraints:
1. OperationContext binds the author identity and any scoped authority relevant to the operation.
2. OperationContext is explicitly derived, it is not inferred from transport, session, or client supplied claims.

This file does not define OperationContext fields.

## 9. Ordering and sync terms

### 9.1 global_seq

global_seq is a node local strictly monotonic sequence number assigned to accepted persisted writes.

Constraints:
1. global_seq defines a total order of accepted writes on a node.
2. global_seq is used to support incremental sync and provenance checks.

This file does not define how global_seq is stored, indexed, or transmitted.

### 9.2 domain_seq

domain_seq is a sequence number scoped to a specific sync domain as defined by the PoC build guide.

Constraint:
1. domain_seq ordering is meaningful only within its domain scope.

This file does not define domain sequencing rules beyond this scope meaning.

### 9.3 Sync

Sync is the process by which nodes exchange envelopes or derived data so that each node can accept, reject, and persist operations according to its own rules.

Constraint:
1. Sync does not imply that a node accepts all received content.

This file does not define sync protocol flows.

### 9.4 Sync domain

A sync domain is an explicit subset of data eligible for sync under defined authorization and scoping rules.

Constraints:
1. Domains constrain what can be requested and what can be sent.
2. Domain scoping limits disclosure and replication.

This file does not define domain membership rules.

### 9.5 Peer

A peer is a remote node that participates in sync with a node.

Constraints:
1. A peer is identified by an identity in the graph.
2. A peer is not inherently trusted.

This file does not define peer discovery or transport requirements.

### 9.6 sync_state

sync_state is the node maintained local record of sync progress and constraints for a specific peer.

Constraint:
1. sync_state is used to reject replayed, malformed, or out of scope sync inputs.

This file does not define sync_state structure.

## 10. Security and trust terms

### 10.1 Cryptographic identity

A cryptographic identity is the association between a graph identity and at least one public key used to verify signatures.

Constraint:
1. Authorship claims are verified against stored public keys.

This file does not define key storage layout or rotation rules.

### 10.2 Authorship

Authorship is the binding between an operation or envelope and the identity that signed it.

Constraints:
1. Authorship is explicit in the envelope.
2. Authorship is verified, not inferred.

### 10.3 Ownership

Ownership is the association between a graph object and the identity that created or controls it under system rules.

Constraint:
1. Ownership is used to enforce mutation rules and reject unauthorized writes.

This file does not define ownership enforcement logic.

### 10.4 Trust boundary

A trust boundary is any interface where data crosses from a less trusted environment to a more trusted environment.

In this repository, the core trust boundaries include:
1. Frontend app to backend interface boundary.
2. Network input to node boundary.
3. App scoped logic to system scoped logic boundary.

This file does not define mitigations beyond vocabulary.

### 10.5 Revocation

Revocation is a graph represented event that invalidates a previously valid key or scoped authority.

Constraints:
1. Revocation affects acceptance of future envelopes signed with the revoked key.
2. Revocation does not rewrite historical persisted objects.

This file does not define revocation object structure.

## 11. Failure, rejection, and invalid input handling

### 11.1 Terminology failures

1. If a normative document uses an undefined term without reference, it is a specification error.
2. If two documents define the same term differently, it is a specification error.

### 11.2 Runtime interpretation failures

For any component that references terms from this file:

1. If an input claims a type, domain, identity, or author that cannot be resolved under the repository’s defined structures, the input is invalid.
2. Invalid inputs are rejected, they are not partially applied.
3. Rejection must not create new persisted graph objects.

This file does not define error codes or logging requirements.

### 11.3 Trust boundary failures

1. Inputs received across a trust boundary are treated as untrusted until validated by the backend’s defined validation and authorization pipeline.
2. If validation cannot be completed due to missing prerequisites, the input is rejected.

This file does not define prerequisite acquisition behavior.
