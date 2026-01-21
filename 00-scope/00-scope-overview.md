



# 00. Scope Overview

## 1. Purpose and scope

This document defines the scope boundary, document authority, and cross-document invariants for the 2WAY system design repository. It establishes what this repository specifies, what it explicitly excludes, and how the contained documents are to be interpreted and reviewed. This document does not define protocol wire formats, storage schemas, or component-level behavior beyond global constraints and invariants; those details live in [01-protocol](../01-protocol/), [02-architecture](../02-architecture/), and [03-data](../03-data/). Terminology is defined in [03-definitions-and-terminology.md](03-definitions-and-terminology.md).

This document is normative for determining whether a concern, requirement, or design decision belongs in this repository.

## 2. Responsibilities

This specification is responsible for:

* Defining the scope and authority of the 2WAY design repository.
* Defining global invariants that apply across protocol, architecture, data, and security specifications.
* Defining mandatory enforcement boundaries between components, including write paths and trust boundaries.
* Defining repository-wide guarantees related to sequencing, validation, authorization, and persistence effects.
* Defining deterministic rejection and failure handling requirements at the scope level.
* Defining how conflicts between documents in this repository are identified and resolved.

This specification is not responsible for:

* Defining protocol wire formats, envelopes, or serialization rules.
* Defining detailed component behavior, manager APIs, or service logic.
* Defining schema meaning, type validation, or value interpretation.
* Defining authorization rules or ACL evaluation logic.
* Defining persistence schemas, indexes, migrations, or query behavior.
* Defining sync ordering, conflict resolution algorithms, or domain selection rules.
* Defining user interface behavior or frontend interaction design.

## 3. Document authority and consistency

This repository is internally authoritative. All documents contained within it are expected to be mutually consistent and collectively sufficient to implement and review the PoC.

Consistency requirements:

* Apparent conflicts between documents are treated as correctness failures until resolved.
* More specific documents override more general documents, unless doing so violates invariants defined in this file.
* No document may introduce behavior that weakens or bypasses the invariants defined here.

## 4. Global invariants and guarantees

### 4.1 Invariants across all interaction surfaces

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

### 4.2 Process and persistence guarantees required by the PoC

The PoC design requires the following guarantees:

* The backend executes as a single long-running process hosting managers and services.
* SQLite is used with a single serialized writer path mediated by Graph Manager.
* Write serialization preserves strict monotonic sequencing and prevents write-write races.
* Rejected operations do not result in any persistent state change.

These guarantees are mandatory for correctness and must not be weakened by implementation choices.

## 5. Allowed behaviors

The design documents in this repository may:

* Define normative constraints that restrict component behavior.
* Specify validation, authorization, and sequencing rules as correctness requirements.
* Define failure and rejection behavior where it materially affects correctness or security.
* Define the PoC inclusion boundary and acceptance definition.
* Reference other documents in this repository as authoritative sources.

## 6. Forbidden behaviors

The design documents in this repository must not:

* Define any alternate write path that bypasses Graph Manager.
* Define any direct database write access outside Storage Manager and Graph Manager.
* Define permission checks outside ACL Manager as a substitute for ACL enforcement.
* Rely on implicit trust derived from transport properties, network location, or UI context.
* Introduce protocol or security behavior that materially changes correctness or security without full specification.

## 7. Trust boundaries and interaction constraints

This scope definition constrains interactions strictly in terms of inputs, outputs, and trust boundaries.

Normative trust boundaries for the PoC:

* Remote peers are untrusted. All inbound remote data is treated as adversarial until validated, authorized, and sequenced.
* Frontend applications are untrusted with respect to backend state mutation and interact only through defined APIs.
* Backend extension services are untrusted relative to core manager invariants and must not bypass validation, authorization, or sequencing.
* Debug and inspection interfaces are administrative, read-only, and subject to explicit authorization.

## 8. Failure, rejection, and invalid input handling

This repository requires deterministic rejection behavior for invalid or unauthorized input.

Scope level requirements:

* Invalid structure, invalid schema meaning, or unauthorized actions are rejected before any persistent write occurs.
* Rejection produces no persistent state changes.
* Rejection does not allocate or advance `global_seq`.
* Rejection does not emit state-changing events.
* Remote sync inputs that are malformed, replayed, unauthorized, or inconsistent with expected sync state are rejected without altering local state.

Error representation and transport specific signaling are defined elsewhere. This document constrains effects only.

## 9. Relationship to other scope documents

This file defines repository level scope and invariants.

Other scope documents define details:

* `01-scope-and-goals.md` defines PoC goals and deliverables.
* `02-non-goals-and-out-of-scope.md` defines explicit exclusions.
* `03-definitions-and-terminology.md` defines normative terminology.
* `04-assumptions-and-constraints.md` defines environmental assumptions and hard constraints.

If a more specific scope document conflicts with this file, the conflict must be resolved by aligning with the invariants defined here.
