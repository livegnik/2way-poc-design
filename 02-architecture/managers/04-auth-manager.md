



# 04 Auth Manager

## 1. Purpose and scope

1.1 This document defines the Auth Manager component of the 2WAY backend.

1.2 The Auth Manager is responsible for resolving local frontend-originated requests into authenticated backend identities and producing the identity-related fields required to construct an `OperationContext`.

1.3 This file covers only local authentication for HTTP and WebSocket entrypoints. Remote peer authentication, signature verification, and sync provenance are explicitly out of scope and owned by Network Manager and State Manager.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Resolving a local frontend session token into a backend `requester_identity_id`, or an explicit unauthenticated state.
* Validating session token presence, uniqueness, expiry, and linkage to a frontend user record.
* Enforcing that authentication is performed before any backend manager or service is invoked.
* Supporting explicit admin-only endpoint gating based on trusted local configuration or identity metadata.
* Providing deterministic authentication outcomes for HTTP and WebSocket entrypoints.
* Emitting authentication-related audit signals through Log Manager where required by system policy.

This specification does not cover the following:

* Authorization or permission evaluation for graph reads or writes. Owned by ACL Manager.
* Creation, refresh, rotation, or revocation of frontend sessions. Owned by the frontend web application.
* Password handling, credential verification, or user onboarding flows. Owned by the frontend.
* Graph mutation, schema validation, or envelope handling. Owned by Graph Manager and Schema Manager.
* Remote peer authentication, envelope signature validation, or sync trust decisions. Owned by Network Manager and State Manager.
* Key generation, key storage, or cryptographic operations. Owned by Key Manager.

## 3. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* Authentication is strictly separated from authorization. A successful authentication result never implies permission.
* Auth Manager never mutates backend graph state.
* Auth Manager never accesses private keys or performs cryptographic verification.
* Auth Manager never infers identity from client-supplied identity claims.
* Auth Manager produces an explicit authenticated or unauthenticated result for every request.
* Authentication results are deterministic given the same session store state and input.
* Auth Manager binds only the `OperationContext.requester_identity_id` and leaves envelope-declared `owner_identity` metadata untouched so Graph Manager can enforce the explicit authorship requirements defined by the protocol serialization and identity specifications.
* These guarantees hold regardless of caller, execution context, input source, or peer behavior.

## 4. Authentication inputs and outputs

### 4.1 Inputs

* Local HTTP request metadata.

  * Session token supplied via header or cookie, as defined by the local interface specification.
  * Route classification indicating whether authentication is required and whether admin gating applies.
  * App context resolved by the HTTP routing layer.
* Local WebSocket connection metadata.

  * Session token supplied during connection establishment.

All inputs are treated as untrusted.

### 4.2 Outputs

* An authentication result used by the HTTP or WebSocket layer to construct an `OperationContext`, containing:

* `requester_identity_id` as an integer, or null if unauthenticated.
* Authentication state classification, authenticated, unauthenticated, or rejected.
* Admin eligibility flag for admin-gated endpoints.
* A rejection category suitable for mapping to the interface error model and audit logging.

### 4.3 OperationContext construction requirements

Per the protocol overview, once authentication succeeds the HTTP or WebSocket layer MUST construct an `OperationContext` that:

* Includes `requester_identity_id`, `app_id`, `is_remote=False`, and `trace_id` before invoking any manager or service.
* Uses trusted route classification and service binding to supply `app_id` and domain scope instead of copying client supplied identifiers.
* Leaves remote-only fields such as `remote_node_identity_id` unset; these are populated exclusively by State Manager for peer-originated sync packages.
* Remains immutable once constructed so ACL Manager and Graph Manager evaluate the same identity binding that Auth Manager produced.

Auth Manager enforces that these inputs are present for local entrypoints; requests lacking the metadata required for a complete `OperationContext` are rejected pre-validation.

## 5. Session token model

### 5.1 Session store authority

* The frontend database is the sole authority for session tokens.
* Each session token must map to exactly one frontend session record.
* Each session record must map to exactly one frontend user record.
* Each frontend user record must map to exactly one backend `identity_id`.

Auth Manager relies exclusively on this mapping and does not persist or cache identity resolution across requests.

This reflects the PoC design separation between `frontend.db` and `backend.db`. 

### 5.2 Validation requirements

For endpoints that require authentication, Auth Manager must validate:

* Token presence.
* Token format constraints as defined by the interface layer.
* Token existence in the frontend session store.
* Token expiry.
* Existence and integrity of the linked frontend user record.
* Existence of the referenced backend identity.

Failure of any check results in rejection.

### 5.3 Unauthenticated access

* Endpoints explicitly marked as public by the interface layer may proceed with `requester_identity_id` set to null.
* All other endpoints require a successfully authenticated identity.
* Auth Manager does not infer public access. It relies on explicit route classification.

## 6. Admin gating

### 6.1 Admin gating semantics

* Admin gating is a route-level constraint.
* Admin eligibility is determined from trusted local configuration or trusted identity metadata.
* Admin gating is evaluated only after successful authentication.

### 6.2 Constraints

* Admin gating is not a general authorization mechanism.
* Admin status does not bypass ACL evaluation.
* Admin gating applies only to endpoints explicitly marked as admin-only.

## 7. Interaction with other components

### 7.1 HTTP layer

Inputs received:

* Session token.
* Route classification.
* App context.

Outputs provided:

* Authentication result used to populate `OperationContext`.

Trust boundary:

* The HTTP layer is trusted only to classify routes and supply raw request metadata. It is not trusted for identity assertions.

### 7.2 WebSocket layer

* WebSocket connections must be authenticated at connection establishment.
* Auth Manager provides identity resolution before the connection is registered.
* Unauthenticated or rejected connections must not receive events.

### 7.3 Storage and session access

* Auth Manager reads session and user records through an approved frontend storage interface.
* Auth Manager does not access backend graph tables or raw SQLite connections.

### 7.4 Downstream managers and services

* Downstream components receive identity information exclusively via `OperationContext`.
* Graph Manager enforces that each operation's explicit `owner_identity` matches the authenticated requester described by `OperationContext`, so envelopes or transport metadata cannot override protocol-mandated authorship semantics.
* All permission checks remain mandatory regardless of authentication outcome.

## 8. Failure handling and rejection behavior

### 8.1 Failure posture

* Fail closed.
* Reject on ambiguity, inconsistency, or store unavailability.

### 8.2 Rejection categories

Auth Manager must distinguish, at minimum:

* Missing token.
* Malformed token.
* Unknown token.
* Expired token.
* Session store unavailable.
* User record missing or inconsistent.
* Backend identity missing.
* Admin gating failure.

These categories are used for audit and diagnostics. The interface layer may map them to a uniform unauthorized response.

### 8.3 Session store unavailability

* If the session store cannot be queried, all authenticated endpoints are rejected.
* Admin endpoints are always rejected in this state.
* Public endpoints may proceed only if explicitly allowed by the interface specification.

### 8.4 Abuse posture

* Repeated authentication failures may be logged with aggregation to avoid amplification.
* Auth Manager does not implement rate limiting or client puzzles.
* Load and abuse mitigation are owned by DoS Guard and the interface layer.

## 9. Security constraints specific to Auth Manager

### 9.1 Identity isolation

* Auth Manager must never accept client-provided identity identifiers, public keys, or app identifiers as authoritative.
* Only the session store linkage is authoritative for identity resolution.

### 9.2 Privilege containment

* Authentication does not imply ownership, visibility, or write access.
* App identity, user identity, and admin status remain orthogonal inputs to ACL evaluation.

### 9.3 Auditability

* Authentication failures and admin gating failures must be observable through Log Manager.
* Auth Manager must not emit graph objects or write audit data into the graph.

### 9.4 Local-only scope

* Auth Manager must never process remote sync traffic or peer-originated envelopes.
* Remote identities are introduced exclusively through Network Manager and State Manager.
