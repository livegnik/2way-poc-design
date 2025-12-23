



# 07 Graph Manager

## 1. Purpose and scope

The Graph Manager is the authoritative coordinator for graph state access within the local node. It is the only permitted write path for graph objects, and it provides the canonical read surface for graph objects where access control, application context, and traversal constraints must be enforced.

This document defines responsibilities, boundaries, invariants, guarantees, allowed and forbidden behaviors, component interactions, and failure handling for the Graph Manager.

This file specifies graph level access behavior only. It does not define schema content, access control policy logic, synchronization protocol behavior, network transport, or storage internals, except where interaction boundaries are required.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Acting as the single entry point for all persisted mutations of Parents, Attributes, Edges, and Ratings.
* Accepting graph envelopes from trusted in process components only, including local services and State Manager for remote application.
* Validating envelope structure and operation shape at the graph layer.
* Delegating type resolution and schema validation to Schema Manager.
* Delegating authorization decisions for reads and writes to ACL Manager.
* Enforcing application context for all operations.
* Enforcing serialized write ordering and global sequencing for all accepted mutations.
* Persisting accepted envelopes atomically through Storage Manager.
* Publishing semantic graph events after commit through Event Manager.
* Providing canonical read operations for graph objects, with authorization and application context enforced.
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
* Graph write operations are always scoped to a single `app_id`.
* Graph read operations execute within a single application context and may access objects owned by other applications only when explicitly permitted by schema and ACL rules.
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
* Executing `app_id`.
* Execution mode, local or remote.
* Sync domain identifier when applicable.
* Remote node identity when applicable.
* Trace identifier.

All inputs are treated as untrusted and must be validated.

### 4.2 Outputs

The Graph Manager returns:

* For writes, an acceptance or rejection result for the entire envelope.
* For accepted writes, assigned global sequence values and created identifiers when required by the caller.
* For reads, a result set containing only authorized objects, as visible from the executing application context.
* For all failures or rejections, a structured error code and a narrow reason suitable for propagation and logging.

Side effects include:

* Persisted state mutations for accepted writes.
* Post commit event publication.
* Audit and diagnostics logging.

### 4.3 Trust boundaries

The Graph Manager relies on the following components as authorities:

* Schema Manager for type existence, type mapping, structural validation, value constraints, and domain membership used for sync participation metadata.
* ACL Manager for allow or deny decisions on read and write operations, including rules that depend on graph structure and distance.
* Storage Manager for transactional persistence and allocation of globally ordered sequence identifiers.
* Event Manager for event delivery.

The Graph Manager does not trust callers to provide correct type identifiers, ownership metadata, sync scope, or safe values.

## 5. Allowed and forbidden behaviors

### 5.1 Explicitly allowed behaviors

The Graph Manager allows:

* Write envelopes from local services, subject to schema validation and authorization.
* Write envelopes from State Manager for remote application, subject to schema validation, authorization, and additional restrictions conveyed by OperationContext.
* Read requests for Parents, Attributes, Edges, and Ratings, subject to authorization and application context.
* Reads of objects owned by other applications, when explicitly permitted by schema visibility and ACL rules.
* Bounded adjacency reads, such as attributes under a parent, edges adjacent to a parent, and ratings attached to a target, subject to authorization.
* Bounded traversal reads required to support authorization checks that depend on graph distance, subject to strict resource limits.

### 5.2 Explicitly forbidden behaviors

The Graph Manager forbids:

* Persisted graph writes performed by any other component.
* Any bypass of schema validation or authorization evaluation.
* Returning any object or object field to a caller when authorization does not permit the read.
* Writing into another application’s graph.
* Creating or mutating edges that span application ownership boundaries.
* Caller supplied values for storage controlled fields, including global sequencing and sync participation metadata.
* Partial application of write envelopes.
* Emitting mutation events prior to a successful commit.
* Exposing unbounded queries or traversals that can cause unbounded scans, unbounded memory growth, or unbounded response sizes.
* Using foreign application graphs as implicit traversal intermediates unless explicitly permitted by schema and ACL rules.

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
* Internal references are consistent.

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

After commit, Graph Manager publishes semantic events via Event Manager. Events include:

* `app_id`.
* Affected object kinds and identifiers.
* The global sequence range for the committed envelope.
* Trace identifier when available.

Event payloads exclude sensitive values unless explicitly required by the consumer and permitted by applicable read authorization rules.

## 7. Read path behavior

### 7.1 Read surface

The Graph Manager provides read operations over persisted graph objects, limited to:

* Direct reads by identifier for Parents, Attributes, Edges, and Ratings.
* Bounded adjacency reads limited to direct relationships.
* Minimal header reads required for validation and authorization evaluation.

Read operations execute within a single application context. Object ownership may belong to a different application if explicitly permitted.

### 7.2 Read processing order

For each read request, Graph Manager enforces:

* Structural validation of request parameters.
* Authorization evaluation through ACL Manager for the requested read scope.
* Storage reads through Storage Manager.
* Result filtering to ensure only authorized objects are returned.

If authorization cannot be determined, the read is rejected.

### 7.3 Authorization on reads

Read authorization is mandatory. Graph Manager:

* Invokes ACL Manager for the read operation using OperationContext and requested scope.
* Applies allow or deny outcomes per object.
* Ensures no unauthorized identifiers or fields are returned.

### 7.4 Resource limits on reads

Read operations must be bounded. Graph Manager enforces:

* Maximum object count per request.
* Maximum scan budget for adjacency reads.
* Rejection of requests exceeding configured limits.

Limits apply identically for local and remote contexts.

## 8. Bounded traversal support for authorization

### 8.1 Purpose

Some authorization decisions depend on graph distance. The Graph Manager provides bounded traversal primitives solely to support such authorization evaluation.

### 8.2 Traversal boundaries

Traversal support is restricted to:

* Fixed maximum depth.
* Fixed maximum frontier size.
* Fixed maximum total visited node count.

Traversal is not a general query mechanism.

### 8.3 Data exposure constraints

Traversal operations must not expose more data than required:

* Results are limited to boolean outcomes or minimal identifiers when permitted.
* Intermediate traversal state is not exposed unless separately authorized.

### 8.4 Failure handling for traversal

Traversal requests are rejected when:

* Configured limits are exceeded.
* Required seed objects cannot be resolved.
* Authorization cannot be evaluated safely.

Rejections must not leak existence information beyond authorization outcomes.

## 9. Failure and rejection handling

### 9.1 Rejection conditions

Graph Manager rejects write envelopes when:

* Structural validation fails.
* Schema validation fails.
* Authorization is denied.
* Application ownership rules are violated.
* Storage controlled fields are supplied.

Graph Manager rejects read requests when:

* Structural validation fails.
* Authorization is denied.
* Requested bounds exceed configured limits.

### 9.2 Failure behavior

On internal failures:

* No partial writes are committed.
* Serialized write context is released.
* A failure result distinct from rejection is returned.

Internal failures include storage errors, sequencing failures, and inconsistent metadata state.

Event publication failures do not invalidate commits but are recorded for diagnostics.

## 10. Minimal state and caching constraints

### 10.1 Permitted in memory state

Graph Manager may maintain minimal in memory state required for correctness, including:

* System scoped identity Parent identifiers and public key Attribute references.
* Transient caches used during request processing.

### 10.2 Forbidden state

Graph Manager must not maintain:

* Long lived application semantic indices.
* Independent schema or policy state.
* State required for recovery after restart.

## 11. Component interactions

### 11.1 Schema Manager

Graph Manager provides:

* `app_id`.
* Operation kind or read scope.
* Type keys and candidate values.

Graph Manager relies on:

* Type validation and mapping.
* Domain membership.

### 11.2 ACL Manager

Graph Manager provides:

* OperationContext.
* Object identifiers and metadata.
* Requested read or write scope.
* Traversal outcomes when required.

Graph Manager relies on allow or deny decisions.

### 11.3 Storage Manager

Graph Manager provides:

* Prepared write operations.
* Bounded read descriptors.

Graph Manager relies on transactional guarantees and sequence allocation.

### 11.4 Event Manager and Log Manager

Graph Manager publishes post commit events and records acceptance, rejection, and failure outcomes with trace identifiers.
