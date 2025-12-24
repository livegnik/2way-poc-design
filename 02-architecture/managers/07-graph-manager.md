



# 07 Graph Manager

## 1. Purpose and scope

The Graph Manager is the authoritative coordinator for graph state access within the local node. It is the only permitted write path for graph objects, and it provides the canonical read surface for graph objects where access control, application context, traversal constraints, consistency guarantees, and default visibility filtering must be enforced.

This document defines responsibilities, boundaries, invariants, guarantees, allowed and forbidden behaviors, concurrency rules, component interactions, and failure handling for the Graph Manager.

This file specifies graph level access behavior only. It does not define schema content, access control policy logic, synchronization protocol behavior, network transport, or storage internals, except where interaction boundaries are required.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Acting as the single entry point for all persisted mutations of Parents, Attributes, Edges, Ratings, and ACL structures (ACL data is represented as Parent and Attribute objects per the protocol object model).
* Accepting graph envelopes only from trusted in process components, including local services and State Manager for remote application after Network Manager verification.
* Validating envelope structure and operation shape at the graph layer, including supervised operation identifiers, `type_key`/`type_id` exclusivity, a declared `owner_identity`, and the canonical `ops` array defined by the serialization specification.
* Enforcing namespace isolation and object reference rules defined in the identifier specification.
* Delegating type resolution and schema validation to Schema Manager.
* Delegating authorization decisions for reads and writes to ACL Manager.
* Enforcing application context for all operations.
* Enforcing serialized write ordering and global sequencing for all accepted mutations.
* Persisting accepted envelopes atomically through Storage Manager.
* Publishing semantic graph events after commit through Event Manager.
* Providing canonical read operations for graph objects, with authorization, application context, consistency guarantees, and default visibility filtering enforced.
* Providing bounded traversal primitives required to support authorization checks that depend on graph distance.
* Enforcing bounded read and traversal budgets.
* Defining the concurrency contract for graph reads and writes at the manager boundary.
* Enforcing strict separation between graph access logic and storage implementation.

This specification does not cover the following:

* Schema definition, migration, or versioning behavior.
* The meaning of types, fields, or application semantics beyond what is required to enforce visibility defaults defined in this file.
* The content of access control policies, rule evaluation, or policy storage.
* Construction of sync packages, per peer sync state, or inbound and outbound sync flows.
* Network transport, encryption, or peer management.
* Storage schemas, SQL details, or indexing strategies.
* Application specific query engines, search, ranking, analytics, denormalized views, or aggregates.

## 3. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* All persisted mutations of Parents, Attributes, Edges, Ratings, and ACL structures pass through the Graph Manager.
* The Graph Manager never performs a persisted write without schema validation and authorization evaluation completing successfully.
* The Graph Manager never returns graph object data to a caller unless authorization evaluation permits that read.
* Remote envelopes are accepted only after OperationContext is constructed by State Manager following Network Manager verification. The Graph Manager never ingests raw network data or performs signature verification.
* All operations in an envelope share the same `app_id`, declared `owner_identity`, and sync domain context, and the enforcement identity is derived from OperationContext rather than transport metadata.
* Graph write operations are always scoped to a single `app_id`.
* Graph read operations execute within a single application context and may access objects owned by other applications only when explicitly permitted by schema and ACL rules.
* Updates never change `app_id`, `type_id`, `owner_identity`, or other immutable metadata defined by the object model.
* Envelope application is atomic, either all operations in an accepted envelope are committed, or none are.
* Global sequencing for committed mutations is strictly monotonic and assigned by a serialized write path.
* Callers cannot choose or influence sequencing, storage controlled fields, or sync participation metadata.
* The Graph Manager does not emit mutation events before commit.
* Reads observe committed state only.
* Reads never observe partially applied envelopes.
* When snapshot binding is requested, read results are consistent with the requested bound across all object kinds.
* Default visibility filtering may exclude otherwise readable objects but can never grant access that authorization has denied.

These guarantees hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 4. Concurrency and execution model

### 4.1 Write serialization

The Graph Manager enforces a single serialized write path:

* At most one write envelope is applied at any time.
* Sequence allocation and persistence occur inside the serialized write context.
* The serialized context spans only the minimum required work to guarantee atomicity and ordering.

### 4.2 Read concurrency

The Graph Manager permits concurrent reads:

* Reads do not acquire the serialized write context.
* Reads may execute concurrently with other reads and with pending writes.
* A read may or may not observe a concurrent write depending on whether that write has committed before the read begins.

### 4.3 Storage coordination assumptions

The Graph Manager assumes that Storage Manager provides:

* Transactional commits for write envelopes.
* A concurrency model where readers do not require explicit coordination with the writer.

The Graph Manager never blocks reads to protect ordering.

## 5. Inputs, outputs, and trust boundaries

### 5.1 Inputs

The Graph Manager accepts:

* An OperationContext for every operation, read or write.
* A graph envelope for write requests.
* A graph read request descriptor for read requests.

OperationContext includes at minimum:

* Requesting identity identifier.
* Executing `app_id`.
* Execution mode, local or remote.
* Sync domain identifier when applicable.
* Remote node identity when applicable.
* Trace identifier.

OperationContext is the authoritative binding for executing identity, `app_id`, remote mode, and sync domain. Envelope hints cannot override it, and no transport metadata is trusted.

All inputs are treated as untrusted and validated.

### 5.2 Outputs

The Graph Manager returns:

* For writes, acceptance or rejection for the entire envelope.
* For accepted writes, assigned global sequence values and created identifiers when required.
* For reads, result sets containing only authorized objects filtered by default visibility rules.
* For failures or rejections, structured error codes and narrow reasons suitable for propagation and logging.

Side effects include:

* Persisted state mutations.
* Post commit event publication.
* Audit and diagnostics logging.

### 5.3 Trust boundaries

The Graph Manager relies on:

* Schema Manager for type existence, mapping, validation, value constraints, and domain membership.
* ACL Manager for allow or deny decisions, masking requirements, and distance based rules.
* State Manager, after Network Manager verification, for remote envelope delivery, sync domain context, and replay protection metadata. The Graph Manager is cryptography agnostic and rejects remote input that bypasses this path.
* Storage Manager for transactional persistence and sequence allocation.
* Event Manager for event delivery.

The Graph Manager does not trust callers to supply correct types, ownership, sync scope, or safe values.

## 6. Allowed and forbidden behaviors

### 6.1 Explicitly allowed behaviors

The Graph Manager allows:

* Write envelopes from local services after validation and authorization.
* Write envelopes from State Manager for remote application under additional context restrictions.
* Read requests for Parents, Attributes, Edges, and Ratings.
* Cross application reads when explicitly permitted by schema visibility and ACL rules.
* Bounded adjacency reads.
* Bounded traversal strictly for authorization support.
* Default visibility filtering driven by Ratings.
* Explicit reads that opt out of default visibility filtering.
* Snapshot bounded reads when supported.

### 6.2 Explicitly forbidden behaviors

The Graph Manager forbids:

* Persisted graph writes from any other component.
* Bypassing schema validation or authorization.
* Returning unauthorized data.
* Writing into another application's graph.
* Mutating objects or issuing edges owned by another identity without explicit schema and ACL authorization.
* Caller supplied storage controlled fields.
* Partial envelope application.
* Emitting events prior to commit.
* Unbounded queries or traversals.
* Using foreign graphs as implicit traversal intermediates.
* Accepting envelopes that declare unsupported operation identifiers, deletion semantics, or violate the supervised `parent_*`, `attr_*`, `edge_*`, and `rating_*` operations defined by the protocol serialization rules.
* Accepting remote envelopes that bypass the Network Manager and State Manager pipeline.
* Issuing raw SQL or direct storage calls. All access goes through Storage Manager.
* Leaking existence through error surfaces when masking is required.

## 7. Write path behavior

### 7.1 Processing order

For each write envelope:

* Structural validation.
* Schema validation and type resolution.
* Authorization evaluation.
* Serialized write context acquisition.
* Sequence allocation and persistence.
* Transaction commit.
* Event publication and logging.

Failure at any stage aborts the envelope.

### 7.2 Structural validation

The Graph Manager validates:

* The envelope contains at least one operation entry in `ops` and no unknown top level fields.
* Every operation `op` value is one of `parent_create`, `parent_update`, `attr_create`, `attr_update`, `edge_create`, `edge_update`, `rating_create`, or `rating_update`.
* Each operation supplies `app_id`, `owner_identity`, and exactly one of `type_key` or `type_id`.
* All operations share the same `app_id`, declared `owner_identity`, sync domain context, and OperationContext `app_id`.
* Required identifiers and references for the object category are present, resolve to existing objects inside the same `app_id`, and updates supply immutable identifiers such as `parent_id`, `attr_id`, `edge_id`, or `rating_id` when required.
* ACL data is represented using canonical Parent and Attribute objects only.
* Caller supplied storage controlled fields such as `id`, `global_seq`, `sync_flags`, or schema compiled fields are absent.

Failure rejects the envelope.

### 7.3 Schema validation

Schema Manager validates:

* Operation kind compatibility.
* Type resolution.
* Value constraints.
* Domain membership.

Any rejection aborts the envelope.

### 7.4 Authorization evaluation

ACL Manager evaluates each operation. Any denial aborts the envelope.

### 7.5 Sequencing and persistence

For accepted envelopes:

* Global sequence values are allocated.
* All operations persist in one transaction.
* Domain membership metadata (`sync_flags`, domain eligibility, and other storage controlled fields) is computed inside Graph Manager using schema and sync-domain configuration, and callers cannot supply or override these values.
* Serialized context is released after commit.

### 7.6 Post commit events

Events are emitted only after commit and must include:

* `app_id`.
* Object identifiers sufficient for re fetch.
* Global sequence range.
* Trace identifier.

Event failure never rolls back committed state.

## 8. Read semantics and behavior

### 8.1 Read surface

Supported reads:

* Direct reads by identifier.
* Bounded adjacency reads.
* Minimal header reads.
* Bounded batch reads by identifier.

Reads execute in one application context. Ownership may differ if permitted.

### 8.2 Read consistency model

* Reads observe committed state only.
* No repeatable read guarantee by default.
* Snapshot binding is optional and explicit.

### 8.3 Snapshot bounded reads

When requested and supported:

* No returned row may have `global_seq` greater than the bound.
* The bound applies across all object kinds.
* Failure to enforce safely aborts the read.

### 8.4 Read processing order

* Structural validation.
* Authorization evaluation.
* Storage reads.
* Default visibility filtering.
* Authorization filtering.
* Response shaping.

### 8.5 Authorization on reads

Authorization is mandatory. Header reads used for authorization must not leak existence unless permitted.

### 8.6 Default visibility filtering using Ratings

Ratings are first class graph objects that can influence default visibility.

Rules:

* Visibility filtering applies only after authorization.
* Suppressing visibility signals exclude objects by default.
* Explicit inclusion can bypass visibility filtering but never authorization.
* Rating interpretation is defined by schema and ACL, not by Graph Manager.
* Rating payloads are opaque to Graph Manager.
* Logical delete behaviors are modeled as schema defined Rating types (often binary) that reference the target Parent, Attribute, or Edge. These Ratings suppress those objects during default reads without pruning the underlying records.

### 8.7 Cross application visibility

Cross application reads require:

* Executing application context.
* Schema level visibility.
* ACL permission.

Adjacency and traversal across ownership boundaries require explicit permission at each step.

### 8.8 Batch read semantics

* Per item authorization and visibility.
* Partial results allowed.
* Whole request fails only on structural or internal failure.

### 8.9 Error and masking rules

* Masked reads return not found.
* Unmasked reads may return permission denied.
* Batch items follow per item masking rules.

### 8.10 Resource limits

Graph Manager enforces:

* Maximum object count.
* Maximum scan budget.
* Maximum payload size.

Limits apply uniformly.

## 9. Bounded traversal support

Traversal exists solely for authorization.

### 9.1 Boundaries

* Fixed depth.
* Fixed frontier.
* Fixed visited count.

### 9.2 Seed rules

Seeds must be admissible. Masking applies if resolution would leak existence.

### 9.3 Exposure constraints

Traversal does not expose intermediate state unless separately authorized.

### 9.4 Failure handling

Traversal failures must not leak existence.

## 10. Failure and rejection handling

### 10.1 Rejection conditions

Writes are rejected on validation, authorization, ownership, or bounds violation.

Reads are rejected on validation, authorization when masking is not required, bounds violation, or invalid snapshot parameters.

### 10.2 Failure behavior

On internal failure:

* No partial writes.
* Serialized context released.
* Failure returned.
* Error surfaces map to the canonical structural, schema, authorization, sync, or resource error classes defined by the protocol, and precedence rules (structural before schema before authorization) are preserved.

Event failures do not invalidate commits.

## 11. Object lifecycle assumptions

Assumptions:

* Objects may be created and mutated.
* Removal is implemented by appending Rating objects that point to the target Parent, Attribute, or Edge and record a delete vote. The Rating is treated as a visibility suppressor while the original object remains persisted, and future schema versions may revise this approach.
* Delete style requests therefore translate into Rating operations rather than bespoke delete operation identifiers.
* Deleted or superseded objects are not returned unless explicitly requested and permitted.

Undefined lifecycle states are treated as current.

## 12. Minimal state and caching constraints

### 12.1 Permitted state

* System identity Parents and key Attributes.
* Transient request scoped caches.
* Short lived memoization.

### 12.2 Forbidden state

* Long lived semantic indices.
* Independent schema or policy state.
* Recovery critical in memory state.

## 13. Component interactions

### 13.1 Schema Manager

Graph Manager provides context and values. Relies on validation, mapping, domain membership, and visibility affecting rating identification.

### 13.2 ACL Manager

Graph Manager provides context, metadata, traversal outcomes, and visibility context. Relies on allow, deny, masking, and distance rules.

### 13.3 Storage Manager

Graph Manager provides prepared operations and bounded reads. Relies on transactions and sequencing.

### 13.4 Event Manager and Log Manager

Graph Manager publishes post commit events and logs outcomes.

### 13.5 State Manager

State Manager is the only source of remote envelopes presented to Graph Manager. It performs sync-domain ordering checks after Network Manager verification, constructs the OperationContext with `is_remote`, `sync_domain`, and `remote_node_identity`, and delivers the envelope for validation. Graph Manager rejects remote input that bypasses State Manager and never performs cryptographic verification itself.

## 14. Interface stability

The Graph Manager is an internal system component. It is not a public API.

Backward compatibility expectations are defined at the interface boundary, not in this document.
