



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

This specification does not define:

* UI message phrasing, localization, or frontend visuals.
* Transport-independent protocol precedence rules (see [01-protocol/10-errors-and-failure-modes.md](../01-protocol/10-errors-and-failure-modes.md)).
* Internal logging schema details.

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

### 6.2 Service code registry with category, status, and meaning

| Service code | Parent family | Category | Local HTTP status | Meaning (when emitted) |
| --- | --- | --- | --- | --- |
| `ERR_SVC_SYS_APP_PUBLISHER_UNTRUSTED` | `ERR_SVC_SYS_APP_*` | `auth` | `400` | App registration/install rejects because signer identity is not trusted for app publication. |
| `ERR_SVC_APP_CAPABILITY_REQUIRED` | `ERR_SVC_APP_*` | `acl` | `400` | Caller lacks the capability required by the target app service or app lifecycle action. |
| `ERR_SVC_APP_CONTEXT_INVALID` | `ERR_SVC_APP_*` | `structural` | `400` | App service `OperationContext` is missing/invalid; reject before invoking managers or mutating state. |
| `ERR_SVC_SYS_APP_SIGNATURE_INVALID` | `ERR_SVC_SYS_APP_*` | `auth` | `400` | Detached app package signature is missing, malformed, or fails verification. |
| `ERR_AUTH_REPLAY` | `ERR_AUTH_*` | `auth` | `401` | Auth registration replay or skew checks failed. |
| `ERR_AUTH_SIGNATURE_INVALID` | `ERR_AUTH_*` | `auth` | `401` | Auth registration signature validation failed. |
| `ERR_AUTH_TOKEN_EXPIRED` | `ERR_AUTH_*` | `auth` | `401` | Auth token lifetime expired. |
| `ERR_AUTH_TOKEN_REVOKED` | `ERR_AUTH_*` | `auth` | `401` | Auth token or bound device was revoked. |
| `ERR_SVC_SYS_SETUP_ACL` | `ERR_SVC_SYS_SETUP_*` | `acl` | `400` | Setup Service authorization/capability checks failed (bootstrap token, invite scope, or installer gate). |
| `ERR_SVC_SYS_SETUP_DEVICE_ATTESTATION` | `ERR_SVC_SYS_SETUP_*` | `auth` | `400` | Setup Service device attestation proof is invalid, missing, stale, or unverifiable. |
| `ERR_SVC_SYS_SETUP_SCHEMA` | `ERR_SVC_SYS_SETUP_*` | `schema` | `400` | Setup payload/content fails schema/structure rules owned by Setup Service. |
| `ERR_CAPABILITY_REVOKED` | frontend state guard | `acl` | `400` | A previously valid capability is now revoked. |
| `ERR_CONFIG_STALE` | frontend state guard | `config` | `400` | Caller config hash is stale versus active backend config snapshot. |
| `ERR_DEVICE_REVOKED` | frontend state guard | `auth` | `400` | Device binding was revoked after earlier issuance. |
| `ERR_SVC_APP_FEED_CAPABILITY` | `ERR_SVC_APP_*` | `acl` | `400` | App feed operation requires a feed capability the caller does not hold. |
| `ERR_SVC_SYS_IDENTITY_CAPABILITY` | `ERR_SVC_SYS_IDENTITY_*` | `acl` | `400` | Identity Service capability checks failed for the requested mutation/action. |
| `ERR_SVC_SYS_IDENTITY_CONTACT_LIMIT` | `ERR_SVC_SYS_IDENTITY_*` | `acl` | `400` | Identity Service contact policy/limit check rejected the action. |
| `ERR_AUTH_INVITE_EXPIRED` | `ERR_AUTH_*` | `auth` | `410` | Invite token/proof expired before acceptance or use. |
| `ERR_OBJECT_VERSION` | frontend state guard | `state` | `400` | Optimistic version precondition failed (`expected_version` mismatch). |
| `ERR_SVC_SYS_OPS_CAPABILITY` | `ERR_SVC_SYS_OPS_*` | `acl` | `400` | Admin/Ops capability checks failed for the requested ops route. |
| `ERR_SVC_SYS_OPS_CONFIG_ACCESS` | `ERR_SVC_SYS_OPS_*` | `config` | `400` | Ops route cannot access requested config export/snapshot under policy. |
| `ERR_SVC_APP_DEPENDENCY_UNAVAILABLE` | `ERR_SVC_APP_*` | `state` | `503` | App service dependency is unavailable. |
| `ERR_SVC_APP_DISABLED` | `ERR_SVC_APP_*` | `state` | `503` | App service is disabled by lifecycle/policy. |
| `ERR_SVC_APP_DRAINING` | `ERR_SVC_APP_*` | `state` | `503` | App service is draining/unloading and refusing new work. |
| `ERR_SVC_APP_LOAD_FAILED` | `ERR_SVC_APP_*` | `state` | `503` | App service failed to load/activate. |
| `ERR_SVC_APP_NOT_READY` | `ERR_SVC_APP_*` | `state` | `503` | App service is initializing/degraded/not ready for work. |
| `ERR_SVC_SYS_DEPENDENCY_UNAVAILABLE` | `ERR_SVC_SYS_*` | `state` | `503` | System service dependency (service or manager) is unavailable. |
| `ERR_SVC_SYS_DISABLED` | `ERR_SVC_SYS_*` | `state` | `503` | System service is disabled by policy or configuration. |
| `ERR_SVC_SYS_DRAINING` | `ERR_SVC_SYS_*` | `state` | `503` | System service is draining/shutting down and refusing new work. |
| `ERR_SVC_SYS_LOAD_FAILED` | `ERR_SVC_SYS_*` | `state` | `503` | System service failed to start/activate. |
| `ERR_SVC_SYS_NOT_READY` | `ERR_SVC_SYS_*` | `state` | `503` | System service is initializing/degraded/not ready for work. |
| `ERR_SVC_SYS_SYNC_PLAN_INVALID` | `ERR_SVC_SYS_SYNC_*` | `structural` | `400` | Sync Service plan payload is structurally invalid after auth/context gates. |

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

## 7. Transport mapping rules

### 7.1 Local HTTP

Status selection is deterministic and evaluated in this order:

1. Unregistered route: `404` without `ErrorDetail` (router-level rejection).
2. `internal_error`: `500`.
3. Authentication codes (`auth_required`, `auth_invalid`, `ERR_AUTH_SIGNATURE_INVALID`, `ERR_AUTH_REPLAY`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`): `401`.
4. `ERR_AUTH_INVITE_EXPIRED`: `410`.
5. `app_not_found`: `404`.
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
