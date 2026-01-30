



# 06 Access Control Model

Defines authorization evaluation rules and enforcement layers for 2WAY graph operations. Specifies authorization inputs, decision ordering, and rejection conditions. Defines required isolation constraints and security properties for access control.

For the meta specifications, see [06-access-control-model meta](../09-appendix/meta/01-protocol/06-access-control-model-meta.md).

## 1. Invariants and guarantees

The access control model enforces the following invariants:

- No operation may mutate [graph state](../02-architecture/managers/07-graph-manager.md) unless explicitly authorized.
- Authorization decisions are derived solely from local graph state and compiled [schemas](../02-architecture/managers/05-schema-manager.md).
- Authorization evaluation has no side effects.
- Authorization is evaluated before any persistent write occurs.

The following guarantees are provided:

- Unauthorized operations are rejected before reaching storage.
- [Schema](../02-architecture/managers/05-schema-manager.md) defined prohibitions cannot be overridden by object level access rules.
- App and domain boundaries are strictly enforced (see [01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).

## 2. Access control inputs

Authorization evaluation operates on the following inputs:

- Authenticated identity identifier ([05-keys-and-identity.md](05-keys-and-identity.md)).
- Device or delegated key identifier, if present in the [OperationContext](../02-architecture/services-and-apps/05-operation-context.md).
- Operation type, including create, update, or read.
- Target object identifiers and object types ([01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).
- App identifier and domain identifier ([01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).
- Local graph state, including [Parents](02-object-model.md), [Attributes](02-object-model.md), [Edges](02-object-model.md), [Ratings](02-object-model.md), and ACL objects.
- Compiled [schema definitions](../02-architecture/managers/05-schema-manager.md) applicable to the operation.

No implicit context, network metadata, or transport level information is used.

## 3. Authorization layers

Authorization is evaluated as a strict sequence of checks. Failure at any step results in rejection.

### 3.1 Ownership rules

Ownership is derived from [Parent](02-object-model.md) authorship.

Rules:

- The creator of a Parent is its permanent owner.
- Owned objects cannot be reassigned to another owner.
- Only the owner may mutate owned objects unless an explicit ACL permits otherwise.
- Remote operations attempting to mutate objects owned by another identity are rejected.

### 3.2 Schema level permissions

Schemas define default access semantics for object types (see [02-architecture/managers/05-schema-manager.md](../02-architecture/managers/05-schema-manager.md)).

Rules:

- Each object type declares whether it is mutable, append only, or immutable.
- Each object type declares which identities may create instances of that type.
- Allowed relations between object types are fixed by schema.
- Cross app object access is forbidden unless explicitly permitted by schema.

[Schema validation](../02-architecture/managers/05-schema-manager.md) occurs before ACL evaluation.

### 3.3 App and domain boundaries

Apps and domains define isolation scopes (see [01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)).

Rules:

- Operations are evaluated only within the app and domain they target.
- Objects from other apps are not visible unless schema rules explicitly allow it.
- Domains may restrict mutation and visibility, including participation in [sync](07-sync-and-consistency.md).

Operations that cross app or domain boundaries without explicit authorization are rejected.

### 3.4 Object level ACLs

ACLs provide explicit permission rules bound to specific objects or object sets.

Rules:

- ACLs are [graph objects](02-object-model.md) evaluated as part of authorization.
- ACLs may grant or deny read or write permissions.
- ACLs cannot override schema level prohibitions.
- Explicit deny rules take precedence over grant rules.

### 3.5 Graph derived constraints

Authorization may depend on graph structure when explicitly defined by [schema](../02-architecture/managers/05-schema-manager.md).

Rules:

- Membership [edges](02-object-model.md) may gate access to group scoped objects.
- Degrees of separation may restrict visibility or interaction.
- [Rating](02-object-model.md) or trust based thresholds may gate participation.

All such constraints must be explicitly declared by schema and evaluated deterministically.

## 4. Allowed behaviors

The following behaviors are allowed when all authorization layers succeed:

- Creation of new objects within the identity's authorized scope.
- Mutation of owned objects when [schema](../02-architecture/managers/05-schema-manager.md) and ACL rules permit mutation.
- Read access to objects permitted by visibility rules.
- Limited interaction with non owned objects when explicitly authorized.

## 5. Forbidden behaviors

The following behaviors are explicitly forbidden:

- Mutating objects owned by another identity without explicit permission.
- Bypassing [schema](../02-architecture/managers/05-schema-manager.md) restrictions through ACLs.
- Reading or writing objects outside the authorized app or domain.
- Inferring permissions from peer identity, network origin, or [transport context](08-network-transport-requirements.md).
- Partial authorization of an operation. Authorization is atomic per operation.

## 6. Interaction with other components

The access control model interacts with other components as follows:

- Inputs are received after [authentication](05-keys-and-identity.md), [signature verification](04-cryptography.md), and [schema validation](../02-architecture/managers/05-schema-manager.md).
- Outputs are allow or reject decisions.
- No direct access to [storage](../03-data/01-sqlite-layout.md) is permitted.
- No [graph mutations](../02-architecture/managers/07-graph-manager.md) occur during authorization evaluation.

Trust boundaries:

- All inputs are treated as untrusted until validated.
- Authorization logic relies only on local graph state and compiled [schemas](../02-architecture/managers/05-schema-manager.md).

## 7. Failure and rejection behavior

On authorization failure:

- The operation is rejected.
- No state is mutated.
- No partial writes occur.
- A deterministic error result is returned to the caller.

Authorization failures do not modify graph state or authorization rules.

## 8. Security properties

The access control model ensures:

- Least privilege enforcement.
- Explicit and auditable permission boundaries.
- Deterministic authorization behavior.
- Structural resistance to privilege escalation within the PoC design.
