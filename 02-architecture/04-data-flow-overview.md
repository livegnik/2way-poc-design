



# 04 Data flow overview

Defines authoritative data flow paths for 2WAY, including bootstrap, read/write, sync, and rejection handling. Specifies ordering, validation, authorization, and persistence boundaries for all flows. Defines visibility suppression and event emission semantics.

For the meta specifications, see [04-data-flow-overview meta](../10-appendix/meta/02-architecture/04-data-flow-overview-meta.md).

## 1. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* All persistent state is expressed exclusively as graph objects defined in [01-protocol/02-object-model.md](../01-protocol/02-object-model.md).
* All graph mutations pass through [Graph Manager](managers/07-graph-manager.md).
* All authorization decisions pass through [ACL Manager](managers/06-acl-manager.md).
* All schema validation passes through [Schema Manager](managers/05-schema-manager.md).
* All database access passes through [Storage Manager](managers/02-storage-manager.md).
* All write operations are serialized and assigned a strictly monotonic global sequence per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).
* All network ingress and egress passes through [Network Manager](managers/10-network-manager.md) per [01-protocol/08-network-transport-requirements.md](../01-protocol/08-network-transport-requirements.md).
* [DoS Guard Manager](managers/14-dos-guard-manager.md) is applied exclusively to network level ingress per [01-protocol/09-dos-guard-and-client-puzzles.md](../01-protocol/09-dos-guard-and-client-puzzles.md).
* All real-time notifications pass through [Event Manager](managers/11-event-manager.md).
* All cryptographic private keys are accessed only by [Key Manager](managers/03-key-manager.md) per [01-protocol/05-keys-and-identity.md](../01-protocol/05-keys-and-identity.md).
* Signature verification and public-key encryption may be performed by authorized managers or services when permitted by [OperationContext](services-and-apps/05-operation-context.md) and identity data in the graph; private keys never leave [Key Manager](managers/03-key-manager.md).
* [OperationContext](services-and-apps/05-operation-context.md) is immutable once constructed and propagated unchanged.
* Domain boundaries are enforced on all reads, writes, and sync operations per [01-protocol/06-access-control-model.md](../01-protocol/06-access-control-model.md) and [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).
* No delete or physical removal operations exist in the PoC.

These guarantees hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 2. Data flow classification

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

## 3. Node bootstrap and user provisioning flows

### 3.1 Scope

This section defines two distinct but related flows:

* One time node bootstrap and Server Graph initialization.
* Repeated user provisioning and User Graph creation after bootstrap.

For the PoC, frontend and backend execution are assumed to occur on the same physical device, so key generation is performed by the backend without altering trust assumptions, while later versions may relocate key generation without changing the data flow model.

### 3.2 Node bootstrap and Server Graph initialization

#### Inputs

* First-run invocation with no existing persistent state.

#### Flow

* [Key Manager](managers/03-key-manager.md) generates node and server level cryptographic material aligned to [01-protocol/05-keys-and-identity.md](../01-protocol/05-keys-and-identity.md).
* [Graph Manager](managers/07-graph-manager.md) creates Server Graph root objects.
* [Schema Manager](managers/05-schema-manager.md) validates all bootstrap objects.
* [ACL Manager](managers/06-acl-manager.md) establishes initial server ownership and default server level ACL bindings.
* [Storage Manager](managers/02-storage-manager.md) persists bootstrap state atomically.
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

### 3.3 User provisioning and User Graph creation

#### Inputs

* Create-user request via the local API ([04-interfaces/01-local-http-api.md](../04-interfaces/01-local-http-api.md)).
* [OperationContext](services-and-apps/05-operation-context.md) representing an authorized administrative identity.

#### Flow

* [Auth Manager](managers/04-auth-manager.md) resolves the caller and constructs [OperationContext](services-and-apps/05-operation-context.md).
* [Key Manager](managers/03-key-manager.md) generates a new user identity keypair aligned to [01-protocol/05-keys-and-identity.md](../01-protocol/05-keys-and-identity.md).
* [Graph Manager](managers/07-graph-manager.md) creates the user identity objects.
* [Graph Manager](managers/07-graph-manager.md) creates the User Graph root objects linked to the Server Graph.
* [Schema Manager](managers/05-schema-manager.md) validates all created objects.
* [ACL Manager](managers/06-acl-manager.md) establishes initial ownership and default user level ACL bindings.
* [Storage Manager](managers/02-storage-manager.md) persists all objects atomically.
* Global sequence is incremented and assigned per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).
* [Event Manager](managers/11-event-manager.md) emits user and identity creation events after commit.

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

## 4. Local read flow

### 4.1 Inputs

* Read request from frontend app or backend service defined in [02-architecture/services-and-apps/**](services-and-apps/).
* [OperationContext](services-and-apps/05-operation-context.md) containing requester identity, app identity, and domain scope.

### 4.2 Flow

* API layer receives request through [04-interfaces/**](../04-interfaces/).
* [OperationContext](services-and-apps/05-operation-context.md) is constructed.
* Service or app service defined in [02-architecture/services-and-apps/**](services-and-apps/) computes query parameters and may apply derived or cached read optimizations without database access.
* [Graph Manager](managers/07-graph-manager.md) evaluates authorization via [ACL Manager](managers/06-acl-manager.md) and executes constrained reads through [Storage Manager](managers/02-storage-manager.md).
* Service or app service applies deterministic visibility suppression based on accessible Rating objects defined in [01-protocol/02-object-model.md](../01-protocol/02-object-model.md) where defined.
* Results are returned to caller.

### 4.3 Allowed behavior

* Visibility filtering based on ACL and domain rules.
* Deterministic suppression based on Rating interpretation.
* Read optimization using derived or cached data that is non-authoritative.
* Read only access to authoritative graph state through [Graph Manager](managers/07-graph-manager.md).

### 4.4 Forbidden behavior

* Reads that bypass [ACL Manager](managers/06-acl-manager.md) or domain checks.
* Reads that bypass [Graph Manager](managers/07-graph-manager.md) for authoritative graph data.
* Direct database access by apps or services.
* Reads that aggregate across domains.
* Read optimizations that introduce new authoritative state.
* Visibility suppression that mutates state.

### 4.5 Failure behavior

* Unauthorized reads are rejected without partial results.
* Domain violations are rejected.
* Storage failures propagate as read failures without side effects.
* Cache or derived data failures degrade performance only.

## 5. Local write flow

### 5.1 Inputs

* Write request from frontend app or backend service defined in [02-architecture/services-and-apps/**](services-and-apps/).
* Envelope containing one or more graph operations defined in [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md).
* [OperationContext](services-and-apps/05-operation-context.md) containing requester identity, app identity, and domain scope.

### 5.2 Flow

* API layer receives request through [04-interfaces/**](../04-interfaces/).
* [OperationContext](services-and-apps/05-operation-context.md) is constructed.
* [Schema Manager](managers/05-schema-manager.md) validates types and constraints.
* [ACL Manager](managers/06-acl-manager.md) evaluates write permissions and domain membership.
* [Graph Manager](managers/07-graph-manager.md) acquires exclusive write access.
* Global sequence is incremented and assigned per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).
* [Storage Manager](managers/02-storage-manager.md) persists all changes atomically.
* [Graph Manager](managers/07-graph-manager.md) releases write access.
* [Event Manager](managers/11-event-manager.md) is notified of committed changes.

### 5.3 Allowed behavior

* Batched graph operations within a single envelope.
* Deterministic ordering of all writes.
* Event emission after commit only.

### 5.4 Forbidden behavior

* Writes outside [Graph Manager](managers/07-graph-manager.md).
* Writes without schema or ACL validation by [Schema Manager](managers/05-schema-manager.md) or [ACL Manager](managers/06-acl-manager.md).
* Writes crossing domain boundaries.
* Concurrent or parallel write paths.

### 5.5 Failure behavior

* Validation or authorization failure rejects the envelope.
* Storage failure rolls back the entire operation.
* Rejected writes produce no events.

## 6. Visibility suppression via Ratings

### 6.1 Scope

Visibility suppression replaces delete semantics in the PoC and is implemented using Rating graph objects defined in [01-protocol/02-object-model.md](../01-protocol/02-object-model.md).

### 6.2 Inputs

* Write request creating or updating a Rating object targeting another graph object defined in [01-protocol/02-object-model.md](../01-protocol/02-object-model.md).

### 6.3 Flow

* Rating enters standard local or remote write flow defined in this document.
* Rating is validated by [Schema Manager](managers/05-schema-manager.md).
* Rating authorship and scope are validated by [ACL Manager](managers/06-acl-manager.md).
* Rating is serialized, sequenced, and persisted like any other object per [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md).
* [Event Manager](managers/11-event-manager.md) emits rating related events after commit.

### 6.4 Interpretation rules

* Ratings do not remove or alter target objects.
* Ratings are interpreted at read time by services or apps defined in [02-architecture/services-and-apps/**](services-and-apps/).
* Interpretation rules are deterministic and app scoped.
* Interpretation respects ACL visibility of Rating objects.

This Rating contains a vote value, where a value of zero represents a suppression signal and serves as the PoC substitute for delete semantics.

Additional fields may be present to represent scoring, reactions, comments, or other annotations, with interpretation defined entirely by the consuming app or service.

### 6.5 Allowed behavior

* Per identity private suppression using private Ratings.
* Shared suppression using Ratings visible to a group or domain.
* Threshold or aggregate based suppression defined by the app.

### 6.6 Forbidden behavior

* Physical deletion of objects.
* Implicit suppression without an explicit Rating.
* Visibility rules that bypass ACL visibility of Ratings enforced by [ACL Manager](managers/06-acl-manager.md).

### 6.7 Failure behavior

* Rating write failures behave as write failures.
* Invalid Ratings are rejected without affecting target objects.

## 7. Event emission flow

### 7.1 Inputs

* Committed graph mutations.
* Internal system signals.

### 7.2 Flow

* Domain events are emitted.
* [Event Manager](managers/11-event-manager.md) dispatches events to subscribers.
* WebSocket layer delivers notifications through [04-interfaces/02-websocket-events.md](../04-interfaces/02-websocket-events.md).

### 7.3 Allowed behavior

* Asynchronous delivery independent of write correctness.

### 7.4 Forbidden behavior

* Events that mutate state.
* Direct WebSocket access by non-Event components outside [Event Manager](managers/11-event-manager.md).

### 7.5 Failure behavior

* Event delivery failure does not affect state.
* Dropped connections do not trigger retries.

## 8. Remote ingress flow

### 8.1 Inputs

* Signed and encrypted package from remote peer defined in [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md) and [01-protocol/04-cryptography.md](../01-protocol/04-cryptography.md).

### 8.2 Flow

* [Network Manager](managers/10-network-manager.md) accepts or rejects the peer connection per [01-protocol/08-network-transport-requirements.md](../01-protocol/08-network-transport-requirements.md).
* [DoS Guard Manager](managers/14-dos-guard-manager.md) applies admission control using dynamic difficulty challenges and rate limits per [01-protocol/09-dos-guard-and-client-puzzles.md](../01-protocol/09-dos-guard-and-client-puzzles.md).
* [Network Manager](managers/10-network-manager.md) receives encrypted payloads only on admitted connections.
* [Key Manager](managers/03-key-manager.md) looks up the claimed key id and validates key existence, allowed purpose, and revocation state per [01-protocol/05-keys-and-identity.md](../01-protocol/05-keys-and-identity.md).
* [Network Manager](managers/10-network-manager.md) verifies the signature over the authenticated message header using public keys per [01-protocol/04-cryptography.md](../01-protocol/04-cryptography.md).
* [Key Manager](managers/03-key-manager.md) decrypts the payload per [01-protocol/04-cryptography.md](../01-protocol/04-cryptography.md).
* [State Manager](managers/09-state-manager.md) validates sync metadata, domain scope, ordering, and replay protection per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).
* Remote [OperationContext](services-and-apps/05-operation-context.md) is derived from the verified peer identity and fixed for the remainder of the flow.
* Envelopes are forwarded to [Graph Manager](managers/07-graph-manager.md).
* Standard local write flow is applied.

### 8.3 Allowed behavior

* Acceptance of remote data only via standard pipelines.
* Replication of Rating objects by domain and ACL visibility.
* Rejection of unauthorized or out-of-domain data.

### 8.4 Forbidden behavior

* Remote writes bypassing [Network Manager](managers/10-network-manager.md) or [DoS Guard Manager](managers/14-dos-guard-manager.md).
* Remote writes bypassing [State Manager](managers/09-state-manager.md) or [Graph Manager](managers/07-graph-manager.md).
* Trust based on transport properties alone.

### 8.5 Failure behavior

* Invalid signatures or revoked keys cause rejection per [01-protocol/10-errors-and-failure-modes.md](../01-protocol/10-errors-and-failure-modes.md).
* Sequence violations cause rejection without partial application per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).
* Rejections are recorded in peer sync state.

## 9. Remote egress flow

### 9.1 Inputs

* Locally committed graph changes.
* Per peer sync state tracked by [State Manager](managers/09-state-manager.md).

### 9.2 Flow

* [State Manager](managers/09-state-manager.md) selects eligible graph objects by domain and sequence per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).
* Envelopes are constructed per [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md).
* [Key Manager](managers/03-key-manager.md) signs the authenticated message header, including sender key id and ciphertext binding per [01-protocol/04-cryptography.md](../01-protocol/04-cryptography.md).
* [Network Manager](managers/10-network-manager.md) establishes or reuses a peer connection, including solving required client puzzles during admission per [01-protocol/09-dos-guard-and-client-puzzles.md](../01-protocol/09-dos-guard-and-client-puzzles.md).
* [Network Manager](managers/10-network-manager.md) resolves the recipient public key from the identity registry and encrypts the payload for the remote peer per [01-protocol/04-cryptography.md](../01-protocol/04-cryptography.md).
* [Network Manager](managers/10-network-manager.md) transmits the encrypted package over the established connection.

### 9.3 Allowed behavior

* Selective and incremental sync.
* Propagation of visibility suppression state via Ratings.

### 9.4 Forbidden behavior

* Sending uncommitted state.
* Sending data outside declared domains.

### 9.5 Failure behavior

* Transmission failure does not affect local state.
* Retry behavior is controlled exclusively by [State Manager](managers/09-state-manager.md).

## 10. Derived and cached data flow

### 10.1 Scope

Derived data includes in-memory indices, caches, and precomputed query results.

### 10.2 Allowed behavior

* Performance optimization only.
* Rebuild from authoritative graph state.

### 10.3 Forbidden behavior

* Treating derived data as authoritative.
* Persisting or syncing derived data.

### 10.4 Failure behavior

* Loss degrades performance only.
* Rebuild requires no network access.

## 11. Rejection propagation and observability

### 11.1 Guarantees

* All rejections propagate to the original caller.
* Remote rejections are reflected in peer sync state.
* Rejections are observable by [Log Manager](managers/12-log-manager.md) and audit systems.

### 11.2 Forbidden behavior

* Silent rejection without caller visibility.
* Partial acceptance of rejected operations.

## 12. Trust boundaries

The following trust boundaries are explicitly crossed as defined in [02-architecture/03-trust-boundaries.md](03-trust-boundaries.md):

* Frontend to backend API boundary.
* Backend to storage boundary.
* Backend to network boundary.
* Local node to remote peer boundary.

At each boundary:

* Identity is explicit.
* Authorization is enforced.
* Data is validated before acceptance.

## 13. Summary of guarantees

This data flow model guarantees:

* Deterministic and ordered state evolution.
* Enforced bootstrap and user provisioning semantics.
* Uniform authorization, domain, and schema enforcement.
* Visibility suppression without data loss.
* Authenticated before decrypt processing for all remote ingress payloads.
* Replay protection enforced by [State Manager](managers/09-state-manager.md) using ordering and peer sync state per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).
* Confidentiality and integrity for peer transport via encryption and signed authenticated headers per [01-protocol/04-cryptography.md](../01-protocol/04-cryptography.md).
* DoS containment on peer connections via [DoS Guard Manager](managers/14-dos-guard-manager.md) admission control with dynamic difficulty challenges per [01-protocol/09-dos-guard-and-client-puzzles.md](../01-protocol/09-dos-guard-and-client-puzzles.md).
* Derived and cached data is non-authoritative and cannot affect correctness when lost.
* Network retry decisions are owned by [State Manager](managers/09-state-manager.md) and driven by per-peer sync state per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).
* Predictable fail-closed behavior under error or load.
* No implicit or hidden data paths.
