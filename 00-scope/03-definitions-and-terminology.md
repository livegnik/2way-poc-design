



# 03. Definitions and terminology

## 1. Purpose and scope

This document defines the normative terminology used across the 2WAY design repository. Its purpose is to establish precise meanings for core terms to ensure consistent interpretation across protocol, architecture, security, data, and interface specifications.

This document does not define behavior, algorithms, or implementation details. It defines vocabulary, scope boundaries, and semantic invariants only.

All terms defined here are binding for the entire repository unless explicitly overridden in a narrower scope document.

## 2. Responsibilities

This document is responsible for:

- Defining canonical meanings of core system terms.
- Disambiguating overloaded or commonly misused terms.
- Establishing invariant properties attached to terms.
- Providing a shared vocabulary across all design documents.

This document is not responsible for:

- Describing implementation details.
- Specifying protocol flows.
- Defining APIs, schemas, or wire formats.
- Explaining rationale or historical context.

## 3. Invariants and guarantees

- Terms defined in this document have a single authoritative meaning.
- Identical terms must not be used with different meanings elsewhere in the repository.
- Undefined terms must be introduced and defined in the document where they first appear.
- Terminology does not imply implementation strategy unless explicitly stated.

## 4. Core system terms

### 4.1 Node

A node is a single autonomous execution environment that hosts a complete 2WAY backend instance.

Properties:
- Maintains its own local persistent graph.
- Enforces validation, authorization, and storage rules independently.
- May participate in network sync with other nodes.
- Is authoritative over its local state.

A node is not a cluster, shard, or replicated service.

### 4.2 Identity

An identity is a graph-level representation of an actor capable of authoring operations.

Properties:
- Represented as a Parent object in app_0.
- Anchored by at least one cryptographic public key.
- Immutable in authorship and ownership.
- May represent a user, device, service, or system component.

An identity is not inferred from network location, session state, or runtime context.

### 4.3 Device

A device is a scoped identity associated with a primary identity.

Properties:
- Possesses its own cryptographic keypair.
- Linked to a primary identity via typed edges.
- Carries explicitly limited authority.
- Can be independently revoked.

A device is not required to be a physical device.

### 4.4 App

An app is a logically isolated domain that defines its own schema, object types, and semantics.

Properties:
- Owns its own namespace of object types.
- May define app-specific Parents, Attributes, Edges, and Ratings.
- Cannot reinterpret or mutate objects owned by another app.
- Is enforced through schema and ACL boundaries.

An app is not equivalent to a frontend UI or executable package.

### 4.5 Service

A service is a backend-resident component that operates within a defined app or system domain.

Properties:
- Executes with explicit manager access.
- Cannot bypass Graph Manager or ACL Manager.
- May define background behavior or derived state.
- Is bound to the schema of its owning domain.

A service is not trusted implicitly beyond its declared scope.

### 4.6 Frontend app

A frontend app is a user-facing application that interacts with the backend exclusively through exposed interfaces.

Properties:
- Cannot directly access backend managers.
- Operates within an explicit OperationContext.
- Is subject to ACL and schema enforcement.

A frontend app is not a security boundary.

## 5. Graph model terms

### 5.1 Graph

The graph is the complete set of persisted objects stored by a node.

Properties:
- Append-oriented with immutable ownership.
- Ordered by a global sequence.
- Typed and schema-constrained.
- Locally authoritative.

The graph is not globally shared or centrally replicated.

### 5.2 Parent

A Parent is a top-level graph object that establishes ownership and identity context.

Properties:
- Created by exactly one identity.
- Immutable in authorship.
- Serves as the anchor for related objects.
- Cannot be reassigned or overwritten.

A Parent is not a container or namespace.

### 5.3 Attribute

An Attribute is a typed value attached to a Parent.

Properties:
- Owned by the Parent’s identity.
- Schema-defined in type and representation.
- Subject to ACL enforcement.
- May be mutable or append-only depending on domain rules.

### 5.4 Edge

An Edge is a typed relationship between two Parents.

Properties:
- Directional.
- Schema-constrained.
- May encode trust, membership, delegation, or association.
- Evaluated during ACL and traversal operations.

Edges do not imply transitive permission unless explicitly defined.

### 5.5 Rating

A Rating is a typed evaluative object scoped to an app-defined meaning.

Properties:
- Interpreted only by the owning app.
- Has no global semantic meaning.
- May influence app-level behavior only.

Ratings are not global reputation signals.

## 6. Operation and envelope terms

### 6.1 Operation

An operation is a request to create, modify, or relate graph objects.

Properties:
- Authored by exactly one identity.
- Subject to validation, schema checks, and ACL enforcement.
- Atomic with respect to graph mutation.

Operations do not imply successful persistence.

### 6.2 Envelope

An envelope is the signed, transportable representation of one or more operations.

Properties:
- Carries author identity.
- Cryptographically signed.
- May be encrypted.
- Verified independently of transport.

An envelope is not trusted until fully validated.

### 6.3 OperationContext

An OperationContext is the execution context derived from an envelope.

Properties:
- Binds identity, device, app, and permissions.
- Is explicitly constructed.
- Is not inferred from runtime state.

OperationContext is mandatory for all graph mutations.

## 7. Sequence and sync terms

### 7.1 global_seq

global_seq is a strictly monotonic sequence number assigned by a node.

Properties:
- Defines total ordering of local operations.
- Cannot be rewritten or reused.
- Anchors provenance and replay detection.

global_seq is node-local.

### 7.2 Sync domain

A sync domain is a defined subset of the graph eligible for replication.

Properties:
- Explicitly declared.
- ACL-constrained.
- App-scoped or system-scoped.
- Selectively shared.

Sync domains do not imply full graph visibility.

### 7.3 Peer

A peer is a remote node participating in sync.

Properties:
- Identified by a graph identity.
- Not inherently trusted.
- Subject to rate limits and ACL rules.

Peers are not assumed to be honest.

## 8. Security and trust terms

### 8.1 Trust boundary

A trust boundary is a point where assumptions about correctness or authority change.

Defined trust boundaries include:
- Frontend to backend.
- Backend to network.
- App to system services.
- Local node to peer node.

No implicit trust crosses a boundary.

### 8.2 Revocation

Revocation is the invalidation of a previously valid key or authority.

Properties:
- Represented as immutable graph structure.
- Takes precedence over subsequent operations.
- Propagated through sync.

Revocation does not rewrite history.

## 9. Allowed and forbidden usage

Allowed:
- Reuse of defined terms with identical meaning across documents.
- Narrowing of terms within a clearly defined local scope.

Forbidden:
- Redefinition of terms without explicit reference.
- Overloading terms with multiple meanings.
- Using informal synonyms for defined terms in normative text.

## 10. Failure and invalid usage handling

- Undefined or ambiguous terminology is treated as a specification error.
- Conflicting definitions invalidate the affected document section.
- Implementations encountering undefined terms must reject dependent behavior until clarified.

This document defines language. It does not define recovery behavior beyond specification consistency.
