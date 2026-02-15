



## 10 Errors and Failure Modes

Defines protocol-level error classes and symbolic `ERR_*` codes for 2WAY operations and sync packages. Specifies validation-stage ordering, deterministic rejection, and component ownership at trust boundaries.

For the meta specifications, see [10-errors-and-failure-modes meta](../10-appendix/meta/01-protocol/10-errors-and-failure-modes-meta.md).

### 1. Invariants and guarantees

The following invariants apply to all failures defined in this file:

* No rejected operation produces persistent state changes (see [02-architecture/managers/02-storage-manager.md](../02-architecture/managers/02-storage-manager.md)).
* No rejected operation advances global or domain [sequence counters](07-sync-and-consistency.md).
* Validation failures are deterministic for identical input and local state.
* The selected rejection reason depends only on input and local state, not on timing or peer identity metadata.
* Rejected remote input is never re-broadcast or re-synced (see [07-sync-and-consistency.md](07-sync-and-consistency.md)).

The protocol guarantees:

* Structural invalidity is detected before [authorization](06-access-control-model.md) checks.
* Authorization failure is detected before any [write attempt](../02-architecture/managers/02-storage-manager.md).
* [Sync integrity](07-sync-and-consistency.md) violations are detected before object materialization or state mutation.
* [Revocation state](05-keys-and-identity.md) takes precedence over ordering and freshness checks.

### 2. Validation stage order and precedence

Each accepted input passes through the following ordered stages:

| Stage | Class | Primary owners | On failure |
| --- | --- | --- | --- |
| 1 | Structural | Interface validation, Graph Manager, State Manager | Reject immediately with structural `ERR_STRUCT_*`. |
| 2 | Cryptographic and identity | Network Manager, Auth/Key boundaries | Reject as untrusted input with `ERR_CRYPTO_*`. |
| 3 | Schema and domain | Schema Manager | Reject operation/package with `ERR_SCHEMA_*`. |
| 4 | Authorization | ACL Manager | Reject with `ERR_AUTH_*` without leaking protected state. |
| 5 | Sync integrity and ordering | State Manager | Reject package with `ERR_SYNC_*`. |
| 6 | Resource and load | Network Manager, DoS Guard boundary | Reject/defer with `ERR_RESOURCE_*`. |

Precedence is strict:

1. Structural
2. Cryptographic and identity
3. Schema and domain
4. Authorization
5. Sync integrity
6. Resource and load

When multiple violations exist, the first class in this ordered list determines the single emitted protocol code.

### 3. Protocol `ERR_*` code registry

Each operation or sync package may produce at most one protocol-level code from this registry.

#### 3.1 Structural errors

| Code | Trigger condition | Typical owner | Rejection scope |
| --- | --- | --- | --- |
| `ERR_STRUCT_MISSING_FIELD` | Required envelope or package field is absent. | Interface validation, Graph Manager, State Manager | Entire operation/package. |
| `ERR_STRUCT_INVALID_TYPE` | Field type or object kind is invalid or unsupported. | Graph Manager, State Manager | Entire operation/package. |
| `ERR_STRUCT_INVALID_ENCODING` | Representation marker, canonicalization, or encoding is invalid. | Interface validation, Graph Manager | Entire operation/package. |
| `ERR_STRUCT_INVALID_IDENTIFIER` | Identifier is missing, malformed, or violates namespace rules. | Graph Manager | Entire operation/package. |

Structural failures are terminal and must short-circuit all later validation.

#### 3.2 Cryptographic and identity errors

| Code | Trigger condition | Typical owner | Rejection scope |
| --- | --- | --- | --- |
| `ERR_CRYPTO_INVALID_SIGNATURE` | Signature cannot be verified against signed payload. | Network Manager, verification boundary | Entire operation/package. |
| `ERR_CRYPTO_MISSING_AUTHOR` | Required author/sender identity reference is absent. | Network Manager, Graph Manager | Entire operation/package. |
| `ERR_CRYPTO_KEY_NOT_BOUND` | Public key is not present or not bound to declared identity. | Key/identity boundary | Entire operation/package. |
| `ERR_CRYPTO_AUTHOR_MISMATCH` | Signature identity does not match declared author/sender. | Network Manager | Entire operation/package. |
| `ERR_CRYPTO_KEY_REVOKED` | Key is revoked/superseded at validation time. | Key Manager, Network Manager | Entire operation/package. |

Cryptographic failures are terminal and indicate untrusted input.

#### 3.3 Schema and domain errors

| Code | Trigger condition | Typical owner | Rejection scope |
| --- | --- | --- | --- |
| `ERR_SCHEMA_TYPE_NOT_ALLOWED` | Type is not permitted for the domain/app context. | Schema Manager | Operation/package. |
| `ERR_SCHEMA_INVALID_VALUE` | Attribute/value violates declared schema constraints. | Schema Manager | Operation/package. |
| `ERR_SCHEMA_EDGE_NOT_ALLOWED` | Edge relationship is forbidden by schema/domain rules. | Schema Manager | Operation/package. |
| `ERR_SCHEMA_IMMUTABLE_OBJECT` | Mutation targets immutable object content. | Schema Manager, Graph Manager | Operation/package. |
| `ERR_SCHEMA_APPEND_ONLY_VIOLATION` | Input violates append-only domain constraints. | Schema Manager, Graph Manager | Operation/package. |

Schema failures are terminal for the affected operation or package.

#### 3.4 Authorization errors

| Code | Trigger condition | Typical owner | Rejection scope |
| --- | --- | --- | --- |
| `ERR_AUTH_NOT_OWNER` | Write attempted by non-owner without qualifying capability. | ACL Manager | Operation/package. |
| `ERR_AUTH_ACL_DENIED` | ACL evaluation denies requested action. | ACL Manager | Operation/package. |
| `ERR_AUTH_SCOPE_EXCEEDED` | Delegated key/capability exceeds granted scope. | ACL Manager, Auth boundary | Operation/package. |
| `ERR_AUTH_VISIBILITY_DENIED` | Visibility rules deny access to required context. | ACL Manager | Operation/package. |

Authorization failures are terminal and must not leak additional protected state.

#### 3.5 Sync integrity errors

| Code | Trigger condition | Typical owner | Rejection scope |
| --- | --- | --- | --- |
| `ERR_SYNC_RANGE_MISMATCH` | Declared sequence range does not match package content. | State Manager | Entire package. |
| `ERR_SYNC_SEQUENCE_INVALID` | Sequence regresses, overlaps, or replays accepted history. | State Manager | Entire package. |
| `ERR_SYNC_REWRITE_ATTEMPT` | Package attempts to rewrite immutable accepted history. | State Manager, Storage boundary | Entire package. |
| `ERR_SYNC_MISSING_DEPENDENCY` | Required dependency objects or prior ranges are absent. | State Manager | Entire package. |
| `ERR_SYNC_DOMAIN_VIOLATION` | Package crosses disallowed domain boundaries. | State Manager | Entire package. |

Sync integrity failures invalidate the full package.

#### 3.6 Resource and load errors

| Code | Trigger condition | Typical owner | Rejection scope |
| --- | --- | --- | --- |
| `ERR_RESOURCE_RATE_LIMIT` | Local/global rate threshold exceeded. | Network Manager, DoS Guard boundary | Request/package. |
| `ERR_RESOURCE_PEER_LIMIT` | Per-peer admission threshold exceeded. | Network Manager | Peer request/package. |
| `ERR_RESOURCE_PUZZLE_FAILED` | Required client puzzle is missing, invalid, or stale. | DoS Guard boundary | Request/package. |

Resource failures may be transient but must still be fail-closed (no partial processing).

### 4. Failure handling behavior

#### 4.1 Rejection behavior

On any failure:

* The input is rejected in full.
* No objects are created, modified, or deleted.
* No sequence counters are advanced.
* No derived actions, callbacks, or event fan-out are triggered from rejected input.

#### 4.2 Operation and package boundaries

* A single operation rejection cannot partially commit sibling writes.
* A sync package rejection invalidates the entire package even if only one contained operation fails.
* Batched processing must roll back to the pre-input state on failure.

#### 4.3 Interaction with components

Failures are detected at specific trust boundaries:

* [Graph Manager](../02-architecture/managers/07-graph-manager.md): structural/object-level validation, ownership gates.
* [Schema Manager](../02-architecture/managers/05-schema-manager.md): schema/domain validation.
* [ACL Manager](../02-architecture/managers/06-acl-manager.md): authorization and visibility.
* [State Manager](../02-architecture/managers/09-state-manager.md): sync ordering/integrity.
* [Network Manager](../02-architecture/managers/10-network-manager.md): admission/rate/peer constraints.

Each component may reject input only within its owned responsibility boundary.

### 5. Peer-facing behavior

For remote peers:

* Rejected input may be silently dropped.
* Repeated fatal violations may result in peer disconnect (see [08-network-transport-requirements.md](08-network-transport-requirements.md)).
* Nodes are not required to disclose internal validation details.
* Rejected input must not be echoed back or re-announced.

For local callers:

* Rejection reason must be surfaced explicitly, directly or through mapped interface error semantics (see [04-error-model.md](../04-interfaces/04-error-model.md)).
* No side effects may be observable after rejection.

### 6. Transport surfacing guidance (when relevant)

This protocol specification is transport-agnostic. When a failure must be surfaced on interfaces that use `ErrorDetail`, mapping is defined by [04-error-model.md](../04-interfaces/04-error-model.md).

Recommended normalization by failure class:

| Protocol class | Typical `ErrorDetail.code` mapping | Typical `ErrorDetail.category` | Typical local HTTP status |
| --- | --- | --- | --- |
| Structural (`ERR_STRUCT_*`) | `envelope_invalid` or `identifier_invalid` | `structural` | `400` |
| Cryptographic/identity (`ERR_CRYPTO_*`) | `auth_invalid` or `network_rejected` | `auth` or `network` | `401` or `400` by interface |
| Schema/domain (`ERR_SCHEMA_*`) | `schema_unknown_type` or `schema_validation_failed` | `schema` | `400` |
| Authorization (`ERR_AUTH_*`) | `acl_denied` | `acl` | `400` |
| Sync integrity (`ERR_SYNC_*`) | `sequence_error` or `network_rejected` | `storage` or `network` | `400` |
| Resource/load (`ERR_RESOURCE_*`) | `dos_challenge_required` or `network_rejected` | `dos` or `network` | `400` |
| Unexpected internal failures | `internal_error` | `internal` | `500` |

The protocol `ERR_*` registry remains authoritative for protocol-stage classification and precedence.

#### 6.1 Service availability overlays on interface routes

Service availability failures are interface-contract outcomes and are not protocol-stage validation symbols in Section 3.

When local interfaces expose service unavailability, they MUST emit specific service-family codes from [04-error-model.md](../04-interfaces/04-error-model.md):

| Interface service family | Code form | Typical category | Typical local HTTP status |
| --- | --- | --- | --- |
| System service availability | `ERR_SVC_SYS_*` | `state` | `503` |
| System service-specific contract failures | `ERR_SVC_SYS_<SERVICE>_*` | route-defined (often `acl`, `schema`, `auth`, or `structural`) | route-defined (typically `400`) |
| App service availability | `ERR_SVC_APP_*` | `state` | `503` |
| App service-specific contract failures | `ERR_SVC_APP_*` (non-availability suffixes) | route-defined (often `acl` or `structural`) | route-defined (typically `400`) |
| Manager-specific surfaced failures | `ERR_MNG_<MANAGER>_*` | manager-defined | interface-defined/normalized |

Bare service-family roots (without a specific suffix) are forbidden and MUST NOT be emitted.
Legacy singleton service roots (for example `ERR_APP_SERVICE_*` or `ERR_APP_SYS_*`) are forbidden on new interface contracts.

### 7. Allowed and forbidden behaviors

#### 7.1 Allowed behaviors

The protocol allows:

* Silent rejection of invalid remote input.
* Early rejection without expensive validation.
* Independent local enforcement of rejection rules per node.
* Peer disconnect after repeated fatal violations.

#### 7.2 Forbidden behaviors

The protocol forbids:

* Partial application of invalid input.
* Automatic correction/mutation of invalid input.
* Acceptance of objects with unverifiable authorship (see [05-keys-and-identity.md](05-keys-and-identity.md)).
* Acceptance of sync packages signed by revoked keys.
* Acceptance of out-of-order or replayed [sync packages](07-sync-and-consistency.md).

### 8. Absence of recovery semantics

This specification defines no automatic recovery behavior.

* Recovery from failure is external to the protocol.
* Rejected input must be corrected and resubmitted.
* Sync resumes only after invalid packages are discarded (see [07-sync-and-consistency.md](07-sync-and-consistency.md)).
