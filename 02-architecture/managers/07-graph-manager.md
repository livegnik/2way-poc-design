



# 07 Graph Manager

## 1. Purpose and scope

### 1.1 Purpose

The Graph Manager is the authoritative coordinator for graph state access within the local node. It is the only permitted write path for graph objects, and it provides the canonical read surface for graph objects where access control and application scoping must be enforced.

### 1.2 Scope

This document defines responsibilities, boundaries, invariants, guarantees, allowed and forbidden behaviors, component interactions, and failure handling for the Graph Manager.

This file specifies graph level access behavior only. It does not define schema content, access control policy logic, synchronization protocol behavior, network transport, or storage internals, except where interaction boundaries are required.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Acting as the single entry point for all persisted mutations of Parents, Attributes, Edges, and Ratings.
* Accepting graph envelopes from trusted in process components only, including local services and State Manager for remote application.
* Validating envelope structure and operation shape at the graph layer.
* Delegating type resolution and schema validation to Schema Manager.
* Delegating authorization decisions for reads and writes to ACL Manager.
* Enforcing application scoping for all reads and writes.
* Enforcing serialized write ordering and global sequencing for all accepted mutations.
* Persisting accepted envelopes atomically through Storage Manager.
* Publishing semantic graph events after commit through Event Manager.
* Providing canonical read operations for graph objects via Storage Manager, with authorization and scoping enforced by Graph Manager.
* Providing bounded traversal primitives required to support authorization checks that depend on graph distance.

This specification does not cover the following:

* Schema definition, migration, or versioning behavior.
* The meaning of types, fields, or application semantics.
* The content of access control policies, rule evaluation, or policy storage.
* Construction of sync packages, per peer sync state, or inbound and outbound sync flows.
* Network transport, encryption, or peer management.
* Storage schemas, SQL details, and indexing strategies beyond required read and write boundaries.
* Application specific query engines, search, ranking, analytics, or denormalized views.

## 3. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* All persisted mutations of Parents, Attributes, Edges, and Ratings pass through the Graph Manager.
* The Graph Manager never performs a persisted write without schema validation and authorization evaluation completing successfully.
* The Graph Manager never returns graph object data to a caller unless authorization evaluation permits that read.
* Graph reads and writes are scoped to a single `app_id`, and cross app access is rejected.
* Envelope application is atomic, either all operations in an accepted envelope are committed, or none are.
* Global sequencing for committed mutations is strictly monotonic and assigned by a serialized write path.
* Callers cannot choose or influence sequencing, storage controlled fields, or sync participation metadata.
* The Graph Manager does not emit mutation events before commit.
* Graph Manager behavior is deterministic given identical inputs and identical persisted state at evaluation time.

These guarantees must hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 4. Inputs, outputs, and trust boundaries

### 4.1 Inputs

The Graph Manager accepts:

* An OperationContext for every operation, read or write.
* A graph envelope for write requests.
* A graph read request descriptor for read requests.

OperationContext includes, at minimum:

* Requesting identity identifier.
* Target `app_id`.
* Execution mode, local or remote.
* Sync domain identifier when applicable.
* Remote node identity when applicable.
* Trace identifier.

All inputs are treated as untrusted and must be validated.

### 4.2 Outputs

The Graph Manager returns:

* For writes, an acceptance or rejection result for the entire envelope.
* For accepted writes, assigned global sequence values and created identifiers when required by the caller.
* For reads, a result set containing only authorized objects, and only within the requested application scope.
* For all failures or rejections, a structured error code and a narrow reason suitable for propagation and logging.

Side effects include:

* Persisted state mutations for accepted writes.
* Post commit event publication.
* Audit and diagnostics logging.

### 4.3 Trust boundaries

The Graph Manager relies on the following components as authorities:

* Schema Manager for type existence, type mapping, structural validation, value constraints, and domain membership used for sync participation metadata.
* ACL Manager for allow or deny decisions on read and write operations, including rules that depend on graph structure.
* Storage Manager for transactional persistence and allocation of globally ordered sequence identifiers.
* Event Manager for event delivery.

The Graph Manager does not trust callers to provide correct type identifiers, ownership metadata, sync scope, or safe values.

## 5. Allowed and forbidden behaviors

### 5.1 Explicitly allowed behaviors

The Graph Manager allows:

* Write envelopes from local services, subject to schema validation and authorization.
* Write envelopes from State Manager for remote application, subject to schema validation, authorization, and additional restrictions conveyed by OperationContext.
* Read requests for Parents, Attributes, Edges, and Ratings, subject to authorization and application scoping.
* Bounded adjacency reads, such as attributes under a parent, edges adjacent to a parent, and ratings attached to a target, subject to authorization.
* Bounded traversal reads required to support authorization checks that depend on graph distance, subject to strict resource limits.

### 5.2 Explicitly forbidden behaviors

The Graph Manager forbids:

* Persisted graph writes performed by any other component.
* Any bypass of schema validation or authorization evaluation.
* Returning any object or object field to a caller when authorization does not permit the read.
* Cross app reads or writes, including following references across application boundaries.
* Caller supplied values for storage controlled fields, including global sequencing and sync participation metadata.
* Partial application of write envelopes.
* Emitting mutation events prior to a successful commit.
* Exposing unbounded queries or traversals that can cause unbounded scans, unbounded memory growth, or unbounded response sizes.

## 6. Write path behavior

### 6.1 Processing order

For each received write envelope, Graph Manager enforces the following order:

* Envelope structural validation.
* Per operation schema validation and type resolution.
* Per operation authorization evaluation.
* Acquisition of the serialized write context.
* Sequence allocation, sync participation metadata derivation, and persistence.
* Transaction commit.
* Post commit event publication and logging.

No later step occurs if an earlier step fails.

### 6.2 Envelope structural validation

The Graph Manager validates that:

* The envelope targets exactly one `app_id`.
* Each operation is a supported graph mutation kind.
* Each operation includes required identifiers and references for its kind.
* The envelope does not attempt to supply storage controlled fields.
* Internal references are consistent, including references to objects created earlier in the same envelope, if such references are allowed by the envelope format used by callers.

Structural validation failure rejects the entire envelope.

### 6.3 Schema validation and type resolution

For each operation, Graph Manager invokes Schema Manager to:

* Validate that the operation kind is permitted for the referenced type.
* Map `type_key` to internal identifiers used by storage.
* Validate value representations and constraints for Attribute and Rating operations.
* Provide domain membership needed to derive sync participation metadata.

Schema Manager rejections reject the entire envelope.

### 6.4 Authorization evaluation

For each operation, Graph Manager invokes ACL Manager with:

* OperationContext.
* Object kind and type identifiers.
* Ownership and authorship metadata required for evaluation.
* Local or remote mode, and remote identity metadata when applicable.

Any denial rejects the entire envelope.

### 6.5 Sequencing and persistence

For accepted envelopes, Graph Manager:

* Obtains strictly increasing global sequence identifiers through Storage Manager within a serialized write context.
* Persists all operations within a single transaction.
* Derives and writes sync participation metadata from schema domain definitions only.
* Releases the serialized write context after commit.

Graph Manager does not perform event publication or network related work while holding the serialized write context.

### 6.6 Post commit events

After commit, Graph Manager publishes semantic events via Event Manager. Events are semantic and not required to be per row. Events include:

* `app_id`.
* Affected object kinds and identifiers.
* The global sequence range for the committed envelope.
* Trace identifier when available.

Event payloads exclude sensitive values unless explicitly required by the consumer and permitted by applicable read authorization rules at the consumer boundary.

## 7. Read path behavior

### 7.1 Read surface

The Graph Manager provides read operations over persisted graph objects, limited to:

* Direct reads by identifier for Parents, Attributes, Edges, and Ratings.
* Bounded adjacency reads, limited to direct relationships:

  * Attributes under a Parent.
  * Edges adjacent to a Parent.
  * Ratings attached to a Parent or Attribute.
* Minimal header reads used for validation and authorization evaluation, including type identifiers and ownership metadata.

Read operations are scoped to a single `app_id` per request.

### 7.2 Read processing order

For each read request, Graph Manager enforces:

* Structural validation of request parameters.
* Authorization evaluation through ACL Manager for the requested read scope.
* Storage reads through Storage Manager.
* Result filtering to ensure only authorized objects are returned.

If authorization cannot be determined due to missing prerequisite objects, the read is rejected.

### 7.3 Authorization on reads

Read authorization is mandatory. Graph Manager:

* Invokes ACL Manager for the read operation, using OperationContext and requested scope.
* Applies allow or deny outcomes to the result set.
* Ensures no unauthorized object identifiers or fields are returned.

### 7.4 Resource limits on reads

Read operations must be bounded. Graph Manager enforces:

* A maximum number of returned objects per request.
* A maximum number of storage rows scanned for adjacency reads.
* Strict rejection for requests that would exceed configured limits.

Limits apply identically for local and remote contexts.

## 8. Bounded traversal support for authorization

### 8.1 Purpose

Some authorization decisions depend on whether two identities or objects are connected within a bounded number of steps. The Graph Manager provides traversal primitives to support such authorization checks without exposing an unbounded query surface.

### 8.2 Traversal boundaries

Traversal support in Graph Manager is restricted to:

* Existence checks and bounded discovery required for authorization evaluation.
* Fixed maximum depth as defined by configuration or schema constraints.
* Fixed maximum frontier size and total visited node count per request.

Traversal support is not a general purpose query engine. It is not intended to return arbitrary path details to callers.

### 8.3 Data exposure constraints

Traversal operations must not expose more data than required for the authorization decision:

* Callers receive boolean or minimal identifiers only when explicitly permitted by ACL Manager for that context.
* Intermediate nodes discovered during traversal are not returned unless separately authorized for read.

### 8.4 Failure handling for traversal

Traversal requests are rejected when:

* The requested depth exceeds configured limits.
* The traversal would exceed scan or memory budgets.
* Required seed objects cannot be resolved within the application scope.

Rejections do not leak existence information beyond what is permitted by authorization outcomes.

## 9. Failure and rejection handling

### 9.1 Rejection conditions

Graph Manager rejects write envelopes when:

* Structural validation fails.
* Schema validation fails.
* Authorization is denied for any operation.
* Application scope violations are detected.
* Referenced target objects required for the operation cannot be resolved.
* Requests attempt to supply storage controlled fields.

Graph Manager rejects read requests when:

* Structural validation fails.
* Authorization is denied.
* Application scope violations are detected.
* Requested bounds exceed configured limits.

Rejections produce no state change.

### 9.2 Failure behavior

On internal failures:

* Writes do not partially commit.
* Serialized write context is released.
* A failure result distinct from rejection is returned.

Internal failures include:

* Storage errors, including constraint and I O failures.
* Sequencing allocation failures.
* Inconsistent internal metadata state required for processing.

Event publication failures do not invalidate a successful commit. They are recorded for diagnostics and health reporting.

## 10. Minimal state and caching constraints

### 10.1 Permitted in memory state

Graph Manager may maintain minimal in memory indices required for correctness and availability checks, including:

* Identity Parent identifiers and their public key Attribute references, limited to the system application scope.
* Transient caches used during request processing that do not affect correctness.

### 10.2 Forbidden state

Graph Manager must not maintain:

* Long lived application semantic indices that implement domain logic.
* Independent copies of schema state or policy state that could diverge from Schema Manager or ACL Manager.
* State required for recovery after restart.

## 11. Component interactions

### 11.1 Schema Manager

Inputs provided by Graph Manager:

* `app_id`.
* Operation kind or read scope.
* Type keys and candidate values, as applicable.

Outputs relied upon by Graph Manager:

* Type mapping and validation outcomes.
* Domain membership used for sync participation metadata.

### 11.2 ACL Manager

Inputs provided by Graph Manager:

* OperationContext.
* Object identifiers and metadata needed for evaluation.
* Requested read or write scope.
* Traversal results where required for bounded distance checks, restricted to what is necessary for the decision.

Outputs relied upon by Graph Manager:

* Allow or deny decisions for read and write.

### 11.3 Storage Manager

Inputs provided by Graph Manager:

* Prepared operations with resolved types and storage controlled fields derived by Graph Manager.
* Read descriptors bounded by limits.

Outputs relied upon by Graph Manager:

* Transactional commit outcomes.
* Allocated global sequence identifiers.
* Retrieved rows for reads, subject to authorization filtering.

### 11.4 Event Manager and Log Manager

Graph Manager:

* Publishes post commit mutation events.
* Records accept, reject, and failure outcomes with trace identifiers and minimal metadata required for audit and diagnostics.

