



# 06 Access Control Model

## 1. Purpose and scope

This document defines the access control model of the 2WAY protocol as implemented in the PoC. It specifies how authorization decisions are derived and enforced for graph operations. It covers permission evaluation semantics only. Authentication, identity construction, schema definition, sync behavior, and storage mechanics are defined elsewhere and are referenced but not restated.

This document is normative for the PoC.

## 2. Responsibilities

The access control model is responsible for:

- Determining whether an authenticated identity is permitted to perform a specific operation on a specific graph object.
- Enforcing ownership and explicit permission boundaries.
- Enforcing app and domain isolation during read and write operations.
- Producing a deterministic allow or reject decision for each operation.

The access control model is not responsible for identity verification, signature validation, schema validation, sync conflict resolution, or persistence.

## 3. Invariants and guarantees

The following invariants are enforced:

- No graph write operation may succeed without passing access control evaluation.
- Authorization decisions are based solely on local state and declared rules.
- Authorization evaluation has no side effects.
- Authorization is evaluated per operation and is not cached across operations.

The following guarantees are provided:

- Unauthorized graph mutations are rejected before persistence.
- Operations cannot bypass access control by using alternative execution paths.
- Authorization behavior is deterministic for a given graph state and operation.

## 4. Authorization inputs

Authorization evaluation operates on the following inputs:

- Authenticated identity identifier.
- Operation type, including create, update, or delete.
- Target object identifiers and object types.
- App identifier and domain identifier associated with the operation.
- Local graph state required to evaluate ownership and ACLs.
- Applicable schema rules.

No implicit context, network metadata, or transport level attributes are used.

## 5. Authorization evaluation model

Authorization is evaluated as a strict gating step after structural and schema validation and before any persistence.

Failure at this stage results in immediate rejection.

### 5.1 Ownership rules

Ownership is derived from Parent authorship.

Rules:

- The identity that creates a Parent is its permanent owner.
- Ownership of a Parent and its owned objects cannot be reassigned.
- Only the owning identity may mutate owned objects unless explicitly permitted by an ACL.

Operations that attempt to mutate objects owned by another identity without permission are rejected.

### 5.2 Schema enforced access constraints

Schemas define baseline access constraints.

Rules:

- Schemas may restrict which identities may create objects of a given type.
- Schemas may declare object types as immutable or append only.
- Schema constraints cannot be overridden by ACLs.

Schema violations result in rejection prior to ACL evaluation.

### 5.3 App and domain isolation

Access control enforces isolation between apps and domains.

Rules:

- Operations are authorized only within the app and domain in which they are defined.
- Objects from different apps are not writable across app boundaries.
- Cross app access is permitted only where explicitly allowed by schema.

Operations that cross app or domain boundaries without explicit allowance are rejected.

### 5.4 Object level ACLs

ACLs provide explicit permission grants.

Rules:

- ACLs are graph objects associated with specific targets.
- ACLs may grant read or write permissions to specific identities.
- ACLs cannot grant permissions that violate schema constraints or ownership invariants.

Absence of an ACL implies denial unless ownership or schema rules permit the operation.

## 6. Allowed behaviors

The following behaviors are allowed when all authorization checks pass:

- Creation of objects by an identity within its permitted scope.
- Mutation of owned objects when schema permits mutation.
- Access to non owned objects when explicitly permitted by ACLs.

All other behaviors are disallowed.

## 7. Forbidden behaviors

The following behaviors are explicitly forbidden:

- Mutating objects owned by another identity without explicit permission.
- Overriding schema constraints using ACLs.
- Writing objects outside the declared app or domain.
- Deriving authorization from transport, peer identity, or network context.
- Partial authorization. Operations are either fully authorized or rejected.

## 8. Interaction with other components

The access control model interacts with other components as follows:

- Input is received from the validation pipeline after authentication and schema validation.
- Output is a binary authorization decision.
- No direct access to storage or network layers exists.

Trust boundaries:

- All inputs are treated as untrusted until validated.
- Only local graph state and schema definitions are trusted for authorization decisions.

## 9. Failure and rejection behavior

On authorization failure:

- The operation is rejected.
- No state is mutated.
- No partial effects occur.
- A deterministic rejection result is returned.

Authorization failures do not alter system state.

## 10. Non responsibilities

The access control model does not:

- Authenticate identities or verify cryptographic signatures.
- Validate object structure or schema correctness.
- Resolve sync conflicts or ordering.
- Enforce rate limits or denial of service protections.
- Persist audit logs beyond signaling rejection.

These concerns are addressed by other components.

## 11. Security properties

The access control model enforces:

- Explicit permission boundaries.
- Least privilege by default.
- Deterministic authorization.
- Structural resistance to privilege escalation.

No heuristic or probabilistic mechanisms are used.
