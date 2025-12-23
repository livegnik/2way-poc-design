



# 04 Data flow overview

## 1. Purpose and scope

This document defines the authoritative data flow model for the 2WAY system as implemented in the PoC. It specifies how data enters, moves through, mutates, and exits the system, including bootstrap, user provisioning, validation, authorization, sequencing, persistence, event emission, synchronization, rejection handling, and visibility suppression. It is limited to data flow semantics and boundaries and does not define schemas, envelopes, storage layouts, network formats, or UI behavior except where required for correctness.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining all allowed data flow paths between frontend, services, managers, storage, and network layers.
* Defining the required ordering of bootstrap, provisioning, validation, authorization, sequencing, persistence, and emission.
* Defining trust boundaries crossed during data movement.
* Defining allowed and forbidden data movements.
* Defining rejection and failure propagation behavior.
* Defining visibility suppression semantics via Rating objects.

This specification does not cover the following:

* Envelope structure or serialization details.
* Schema definitions or schema evolution rules.
* ACL rule syntax or policy composition.
* Database schemas, indices, or query strategies.
* Transport protocols, routing, or discovery mechanisms.
* UI level behavior or frontend state management.

## 3. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* All persistent state is expressed exclusively as graph objects.
* All graph mutations pass through Graph Manager.
* All authorization decisions pass through ACL Manager.
* All schema validation passes through Schema Manager.
* All database access passes through Storage Manager.
* All write operations are serialized and assigned a strictly monotonic global sequence.
* All network ingress and egress passes through Network Manager.
* DoS Guard Manager is applied exclusively to network level ingress.
* All real-time notifications pass through Event Manager.
* All cryptographic private keys are accessed only by Key Manager.
* OperationContext is immutable once constructed and propagated unchanged.
* Domain boundaries are enforced on all reads, writes, and sync operations.
* No delete or physical removal operations exist in the PoC.

These guarantees hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 4. Data flow classification

All data movement in the system is classified into the following flow categories:

* Node bootstrap and Server Graph initialization.
* User provisioning and User Graph creation.
* Local read flow.
* Local write flow.
* Visibility suppression via Ratings.
* Event emission flow.
* Remote ingress flow.
* Remote egress flow.
* Derived and cached data flow.

No other data flow categories are permitted.

## 5. Node bootstrap and user provisioning flows

### 5.1 Scope

This section defines two distinct but related flows:

* One time node bootstrap and Server Graph initialization.
* Repeated user provisioning and User Graph creation after bootstrap.

For the PoC, frontend and backend execution are assumed to occur on the same physical device, so key generation is performed by the backend without altering trust assumptions, while later versions may relocate key generation without changing the data flow model.

### 5.2 Node bootstrap and Server Graph initialization

#### Inputs

* First-run invocation with no existing persistent state.

#### Flow

* Key Manager generates node and server level cryptographic material.
* Graph Manager creates Server Graph root objects.
* Schema Manager validates all bootstrap objects.
* ACL Manager establishes initial server ownership and default server level ACL bindings.
* Storage Manager persists bootstrap state atomically.
* Global sequence is initialized and anchored for the Server Graph.

#### Allowed behavior

* Creation of Server Graph root objects only.
* Single execution per server instance.

#### Forbidden behavior

* Creation of User Graphs during bootstrap.
* Any non-bootstrap write before completion.
* Re-execution after persistent state exists.

#### Failure behavior

* Partial bootstrap state is not persisted.
* Failure leaves the system uninitialized.

### 5.3 User provisioning and User Graph creation

#### Inputs

* Create-user request via the local API.
* OperationContext representing an authorized administrative identity.

#### Flow

* Auth Manager resolves the caller and constructs OperationContext.
* Key Manager generates a new user identity keypair.
* Graph Manager creates the user identity objects.
* Graph Manager creates the User Graph root objects linked to the Server Graph.
* Schema Manager validates all created objects.
* ACL Manager establishes initial ownership and default user level ACL bindings.
* Storage Manager persists all objects atomically.
* Global sequence is incremented and assigned.
* Event Manager emits user and identity creation events after commit.

#### Allowed behavior

* Repeated execution to create multiple users.
* Creation of multiple User Graphs sharing a single Server Graph.
* Administrative provisioning of users according to ACL policy.

#### Forbidden behavior

* Creating users without Key Manager key generation.
* Creating users outside Graph Manager.
* Assigning ownership of a user identity to an unrelated identity unless explicitly permitted by schema and ACL rules.

#### Failure behavior

* Any failure rolls back the entire user creation operation.
* No partial user identity or User Graph state is persisted.
* No events are emitted on failure.

## 6. Local read flow

### 6.1 Inputs

* Read request from frontend app or backend service.
* OperationContext containing requester identity, app identity, and domain scope.

### 6.2 Flow

* API layer receives request.
* OperationContext is constructed.
* ACL Manager evaluates read permissions and domain membership.
* Service or app backend extension may compute query parameters and apply derived or cached read optimizations without database access.
* Storage Manager executes constrained read using parameters provided by the caller.
* Service or app backend extension applies deterministic visibility suppression based on accessible Rating objects where defined.
* Results are returned to caller.

### 6.3 Allowed behavior

* Visibility filtering based on ACL and domain rules.
* Deterministic suppression based on Rating interpretation.
* Read optimization using derived or cached data that is non-authoritative.
* Read only access to authoritative graph state through Storage Manager.

### 6.4 Forbidden behavior

* Reads that bypass ACL Manager or domain checks.
* Direct database access by apps or services.
* Reads that aggregate across domains.
* Read optimizations that introduce new authoritative state.
* Visibility suppression that mutates state.

### 6.5 Failure behavior

* Unauthorized reads are rejected without partial results.
* Domain violations are rejected.
* Storage failures propagate as read failures without side effects.
* Cache or derived data failures degrade performance only.

## 7. Local write flow

### 7.1 Inputs

* Write request from frontend app or backend service.
* Envelope containing one or more graph operations.
* OperationContext containing requester identity, app identity, and domain scope.

### 7.2 Flow

* API layer receives request.
* OperationContext is constructed.
* Schema Manager validates types and constraints.
* ACL Manager evaluates write permissions and domain membership.
* Graph Manager acquires exclusive write access.
* Global sequence is incremented and assigned.
* Storage Manager persists all changes atomically.
* Graph Manager releases write access.
* Event Manager is notified of committed changes.

### 7.3 Allowed behavior

* Batched graph operations within a single envelope.
* Deterministic ordering of all writes.
* Event emission after commit only.

### 7.4 Forbidden behavior

* Writes outside Graph Manager.
* Writes without schema or ACL validation.
* Writes crossing domain boundaries.
* Concurrent or parallel write paths.

### 7.5 Failure behavior

* Validation or authorization failure rejects the envelope.
* Storage failure rolls back the entire operation.
* Rejected writes produce no events.

## 8. Visibility suppression via Ratings

### 8.1 Scope

Visibility suppression replaces delete semantics in the PoC and is implemented using Rating graph objects.

### 8.2 Inputs

* Write request creating or updating a Rating object targeting another graph object.

### 8.3 Flow

* Rating enters standard local or remote write flow.
* Rating is validated by Schema Manager.
* Rating authorship and scope are validated by ACL Manager.
* Rating is serialized, sequenced, and persisted like any other object.
* Event Manager emits rating related events after commit.

### 8.4 Interpretation rules

* Ratings do not remove or alter target objects.
* Ratings are interpreted at read time by services or apps.
* Interpretation rules are deterministic and app scoped.
* Interpretation respects ACL visibility of Rating objects.

This Rating contains a vote value, where a value of zero represents a suppression signal and serves as the PoC substitute for delete semantics.

Additional fields may be present to represent scoring, reactions, comments, or other annotations, with interpretation defined entirely by the consuming app or service.

### 8.5 Allowed behavior

* Per identity private suppression using private Ratings.
* Shared suppression using Ratings visible to a group or domain.
* Threshold or aggregate based suppression defined by the app.

### 8.6 Forbidden behavior

* Physical deletion of objects.
* Implicit suppression without an explicit Rating.
* Visibility rules that bypass ACL visibility of Ratings.

### 8.7 Failure behavior

* Rating write failures behave as write failures.
* Invalid Ratings are rejected without affecting target objects.

## 9. Event emission flow

### 9.1 Inputs

* Committed graph mutations.
* Internal system signals.

### 9.2 Flow

* Domain events are emitted.
* Event Manager dispatches events to subscribers.
* WebSocket layer delivers notifications.

### 9.3 Allowed behavior

* Asynchronous delivery independent of write correctness.

### 9.4 Forbidden behavior

* Events that mutate state.
* Direct WebSocket access by non-Event components.

### 9.5 Failure behavior

* Event delivery failure does not affect state.
* Dropped connections do not trigger retries.

## 10. Remote ingress flow

### 10.1 Inputs

* Signed and encrypted package from remote peer.

### 10.2 Flow

* Network Manager accepts or rejects the peer connection.
* DoS Guard Manager applies admission control using dynamic difficulty challenges and rate limits.
* Network Manager receives encrypted payloads only on admitted connections.
* Key Manager looks up the claimed key id and validates key existence, allowed purpose, and revocation state.
* Key Manager verifies the signature over the authenticated message header.
* Key Manager decrypts the payload.
* State Manager validates sync metadata, domain scope, ordering, and replay protection.
* Remote OperationContext is derived from the verified peer identity and fixed for the remainder of the flow.
* Envelopes are forwarded to Graph Manager.
* Standard local write flow is applied.

### 10.3 Allowed behavior

* Acceptance of remote data only via standard pipelines.
* Replication of Rating objects by domain and ACL visibility.
* Rejection of unauthorized or out-of-domain data.

### 10.4 Forbidden behavior

* Remote writes bypassing Network Manager or DoS Guard Manager.
* Remote writes bypassing State Manager or Graph Manager.
* Trust based on transport properties alone.

### 10.5 Failure behavior

* Invalid signatures or revoked keys cause rejection.
* Sequence violations cause rejection without partial application.
* Rejections are recorded in peer sync state.

## 11. Remote egress flow

### 11.1 Inputs

* Locally committed graph changes.
* Per peer sync state.

### 11.2 Flow

* State Manager selects eligible graph objects by domain and sequence.
* Envelopes are constructed.
* Key Manager signs the authenticated message header, including sender key id and ciphertext binding.
* Network Manager establishes or reuses a peer connection, including solving required client puzzles during admission.
* Key Manager looks up the recipient peer key material required for encryption.
* Network Manager encrypts the payload for the remote peer.
* Network Manager transmits the encrypted package over the established connection.

### 11.3 Allowed behavior

* Selective and incremental sync.
* Propagation of visibility suppression state via Ratings.

### 11.4 Forbidden behavior

* Sending uncommitted state.
* Sending data outside declared domains.

### 11.5 Failure behavior

* Transmission failure does not affect local state.
* Retry behavior is controlled exclusively by State Manager.

## 12. Derived and cached data flow

### 12.1 Scope

Derived data includes in-memory indices, caches, and precomputed query results.

### 12.2 Allowed behavior

* Performance optimization only.
* Rebuild from authoritative graph state.

### 12.3 Forbidden behavior

* Treating derived data as authoritative.
* Persisting or syncing derived data.

### 12.4 Failure behavior

* Loss degrades performance only.
* Rebuild requires no network access.

## 13. Rejection propagation and observability

### 13.1 Guarantees

* All rejections propagate to the original caller.
* Remote rejections are reflected in peer sync state.
* Rejections are observable by Log Manager and audit systems.

### 13.2 Forbidden behavior

* Silent rejection without caller visibility.
* Partial acceptance of rejected operations.

## 14. Trust boundaries

The following trust boundaries are explicitly crossed:

* Frontend to backend API boundary.
* Backend to storage boundary.
* Backend to network boundary.
* Local node to remote peer boundary.

At each boundary:

* Identity is explicit.
* Authorization is enforced.
* Data is validated before acceptance.

## 15. Summary of guarantees

This data flow model guarantees:

* Deterministic and ordered state evolution.
* Enforced bootstrap and user provisioning semantics.
* Uniform authorization, domain, and schema enforcement.
* Visibility suppression without data loss.
* Authenticated before decrypt processing for all remote ingress payloads.
* Replay protection enforced by State Manager using ordering and peer sync state.
* Confidentiality and integrity for peer transport via encryption and signed authenticated headers.
* DoS containment on peer connections via DoS Guard Manager admission control with dynamic difficulty challenges.
* Derived and cached data is non-authoritative and cannot affect correctness when lost.
* Network retry decisions are owned by State Manager and driven by per-peer sync state.
* Predictable fail-closed behavior under error or load.
* No implicit or hidden data paths.
