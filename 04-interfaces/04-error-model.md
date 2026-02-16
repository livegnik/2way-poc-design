



# 04 Error model

Defines canonical error payloads, categories, symbolic code registries, and transport mapping rules for 2WAY interfaces. Errors are fail-closed and must never produce partial persistence.

For the meta specifications, see [04-error-model meta](../10-appendix/meta/04-interfaces/04-error-model-meta.md).

## 1. Purpose and scope

This specification defines:

* The canonical `ErrorDetail` payload shape.
* Canonical local error codes and categories.
* Protocol `ERR_*` normalization when protocol failures are surfaced through interface payloads.
* Service-specific `ERR_*` code mapping, including local HTTP status where relevant.
* Error-code family naming and ownership rules for services and managers.

## 2. Canonical `ErrorDetail` representation

All interface-visible errors emitted by managers and service layers use `ErrorDetail`:

```json
{
  "code": "<error_code>",
  "category": "<category>",
  "message": "<human readable message>",
  "data": { "...": "..." }
}
```

Field requirements:

| Field | Type | Requirement | Notes |
| --- | --- | --- | --- |
| `code` | string | Required | Must be one canonical local code or a registered service `ERR_*` code from this spec. |
| `category` | string | Required | Must match the category registry in Section 3. |
| `message` | string | Required | Human-readable, deterministic, and safe to expose. |
| `data` | object | Required | Machine-consumable details; may be empty `{}`. |

`ErrorDetail` is created through the `error_detail` helper. Implementations must not emit ad-hoc payload shapes.

## 3. Category registry

Categories reflect the earliest failure stage that owns the rejection:

| Category | Meaning | Primary owners |
| --- | --- | --- |
| `structural` | Input shape, type, encoding, or identifier format invalid. | Interface validation, Graph Manager |
| `schema` | Schema/type/domain constraints failed. | Schema Manager |
| `acl` | Authorization or visibility denied. | ACL Manager |
| `storage` | Persistence, sequencing, or cursor/state-write rejection. | Storage Manager, State Manager |
| `state` | Caller state assumptions stale or conflicting. | Graph Manager, service layers |
| `config` | Configuration missing, stale, or invalid. | Config Manager, service layers |
| `auth` | Identity/authentication proof invalid or missing. | Auth Manager, auth boundary |
| `network` | Admission, peer transport, or sync ingress rejection. | Network Manager, State Manager |
| `dos` | Challenge or throttling gate failure. | DoS Guard boundary |
| `internal` | Unexpected internal failure. | Owning manager/service |

## 4. Canonical local error codes

Canonical codes are used directly in local interface responses unless a service-specific `ERR_*` is required by contract.

| Code | Category | Default local HTTP status | Meaning |
| --- | --- | --- | --- |
| `envelope_invalid` | `structural` | `400` | Envelope failed structural validation. |
| `object_invalid` | `structural` | `400` | Object model invariants failed. |
| `identifier_invalid` | `structural` | `400` | Identifier or namespace validation failed. |
| `schema_unknown_type` | `schema` | `400` | Referenced schema type is unknown/not registered. |
| `schema_validation_failed` | `schema` | `400` | Input violates schema constraints. |
| `acl_denied` | `acl` | `400` | ACL/visibility policy denies action. |
| `storage_error` | `storage` | `400` | Storage transaction or persistence failure. |
| `sequence_error` | `storage` | `400` | Sequence/cursor ordering violation. |
| `config_invalid` | `config` | `400` | Required config invalid or unavailable. |
| `auth_required` | `auth` | `401` | Missing required authentication context. |
| `auth_invalid` | `auth` | `401` | Provided authentication invalid. |
| `network_rejected` | `network` | `400` | Network/sync admission rejected input. |
| `dos_challenge_required` | `dos` | `400` | Client must satisfy DoS challenge. |
| `app_not_found` | `state` | `404` | Requested app slug/registry entry not found. |
| `internal_error` | `internal` | `500` | Unexpected internal failure. |

Implementations must not invent additional canonical codes without updating this specification.

## 5. Protocol `ERR_*` normalization (when surfaced through interfaces)

Protocol `ERR_*` codes are defined in [01-protocol/10-errors-and-failure-modes.md](../01-protocol/10-errors-and-failure-modes.md). They are protocol-stage symbols and may be normalized to canonical local codes when exposed through local HTTP or WebSocket error payloads.

| Protocol family | Protocol symbols | Typical normalized `ErrorDetail.code` | Category | Typical local HTTP status |
| --- | --- | --- | --- | --- |
| Structural | `ERR_STRUCT_MISSING_FIELD`, `ERR_STRUCT_INVALID_TYPE`, `ERR_STRUCT_INVALID_ENCODING` | `envelope_invalid` | `structural` | `400` |
| Structural identifier | `ERR_STRUCT_INVALID_IDENTIFIER` | `identifier_invalid` | `structural` | `400` |
| Cryptographic and identity | `ERR_CRYPTO_INVALID_SIGNATURE`, `ERR_CRYPTO_MISSING_AUTHOR`, `ERR_CRYPTO_KEY_NOT_BOUND`, `ERR_CRYPTO_AUTHOR_MISMATCH`, `ERR_CRYPTO_KEY_REVOKED` | `auth_invalid` or `network_rejected` | `auth` or `network` | `401` or `400` by route |
| Schema and domain | `ERR_SCHEMA_TYPE_NOT_ALLOWED`, `ERR_SCHEMA_INVALID_VALUE`, `ERR_SCHEMA_EDGE_NOT_ALLOWED`, `ERR_SCHEMA_IMMUTABLE_OBJECT`, `ERR_SCHEMA_APPEND_ONLY_VIOLATION` | `schema_unknown_type` or `schema_validation_failed` | `schema` | `400` |
| Authorization | `ERR_AUTH_NOT_OWNER`, `ERR_AUTH_ACL_DENIED`, `ERR_AUTH_SCOPE_EXCEEDED`, `ERR_AUTH_VISIBILITY_DENIED` | `acl_denied` | `acl` | `400` |
| Sync integrity | `ERR_SYNC_RANGE_MISMATCH`, `ERR_SYNC_SEQUENCE_INVALID`, `ERR_SYNC_REWRITE_ATTEMPT`, `ERR_SYNC_MISSING_DEPENDENCY`, `ERR_SYNC_DOMAIN_VIOLATION` | `sequence_error` or `network_rejected` | `storage` or `network` | `400` |
| Resource/load | `ERR_RESOURCE_RATE_LIMIT`, `ERR_RESOURCE_PEER_LIMIT`, `ERR_RESOURCE_PUZZLE_FAILED` | `dos_challenge_required` or `network_rejected` | `dos` or `network` | `400` |

Route-specific interface specs may choose direct service `ERR_*` emissions instead of normalized canonical codes.

## 6. Service and interface `ERR_*` code registry

Service- and interface-specific symbols are returned directly in `ErrorDetail.code` when required by interface contracts.

### 6.1 Naming and family governance

Family names encode parent ownership. A code that belongs to a service or manager MUST include that parent family:

| Family pattern | Parent owner | Where it is used | Meaning |
| --- | --- | --- | --- |
| `ERR_SVC_SYS_<SERVICE>_*` | One named system service (`SETUP`, `IDENTITY`, `SYNC`, `OPS`, `APP`) | Interface-visible system service rejections | System service contract rejected the request for a service-owned reason. |
| `ERR_SVC_APP_*` | App service layer (`service_class=app`) | Interface-visible app service/lifecycle rejections | App service contract rejected the request for an app-owned reason. |
| `ERR_AUTH_*` | Auth/session boundary | Interface-visible auth/session failures | Authentication/session proof checks failed before service work can proceed. |
| `ERR_MNG_<MANAGER>_*` | One named manager (`NETWORK`, `STATE`, etc.) | Manager APIs, internal exceptions, or explicit interface surfaces | Manager-owned rejection reason; interfaces may normalize unless contract requires direct exposure. |

Naming rules:

* Bare family roots are forbidden: `ERR_SVC_SYS_*`, `ERR_SVC_APP_*`, and `ERR_MNG_*` MUST include a concrete suffix.
* Legacy singleton roots for service errors are forbidden in new interfaces (`ERR_APP_SERVICE_*`, `ERR_APP_SYS_*`).
* Service-specific `ERR_*` codes MUST carry the correct parent family and must not be emitted as unscoped standalone symbols.

### 6.2 Service code registry with category, status, retryability, and normalization policy

`retryable` means the same operation may succeed after bounded backoff with no payload change. "May be normalized away at interfaces" is `No` for contract-visible service/auth/frontend codes listed below.

#### 6.2.1 Setup Service (`ERR_SVC_SYS_SETUP_*`)

| Service code | Category | Local HTTP status | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- | --- |
| `ERR_SVC_SYS_SETUP_ACL` | `acl` | `400` | `false` | No | Setup Service capability checks failed (invite scope, bootstrap role, or installer gate). |
| `ERR_SVC_SYS_SETUP_BOOTSTRAP_TOKEN_INVALID` | `auth` | `400` | `false` | No | Bootstrap token is invalid, expired, revoked, or otherwise unusable. |
| `ERR_SVC_SYS_SETUP_ALREADY_INSTALLED` | `state` | `400` | `false` | No | Setup install flow was invoked after installation already completed. |
| `ERR_SVC_SYS_SETUP_SCHEMA` | `schema` | `400` | `false` | No | Setup payload/content violates Setup-owned schema rules. |
| `ERR_SVC_SYS_SETUP_DEVICE_ATTESTATION` | `auth` | `400` | `false` | No | Device attestation proof is missing, stale, malformed, or unverifiable. |
| `ERR_SVC_SYS_SETUP_INVITE_LIMIT` | `config` | `400` | `true` | No | Setup invite issuance exceeded configured pending-invite limits. |
| `ERR_SVC_SYS_SETUP_INVITE_NOT_FOUND` | `state` | `400` | `false` | No | Setup invite token does not resolve to a pending invite. |

#### 6.2.2 Identity Service (`ERR_SVC_SYS_IDENTITY_*`)

| Service code | Category | Local HTTP status | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- | --- |
| `ERR_SVC_SYS_IDENTITY_CAPABILITY` | `acl` | `400` | `false` | No | Identity Service capability checks failed for the requested mutation/action. |
| `ERR_SVC_SYS_IDENTITY_CONTACT_LIMIT` | `acl` | `400` | `false` | No | Identity Service contact policy/limit rejected the action. |
| `ERR_SVC_SYS_IDENTITY_NOT_FOUND` | `state` | `400` | `false` | No | Target identity does not exist for the requested Identity Service operation. |
| `ERR_SVC_SYS_IDENTITY_INVITE_NOT_FOUND` | `state` | `400` | `false` | No | Identity invite token does not resolve to an active invite. |

#### 6.2.3 Sync Service (`ERR_SVC_SYS_SYNC_*`)

| Service code | Category | Local HTTP status | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- | --- |
| `ERR_SVC_SYS_SYNC_PLAN_INVALID` | `structural` | `400` | `false` | No | Sync plan payload is structurally invalid after auth/context gates. |
| `ERR_SVC_SYS_SYNC_CAPABILITY` | `acl` | `400` | `false` | No | Caller lacks sync-management capability required by Sync Service policy. |
| `ERR_SVC_SYS_SYNC_PEER_NOT_FOUND` | `state` | `400` | `false` | No | Referenced peer does not exist in sync metadata. |
| `ERR_SVC_SYS_SYNC_TRANSITION_INVALID` | `state` | `400` | `false` | No | Requested pause/resume transition is invalid for the current peer state. |

#### 6.2.4 Admin/Ops Service (`ERR_SVC_SYS_OPS_*`)

| Service code | Category | Local HTTP status | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- | --- |
| `ERR_SVC_SYS_OPS_CAPABILITY` | `acl` | `400` | `false` | No | Admin/Ops capability checks failed for the requested ops route. |
| `ERR_SVC_SYS_OPS_CONFIG_ACCESS` | `config` | `400` | `false` | No | Ops route cannot access requested config export/snapshot under policy. |
| `ERR_SVC_SYS_OPS_APP_NOT_FOUND` | `state` | `404` | `false` | No | Requested app service slug does not resolve to an installed app service. |

#### 6.2.5 System app-lifecycle service (`ERR_SVC_SYS_APP_*`)

| Service code | Category | Local HTTP status | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- | --- |
| `ERR_SVC_SYS_APP_SIGNATURE_INVALID` | `auth` | `400` | `false` | No | Detached app package signature is missing, malformed, or fails verification. |
| `ERR_SVC_SYS_APP_PUBLISHER_UNTRUSTED` | `auth` | `400` | `false` | No | App registration/install rejects because signer identity is not trusted for app publication. |

#### 6.2.6 App service (`ERR_SVC_APP_*`)

| Service code | Category | Local HTTP status | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- | --- |
| `ERR_SVC_APP_CONTEXT_INVALID` | `structural` | `400` | `false` | No | App service `OperationContext` is missing/invalid; reject before invoking managers or mutating state. |
| `ERR_SVC_APP_CAPABILITY_REQUIRED` | `acl` | `400` | `false` | No | Caller lacks capability required by the target app service/lifecycle action. |
| `ERR_SVC_APP_FEED_CAPABILITY` | `acl` | `400` | `false` | No | App feed operation requires a feed capability the caller does not hold. |
| `ERR_SVC_APP_DISABLED` | `state` | `503` | `false` | No | App service is disabled by lifecycle/policy. |
| `ERR_SVC_APP_NOT_READY` | `state` | `503` | `true` | No | App service is initializing/degraded/not ready for work. |
| `ERR_SVC_APP_DEPENDENCY_UNAVAILABLE` | `state` | `503` | `true` | No | App service dependency is unavailable. |
| `ERR_SVC_APP_DRAINING` | `state` | `503` | `true` | No | App service is draining/unloading and refusing new work. |
| `ERR_SVC_APP_LOAD_FAILED` | `state` | `503` | `false` | No | App service failed to load/activate. |

#### 6.2.7 Auth/session boundary (`ERR_AUTH_*`)

| Service code | Category | Local HTTP status | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- | --- |
| `ERR_AUTH_SIGNATURE_INVALID` | `auth` | `401` | `false` | No | Auth registration signature validation failed. |
| `ERR_AUTH_REPLAY` | `auth` | `401` | `false` | No | Auth registration replay or timestamp skew checks failed. |
| `ERR_AUTH_TOKEN_EXPIRED` | `auth` | `401` | `false` | No | Auth token lifetime expired. |
| `ERR_AUTH_TOKEN_REVOKED` | `auth` | `401` | `false` | No | Auth token or bound device was revoked. |
| `ERR_AUTH_INVITE_EXPIRED` | `auth` | `410` | `false` | No | Invite token/proof expired before acceptance or use. |

#### 6.2.8 Frontend state-guard codes

| Service code | Category | Local HTTP status | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- | --- |
| `ERR_CAPABILITY_REVOKED` | `acl` | `400` | `false` | No | A previously valid capability is now revoked. |
| `ERR_DEVICE_REVOKED` | `auth` | `400` | `false` | No | Device binding was revoked after earlier issuance. |
| `ERR_OBJECT_VERSION` | `state` | `400` | `true` | No | Optimistic version precondition failed (`expected_version` mismatch). |
| `ERR_CONFIG_STALE` | `config` | `400` | `true` | No | Caller config hash is stale versus active backend config snapshot. |

#### 6.2.9 Shared service availability codes (`ERR_SVC_SYS_*`)

| Service code | Category | Local HTTP status | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- | --- |
| `ERR_SVC_SYS_DISABLED` | `state` | `503` | `false` | No | System service is disabled by policy or configuration. |
| `ERR_SVC_SYS_NOT_READY` | `state` | `503` | `true` | No | System service is initializing/degraded/not ready for work. |
| `ERR_SVC_SYS_DEPENDENCY_UNAVAILABLE` | `state` | `503` | `true` | No | System service dependency (service or manager) is unavailable. |
| `ERR_SVC_SYS_DRAINING` | `state` | `503` | `true` | No | System service is draining/shutting down and refusing new work. |
| `ERR_SVC_SYS_LOAD_FAILED` | `state` | `503` | `false` | No | System service failed to start/activate. |

### 6.3 Service availability metadata (`ERR_SVC_SYS_*`, `ERR_SVC_APP_*`)

Service availability errors MUST include a structured `ErrorDetail.data` object with the fields below:

| Field | Required | Type | Rules |
| --- | --- | --- | --- |
| `service_class` | Yes | string | `system` or `app`. |
| `service_name` | Yes for `service_class=system` | string | 1-64 chars, lowercase `[a-z0-9_.-]+` (example: `ops`, `identity`, `sync`). |
| `service_slug` | Yes for `service_class=app` | string | 1-64 chars, lowercase `[a-z0-9_.-]+`. |
| `service_state` | Yes | string | One of `disabled`, `initializing`, `not_ready`, `degraded`, `dependency_unavailable`, `draining`, `load_failed`. |
| `retryable` | Yes | boolean | `true` if the caller may retry after backoff, else `false`. |
| `retry_after_ms` | Conditionally | integer | Optional backoff hint; include when `retryable=true` and a bounded retry delay is known. |
| `dependency` | Conditionally | string | Required when code is `*_DEPENDENCY_UNAVAILABLE`; names missing dependency. |
| `disabled_by` | Conditionally | string | Optional reason key when code is `*_DISABLED` (example: `service.ops.admin_routes_enabled`). |

Per-code state and retry mapping:

| Service code | Allowed `service_state` values | `retryable` |
| --- | --- | --- |
| `ERR_SVC_SYS_DISABLED` | `disabled` | `false` |
| `ERR_SVC_SYS_NOT_READY` | `initializing`, `not_ready`, `degraded` | `true` |
| `ERR_SVC_SYS_DEPENDENCY_UNAVAILABLE` | `dependency_unavailable` | `true` |
| `ERR_SVC_SYS_DRAINING` | `draining` | `true` |
| `ERR_SVC_SYS_LOAD_FAILED` | `load_failed` | `false` |
| `ERR_SVC_APP_DISABLED` | `disabled` | `false` |
| `ERR_SVC_APP_NOT_READY` | `initializing`, `not_ready`, `degraded` | `true` |
| `ERR_SVC_APP_DEPENDENCY_UNAVAILABLE` | `dependency_unavailable` | `true` |
| `ERR_SVC_APP_DRAINING` | `draining` | `true` |
| `ERR_SVC_APP_LOAD_FAILED` | `load_failed` | `false` |

Availability-code selection rules:

* Use `ERR_SVC_SYS_DISABLED` or `ERR_SVC_APP_DISABLED` when a policy/config/lifecycle switch explicitly disables the route.
* Use `ERR_SVC_SYS_NOT_READY` or `ERR_SVC_APP_NOT_READY` when service readiness is not satisfied.
* Use `ERR_SVC_SYS_DEPENDENCY_UNAVAILABLE` or `ERR_SVC_APP_DEPENDENCY_UNAVAILABLE` when a required dependency is unavailable.
* Use `ERR_SVC_SYS_DRAINING` or `ERR_SVC_APP_DRAINING` during quiesce/shutdown unload windows.
* Use `ERR_SVC_SYS_LOAD_FAILED` or `ERR_SVC_APP_LOAD_FAILED` when service activation/load failed and the service cannot start.

### 6.4 Frontend `ERR_*` emission guidance

* `ERR_CAPABILITY_REVOKED`: emitted when a request depends on a capability edge that is no longer valid.
* `ERR_DEVICE_REVOKED`: emitted when device binding was revoked after prior issuance.
* `ERR_OBJECT_VERSION`: emitted when expected object version does not match current version.
* `ERR_CONFIG_STALE`: emitted when caller config hash does not match current config snapshot.

### 6.5 Manager-specific registry (`ERR_MNG_<MANAGER>_*`)

Manager codes are authoritative at manager boundaries. Interface contracts may expose them directly, but the default posture is normalization into canonical local codes unless a route explicitly requires direct `ERR_MNG_*`.

#### 6.5.1 Config Manager (`ERR_MNG_CONFIG_*`)

| Code | Category | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- |
| `ERR_MNG_CONFIG_SCHEMA_INVALID` | `config` | `false` | Yes | Config key/value fails schema validation or registration policy. |
| `ERR_MNG_CONFIG_UPDATE_QUEUE_FULL` | `config` | `true` | Yes | Config update queue is saturated and cannot accept more changes. |
| `ERR_MNG_CONFIG_PERSISTENCE_FAILED` | `storage` | `true` | Yes | Config snapshot persistence failed atomically. |

#### 6.5.2 Storage Manager (`ERR_MNG_STORAGE_*`)

| Code | Category | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- |
| `ERR_MNG_STORAGE_UNAVAILABLE` | `storage` | `false` | Yes | SQLite surface is unavailable for read/write operations. |
| `ERR_MNG_STORAGE_MIGRATION_FAILED` | `storage` | `false` | Yes | Startup migration/provisioning failed and storage is not usable. |
| `ERR_MNG_STORAGE_TX_ABORTED` | `storage` | `true` | Yes | Storage transaction aborted and was rolled back without partial commit. |

#### 6.5.3 Key Manager (`ERR_MNG_KEY_*`)

| Code | Category | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- |
| `ERR_MNG_KEY_NODE_KEY_MISSING` | `auth` | `false` | Yes | Required node key material is missing or unreadable. |
| `ERR_MNG_KEY_SCOPE_KEY_MISSING` | `auth` | `false` | Yes | Requested key scope has no usable key binding. |
| `ERR_MNG_KEY_BINDING_MISMATCH` | `auth` | `false` | Yes | Key material does not match graph identity binding constraints. |

#### 6.5.4 Auth Manager (`ERR_MNG_AUTH_*`)

| Code | Category | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- |
| `ERR_MNG_AUTH_TOKEN_STORE_UNAVAILABLE` | `auth` | `true` | Yes | Auth token store is unavailable for validation/revocation checks. |
| `ERR_MNG_AUTH_ADMIN_GATE_DENIED` | `acl` | `false` | Yes | Caller lacks admin gating requirements after successful authentication. |
| `ERR_MNG_AUTH_CONTEXT_INCOMPLETE` | `structural` | `false` | Yes | Required auth context fields are missing to build `OperationContext`. |

#### 6.5.5 Schema Manager (`ERR_MNG_SCHEMA_*`)

| Code | Category | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- |
| `ERR_MNG_SCHEMA_TYPE_UNKNOWN` | `schema` | `false` | Yes | Referenced schema type is unknown/unregistered in active schema set. |
| `ERR_MNG_SCHEMA_VALIDATION_FAILED` | `schema` | `false` | Yes | Payload violates compiled schema constraints. |
| `ERR_MNG_SCHEMA_REGISTRY_UNAVAILABLE` | `internal` | `true` | Yes | Schema registry is unavailable/degraded for safe validation. |

#### 6.5.6 ACL Manager (`ERR_MNG_ACL_*`)

| Code | Category | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- |
| `ERR_MNG_ACL_IDENTITY_MISSING` | `acl` | `false` | Yes | ACL evaluation lacks required caller identity context. |
| `ERR_MNG_ACL_POLICY_DENIED` | `acl` | `false` | Yes | ACL policy explicitly denies the requested action. |
| `ERR_MNG_ACL_EVALUATION_UNAVAILABLE` | `internal` | `true` | Yes | ACL engine/caches are unavailable, forcing fail-closed rejection. |

#### 6.5.7 Graph Manager (`ERR_MNG_GRAPH_*`)

| Code | Category | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- |
| `ERR_MNG_GRAPH_OPERATION_INVALID` | `structural` | `false` | Yes | Graph operation set is malformed or violates graph-level invariants. |
| `ERR_MNG_GRAPH_SEQUENCE_CONFLICT` | `storage` | `true` | Yes | Graph sequencing precondition failed before commit. |
| `ERR_MNG_GRAPH_READ_BOUNDS_EXCEEDED` | `state` | `false` | Yes | Graph read exceeded deterministic traversal/resource bounds. |

#### 6.5.8 App Manager (`ERR_MNG_APP_*`)

| Code | Category | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- |
| `ERR_MNG_APP_SLUG_UNKNOWN` | `state` | `false` | Yes | App slug does not resolve in the app registry. |
| `ERR_MNG_APP_REGISTRY_INCONSISTENT` | `internal` | `false` | Yes | App registry integrity checks failed. |
| `ERR_MNG_APP_LOAD_REJECTED` | `state` | `true` | Yes | App load/start request was rejected due to transient runtime state. |

#### 6.5.9 State Manager (`ERR_MNG_STATE_*`)

| Code | Category | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- |
| `ERR_MNG_STATE_SEQUENCE_INVALID` | `storage` | `false` | Yes | Inbound/outbound sequence invariants were violated. |
| `ERR_MNG_STATE_SYNC_CURSOR_CONFLICT` | `storage` | `true` | Yes | Sync cursor/checkpoint update conflicts with current persisted state. |
| `ERR_MNG_STATE_OUTBOUND_ACL_UNAVAILABLE` | `internal` | `true` | Yes | Outbound sync ACL check could not be completed safely. |

#### 6.5.10 Network Manager (`ERR_MNG_NETWORK_*`)

| Code | Category | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- |
| `ERR_MNG_NETWORK_ADMISSION_CLOSED` | `network` | `true` | Yes | Admission surface is closed for new sessions/dials. |
| `ERR_MNG_NETWORK_CHALLENGE_TIMEOUT` | `dos` | `true` | Yes | Required admission challenge timed out before completion. |
| `ERR_MNG_NETWORK_PEER_UNREACHABLE` | `network` | `true` | Yes | Peer discovery/dial reached bounded failure thresholds. |

#### 6.5.11 Event Manager (`ERR_MNG_EVENT_*`)

| Code | Category | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- |
| `ERR_MNG_EVENT_SUBSCRIPTION_REJECTED` | `acl` | `false` | Yes | Subscription/authz rules reject the requested event scope/filter. |
| `ERR_MNG_EVENT_BUFFER_OVERFLOW` | `state` | `true` | Yes | Event queue/buffer limits were exceeded under backpressure. |
| `ERR_MNG_EVENT_RESUME_TOKEN_INVALID` | `structural` | `false` | Yes | Resume token is malformed, stale, or invalid for current stream state. |

#### 6.5.12 Log Manager (`ERR_MNG_LOG_*`)

| Code | Category | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- |
| `ERR_MNG_LOG_RECORD_INVALID` | `structural` | `false` | Yes | Submitted log record failed schema/normalization validation. |
| `ERR_MNG_LOG_MANDATORY_SINK_UNAVAILABLE` | `internal` | `true` | Yes | Mandatory log sink is unavailable and fail-closed policy applies. |
| `ERR_MNG_LOG_BACKPRESSURE_ACTIVE` | `state` | `true` | Yes | Log pipeline backpressure limits reject additional submissions. |

#### 6.5.13 Health Manager (`ERR_MNG_HEALTH_*`)

| Code | Category | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- |
| `ERR_MNG_HEALTH_SIGNAL_INVALID` | `structural` | `false` | Yes | Health signal payload is malformed or fails validation. |
| `ERR_MNG_HEALTH_DEPENDENCY_DEGRADED` | `state` | `true` | Yes | Critical dependency health is degraded and readiness is blocked. |
| `ERR_MNG_HEALTH_SNAPSHOT_UNAVAILABLE` | `internal` | `true` | Yes | Health snapshot cannot be produced safely from current signals. |

#### 6.5.14 DoS Guard Manager (`ERR_MNG_DOS_*`)

| Code | Category | `retryable` | May be normalized away at interfaces | Meaning (when emitted) |
| --- | --- | --- | --- | --- |
| `ERR_MNG_DOS_ADMISSION_DENIED` | `dos` | `true` | Yes | DoS policy denied admission for current telemetry/risk posture. |
| `ERR_MNG_DOS_CHALLENGE_REQUIRED` | `dos` | `true` | Yes | Admission requires client puzzle/challenge completion. |
| `ERR_MNG_DOS_PUZZLE_VERIFICATION_FAILED` | `dos` | `true` | Yes | Client puzzle response failed verification or expired. |

## 7. Transport mapping rules

### 7.1 Local HTTP

Status selection is deterministic and evaluated in this order:

1. Unregistered route: `404` without `ErrorDetail` (router-level rejection).
2. `internal_error`: `500`.
3. Authentication codes (`auth_required`, `auth_invalid`, `ERR_AUTH_SIGNATURE_INVALID`, `ERR_AUTH_REPLAY`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`): `401`.
4. `ERR_AUTH_INVITE_EXPIRED`: `410`.
5. `app_not_found` and `ERR_SVC_SYS_OPS_APP_NOT_FOUND`: `404`.
6. Service availability code families (`ERR_SVC_SYS_*`, `ERR_SVC_APP_*`): `503`.
7. Any other `ErrorDetail` code defined by this spec: `400`.
8. Unexpected failures without a canonical `ErrorDetail`: `500`.

Route-level interface specs may define a narrower allowed code set, but must not violate this status mapping.

### 7.2 WebSocket

* Handshake authentication failures reject the upgrade with HTTP `401` and `ErrorDetail`.
* Post-handshake event errors use the `error` event envelope from [14-events-interface.md](14-events-interface.md) with `ErrorDetail`.
* Close reason mapping is defined by [02-websocket-events.md](02-websocket-events.md) and [14-events-interface.md](14-events-interface.md).

### 7.3 Internal manager APIs

Manager-level errors are raised as exceptions carrying `ErrorDetail`; interface layers translate those to transport responses.

When a manager-specific code is emitted directly (without normalization), it MUST use the `ERR_MNG_<MANAGER>_*` family (for example, `ERR_MNG_NETWORK_ADMISSION_CLOSED`).

## 8. Failure precedence

Precedence is strict and fail-closed:

1. Structural
2. Cryptographic/authentication
3. Schema/domain
4. ACL/authorization
5. Storage/state
6. Internal fallback

The first failure encountered must be returned; later stages must not execute.

## 9. Emission responsibilities (high-level)

* Structural and identifier failures: interface validation and Graph Manager.
* Schema failures: Schema Manager.
* ACL failures: ACL Manager.
* Storage and sequence failures: Storage Manager and State Manager.
* Auth failures: Auth Manager and auth-facing interfaces.
* Network/DoS failures: Network Manager and DoS Guard boundary.

## 10. Forbidden behaviors

* Returning partial success on failure.
* Emitting non-canonical error payload shapes.
* Emitting unregistered error codes from this specification.
* Leaking stack traces or internal implementation details over external interfaces.

## 11. Requirement ID anchors

This specification is authoritative for these error-model requirement IDs:

* R108
* R111
* R178-R181
* R185-R187
