



# 07 Graph Manager

## 1. Purpose and scope

The Graph Manager is the authoritative coordinator for all graph state mutations within the local node. It validates, authorizes, orders, and persists graph mutations against per app storage, enforcing global consistency and security invariants.

This document defines the responsibilities, boundaries, invariants, guarantees, allowed and forbidden behaviors, component interactions, and failure handling for the Graph Manager.

This file specifies graph level behavior only. It does not define schema semantics, access control policy logic, sync protocol behavior, network transport, or storage internals, except where interaction boundaries are explicitly required.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Acting as the single entry point for all graph mutations that affect persistent state.
* Accepting mutation requests only from trusted in process components.
* Validating graph operation structure and internal consistency.
* Delegating type resolution and structural validation to the Schema Manager.
* Delegating authorization decisions to the ACL Manager.
* Enforcing write ordering and serialization guarantees.
* Assigning globally ordered sequence identifiers to accepted mutations.
* Persisting graph mutations atomically via the Storage Manager.
* Computing and applying sync participation metadata derived from schema domain definitions.
* Emitting post commit graph mutation events.
* Recording acceptance and rejection outcomes for audit and diagnostics.

This specification does not cover the following:

* Definition, creation, or evolution of schemas.
* Interpretation of application level semantics.
* Definition or evaluation of access control rules.
* Network communication, peer coordination, or sync protocol execution.
* Storage engine implementation details or SQL schema design.
* Deletion semantics beyond what is defined as graph mutation types elsewhere.
* Conflict resolution logic beyond atomic application or rejection.

## 3. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* All persistent graph mutations pass through the Graph Manager.
* No mutation is persisted without prior schema validation and authorization.
* Graph mutations are applied atomically per envelope.
* Mutation ordering is globally consistent and monotonic.
* Sequence assignment is serialized and cannot be influenced by callers.
* Graph state cannot be mutated across application boundaries.
* Graph Manager behavior is deterministic given identical inputs and system state.
* No partial state is observable from rejected or failed mutations.

These guarantees must hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 4. Inputs, outputs, and trust boundaries

### 4.1 Inputs

The Graph Manager accepts mutation requests in the form of graph envelopes accompanied by an OperationContext.

The OperationContext includes:

* Requesting identity identifier.
* Application identifier.
* Execution mode, local or remote.
* Sync domain identifier when applicable.
* Remote node identity when applicable.
* Trace identifier.

Graph envelopes contain a finite set of graph operations, limited to graph object creation and mutation types defined by the schema layer.

All inputs are treated as untrusted and subject to full validation.

### 4.2 Outputs

The Graph Manager produces the following outputs:

* An acceptance or rejection result for the entire envelope.
* Assigned sequence identifiers and object identifiers for accepted operations when required by the caller.
* Structured rejection or failure reasons suitable for propagation and logging.

Side effects include:

* Persistent graph state changes.
* Emitted graph mutation events.
* Audit and diagnostic log entries.

### 4.3 Trust boundaries

The Graph Manager establishes the following trust boundaries:

* Schema Manager is authoritative for type existence, structure, value constraints, and domain membership.
* ACL Manager is authoritative for authorization decisions.
* Storage Manager is authoritative for persistence, transactional integrity, and sequence allocation.
* Event Manager is authoritative for event delivery.
* Callers are not trusted to provide correct types, ownership, sync scope, or values.

## 5. Allowed and forbidden behaviors

### 5.1 Explicitly allowed behaviors

The Graph Manager allows:

* Local graph mutations issued by system services and application extensions, subject to validation and authorization.
* Remote graph mutations applied through the State Manager, subject to schema constraints, authorization, and sync domain restrictions.
* Mixed operation envelopes, provided all operations validate and authorize successfully.
* Rejection of entire envelopes on any validation or authorization failure.

### 5.2 Explicitly forbidden behaviors

The Graph Manager forbids:

* Direct persistence of graph state by any other component.
* Bypassing schema validation or authorization.
* Mutating graph state outside the declared application scope.
* Creating or modifying objects with undefined or mismatched types.
* Changing ownership or authorship of existing graph objects.
* Caller supplied control over sequence identifiers or sync metadata.
* Partial application of envelopes.
* Side effects, including event emission, prior to successful commit.

## 6. Core behavior

### 6.1 Processing order

For each received envelope, the Graph Manager enforces the following strict order:

* Envelope structural validation.
* Schema validation and type resolution.
* Authorization evaluation.
* Acquisition of the serialized write context.
* Sequence allocation and persistence.
* Transaction commit.
* Event emission and logging.

No later step may occur if an earlier step fails.

### 6.2 Structural validation

The Graph Manager validates that:

* The envelope targets a single application.
* All operations are supported graph mutation kinds.
* Required references for each operation type are present.
* No reserved or storage controlled fields are supplied by the caller.
* Internal references within the envelope are consistent.

Structural validation failures cause immediate envelope rejection.

### 6.3 Schema interaction

For each operation, the Graph Manager invokes the Schema Manager to:

* Resolve external type identifiers to internal type identifiers.
* Validate that the operation kind is permitted for the resolved type.
* Validate value representations and constraints.
* Determine sync domain membership for the operation type.

Schema Manager output is treated as authoritative. Any schema rejection causes envelope rejection.

### 6.4 Authorization interaction

For each operation, the Graph Manager invokes the ACL Manager with:

* OperationContext.
* Object kind and type identifiers.
* Ownership and authorship metadata.
* Local or remote execution mode.
* Sync domain information when applicable.

Authorization is evaluated per operation. A single denial causes rejection of the entire envelope.

### 6.5 Persistence and ordering

For accepted envelopes, the Graph Manager:

* Acquires exclusive access to the sequence allocation path.
* Assigns strictly increasing sequence identifiers.
* Computes sync participation metadata from schema domain membership.
* Persists all operations within a single atomic transaction.
* Releases exclusive access after commit.

The Graph Manager does not perform network operations, event emission, or logging while holding the serialized write context.

### 6.6 Sync participation metadata

Sync participation metadata is derived solely from schema domain definitions.

* Callers cannot influence sync scope directly.
* Local only schema types are never marked for sync.
* Multi domain membership is represented explicitly where defined.

The Graph Manager relies on the data layer to store and index this metadata.

### 6.7 Event emission

After successful commit, the Graph Manager emits graph mutation events that include:

* Application identifier.
* Object kinds and identifiers affected.
* Sequence identifier range.
* Trace identifier when available.

Event payloads exclude sensitive values unless explicitly permitted by downstream consumers.

## 7. Failure and rejection handling

### 7.1 Rejection conditions

The Graph Manager rejects envelopes when:

* Structural validation fails.
* Schema validation fails.
* Authorization is denied for any operation.
* Referenced graph objects do not exist where required.
* Application scope violations are detected.
* Sync domain restrictions prohibit the mutation.

Rejections result in no persistent changes.

### 7.2 Failure behavior

On internal failures:

* No partial state is committed.
* The serialized write context is released.
* A failure result distinct from rejection is returned.

Internal failures include:

* Storage errors.
* Sequence allocation failures.
* Inconsistent schema or metadata state.

Event emission failures do not affect commit success but are recorded and surfaced to health monitoring.

### 7.3 Atomicity

Envelope application is strictly atomic. Partial persistence is forbidden under all conditions.

## 8. Minimal state and constraints

### 8.1 Permitted in memory state

The Graph Manager may maintain only transient state necessary for request processing, including:

* Short lived resolution caches where correctness is unaffected.
* Temporary operation context data.

All such state must be discardable without affecting correctness.

### 8.2 Forbidden state

The Graph Manager must not maintain:

* Long lived application semantic state.
* Independent authorization or schema caches.
* State required for recovery after process restart.

## 9. Component interactions summary

The Graph Manager interacts with other components strictly through defined inputs and outputs.

* Schema Manager for validation and type resolution.
* ACL Manager for authorization decisions.
* Storage Manager for persistence and sequencing.
* Event Manager for post commit notifications.
* Log Manager for audit and diagnostics.

No other component is permitted to mutate graph state directly.
