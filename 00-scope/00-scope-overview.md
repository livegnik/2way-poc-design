



# 00 Scope Overview

Defines repository-wide invariants and trust boundaries for 2WAY implementations, specifies mandatory enforcement boundaries and sequencing and persistence constraints, and constrains handling of invalid input across all interaction surfaces.

For the meta specifications, see [00-scope-overview meta](../09-appendix/meta/00-scope/00-scope-overview-meta.md).

## 1. Global invariants and guarantees

### 1.1 Invariants across all interaction surfaces

Across all interaction surfaces, including local HTTP, WebSocket, backend extensions, and remote sync, the following invariants hold:

* Graph Manager is the only permitted write path for persistent state.
* Storage Manager is the only component permitted to issue raw database operations.
* All payloads are validated by Schema Manager prior to persistence.
* All authorization decisions are enforced by ACL Manager.
* All persistent writes receive a strictly monotonic `global_seq`.
* All sync state transitions are applied by State Manager.
* All state change notifications flow through Event Manager.
* All authentication and requester resolution are mediated by Auth Manager.
* All private keys are owned and accessed exclusively by Key Manager.
* All audit logging is mediated by Log Manager.
* All request-scoped work is bound to a complete [`OperationContext`](../02-architecture/services-and-apps/05-operation-context.md).
* Client-side signing does not bypass backend validation or authorization.

### 1.2 Process and persistence guarantees required by the PoC

The PoC design requires the following guarantees:

* The backend executes as a single long-running process hosting managers and services.
* SQLite is used with a single serialized writer path mediated by Graph Manager.
* Write serialization preserves strict monotonic sequencing and prevents write-write races.
* Rejected operations do not result in any persistent state change.

## 2. Trust boundaries and interaction constraints

This scope definition constrains interactions strictly in terms of inputs, outputs, and trust boundaries.

Normative trust boundaries for the PoC:

* Remote peers are untrusted. All inbound remote data is treated as adversarial until validated, authorized, and sequenced.
* Frontend applications are untrusted with respect to backend state mutation and interact only through defined APIs.
* Backend extension services are untrusted relative to core manager invariants and must not bypass validation, authorization, or sequencing.
* Debug and inspection interfaces are administrative, read-only, and subject to explicit authorization.

## 3. Failure, rejection, and invalid input handling

This repository requires deterministic rejection behavior for invalid or unauthorized input.

Scope level requirements:

* Invalid structure, invalid schema meaning, or unauthorized actions are rejected before any persistent write occurs.
* Rejection produces no persistent state changes.
* Rejection does not allocate or advance `global_seq`.
* Rejection does not emit state-changing events.
* Remote sync inputs that are malformed, replayed, unauthorized, or inconsistent with expected sync state are rejected without altering local state.

Error representation and transport specific signaling are defined elsewhere. This document constrains effects only.
