



# 06 Access Control Model

## 1. Purpose and scope

This document defines the access control model of the 2WAY protocol as implemented in the PoC. It specifies how permissions are expressed, evaluated, and enforced at the protocol level. It covers authorization semantics only. Authentication, identity representation, cryptographic verification, schema definition, sync behavior, and storage mechanics are defined elsewhere and are referenced but not restated.

This document is normative for the PoC.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

- Determining whether an authenticated identity is permitted to perform a specific operation on a specific graph object.
- Enforcing ownership, schema rules, and explicit access control constraints.
- Enforcing app and domain isolation during graph mutations and reads.
- Producing deterministic authorization decisions based solely on local state.

This specification does not cover the following:

- Authenticate identities or verify cryptographic signatures.
- Perform schema compilation or migration.
- Resolve conflicts during sync.
- Enforce rate limits or denial of service protections.
- Persist audit logs beyond standard error reporting.

These concerns are defined in other documents.

## 3. Invariants and guarantees

The access control model enforces the following invariants:

- No operation may mutate graph state unless explicitly authorized.
- Authorization decisions are derived solely from local graph state and compiled schemas.
- Authorization evaluation has no side effects.
- Authorization is evaluated before any persistent write occurs.

The following guarantees are provided:

- Unauthorized operations are rejected before reaching storage.
- Schema defined prohibitions cannot be overridden by object level access rules.
- App and domain boundaries are strictly enforced.

## 4. Access control inputs

Authorization evaluation operates on the following inputs:

- Authenticated identity identifier.
- Device or delegated key identifier, if present in the OperationContext.
- Operation type, including create, update, or read.
- Target object identifiers and object types.
- App identifier and domain identifier.
- Local graph state, including Parents, Attributes, Edges, Ratings, and ACL objects.
- Compiled schema definitions applicable to the operation.

No implicit context, network metadata, or transport level information is used.

## 5. Authorization layers

Authorization is evaluated as a strict sequence of checks. Failure at any step results in rejection.

### 5.1 Ownership rules

Ownership is derived from Parent authorship.

Rules:

- The creator of a Parent is its permanent owner.
- Owned objects cannot be reassigned to another owner.
- Only the owner may mutate owned objects unless an explicit ACL permits otherwise.
- Remote operations attempting to mutate objects owned by another identity are rejected.

### 5.2 Schema level permissions

Schemas define default access semantics for object types.

Rules:

- Each object type declares whether it is mutable, append only, or immutable.
- Each object type declares which identities may create instances of that type.
- Allowed relations between object types are fixed by schema.
- Cross app object access is forbidden unless explicitly permitted by schema.

Schema validation occurs before ACL evaluation.

### 5.3 App and domain boundaries

Apps and domains define isolation scopes.

Rules:

- Operations are evaluated only within the app and domain they target.
- Objects from other apps are not visible unless schema rules explicitly allow it.
- Domains may restrict mutation and visibility, including participation in sync.

Operations that cross app or domain boundaries without explicit authorization are rejected.

### 5.4 Object level ACLs

ACLs provide explicit permission rules bound to specific objects or object sets.

Rules:

- ACLs are graph objects evaluated as part of authorization.
- ACLs may grant or deny read or write permissions.
- ACLs cannot override schema level prohibitions.
- Explicit deny rules take precedence over grant rules.

### 5.5 Graph derived constraints

Authorization may depend on graph structure when explicitly defined by schema.

Rules:

- Membership edges may gate access to group scoped objects.
- Degrees of separation may restrict visibility or interaction.
- Rating or trust based thresholds may gate participation.

All such constraints must be explicitly declared by schema and evaluated deterministically.

## 6. Allowed behaviors

The following behaviors are allowed when all authorization layers succeed:

- Creation of new objects within the identity’s authorized scope.
- Mutation of owned objects when schema and ACL rules permit mutation.
- Read access to objects permitted by visibility rules.
- Limited interaction with non owned objects when explicitly authorized.

## 7. Forbidden behaviors

The following behaviors are explicitly forbidden:

- Mutating objects owned by another identity without explicit permission.
- Bypassing schema restrictions through ACLs.
- Reading or writing objects outside the authorized app or domain.
- Inferring permissions from peer identity, network origin, or transport context.
- Partial authorization of an operation. Authorization is atomic per operation.

## 8. Interaction with other components

The access control model interacts with other components as follows:

- Inputs are received after authentication, signature verification, and schema validation.
- Outputs are allow or reject decisions.
- No direct access to storage is permitted.
- No graph mutations occur during authorization evaluation.

Trust boundaries:

- All inputs are treated as untrusted until validated.
- Authorization logic relies only on local graph state and compiled schemas.

## 9. Failure and rejection behavior

On authorization failure:

- The operation is rejected.
- No state is mutated.
- No partial writes occur.
- A deterministic error result is returned to the caller.

Authorization failures do not modify graph state or authorization rules.

## 10. Security properties

The access control model ensures:

- Least privilege enforcement.
- Explicit and auditable permission boundaries.
- Deterministic authorization behavior.
- Structural resistance to privilege escalation within the PoC design.
