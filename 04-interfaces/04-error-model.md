



# 04 Error model

Defines canonical error shapes, categories, and transport mapping for 2WAY. Errors are fail-closed and must not cause partial persistence.

For the meta specifications, see [04-error-model meta](../10-appendix/meta/04-interfaces/04-error-model-meta.md).

## 1. Purpose and scope

The error model provides a unified representation for failures across the backend, including protocol validation, schema enforcement, ACL denial, storage failures, and network admission. It does not define UI behavior; it defines payload shapes and manager-level semantics.

## 2. Error representation

All errors emitted by managers use `ErrorDetail`:

```
{
  "code": "<error_code>",
  "category": "<category>",
  "message": "<human readable message>",
  "data": { ... }
}
```

`ErrorDetail` is created via the `error_detail` helper and must include a canonical `code` and derived `category`.

## 3. Categories

Categories reflect the earliest failure stage:

* `structural`
* `schema`
* `acl`
* `storage`
* `state`
* `config`
* `auth`
* `network`
* `dos`
* `internal`

## 4. Error codes (canonical)

The following codes are defined for the PoC:

* `envelope_invalid`
* `object_invalid`
* `identifier_invalid`
* `schema_unknown_type`
* `schema_validation_failed`
* `acl_denied`
* `storage_error`
* `sequence_error`
* `config_invalid`
* `auth_required`
* `auth_invalid`
* `network_rejected`
* `dos_challenge_required`
* `app_not_found`
* `internal_error`

Implementations must not invent ad-hoc codes without updating this file.

## 5. Protocol ERR_* codes

Defined in [01-protocol/10-errors-and-failure-modes.md](../01-protocol/10-errors-and-failure-modes.md):

* `ERR_STRUCT_MISSING_FIELD`
* `ERR_STRUCT_INVALID_TYPE`
* `ERR_STRUCT_INVALID_ENCODING`
* `ERR_STRUCT_INVALID_IDENTIFIER`
* `ERR_CRYPTO_INVALID_SIGNATURE`
* `ERR_CRYPTO_MISSING_AUTHOR`
* `ERR_CRYPTO_KEY_NOT_BOUND`
* `ERR_CRYPTO_AUTHOR_MISMATCH`
* `ERR_CRYPTO_KEY_REVOKED`
* `ERR_SCHEMA_TYPE_NOT_ALLOWED`
* `ERR_SCHEMA_INVALID_VALUE`
* `ERR_SCHEMA_EDGE_NOT_ALLOWED`
* `ERR_SCHEMA_IMMUTABLE_OBJECT`
* `ERR_SCHEMA_APPEND_ONLY_VIOLATION`
* `ERR_AUTH_NOT_OWNER`
* `ERR_AUTH_ACL_DENIED`
* `ERR_AUTH_SCOPE_EXCEEDED`
* `ERR_AUTH_VISIBILITY_DENIED`
* `ERR_SYNC_RANGE_MISMATCH`
* `ERR_SYNC_SEQUENCE_INVALID`
* `ERR_SYNC_REWRITE_ATTEMPT`
* `ERR_SYNC_MISSING_DEPENDENCY`
* `ERR_SYNC_DOMAIN_VIOLATION`
* `ERR_RESOURCE_RATE_LIMIT`
* `ERR_RESOURCE_PEER_LIMIT`
* `ERR_RESOURCE_PUZZLE_FAILED`

## 6. Service-referenced codes

Referenced in [02-system-services.md](../02-architecture/services-and-apps/02-system-services.md):

* `ERR_BOOTSTRAP_SCHEMA`
* `ERR_BOOTSTRAP_ACL`
* `ERR_BOOTSTRAP_DEVICE_ATTESTATION`
* `ERR_INVITE_EXPIRED`
* `ERR_IDENTITY_CONTACT_LIMIT`
* `ERR_IDENTITY_CAPABILITY`
* `ERR_FEED_CAPABILITY`
* `ERR_SYNC_PLAN_INVALID`
* `ERR_OPS_CAPABILITY`
* `ERR_OPS_CONFIG_ACCESS`

Referenced in [03-app-backend-extensions.md](../02-architecture/services-and-apps/03-app-backend-extensions.md):

* `ERR_APP_EXTENSION_CONTEXT`
* `ERR_APP_EXTENSION_CAPABILITY`
* `ERR_APP_SIGNATURE_INVALID`
* `ERR_APP_PUBLISHER_UNTRUSTED`

Referenced in [13-auth-session.md](13-auth-session.md):

* `ERR_AUTH_SIGNATURE_INVALID`
* `ERR_AUTH_REPLAY`
* `ERR_AUTH_TOKEN_EXPIRED`
* `ERR_AUTH_TOKEN_REVOKED`

Referenced in [04-frontend-apps.md](../02-architecture/services-and-apps/04-frontend-apps.md):

* `ERR_CAPABILITY_REVOKED`
* `ERR_DEVICE_REVOKED`
* `ERR_OBJECT_VERSION`
* `ERR_CONFIG_STALE`

### 6.1 Service code mapping to ErrorDetail

Service-specific `ERR_*` codes are surfaced to local callers using the canonical `ErrorDetail` shape. The `ErrorDetail.code` MUST equal the `ERR_*` symbol, and the `ErrorDetail.category` MUST follow the mapping below.

| Service code | ErrorDetail category | Notes |
| --- | --- | --- |
| `ERR_BOOTSTRAP_SCHEMA` | `schema` | Bootstrap schema validation failure. |
| `ERR_BOOTSTRAP_ACL` | `acl` | Bootstrap ACL denial. |
| `ERR_BOOTSTRAP_DEVICE_ATTESTATION` | `auth` | Device attestation failed. |
| `ERR_AUTH_SIGNATURE_INVALID` | `auth` | Registration signature invalid. |
| `ERR_AUTH_REPLAY` | `auth` | Registration payload replay detected. |
| `ERR_AUTH_TOKEN_EXPIRED` | `auth` | Auth token expired. |
| `ERR_AUTH_TOKEN_REVOKED` | `auth` | Auth token revoked. |
| `ERR_IDENTITY_CONTACT_LIMIT` | `acl` | Contact limit enforced by policy. |
| `ERR_IDENTITY_CAPABILITY` | `acl` | Missing or unknown capability. |
| `ERR_FEED_CAPABILITY` | `acl` | Missing capability for feed action. |
| `ERR_SYNC_PLAN_INVALID` | `structural` | Sync plan validation failure. |
| `ERR_OPS_CAPABILITY` | `acl` | Missing admin capability. |
| `ERR_OPS_CONFIG_ACCESS` | `config` | Config export denied or invalid. |
| `ERR_APP_EXTENSION_CONTEXT` | `structural` | Missing or invalid OperationContext. |
| `ERR_APP_EXTENSION_CAPABILITY` | `acl` | Missing capability for extension action. |
| `ERR_APP_SIGNATURE_INVALID` | `auth` | App package signature invalid. |
| `ERR_APP_PUBLISHER_UNTRUSTED` | `auth` | Publisher missing or not trusted. |
| `ERR_CAPABILITY_REVOKED` | `acl` | Capability revoked after issuance. |
| `ERR_DEVICE_REVOKED` | `auth` | Device credential revoked. |
| `ERR_OBJECT_VERSION` | `state` | Client attempted to mutate a stale object version. |
| `ERR_CONFIG_STALE` | `config` | Config snapshot was stale. |
| `ERR_INVITE_EXPIRED` | `auth` | Bootstrap invite expired. |

### 6.2 HTTP status mapping for service codes

Unless a service explicitly documents a different status code, all service-specific `ERR_*` responses are returned with HTTP `400` and the canonical `ErrorDetail` payload.
Authentication failures use `401` for `auth_required`, `auth_invalid`, `ERR_AUTH_SIGNATURE_INVALID`, `ERR_AUTH_REPLAY`, `ERR_AUTH_TOKEN_EXPIRED`, and `ERR_AUTH_TOKEN_REVOKED` where applicable.

### 6.3 Frontend ERR_* emission guidance

The following frontend-referenced codes are emitted under these conditions:

* `ERR_CAPABILITY_REVOKED` — emitted by Auth/ACL enforcement when a previously granted capability edge has been revoked and the current request still relies on it.
* `ERR_DEVICE_REVOKED` — emitted by Auth Manager when the authenticated device binding has been revoked.
* `ERR_OBJECT_VERSION` — emitted by Graph Manager when a mutation includes an expected object version and it does not match the current version.
* `ERR_CONFIG_STALE` — emitted by service layers when the caller’s OperationContext config hash does not match the current Config Manager snapshot.

## 7. Failure precedence

Failure precedence is strict:

1. Structural validation failures
2. Cryptographic/authentication failures
3. Schema validation failures
4. ACL failures
5. Storage failures

The first failure encountered must be returned and later stages must not execute.

## 8. Transport mapping

### 6.1 Local HTTP

* `401` for authentication failures (`auth_required`, `auth_invalid`, `ERR_AUTH_SIGNATURE_INVALID`, `ERR_AUTH_REPLAY`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`).
* `400` for other `ErrorDetail` failures.
* `500` for `internal_error`.
* `404` for unregistered routes (router-level rejection; no `ErrorDetail`).
* `404` for `app_not_found` on registered routes that resolve an app slug.
* `410` for expired bootstrap invites (`ERR_INVITE_EXPIRED`).
* `500` for unexpected internal errors without an `ErrorDetail`.

Response payloads use the `ErrorDetail` shape.

### 6.2 WebSocket

Authentication failures result in immediate connection rejection (no session) with HTTP `401` and an `ErrorDetail` payload. When events are added, error events must use the `ErrorDetail` shape and follow the error envelope in [14-events-interface.md](14-events-interface.md).

### 6.3 Internal manager APIs

Manager errors are raised as exceptions that carry `ErrorDetail`. Interface layers translate them into transport responses.

## 9. Emission responsibilities (high-level)

* Structural and identifier errors: Graph Manager and interface validation.
* Schema errors: Schema Manager.
* ACL errors: ACL Manager.
* Storage and sequencing errors: Storage Manager and State Manager.
* Auth errors: Auth Manager and interface layer.
* DoS and network errors: DoS Guard Manager and Network Manager.

## 10. Forbidden behaviors

* Returning partial success when a failure occurs.
* Emitting non-canonical error shapes.
* Leaking stack traces or internal errors over external interfaces.
