



# 07 Graph Manager

Defines graph read and write coordination, validation ordering, and sequencing. Specifies internal engines, concurrency rules, and graph traversal constraints. Defines manager interactions, startup/shutdown behavior, and failure handling.

For the meta specifications, see [07-graph-manager meta](../../10-appendix/meta/02-architecture/managers/07-graph-manager-meta.md).

## 1. Internal engines and ownership model

The [Graph Manager](07-graph-manager.md) is internally composed of explicit execution engines. These engines are logical ownership boundaries within the manager. They do not expose independent public interfaces and are not standalone managers.

Introducing engines does not replace or abstract existing behavior. Each engine is defined as the owner of behavior already specified elsewhere in this document.

### 1.1 Graph Write Engine

The Graph Write Engine owns the complete persisted mutation path.

It is responsible for:

* Intake of write envelopes from trusted callers.
* Structural validation coordination.
* Schema validation coordination.
* Authorization evaluation coordination.
* Acquisition and release of the serialized write context.
* Global sequence allocation.
* Atomic persistence through [Storage Manager](02-storage-manager.md).
* Computation of storage controlled metadata.
* Coordination of post commit event publication.
* Fail closed handling of all write failures.

All behavior described in Sections 7 and 10 with respect to writes is owned by the Graph Write Engine.

### 1.2 Graph Read Engine

The Graph Read Engine owns all read entry points.

It is responsible for:

* Intake of read request descriptors.
* Structural validation of read requests.
* Authorization evaluation for read access.
* Coordination of bounded reads through [Storage Manager](02-storage-manager.md).
* Enforcement of snapshot bounds when requested.
* Application of default visibility filtering.
* Enforcement of resource and budget limits.
* Response shaping and masking.

All behavior described in Sections 8 and 9 with respect to reads is owned by the Graph Read Engine.

### 1.3 RAM Graph Engine

The RAM Graph Engine maintains transient in memory representations of graph relationships required for authorization.

It is responsible for:

* Maintaining adjacency views required for authorization checks.
* Supporting bounded adjacency queries.
* Supporting traversal execution requested by the Traversal Engine.
* Rebuilding its state from persisted storage on startup.
* Updating its state after committed writes.

The RAM Graph Engine is never authoritative. It never persists state directly and must tolerate restart without recovery beyond reconstruction from persisted graph data.

### 1.4 Traversal Engine

The Traversal Engine performs bounded graph traversal strictly to support authorization decisions.

It is responsible for:

* Executing fixed depth traversals.
* Enforcing frontier size limits.
* Enforcing visited node limits.
* Applying masking rules to prevent existence leakage.
* Returning traversal results only to the [ACL Manager](06-acl-manager.md) and [Graph Manager](07-graph-manager.md) internals.

Traversal results are never returned directly to external callers.

### 1.5 Sequencing Engine

The Sequencing Engine manages global ordering of mutations.

It is responsible for:

* Allocation of strictly monotonic global sequence values.
* Isolation of sequencing from caller influence.
* Operation only inside the serialized write context.

## 2. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* All persisted mutations of Parents, Attributes, Edges, Ratings, and ACL structures pass through the [Graph Manager](07-graph-manager.md), per [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* The [Graph Manager](07-graph-manager.md) never performs a persisted write without schema validation and authorization evaluation completing successfully, enforcing the sequencing posture in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) and the validation ordering in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* The [Graph Manager](07-graph-manager.md) never returns graph object data to a caller unless authorization evaluation permits that read, per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Remote envelopes are accepted only after [OperationContext](../services-and-apps/05-operation-context.md) is constructed by [State Manager](09-state-manager.md) following [Network Manager](10-network-manager.md) verification, as required by [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md).
* The [Graph Manager](07-graph-manager.md) never ingests raw network data or performs cryptographic verification per [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md).
* All operations in an envelope share the same `app_id`, declared `owner_identity`, and sync domain context per [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md), and the `owner_identity` must reference a valid identity Parent defined in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Graph write operations are always scoped to a single `app_id`, matching the namespace rules in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Graph read operations execute within a single application context for the same reason.
* Updates never change immutable metadata such as `app_id`, `type_id`, or `owner_identity`, in accordance with the immutability rules in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* Envelope application is atomic per [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Global sequencing is strictly monotonic and is assigned only by [Graph Manager](07-graph-manager.md) per [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Structural validation rejects envelopes with unknown keys, unsupported operation identifiers, empty `ops`, missing required fields, or forbidden fields such as `global_seq` or `sync_flags`, matching [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Callers cannot influence sequencing, storage controlled fields, or sync participation metadata, ensuring the sequencing guarantees in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Mutation events are never emitted before commit, matching the sequencing posture in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Reads observe committed state only, satisfying the consistency rules in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Reads never observe partially applied envelopes, per [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Snapshot bounded reads are consistent across object kinds per [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Default visibility filtering never grants access denied by authorization, restating [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

These guarantees hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 3. Startup, readiness, and shutdown

### 3.1 Startup behavior

On startup the [Graph Manager](07-graph-manager.md):

* Initializes the Sequencing Engine.
* Verifies connectivity to [Storage Manager](02-storage-manager.md).
* Verifies availability of [Schema Manager](05-schema-manager.md) and [ACL Manager](06-acl-manager.md).
* Rebuilds RAM Graph Engine state from persisted graph data.
* Rejects all requests until initialization completes successfully.

### 3.2 Readiness

The [Graph Manager](07-graph-manager.md) is considered ready only when:

* [Storage Manager](02-storage-manager.md) transactional guarantees are available.
* [Schema Manager](05-schema-manager.md) and [ACL Manager](06-acl-manager.md) are reachable.
* Global sequence state is initialized.
* RAM Graph Engine has completed reconstruction.

### 3.3 Shutdown behavior

On shutdown the [Graph Manager](07-graph-manager.md):

* Rejects new requests.
* Completes or aborts in flight serialized writes.
* Releases internal resources.
* Performs no in memory recovery beyond persistence guarantees.

## 4. Concurrency and execution model

### 4.1 Write serialization

The [Graph Manager](07-graph-manager.md) enforces a single serialized write path:

* At most one write envelope is applied at any time.
* Sequence allocation and persistence occur inside the serialized context.
* The serialized context spans only the minimum required work.

### 4.2 Read concurrency

The [Graph Manager](07-graph-manager.md) permits concurrent reads:

* Reads do not acquire the serialized write context.
* Reads may execute concurrently with writes.
* Reads may or may not observe a concurrent write depending on commit timing.

### 4.3 Storage coordination assumptions

The [Graph Manager](07-graph-manager.md) assumes [Storage Manager](02-storage-manager.md) provides transactional commits for write envelopes and a concurrency model where readers do not require explicit coordination with the writer.

## 5. Inputs, outputs, and trust boundaries

### 5.1 Inputs

The [Graph Manager](07-graph-manager.md) accepts:

* An [OperationContext](../services-and-apps/05-operation-context.md) for every operation.
* A graph envelope for write requests.
* A graph read request descriptor for read requests.

[OperationContext](../services-and-apps/05-operation-context.md) includes at minimum:

* Requesting identity identifier.
* Executing `app_id`.
* Execution mode.
* Sync domain identifier when applicable.
* Remote node identity when applicable.
* Trace identifier.

[OperationContext](../services-and-apps/05-operation-context.md) fields must align with the construction rules defined in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) and [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md), including remote indicators, sync domain binding, and traceability metadata.

All inputs are treated as untrusted.

### 5.2 Outputs

The [Graph Manager](07-graph-manager.md) returns:

* Acceptance or rejection for the entire write envelope.
* Assigned global sequence values and created identifiers.
* Authorized read result sets filtered by visibility rules.
* Structured error codes suitable for propagation and logging.

Side effects include persisted state mutations, post commit events, and audit logging.

### 5.3 Trust boundaries

The [Graph Manager](07-graph-manager.md) relies on:

* [Schema Manager](05-schema-manager.md) for validation and domain membership.
* [ACL Manager](06-acl-manager.md) for authorization and masking.
* [State Manager](09-state-manager.md) for delivery of verified remote envelopes.
* [Storage Manager](02-storage-manager.md) for transactional persistence and sequencing.
* [Event Manager](11-event-manager.md) and [Log Manager](12-log-manager.md) for delivery and logging.

## 6. Allowed and forbidden behaviors

### 6.1 Explicitly allowed behaviors

The [Graph Manager](07-graph-manager.md) allows:

* Write envelopes from trusted local services, per [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Write envelopes from [State Manager](09-state-manager.md) for remote application, after the [Network Manager](10-network-manager.md) and [State Manager](09-state-manager.md) path defined in [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md).
* Authorized reads of Parents, Attributes, Edges, and Ratings that satisfy the enforcement rules in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Bounded adjacency reads.
* Bounded traversal strictly for authorization.
* Default visibility filtering.
* Snapshot bounded reads when supported.

### 6.2 Explicitly forbidden behaviors

The [Graph Manager](07-graph-manager.md) forbids:

* Persisted graph writes from any other component, preserving the single write boundary defined in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Bypassing schema validation or authorization, which would violate [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) and [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Returning unauthorized data, forbidden by [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Writing into another application's graph, which breaks [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Partial envelope application, disallowed by [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Emitting events prior to commit, which would contradict the ordering rules in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Unbounded reads or traversals, violating the fail-closed posture in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Accepting remote envelopes that bypass [State Manager](09-state-manager.md), which would conflict with [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md).
* Issuing direct storage calls, which would bypass the manager boundaries in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).

## 7. Write path behavior

### 7.1 Processing order

For each write envelope:

* Structural validation.
* Schema validation.
* Authorization evaluation.
* Serialized execution.
* Atomic commit.
* Post commit event emission.

### 7.2 Structural validation

The [Graph Manager](07-graph-manager.md) validates:

* Presence of at least one operation.
* Supported operation identifiers that are limited to `parent_create`, `parent_update`, `attr_create`, `attr_update`, `edge_create`, `edge_update`, `rating_create`, and `rating_update` per [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Consistent `app_id` and `owner_identity`, referencing the identifier semantics in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md) and the identity guarantees in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Correct identifier usage, including `type_key` XOR `type_id` semantics per [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Absence of storage controlled fields such as `global_seq` and `sync_flags`.
* Absence of unknown envelope or operation keys defined outside [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).

### 7.3 Schema validation

Schema validation is delegated to [Schema Manager](05-schema-manager.md) so that schema compilation and enforcement remain authoritative per [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).

### 7.4 Authorization evaluation

Authorization is delegated to [ACL Manager](06-acl-manager.md), preserving the access control sequencing defined in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

### 7.5 Sequencing and persistence

For accepted envelopes:

* Global sequence values are allocated per [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* All operations persist in one transaction, satisfying the atomicity rules in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Storage controlled metadata is computed internally to preserve the storage ownership boundaries in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).

### 7.6 Post commit events

Events are emitted only after commit, following the ordering guarantees in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). Event failure never rolls back committed state.

## 8. Read semantics and behavior

### 8.1 Read surface

Supported reads include:

* Direct reads by identifier.
* Bounded adjacency reads.
* Batch reads.

Direct identifier reads observe the resolution guarantees defined by [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md) and do not leak unauthorized data per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

### 8.2 Read consistency model

Reads observe committed state only per [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). Snapshot binding is optional and explicit.

### 8.3 Authorization and visibility

Authorization is mandatory per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md). Visibility filtering applies after authorization.

### 8.4 Resource limits

  All reads enforce fixed budgets per the fail-closed resource constraints defined in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

## 9. Bounded traversal support

Traversal exists solely to support authorization, as required by [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

Constraints:

* Fixed depth.
* Fixed frontier.
* Fixed visited count.
* No exposure of intermediate nodes.

## 10. Failure and rejection handling

Failures fail closed per [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

* No partial writes occur, consistent with [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Serialized context is released.
* Errors follow protocol precedence rules defined by [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md), including structural failures taking precedence over schema and ACL failures.

Graph Manager failure mapping to `ErrorDetail.code`:

* Structural validation failure -> `envelope_invalid`
* Identifier validation failure -> `identifier_invalid`
* Unknown type resolution -> `schema_unknown_type`
* Schema validation failure -> `schema_validation_failed`
* ACL denial -> `acl_denied`
* Sequencing violation -> `sequence_error`
* Persistence failure -> `storage_error`

## 11. Object lifecycle assumptions

* Objects may be created and mutated following the category semantics in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* Removal is implemented via Rating based visibility suppression consistent with application schemas defined atop [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* Lifecycle semantics are schema defined and enforced via [Schema Manager](05-schema-manager.md) per [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).

## 12. Minimal state and caching constraints

### 12.1 Permitted state

* System identity Parents required to fulfill graph level responsibilities defined in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Transient request scoped caches that do not violate the manager boundary rules defined in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).

### 12.2 Forbidden state

* Long lived semantic indices that would conflict with [Storage Manager](02-storage-manager.md) ownership in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Recovery critical in memory state, which would break the failure posture in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

## 13. Component interactions

### 13.1 Schema Manager

Provides validation, mapping, and domain membership per [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).

### 13.2 ACL Manager

Provides authorization, masking, and distance rules per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

### 13.3 Storage Manager

Provides transactional persistence and sequencing required by [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).

### 13.4 Event Manager and Log Manager

Deliver post commit events and logs in the order required by [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).

### 13.5 State Manager

Delivers verified remote envelopes and constructs [OperationContext](../services-and-apps/05-operation-context.md), preserving the remote ingestion posture in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md).

## 14. Interface stability

The [Graph Manager](07-graph-manager.md) is an internal system component. It is not a public API.

Backward compatibility expectations are defined at the manager boundary.
