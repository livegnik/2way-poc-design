# 03 Definitions and terminology

Defines canonical terms used across the 2WAY design repository. Specifies normative meanings for core entities, graph objects, and validation concepts. Defines constraints and usage rules for terminology.

For the meta specifications, see [03-definitions-and-terminology meta](../10-appendix/meta/00-scope/03-definitions-and-terminology-meta.md).

Previous drafts used SBPS, IRS, SOS, OCS and 'extension/plugin' terminology. These are now Setup Service, Identity Service, Sync Service, Admin Service, and app service(s).

## 1. Invariants and guarantees

### 1.1 Terminology invariants

- Terms defined in this file have a single authoritative meaning across the repository.
- The canonical object type names are defined in [Section 5](#5-graph-model-terms).
- Canonical names must not be aliased, abbreviated, or replaced with synonyms in normative text.
- If a document introduces a new term, it must define it locally or reference a file that defines it.

### 1.2 Repository guarantees

- Any normative use of a term defined here is interpreted as the definition in this file.
- Any conflicting definition elsewhere is treated as a specification error and must be corrected to match this file.

## 2. Allowed and forbidden terminology usage

### 2.1 Allowed usage

- Using these terms verbatim as headings, identifiers, or normative labels.
- Narrowing a term within a specific file if the file explicitly states the narrower scope and does not conflict with this file.
- Referencing a different file for formal structure while keeping the term meaning consistent.

### 2.2 Forbidden usage

- Redefining a term in a different document without an explicit override statement and scope.
- Using synonyms in place of canonical object type names in normative requirements.
- Using the same word to refer to two different concepts, even if context appears clear.

### 2.3 Naming conventions

`snake_case` is lowercase ASCII text with underscores used to separate words.

## 3. System and runtime terms

### 3.1 Backend

`backend` is the trusted local execution environment that hosts system logic and exposes interfaces to external clients.

Trust boundary:

- The backend is trusted to enforce all validation and access control rules defined by this repository.
- External clients are not trusted by default.

### 3.2 Manager

`manager` is a backend component that owns a narrow, explicit responsibility and exposes a stable interface for that responsibility.

Constraints:

- Managers are the only backend components permitted to perform their responsibility directly.
- Write paths that mutate persisted state are mediated by the backend write pipeline as defined by the architecture specifications.

### 3.3 Service

`service` is backend-resident logic that implements scoped or system behavior using managers.

Constraints:

- A service does not bypass manager enforced rules.
- A service is constrained by validation and authorization rules for the objects it attempts to create or mutate.

### 3.4 System service

`system service` is a backend-resident service that implements system-scoped behavior across apps under core policy.

Constraints:

- A system service operates under system-scoped schema and authorization rules.
- A system service does not assert app-specific semantics beyond those explicitly delegated.

### 3.5 Application service

`application service` is a backend-resident service that implements app-scoped behavior for a specific app.

Constraints:

- An application service is bound to a single app context.
- An application service does not bypass app-scoped schema or ACL enforcement.

### 3.6 Frontend

`frontend` is any external client surface that initiates requests into the backend, including user-facing apps, automation clients, and integration tooling.

Constraints:

- Frontend inputs are untrusted until validated by the backend.
- Frontend behavior does not define or override backend rules.

### 3.7 Frontend app

`frontend app` is a user-facing application that interacts with the backend only through the backend's exposed interfaces.

Constraints:

- A frontend app does not directly invoke managers.
- A frontend app does not bypass backend validation or authorization.

### 3.8 Node

`node` is a single running 2WAY backend instance with its own local persistent state.

Constraints:

- A node assigns and maintains its own monotonic ordering for local accepted writes.
- A node enforces validation and authorization for all accepted mutations.
- A node may exchange data with other nodes.

`node` is not a cluster, shard, or externally managed service.

### 3.9 Identity

`identity` is a first-class actor represented in the system and used to attribute actions and authority.

Constraints:

- Every identity is bound to at least one public key used to verify signatures.
- The public key material used for verification is stored in persisted storage under the identity's root record.
- Identity resolution for an operation is explicit and performed by the backend, not inferred from transport metadata.

### 3.10 identifier, identity_id, and owner_identity

`identifier` is a stable value used to uniquely reference a specific entity or object within its defined scope.

`identity_id` is the identifier for an identity.

`owner_identity` is the identity_id recorded as the owner of a graph object.

## 4. App and type system terms

### 4.1 App

`app` is a logical domain that defines its own object semantics.

Properties:

- App semantics are isolated. Objects and their meanings are app-scoped.
- App boundaries are enforced by validation and authorization rules.

### 4.2 app_id and app_slug

`app_id` is the numeric identifier used to bind storage and object identifiers to an app. `app_slug` is the stable string name used for human-readable identification and routing.

Constraints:

- app_id determines the per-app table set in storage.
- app_slug identifies the app in configuration and higher-level interfaces.

### 4.3 Type

`type` is an app-scoped identifier for a specific object category within an app.

Two representations are used:

- `type_key` is a stable string key used in schema definitions and normative text.
- `type_id` is a numeric identifier used in persisted storage.

Constraint:

- type_key to type_id mapping is app-scoped.

### 4.4 Schema

`schema` is an app-scoped declaration of allowed types and relationships among types.

Constraint:

- Schema validation uses schema declared constraints to accept or reject operations.

### 4.5 app_0

`app_0` is the reserved system app identifier used for core system identities, keys, and system-scoped schema.

### 4.6 Value kind

`value kind` is the schema level classification used to validate the representation of a value.

In this schema model, `value_kind` includes:

- text.
- number.
- json.

## 5. Graph model terms

### 5.1 Graph

`graph` is the set of persisted objects stored by a node across all apps.

Constraints:

- The graph is local to a node.
- The graph is the authoritative record for the node's accepted operations.

### 5.2 Graph object

`graph object` is a persisted record of one of the fundamental object types.

The fundamental object types are:

- `Parent` is the root object that anchors ownership and related objects. See [Section 5.3](#53-parent).
- `Attribute` is a typed value associated with a Parent. See [Section 5.4](#54-attribute).
- `Edge` is a typed directed relationship between two Parents. See [Section 5.5](#55-edge).
- `Rating` is a typed evaluative object with app-scoped semantics. See [Section 5.6](#56-rating).
- `ACL` is a permissions object that governs visibility and mutation within a scope. See [Section 5.7](#57-acl).

### 5.3 Parent

`Parent` is a top-level graph object that anchors ownership and is the root for related objects.

Constraints:

- A Parent has a designated identity used for authorization decisions.
- A Parent is the anchor for Attributes and an endpoint for Edges.

### 5.4 Attribute

`Attribute` is a typed value associated with a Parent.

Constraints:

- Attribute meaning is defined by the app schema.
- Attribute representation is validated against value kind constraints.

### 5.5 Edge

`Edge` is a typed directed relationship between two Parents.

Constraints:

- Edge meaning is defined by the app schema.
- Edge validity is constrained by schema declared allowed relations.

### 5.6 Rating

`Rating` is a typed evaluative object with app-scoped semantics.

Constraints:

- Rating meaning is interpreted only within the app that defines the rating type.
- Ratings do not imply a global reputation model.

### 5.7 ACL

`ACL` is a graph object that defines visibility and mutation permissions for target objects within a defined scope.

Constraints:

- ACL interpretation is defined by the authorization model.
- ACL evaluation is applied to read and write decisions according to the access control specifications.

### 5.8 Graph object identifiers

`parent_id` is the app-scoped identifier of a Parent.

`attr_id` is the app-scoped identifier of an Attribute.

`edge_id` is the app-scoped identifier of an Edge.

`rating_id` is the app-scoped identifier of a Rating.

`object_id` is a generic identifier for a graph object when the specific object type is not material to the statement.

`object_kind` is the object type category label used to distinguish Parent, Attribute, Edge, Rating, and ACL.

`value_json` is the JSON-encoded representation of an Attribute value when serialized or persisted.

### 5.9 Object linkage identifiers

`src_parent_id` is the identifier of the source Parent in a directed Edge.

`dst_parent_id` is the identifier of the destination Parent in a directed Edge.

`target_parent_id` is the identifier of the Parent that an object refers to.

`target_attr_id` is the identifier of the Attribute that an object refers to.

`subject_parent_id` is the identifier of the Parent that an action, message, or evaluation is about.

`dst_attr_id` is the identifier of the destination Attribute when an Attribute references another Attribute.

## 6. Operation and validation terms

### 6.1 Operation

`operation` is a request to create, update, or relate graph objects.

Constraints:

- An operation is subject to validation and authorization.
- An operation may be rejected and therefore not persisted.

### 6.2 Envelope

`envelope` is a signed container used to carry one or more operations for local processing or inter-node exchange.

Constraints:

- An envelope includes an explicit author identity reference.
- An envelope is not trusted until verified and validated.

### 6.3 OperationContext identifiers

`requester_identity_id` is the identifier of the identity resolved as the requester for an operation.

`device_id` is the identifier of a device acting on behalf of an identity.

`delegated_key_id` is the identifier of a delegated signing key used for scoped authority.

`actor_type` is the declared caller category such as user, service, automation, or delegation.

`capability` is the explicit action label evaluated by authorization rules.

`is_remote` is a flag indicating whether the context originated from inter-node exchange.

`sync_domain` is the identifier used to scope inter-node exchange processing to a specific domain.

`remote_node_identity_id` is the identifier of the remote node's identity for inter-node exchange processing.

`trace_id` is the identifier used to correlate related operations and requests across logs and telemetry.

`correlation_id` is an optional identifier used to correlate multiple related requests.

`app_version` is an optional version identifier for a frontend app or service.

`app_variant` is an optional variant identifier for a frontend app.

`schema_version` is an optional identifier for a schema release.

`user_id` is an external user identifier supplied by a client and treated as non-authoritative metadata.

`locale` is an optional client locale identifier.

`timezone` is an optional client timezone identifier.

### 6.4 OperationContext

`OperationContext` is the backend derived context used to validate and authorize an operation.

Constraints:

- OperationContext binds the `requester_identity_id` and any scoped authority relevant to the operation.
- OperationContext is explicitly derived; it is not inferred from transport metadata or client supplied claims.
- For inter-node exchange processing, OperationContext may include `sync_domain` and `remote_node_identity_id`.
- OperationContext includes `trace_id` for request correlation.

### 6.5 Operation kind labels

`parent_create`, `parent_update`, `attr_create`, `attr_update`, `edge_create`, `edge_update`, `rating_create`, and `rating_update` are operation kind labels that describe creation or update of the corresponding object type.

## 7. Ordering and sync terms

### 7.1 global_seq

`global_seq` is a node-local strictly monotonic sequence number assigned to accepted persisted writes.

Constraints:

- global_seq defines a total order of accepted writes on a node.
- global_seq is used to support incremental exchange and provenance checks.

### 7.2 Sync

`sync` is the process by which nodes exchange envelopes or derived data so that each node can accept, reject, and persist operations according to its own rules.

Constraint:

- `sync` does not imply that a node accepts all received content.

### 7.3 Sync domain

`sync domain` is an explicit subset of data eligible for sync under defined authorization and scoping rules.

Constraints:

- Domains constrain what can be requested and what can be sent.
- Domain scoping limits disclosure and replication.

### 7.4 domain_seq

`domain_seq` is a sequence number scoped to a specific sync domain.

Constraint:

- domain_seq ordering is meaningful only within its domain scope.

### 7.5 Peer

`peer` is a remote node that participates in sync with a node.

Constraints:

- A peer is identified by an identity in the graph.
- A peer is not inherently trusted.

### 7.6 sync_state

`sync_state` is the node maintained local record of sync progress and constraints for a specific peer.

Constraint:

- sync_state is used to reject replayed, malformed, out of order, or out of scope sync inputs.

### 7.7 sync_flags

`sync_flags` is a bitset or enumerated label set used to express sync related state or eligibility for a graph object.

### 7.8 from_seq and to_seq

`from_seq` is the lower bound sequence for a sync request or response window.

`to_seq` is the upper bound sequence for a sync request or response window.

### 7.9 peer_id and sender_identity

`peer_id` is the identifier for a peer record maintained by a node to track sync state.

`sender_identity` is the identity that authored or transmitted a sync message or envelope.

## 8. Security and trust terms

### 8.1 Cryptographic identity

`cryptographic identity` is the association between an identity and at least one public key used to verify signatures.

Constraint:

- Signature claims are verified against stored public keys.

### 8.2 Authorship

`authorship` is the binding between an operation or envelope and the identity that signed it.

Constraints:

- `authorship` is explicit in the envelope.
- `authorship` is verified, not inferred.

### 8.3 Ownership

`ownership` is the association between a graph object and the identity that owns it under system rules.

Constraint:

- `ownership` is used to enforce mutation rules and reject unauthorized writes.

### 8.4 Trust boundary

`trust boundary` is any interface where data crosses from a less trusted environment to a more trusted environment.

Core trust boundaries include:

- Frontend app to backend interface boundary.
- Network input to node boundary.
- App-scoped logic to system-scoped logic boundary.

### 8.5 Revocation

`revocation` is a graph represented event that invalidates a previously valid key or scoped authority.

Constraints:

- Revocation affects acceptance of future envelopes signed with the revoked key.
- Revocation does not rewrite historical persisted objects.

## 9. Failure, rejection, and invalid input handling

### 9.1 Terminology failures

- If a normative document uses an undefined term without reference, it is a specification error.
- If two documents define the same term differently, it is a specification error.

### 9.2 Runtime interpretation failures

For any component that references terms from this file:

- If an input claims a type, domain, identity, or author that cannot be resolved under the repository's defined structures, the input is invalid.
- Invalid inputs are rejected, they are not partially applied.
- Rejection must not create new persisted graph objects.

### 9.3 Trust boundary failures

- Inputs received across a trust boundary are treated as untrusted until validated by the backend's defined validation and authorization pipeline.
- If validation cannot be completed due to missing prerequisites, the input is rejected.

