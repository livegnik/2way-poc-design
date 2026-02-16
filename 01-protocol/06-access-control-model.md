



# 06 Access Control Model

Defines authorization evaluation rules and enforcement layers for 2WAY graph operations. Specifies authorization inputs, decision ordering, and rejection conditions. Defines required isolation constraints and security properties for access control.

For the meta specifications, see [06-access-control-model meta](../10-appendix/meta/01-protocol/06-access-control-model-meta.md).

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

- Authenticated identity identifier ([05-keys-and-identity.md](05-keys-and-identity.md)). For local requests this is `OperationContext.requester_identity_id`. For remote sync, the effective actor identity is the operation `owner_identity`.
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
- Ownership comparisons use the effective actor identity (local `OperationContext.requester_identity_id`, or remote operation `owner_identity`).

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
- ACL evaluation is required unless the enforcement matrix below explicitly marks an operation as "no ACL check."

### 3.5 ACL enforcement matrix and bypass rules

Authorization must follow the matrix below. These rules are normative and apply to both local and remote contexts unless explicitly scoped otherwise.
The ACL Manager MUST apply this matrix exactly.

Definitions:

- **Effective requester identity**: `OperationContext.requester_identity_id` for local requests; operation `owner_identity` for remote sync.
- **Own data**: objects where `owner_identity` equals the effective requester identity (including the Parent and any attached Attributes, Edges, or Ratings with the same owner identity).
- **Own parent**: a Parent whose `owner_identity` equals the effective requester identity.
- **Admin action**: an operation explicitly marked as admin-only by the interface surface and executed by an identity that holds the `system.admin` capability.

| Action type | ACL check? | Notes |
| --- | --- | --- |
| Querying own data | No | Query scope is limited to zeroth-degree objects owned by the requester. Schema and app/domain boundaries still apply. |
| Creating objects under own parent | No | Schema creation rules still apply. |
| Creating objects under a parent owned by another identity | Yes | Requires ACL allow for write or create. |
| Modifying or tombstoning (visibility suppression) of own objects | No | Schema mutability and suppression rules still apply; physical deletion is forbidden. |
| Modifying or tombstoning (visibility suppression) of objects owned by another identity | Yes | Requires ACL allow for write or update. |
| Querying system (`app_0`) or app-managed data not owned by the requester | Yes | ACL must allow read unless the action is admin-only. |
| Syncing data with another user | Yes | [State Manager](../02-architecture/managers/09-state-manager.md) MUST enforce ACL checks before exporting any object to a remote peer. |
| Admin actions | No | Admin actions MUST require `system.admin` capability and bypass object-level ACL checks only. Schema validation, structural validation, and app/domain scoping remain in force. |

Additional rules:

- Operations targeting own data MUST NOT require object-level ACL checks; schema and app/domain rules still apply.
- Operations targeting objects owned by another identity MUST require explicit ACL allow for the relevant verb.
- Physical deletion of graph objects is forbidden; deletion semantics are expressed as schema-defined tombstoning or visibility suppression.

### 3.6 Canonical ACL objects (app_0 schema)

ACLs are stored as a Parent plus Attributes in the same `app_id` scope as the objects they govern (system-scope ACLs live in `app_0`). The canonical ACL schema uses the following types:

ACL root Parent: `acl.root`

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `target_type` | Yes | string | `parent`, `attr`, `edge`, `rating`, `app`, or `domain`. |
| `target_id` | Cond | string | Required when `target_type` is `parent`, `attr`, `edge`, or `rating`. |
| `target_app_id` | Cond | int | Required when `target_type` is `app`. |
| `target_domain` | Cond | string | Required when `target_type` is `domain`. |
| `created_at` | Yes | string | RFC3339 timestamp. |

ACL Attributes (attached to `acl.root`):

* `acl.read.allow`
* `acl.read.deny`
* `acl.write.allow`
* `acl.write.deny`

Each ACL attribute `value_json` MUST be:

```
{
  "identities": [<int>],
  "apps": [<int>],
  "capabilities": ["<string>"]
}
```

Rules:

- Empty arrays are permitted and mean "no principals of that class".
- Omitted keys are treated as empty arrays.
- ACLs MUST be evaluated only within the ACL's `app_id` scope unless schema explicitly delegates cross-app access.

### 3.7 Canonical capability objects (app_0 schema)

Capabilities are stored as typed Parents in `app_0`, and grants are stored as typed Edges.

Capability definition Parent: `capability.definition`

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `name` | Yes | string | 1-128 chars, unique within `app_0`. |
| `scope` | Yes | string | `system` or `app`. |
| `app_id` | Cond | int | Required when `scope=app`. |
| `description` | No | string | 0-256 chars. |
| `created_at` | Yes | string | RFC3339 timestamp. |

Capability grant Edge: `capability.edge`

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `granted_by` | Yes | string | Identity id that granted the capability. |
| `granted_at` | Yes | string | RFC3339 timestamp. |
| `expires_at` | No | string | RFC3339 timestamp. |

Edge structure rules:

- `src_parent_id` MUST reference the recipient identity Parent.
- `dst_parent_id` MUST reference the `capability.definition` Parent.
- Capability edges MUST reside in `app_0` regardless of the target app scope.
- Capability edges with `expires_at` in the past MUST be treated as revoked.
- Revoked or expired capability edges MUST NOT grant authorization and MUST produce `ERR_CAPABILITY_REVOKED` when the request relies on them.

Publisher trust:

- A publisher is trusted for app publication only if it holds a `capability.edge` to `capability.definition` where `name=system.apps.publish`.

Reserved capability names:

- `system.admin` (admin-only actions; bypasses object-level ACL checks per Section 3.5).
- `system.apps.publish` (publisher trust for app installation).


### 3.8 Graph derived constraints

Authorization may depend on graph structure when explicitly defined by [schema](../02-architecture/managers/05-schema-manager.md).

Rules:

- Membership [edges](02-object-model.md) may gate access to group scoped objects. Group membership is represented using `system.group` Parents and `system.group_member` Edges in `app_0` (see [02-object-model.md](02-object-model.md) Section 6.6).
- Degrees of separation may restrict visibility or interaction.
- [Rating](02-object-model.md) or trust based thresholds may gate participation.

All such constraints must be explicitly declared by schema and evaluated deterministically.

## 4. Allowed behaviors

The following behaviors are allowed when all authorization layers succeed:

- Creation of new objects within the identity's authorized scope.
- Mutation of owned objects when [schema](../02-architecture/managers/05-schema-manager.md) rules permit mutation (ACL checks apply only when required by the enforcement matrix).
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

Error mapping:

- Ownership violation -> `ERR_AUTH_NOT_OWNER`.
- ACL deny -> `ERR_AUTH_ACL_DENIED`.
- Delegation or device scope exceeded -> `ERR_AUTH_SCOPE_EXCEEDED`.
- Domain visibility denied -> `ERR_AUTH_VISIBILITY_DENIED`.
- Revoked or expired capability -> `ERR_CAPABILITY_REVOKED`.

When surfaced via interfaces, authorization failures use `ErrorDetail.code=acl_denied` unless the interface explicitly emits a service-level `ERR_*` code per [04-error-model.md](../04-interfaces/04-error-model.md).

## 8. Security properties

The access control model ensures:

- Least privilege enforcement.
- Explicit and auditable permission boundaries.
- Deterministic authorization behavior.
- Structural resistance to privilege escalation within the protocol design.
