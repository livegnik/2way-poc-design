


# 04 Auth Manager

## 1. Purpose and scope

The Auth Manager is the local authentication authority for the 2WAY backend. It resolves frontend-originated HTTP and WebSocket requests into authenticated backend identities and produces the identity-binding inputs required to construct a valid `OperationContext`.

Its scope ends at the local entrypoints. It never authenticates remote peers, handles sync provenance, or performs cryptographic verification of envelopes, and it never overlaps with authorization, graph mutation, or session lifecycle management. Those responsibilities belong to other managers.

This specification consumes the protocol contracts defined in:
* `01-protocol/00-protocol-overview.md`
* `01-protocol/02-object-model.md`
* `01-protocol/03-serialization-and-envelopes.md`
* `01-protocol/05-keys-and-identity.md`
* `01-protocol/06-access-control-model.md`
* `01-protocol/07-sync-and-consistency.md`
* `01-protocol/08-network-transport-requirements.md`
* `01-protocol/09-errors-and-failure-modes.md`

Those files remain normative for all behaviors described here.

## 2. Responsibilities and boundaries

This specification is responsible for the following

* Resolving a local frontend session token into a backend `requester_identity_id`, in alignment with the `OperationContext` construction workflow in `01-protocol/00-protocol-overview.md`.
* Producing an explicit authentication outcome for every local request so downstream managers can enforce the sequencing defined in `01-protocol/06-access-control-model.md`.
* Enforcing authentication before any backend manager or service is invoked so that authorization obeys the ordering defined in `01-protocol/06-access-control-model.md`.
* Supporting route-level admin gating based on trusted local configuration or identity metadata without bypassing the app and domain rules in `01-protocol/01-identifiers-and-namespaces.md`.
* Binding authentication results into `OperationContext` inputs in a deterministic and immutable manner so envelope submission behaves exactly as described in `01-protocol/03-serialization-and-envelopes.md`.
* Providing authenticated identity resolution for both HTTP and WebSocket entrypoints.
* Rejecting unauthenticated or malformed requests with explicit failure classification that maps to `01-protocol/09-errors-and-failure-modes.md`.
* Emitting authentication and admin-gating audit signals via Log Manager so that authentication-stage failures propagate into the observability posture described in `01-protocol/09-errors-and-failure-modes.md`.
* Operating as a strict trust boundary between untrusted frontend input and trusted backend execution, keeping remote identity handling with Network Manager per `01-protocol/08-network-transport-requirements.md`.

This specification does not cover the following

* Authorization or permission evaluation. Owned by ACL Manager per `01-protocol/06-access-control-model.md`.
* Graph mutation or schema validation. Owned by Graph Manager and Schema Manager per `01-protocol/02-object-model.md` and `01-protocol/03-serialization-and-envelopes.md`.
* Session creation, refresh, rotation, or revocation. Owned by the frontend application and outside the protocol scope.
* Password handling, credential verification, or user onboarding. Owned by the frontend.
* Cryptographic signing, verification, or key access. Owned by Key Manager and Network Manager per `01-protocol/04-cryptography.md` and `01-protocol/05-keys-and-identity.md`.
* Remote peer authentication, handshake validation, or sync provenance. Owned by Network Manager and State Manager per `01-protocol/08-network-transport-requirements.md` and `01-protocol/07-sync-and-consistency.md`.
* Rate limiting, client puzzles, or abuse mitigation. Owned by DoS Guard and the interface layer.

## 3. Invariants and guarantees

Across all relevant components and execution contexts defined in this file, the following invariants hold:

* Authentication is strictly separated from authorization in accordance with `01-protocol/06-access-control-model.md`.
* Authentication never implies permission, visibility, or ownership.
* Auth Manager never mutates backend graph state.
* Auth Manager never accesses private keys or performs cryptographic operations, keeping cryptographic enforcement with the actors defined in `01-protocol/04-cryptography.md`.
* Auth Manager never trusts client-supplied identity claims, consistent with the prohibition on inferred identity in `01-protocol/05-keys-and-identity.md`.
* Every request produces exactly one explicit authentication outcome.
* Authentication results are deterministic given identical session store state.
* `OperationContext.requester_identity_id` is bound exclusively by Auth Manager so that the HTTP layer can provide the context described in `01-protocol/00-protocol-overview.md`.
* Envelope-declared authorship is never overridden or inferred by Auth Manager, matching the authorship guarantees in `01-protocol/05-keys-and-identity.md`.
* All guarantees hold regardless of caller, execution context, or input source.

## 4. Authentication lifecycle and execution phases

Auth Manager operates as a pure execution engine with explicit phases. These phases are derived from legacy architecture flows and remain valid.

### 4.1 Phase 1, Input acquisition

* Receive raw request metadata from HTTP or WebSocket layer.
* Extract session token from header or cookie.
* Receive trusted route classification and app context from the interface layer.
* Treat all extracted data as untrusted input.

### 4.2 Phase 2, Token validation

* Validate token presence.
* Validate token format.
* Validate token existence in frontend session store.
* Validate token expiry.
* Resolve linked frontend user record.
* Resolve linked backend identity.

Any failure terminates execution and produces a rejected authentication result.

### 4.3 Phase 3, Admin gating evaluation

* Executed only after successful authentication.
* Apply admin-only route constraints if applicable.
* Determine admin eligibility from trusted local configuration or identity metadata.
* Failure produces a rejected authentication result.

### 4.4 Phase 4, Authentication result emission

* Produce a complete authentication result.
* Bind identity and flags for `OperationContext` construction.
* Emit audit signals where required.
* Return control to interface layer.

## 5. Authentication inputs and outputs

### 5.1 Inputs

#### HTTP entrypoints

* Session token from header or cookie.
* Trusted route classification.
* App context resolved by routing layer.

#### WebSocket entrypoints

* Session token supplied during connection establishment.

All inputs are untrusted.

### 5.2 Outputs

Auth Manager produces an authentication result containing:

* `requester_identity_id`, integer or null.
* Authentication state, authenticated, unauthenticated, or rejected.
* Admin eligibility flag.
* Rejection category.

### 5.3 OperationContext construction requirements

The interface layer MUST construct an `OperationContext` only after Auth Manager success, matching the lifecycle defined in `01-protocol/00-protocol-overview.md`.

Requirements:

* `requester_identity_id` set exactly as produced by Auth Manager.
* `app_id` supplied from trusted routing logic.
* `is_remote` set to false, reflecting the local submission posture in `01-protocol/00-protocol-overview.md`.
* `trace_id` generated by the interface layer.
* Remote-only fields unset.
* Context treated as immutable after construction.

Requests lacking sufficient metadata to build a valid `OperationContext` are rejected so that downstream validation may apply the ordering defined in `01-protocol/06-access-control-model.md`.

## 6. Session token model

### 6.1 Authority and ownership

* Frontend database is the sole session authority for local requests referenced in `01-protocol/00-protocol-overview.md`.
* Each token maps to exactly one session record.
* Each session maps to exactly one frontend user.
* Each frontend user maps to exactly one backend identity.

Auth Manager does not cache session resolutions.

### 6.2 Validation requirements

For authenticated endpoints, Auth Manager validates:

* Token presence.
* Token format.
* Token existence.
* Token expiry.
* User record integrity.
* Backend identity existence.

Failure of any check results in rejection.

### 6.3 Unauthenticated access

* Public endpoints may proceed with `requester_identity_id = null`.
* All other endpoints require authentication.
* Public access is explicit, never inferred.

## 7. Admin gating

### 7.1 Semantics

* Admin gating is evaluated after authentication.
* Admin eligibility is required only for explicitly marked routes.

### 7.2 Constraints

* Admin status does not bypass ACL evaluation per `01-protocol/06-access-control-model.md`.
* Admin status does not grant implicit permissions.
* Admin gating applies only to route-level constraints.

## 8. Interaction with other components

### 8.1 HTTP layer

Inputs:

* Session token.
* Route classification.
* App context.

Outputs:

* Authentication result for `OperationContext`.

Trust boundary:

* HTTP layer supplies metadata but never identity assertions, consistent with `01-protocol/05-keys-and-identity.md`.

### 8.2 WebSocket layer

* Authentication occurs at connection establishment.
* Unauthenticated connections are rejected.
* Rejected connections receive no events.

### 8.3 Storage access

* Auth Manager reads frontend session and user records through approved interfaces.
* Auth Manager never accesses backend graph tables or raw SQLite connections.

### 8.4 Downstream managers

* Identity binding flows only through `OperationContext`.
* Graph Manager enforces authorship and ownership independently per `01-protocol/05-keys-and-identity.md`.
* ACL Manager performs all authorization checks regardless of authentication outcome per `01-protocol/06-access-control-model.md`.

## 9. Failure handling and rejection behavior

### 9.1 Failure posture

* Fail closed.
* Reject on ambiguity, inconsistency, or unavailability, following the posture in `01-protocol/09-errors-and-failure-modes.md`.

### 9.2 Rejection categories

At minimum:

* Missing token.
* Malformed token.
* Unknown token.
* Expired token.
* Session store unavailable.
* User record missing.
* Backend identity missing.
* Admin gating failure.

These categories map to the canonical classification ordering in `01-protocol/09-errors-and-failure-modes.md`.

### 9.3 Session store unavailability

* All authenticated endpoints rejected.
* Admin endpoints always rejected.
* Public endpoints proceed only if explicitly allowed.

### 9.4 Abuse posture

* Authentication failures may be logged with aggregation.
* No rate limiting or puzzles implemented here.
* Abuse mitigation owned elsewhere.

## 10. Security constraints specific to Auth Manager

### 10.1 Identity isolation

* Client-supplied identity claims are ignored, reflecting the prohibition on inferred identity in `01-protocol/05-keys-and-identity.md`.
* Session linkage is the only authoritative identity source for local submissions as described in `01-protocol/00-protocol-overview.md`.

### 10.2 Privilege containment

* Authentication does not imply authorization per `01-protocol/06-access-control-model.md`.
* App identity and user identity remain distinct inputs.

### 10.3 Auditability

* Authentication and admin gating failures are observable via Log Manager.
* Auth Manager does not emit graph objects.

### 10.4 Local-only scope

* Auth Manager never processes remote traffic.
* Remote identities are introduced exclusively by Network Manager and State Manager per `01-protocol/08-network-transport-requirements.md`.
