



# 07 Graph Manager

## 1. Purpose and scope

The Graph Manager is the authoritative coordinator for graph state access within the local node. It is the only permitted write path for graph objects, and it provides the canonical read surface for graph objects where access control, application context, traversal constraints, consistency guarantees, and default visibility filtering must be enforced.

This document defines responsibilities, boundaries, invariants, guarantees, allowed and forbidden behaviors, concurrency rules, component interactions, startup and shutdown behavior, internal execution engines, and failure handling for the Graph Manager.

This file specifies graph level access behavior only. It does not define schema content, access control policy logic, synchronization protocol behavior, network transport, cryptographic verification, peer discovery, or storage internals, except where interaction boundaries are required.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Acting as the single entry point for all persisted mutations of Parents, Attributes, Edges, Ratings, and ACL structures per `01-protocol/00-protocol-overview.md`. ACL data is represented as Parent and Attribute objects per the protocol object model.
* Accepting graph envelopes only from trusted in process components, including local services and State Manager for remote application after Network Manager verification, exactly as allowed by `01-protocol/03-serialization-and-envelopes.md` and constrained by `01-protocol/04-cryptography.md`.
* Validating envelope structure and operation shape at the graph layer, including supervised operation identifiers, the required `ops` array, `type_key` and `type_id` exclusivity, declared `owner_identity`, and rejection of forbidden fields such as `global_seq` or `sync_flags` per `01-protocol/03-serialization-and-envelopes.md`.
* Enforcing namespace isolation and object reference rules defined in `01-protocol/01-identifiers-and-namespaces.md`.
* Delegating type resolution and schema validation to Schema Manager.
* Delegating authorization decisions for reads and writes to ACL Manager per the ordering defined in `01-protocol/00-protocol-overview.md`.
* Enforcing application context for all operations.
* Enforcing serialized write ordering and global sequencing for all accepted mutations per `01-protocol/07-sync-and-consistency.md`.
* Persisting accepted envelopes atomically through Storage Manager.
* Publishing semantic graph events after commit through Event Manager.
* Providing canonical read operations for graph objects, with authorization, application context, consistency guarantees, and default visibility filtering enforced.
* Providing bounded traversal primitives required to support authorization checks that depend on graph distance.
* Enforcing bounded read and traversal budgets.
* Defining the concurrency contract for graph reads and writes at the manager boundary.
* Enforcing strict separation between graph access logic and storage implementation.
* Remaining cryptographically agnostic by never performing signing, verification, encryption, or decryption, and by rejecting any remote sourced envelope that bypasses the Network Manager and State Manager path, per `01-protocol/04-cryptography.md`.
* Defining startup, readiness, and shutdown behavior for safe operation.
* Defining internal execution engines and their ownership of behavior.

This specification does not cover the following:

* Schema definition, migration, or versioning behavior.
* The meaning of types, fields, or application semantics beyond what is required to enforce visibility defaults defined in this file.
* The content of access control policies, rule evaluation, or policy storage.
* Construction of sync packages, per peer sync state, or inbound and outbound sync flows.
* Network transport, encryption, signature verification, or peer management.
* Storage schemas, SQL details, or indexing strategies.
* Application specific query engines, search, ranking, analytics, denormalized views, or aggregates.

## 3. Internal engines and ownership model

The Graph Manager is internally composed of explicit execution engines. These engines are logical ownership boundaries within the manager. They do not expose independent public interfaces and are not standalone managers.

Introducing engines does not replace or abstract existing behavior. Each engine is defined as the owner of behavior already specified elsewhere in this document.

### 3.1 Graph Write Engine

The Graph Write Engine owns the complete persisted mutation path.

It is responsible for:

* Intake of write envelopes from trusted callers.
* Structural validation coordination.
* Schema validation coordination.
* Authorization evaluation coordination.
* Acquisition and release of the serialized write context.
* Global sequence allocation.
* Atomic persistence through Storage Manager.
* Computation of storage controlled metadata.
* Coordination of post commit event publication.
* Fail closed handling of all write failures.

All behavior described in Sections 7 and 10 with respect to writes is owned by the Graph Write Engine.

### 3.2 Graph Read Engine

The Graph Read Engine owns all read entry points.

It is responsible for:

* Intake of read request descriptors.
* Structural validation of read requests.
* Authorization evaluation for read access.
* Coordination of bounded reads through Storage Manager.
* Enforcement of snapshot bounds when requested.
* Application of default visibility filtering.
* Enforcement of resource and budget limits.
* Response shaping and masking.

All behavior described in Sections 8 and 9 with respect to reads is owned by the Graph Read Engine.

### 3.3 RAM Graph Engine

The RAM Graph Engine maintains transient in memory representations of graph relationships required for authorization.

It is responsible for:

* Maintaining adjacency views required for authorization checks.
* Supporting bounded adjacency queries.
* Supporting traversal execution requested by the Traversal Engine.
* Rebuilding its state from persisted storage on startup.
* Updating its state after committed writes.

The RAM Graph Engine is never authoritative. It never persists state directly and must tolerate restart without recovery beyond reconstruction from persisted graph data.

### 3.4 Traversal Engine

The Traversal Engine performs bounded graph traversal strictly to support authorization decisions.

It is responsible for:

* Executing fixed depth traversals.
* Enforcing frontier size limits.
* Enforcing visited node limits.
* Applying masking rules to prevent existence leakage.
* Returning traversal results only to the ACL Manager and Graph Manager internals.

Traversal results are never returned directly to external callers.

### 3.5 Sequencing Engine

The Sequencing Engine manages global ordering of mutations.

It is responsible for:

* Allocation of strictly monotonic global sequence values.
* Isolation of sequencing from caller influence.
* Operation only inside the serialized write context.

## 4. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* All persisted mutations of Parents, Attributes, Edges, Ratings, and ACL structures pass through the Graph Manager, per `01-protocol/00-protocol-overview.md`.
* The Graph Manager never performs a persisted write without schema validation and authorization evaluation completing successfully.
* The Graph Manager never returns graph object data to a caller unless authorization evaluation permits that read.
* Remote envelopes are accepted only after OperationContext is constructed by State Manager following Network Manager verification, as required by `01-protocol/03-serialization-and-envelopes.md` and `01-protocol/04-cryptography.md`.
* The Graph Manager never ingests raw network data or performs cryptographic verification per `01-protocol/04-cryptography.md`.
* All operations in an envelope share the same `app_id`, declared `owner_identity`, and sync domain context per `01-protocol/07-sync-and-consistency.md`.
* Graph write operations are always scoped to a single `app_id`.
* Graph read operations execute within a single application context.
* Updates never change immutable metadata such as `app_id`, `type_id`, or `owner_identity`.
* Envelope application is atomic per `01-protocol/03-serialization-and-envelopes.md`.
* Global sequencing is strictly monotonic and is assigned only by Graph Manager per `01-protocol/07-sync-and-consistency.md`.
* Structural validation rejects envelopes with unknown keys, unsupported operation identifiers, empty `ops`, missing required fields, or forbidden fields such as `global_seq` or `sync_flags`, matching `01-protocol/03-serialization-and-envelopes.md`.
* Callers cannot influence sequencing, storage controlled fields, or sync participation metadata.
* Mutation events are never emitted before commit.
* Reads observe committed state only.
* Reads never observe partially applied envelopes.
* Snapshot bounded reads are consistent across object kinds.
* Default visibility filtering never grants access denied by authorization.

These guarantees hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 5. Startup, readiness, and shutdown

### 5.1 Startup behavior

On startup the Graph Manager:

* Initializes the Sequencing Engine.
* Verifies connectivity to Storage Manager.
* Verifies availability of Schema Manager and ACL Manager.
* Rebuilds RAM Graph Engine state from persisted graph data.
* Rejects all requests until initialization completes successfully.

### 5.2 Readiness

The Graph Manager is considered ready only when:

* Storage Manager transactional guarantees are available.
* Schema Manager and ACL Manager are reachable.
* Global sequence state is initialized.
* RAM Graph Engine has completed reconstruction.

### 5.3 Shutdown behavior

On shutdown the Graph Manager:

* Rejects new requests.
* Completes or aborts in flight serialized writes.
* Releases internal resources.
* Performs no in memory recovery beyond persistence guarantees.

## 6. Concurrency and execution model

### 6.1 Write serialization

The Graph Manager enforces a single serialized write path:

* At most one write envelope is applied at any time.
* Sequence allocation and persistence occur inside the serialized context.
* The serialized context spans only the minimum required work.

### 6.2 Read concurrency

The Graph Manager permits concurrent reads:

* Reads do not acquire the serialized write context.
* Reads may execute concurrently with writes.
* Reads may or may not observe a concurrent write depending on commit timing.

### 6.3 Storage coordination assumptions

The Graph Manager assumes Storage Manager provides transactional commits for write envelopes and a concurrency model where readers do not require explicit coordination with the writer.

## 7. Inputs, outputs, and trust boundaries

### 7.1 Inputs

The Graph Manager accepts:

* An OperationContext for every operation.
* A graph envelope for write requests.
* A graph read request descriptor for read requests.

OperationContext includes at minimum:

* Requesting identity identifier.
* Executing `app_id`.
* Execution mode.
* Sync domain identifier when applicable.
* Remote node identity when applicable.
* Trace identifier.

OperationContext fields must align with the construction rules defined in `01-protocol/00-protocol-overview.md` and `01-protocol/03-serialization-and-envelopes.md`, including remote indicators, sync domain binding, and traceability metadata.

All inputs are treated as untrusted.

### 7.2 Outputs

The Graph Manager returns:

* Acceptance or rejection for the entire write envelope.
* Assigned global sequence values and created identifiers.
* Authorized read result sets filtered by visibility rules.
* Structured error codes suitable for propagation and logging.

Side effects include persisted state mutations, post commit events, and audit logging.

### 7.3 Trust boundaries

The Graph Manager relies on:

* Schema Manager for validation and domain membership.
* ACL Manager for authorization and masking.
* State Manager for delivery of verified remote envelopes.
* Storage Manager for transactional persistence and sequencing.
* Event Manager and Log Manager for delivery and logging.

## 8. Allowed and forbidden behaviors

### 8.1 Explicitly allowed behaviors

The Graph Manager allows:

* Write envelopes from trusted local services, per `01-protocol/03-serialization-and-envelopes.md`.
* Write envelopes from State Manager for remote application, after the Network Manager and State Manager path defined in `01-protocol/04-cryptography.md`.
* Authorized reads of Parents, Attributes, Edges, and Ratings.
* Bounded adjacency reads.
* Bounded traversal strictly for authorization.
* Default visibility filtering.
* Snapshot bounded reads when supported.

### 8.2 Explicitly forbidden behaviors

The Graph Manager forbids:

* Persisted graph writes from any other component.
* Bypassing schema validation or authorization.
* Returning unauthorized data.
* Writing into another application's graph.
* Partial envelope application.
* Emitting events prior to commit.
* Unbounded reads or traversals.
* Accepting remote envelopes that bypass State Manager.
* Issuing direct storage calls.

## 9. Write path behavior

### 9.1 Processing order

For each write envelope:

* Structural validation.
* Schema validation.
* Authorization evaluation.
* Serialized execution.
* Atomic commit.
* Post commit event emission.

### 9.2 Structural validation

The Graph Manager validates:

* Presence of at least one operation.
* Supported operation identifiers that are limited to `parent_create`, `parent_update`, `attr_create`, `attr_update`, `edge_create`, `edge_update`, `rating_create`, and `rating_update` per `01-protocol/03-serialization-and-envelopes.md`.
* Consistent `app_id` and `owner_identity`.
* Correct identifier usage, including `type_key` XOR `type_id` semantics per `01-protocol/03-serialization-and-envelopes.md`.
* Absence of storage controlled fields such as `global_seq` and `sync_flags`.
* Absence of unknown envelope or operation keys defined outside `01-protocol/03-serialization-and-envelopes.md`.

### 9.3 Schema validation

Schema validation is delegated to Schema Manager.

### 9.4 Authorization evaluation

Authorization is delegated to ACL Manager.

### 9.5 Sequencing and persistence

For accepted envelopes:

* Global sequence values are allocated.
* All operations persist in one transaction.
* Storage controlled metadata is computed internally.

### 9.6 Post commit events

Events are emitted only after commit. Event failure never rolls back committed state.

## 10. Read semantics and behavior

### 10.1 Read surface

Supported reads include:

* Direct reads by identifier.
* Bounded adjacency reads.
* Batch reads.

Direct identifier reads observe the resolution guarantees defined by `01-protocol/01-identifiers-and-namespaces.md`.

### 10.2 Read consistency model

Reads observe committed state only. Snapshot binding is optional and explicit.

### 10.3 Authorization and visibility

Authorization is mandatory. Visibility filtering applies after authorization.

### 10.4 Resource limits

All reads enforce fixed budgets.

## 11. Bounded traversal support

Traversal exists solely to support authorization.

Constraints:

* Fixed depth.
* Fixed frontier.
* Fixed visited count.
* No exposure of intermediate nodes.

## 12. Failure and rejection handling

Failures fail closed.

* No partial writes occur.
* Serialized context is released.
* Errors follow protocol precedence rules defined by `01-protocol/09-errors-and-failure-modes.md`, including structural failures taking precedence over schema and ACL failures.

## 13. Object lifecycle assumptions

* Objects may be created and mutated.
* Removal is implemented via Rating based visibility suppression.
* Lifecycle semantics are schema defined.

## 14. Minimal state and caching constraints

### 14.1 Permitted state

* System identity Parents.
* Transient request scoped caches.

### 14.2 Forbidden state

* Long lived semantic indices.
* Recovery critical in memory state.

## 15. Component interactions

### 15.1 Schema Manager

Provides validation, mapping, and domain membership.

### 15.2 ACL Manager

Provides authorization, masking, and distance rules.

### 15.3 Storage Manager

Provides transactional persistence and sequencing.

### 15.4 Event Manager and Log Manager

Deliver post commit events and logs.

### 15.5 State Manager

Delivers verified remote envelopes and constructs OperationContext.

## 16. Interface stability

The Graph Manager is an internal system component. It is not a public API.

Backward compatibility expectations are defined at the manager boundary.
