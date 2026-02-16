



# 06 App Lifecycle Interface

Defines application lifecycle endpoints for app installation, enable and disable, open, uninstall, and repair. These endpoints are local-only and require authenticated admin or installer identities per [03-app-services.md](../02-architecture/services-and-apps/03-app-services.md) and [06-flows/02-app-install-and-permissions.md](../06-flows/02-app-install-and-permissions.md).

For the meta specifications, see [06-app-lifecycle meta](../10-appendix/meta/04-interfaces/06-app-lifecycle-meta.md).

## 1. Purpose and scope

This document specifies lifecycle operations required for app installation and management. It formalizes the register flow defined in [06-flows/02-app-install-and-permissions.md](../06-flows/02-app-install-and-permissions.md), defines the canonical app artifact contract for installation, and adds explicit lifecycle transition rules implied by [App Manager](../02-architecture/managers/08-app-manager.md). All endpoints are local-only.

## 2. Endpoint index

| Route | Method | Auth | Summary |
| --- | --- | --- | --- |
| `/api/system/apps/register` | POST | Required | Register and install an app package. |
| `/api/system/apps/list` | GET | Required | List registered apps and status. |
| `/api/system/apps/{slug}/enable` | POST | Required | Enable an installed app. |
| `/api/system/apps/{slug}/disable` | POST | Required | Disable an installed app. |
| `/api/system/apps/{slug}/uninstall` | POST | Required | Uninstall an app package. |
| `/api/system/apps/{slug}/repair` | POST | Required | Repair an app installation and rebuild caches. |
| `/api/system/apps/{slug}/open` | POST | Required | Record an app open intent and return launch metadata. |

## 2.1 Lifecycle error family legend

App lifecycle routes use parent-scoped families. Legacy singleton roots such as `ERR_APP_SERVICE_*` or `ERR_APP_SYS_*` are forbidden.

| Family or code | Parent owner | Meaning |
| --- | --- | --- |
| `ERR_SVC_APP_CONTEXT_INVALID` | App service family (`ERR_SVC_APP_*`) | Request lacks a valid app-service [OperationContext](../02-architecture/services-and-apps/05-operation-context.md); rejection happens before lifecycle mutation. |
| `ERR_SVC_APP_CAPABILITY_REQUIRED` | App service family (`ERR_SVC_APP_*`) | Caller is authenticated but missing required app lifecycle capability. |
| `ERR_SVC_SYS_APP_SIGNATURE_INVALID` | System app-lifecycle family (`ERR_SVC_SYS_APP_*`) | App package signature or signer material failed verification. |
| `ERR_SVC_SYS_APP_PUBLISHER_UNTRUSTED` | System app-lifecycle family (`ERR_SVC_SYS_APP_*`) | Publisher identity is missing or not trusted for app publication. |
| `ERR_SVC_APP_NOT_READY`, `ERR_SVC_APP_DISABLED`, `ERR_SVC_APP_DEPENDENCY_UNAVAILABLE`, `ERR_SVC_APP_DRAINING`, `ERR_SVC_APP_LOAD_FAILED` | App service availability family (`ERR_SVC_APP_*`) | Target app service is unavailable and must fail with HTTP `503`. |

## 2.2 Lifecycle state model and transitions

Canonical persisted lifecycle state values:

* `installed_disabled`
* `installed_enabled`
* `degraded`
* `draining`
* `removed`

Transition matrix:

| Operation | Allowed from | Resulting state |
| --- | --- | --- |
| Register (`POST /register`) | no existing row, or same `slug` + same `version` (idempotent) | `installed_enabled` when `enabled=true`, else `installed_disabled` |
| Enable (`POST /{slug}/enable`) | `installed_disabled` or `degraded` | `installed_enabled` |
| Disable (`POST /{slug}/disable`) | `installed_enabled`, `degraded`, or `draining` | `installed_disabled` |
| Repair (`POST /{slug}/repair`) | `installed_enabled`, `installed_disabled`, `degraded`, or `draining` | previous enabled/disabled posture restored; may clear `degraded` |
| Open (`POST /{slug}/open`) | `installed_enabled` | `installed_enabled` (no state change) |
| Uninstall (`POST /{slug}/uninstall`) | `installed_disabled` or `degraded` | `removed` |

Rules:

* Uninstall from `installed_enabled` or `draining` MUST be rejected with `object_invalid`; disable first.
* Open while disabled MUST return `ERR_SVC_APP_DISABLED`.
* Any disallowed transition MUST return `object_invalid`.

## 2.3 Canonical app artifact contract

The install artifact contract in this section is authoritative for package layout, manifest shape, graph bundle constraints, and signature rules.

### 2.3.1 ZIP container and required files

The multipart register payload includes:

* `package_zip` (required): raw ZIP bytes
* `package_sig` (required): detached signature metadata for the ZIP bytes

ZIP requirements:

* ZIP root MUST include `manifest.json` and `schema.json`.
* `acl.json` is optional.
* If `manifest.composition` is `service` or `hybrid`, ZIP root MUST include `app-service/` containing the backend app-service payload.
* Unknown top-level files are allowed for app payloads, but lifecycle validation ignores them unless referenced by `manifest.json`.
* Filenames are informational; `manifest.json` is authoritative.

### 2.3.2 `manifest.json` schema

`manifest.json` MUST be a JSON object with unknown fields rejected at all levels.

Required fields:

* `slug` (string): lowercase app slug, 1-64 chars, pattern `^[a-z0-9][a-z0-9._-]*$`.
* `version` (string): semantic version (`MAJOR.MINOR.PATCH`).
* `composition` (string enum): `frontend`, `service`, or `hybrid`.
* `capabilities` (array[string]): capability names requested by the app.
* `dependencies` (array[string]): dependent app slugs.
* `config_keys` (array[string]): configuration keys under `app.<slug>.*`.
* `requires` (object):
  * `platform.min_version` (string, required)
  * `managers` (array[string], optional)
  * `permissions` (array[string], optional)

Optional fields:

* `title` (string)
* `description` (string)
* `supports.frontend.min_version` (string)
* `service` (object): scheduler and runtime hints for app-service payloads
* `frontend` (object): bundle metadata for frontend payloads

Conditional requirements:

* If `composition=service` or `composition=hybrid`, `service` object is required and MUST include:
  * `entrypoint` (string, required)
  * `runtime` (string, required)

Forbidden fields:

* `app_id`
* Any node-local identifier or sequence field (`global_seq`, `sync_flags`, `domain_seq`).

### 2.3.3 `schema.json` and `acl.json` bundle schema

`schema.json` MUST be:

```
{
  "objects": [ { ... graph operation ... } ]
}
```

`acl.json` (if present) MUST use the same shape.

Bundle rules:

* `schema.objects` is required and non-empty.
* `acl.objects` is optional.
* Objects must conform to [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md) Section 6 operation grammar except where overridden here for install templates.
* Only create operations are allowed (`parent_create`, `attr_create`, `edge_create`, `rating_create`).
* Exactly one of `type_key` or `type_id` MUST be present per operation.
* `global_seq` and `sync_flags` are forbidden fields on all bundle objects.
* `app_id` and `owner_identity` are forbidden fields on bundle objects. The register flow injects local values before commit.
* Unknown object fields are rejected.

### 2.3.4 `package_sig` schema and verification

`package_sig` MUST be UTF-8 JSON:

```
{
  "publisher_public_key": "<base64>",
  "signature": "<base64>"
}
```

Rules:

* Required fields: `publisher_public_key` and `signature`.
* `publisher_public_key` MUST resolve to an existing publisher identity in the local graph.
* Signature verification is computed over the raw `package_zip` bytes exactly as received (no re-zip, no canonical JSON transform).
* Signature algorithm is derived from the resolved publisher key type and protocol cryptography rules (PoC: secp256k1).
* Unknown fields are rejected.
* The resolved publisher must be trusted for `system.apps.publish` in `app_0`; otherwise install is rejected.
* If `publisher_public_key` is missing from the local graph, install is rejected and the caller must add the publisher identity before retrying.

### 2.3.5 Slug-first identity and app_id binding

`app_id` is node-local and assigned only by [App Manager](../02-architecture/managers/08-app-manager.md). Therefore:

* Package artifacts MUST be slug-first and MUST NOT declare `app_id`.
* The installer resolves `slug` to local `app_id` during registration.
* Responses may include local `app_id`, but package identity remains `slug` + `version`.

## 3. POST /api/system/apps/register

Request body (multipart/form-data):

* `package_zip` (file, required) - `<slug>_app.zip` containing `manifest.json`, `schema.json`, and optional `acl.json`.
* `package_sig` (file, required) - `<slug>_app_sig.txt` containing detached signature metadata for the ZIP bytes.
* `device_id` (int, optional) - installer device id.
* `enabled` (bool, optional) - enable after install.

Rules:

* `manifest` and `schema` are required.
* `device_id` is optional and represents the installer device.
* Installation MUST be idempotent for the same slug and version.
* `manifest.slug` and `manifest.version` are required.
* The ZIP payload MUST include `manifest.json` and `schema.json`. `acl.json` is optional.
* If `manifest.composition` is `service` or `hybrid`, `app-service/` payload is required and MUST load through [App Manager](../02-architecture/managers/08-app-manager.md) after validation.
* App installation MUST be blocked unless the publisher identity exists in the graph and is marked trusted for app publication. If missing or untrusted, the caller MUST be prompted to add or trust the publisher before installation proceeds.
* A publisher is trusted when its identity carries the `system.apps.publish` capability edge in `app_0`.
* `manifest.app_id` and any node-local identifier fields in artifacts are forbidden.

Response:

```
{
  "app_id": <int>,
  "slug": "<string>",
  "version": "<string>",
  "status": "installed_enabled|installed_disabled|degraded|draining|removed",
  "enabled": true
}
```

Errors:

* `ERR_SVC_APP_CONTEXT_INVALID`
* `ERR_SVC_APP_CAPABILITY_REQUIRED`
* `ERR_SVC_SYS_APP_SIGNATURE_INVALID`
* `ERR_SVC_SYS_APP_PUBLISHER_UNTRUSTED`
* `schema_validation_failed`
* `object_invalid` (invalid lifecycle transition, invalid composition-specific payload requirements, or invalid app-service payload metadata)
* `acl_denied`
* `storage_error`
* `auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`
* `envelope_invalid` (malformed multipart, malformed JSON files, missing required parts, unknown fields)
* `internal_error`

## 4. GET /api/system/apps/list

Response:

```
{
  "apps": [
    {
      "app_id": <int>,
      "slug": "<string>",
      "version": "<string>",
      "status": "installed_enabled|installed_disabled|degraded|draining|removed",
      "enabled": true
    }
  ]
}
```

Errors:

* `ERR_SVC_APP_CAPABILITY_REQUIRED`
* `ERR_SVC_APP_NOT_READY`, `ERR_SVC_APP_DISABLED`, `ERR_SVC_APP_DEPENDENCY_UNAVAILABLE`, `ERR_SVC_APP_DRAINING`, or `ERR_SVC_APP_LOAD_FAILED` when app service inventory is unavailable or runtime state cannot be resolved.
* `storage_error`
* `auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`
* `internal_error`

## 5. POST /api/system/apps/{slug}/enable

Request body:

```
{ "device_id": <int> }
```

Response:

```
{"ok": true}
```

Errors:

* `ERR_SVC_APP_CAPABILITY_REQUIRED`
* `ERR_SVC_APP_NOT_READY`, `ERR_SVC_APP_DISABLED`, `ERR_SVC_APP_DEPENDENCY_UNAVAILABLE`, `ERR_SVC_APP_DRAINING`, or `ERR_SVC_APP_LOAD_FAILED` when the target app service is installed but unavailable.
* `storage_error`
* `auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`
* `404` (`app_not_found`) when `slug` is unknown.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`object_invalid`) for invalid lifecycle transitions.
* `internal_error`

## 6. POST /api/system/apps/{slug}/disable

Request body:

```
{ "device_id": <int> }
```

Response:

```
{"ok": true}
```

Errors:

* `ERR_SVC_APP_CAPABILITY_REQUIRED`
* `ERR_SVC_APP_NOT_READY`, `ERR_SVC_APP_DISABLED`, `ERR_SVC_APP_DEPENDENCY_UNAVAILABLE`, `ERR_SVC_APP_DRAINING`, or `ERR_SVC_APP_LOAD_FAILED` when the target app service is unavailable.
* `storage_error`
* `auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`
* `404` (`app_not_found`) when `slug` is unknown.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`object_invalid`) for invalid lifecycle transitions.
* `internal_error`

## 7. POST /api/system/apps/{slug}/uninstall

Request body:

```
{ "device_id": <int> }
```

Response:

```
{"ok": true}
```

Errors:

* `ERR_SVC_APP_CAPABILITY_REQUIRED`
* `ERR_SVC_APP_NOT_READY`, `ERR_SVC_APP_DISABLED`, `ERR_SVC_APP_DEPENDENCY_UNAVAILABLE`, `ERR_SVC_APP_DRAINING`, or `ERR_SVC_APP_LOAD_FAILED` when the target app service is unavailable.
* `storage_error`
* `auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`
* `404` (`app_not_found`) when `slug` is unknown.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`object_invalid`) for invalid lifecycle transitions.
* `internal_error`

## 8. POST /api/system/apps/{slug}/repair

Request body:

```
{ "device_id": <int> }
```

Response:

```
{"ok": true}
```

Errors:

* `ERR_SVC_APP_CAPABILITY_REQUIRED`
* `ERR_SVC_APP_NOT_READY`, `ERR_SVC_APP_DISABLED`, `ERR_SVC_APP_DEPENDENCY_UNAVAILABLE`, `ERR_SVC_APP_DRAINING`, or `ERR_SVC_APP_LOAD_FAILED` when repair dependencies are unavailable.
* `storage_error`
* `auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`
* `404` (`app_not_found`) when `slug` is unknown.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`object_invalid`) for invalid lifecycle transitions.
* `internal_error`

## 9. POST /api/system/apps/{slug}/open

Request body:

```
{ "device_id": <int> }
```

Response:

```
{
  "app_id": <int>,
  "slug": "<string>",
  "status": "installed_enabled|installed_disabled|degraded|draining|removed",
  "enabled": true
}
```

Errors:

* `ERR_SVC_APP_CAPABILITY_REQUIRED`
* `ERR_SVC_APP_NOT_READY`, `ERR_SVC_APP_DISABLED`, `ERR_SVC_APP_DEPENDENCY_UNAVAILABLE`, `ERR_SVC_APP_DRAINING`, or `ERR_SVC_APP_LOAD_FAILED` when the target app service is unavailable.
* `storage_error`
* `auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`
* `404` (`app_not_found`) when `slug` is unknown.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`object_invalid`) for invalid lifecycle transitions.
* `internal_error`

## 10. Validation and ordering

* All lifecycle endpoints MUST construct a complete [OperationContext](../02-architecture/services-and-apps/05-operation-context.md) before invoking managers.
* Missing or invalid payloads MUST be rejected before any manager mutation.
* [App Manager](../02-architecture/managers/08-app-manager.md) MUST enforce the lifecycle transition matrix in Section 2.2.
* Signature and publisher trust checks MUST complete before `app_id` allocation and before any schema or ACL mutation.
* For `service` and `hybrid` packages, app-service payload extraction and loading happen only after manifest/schema/ACL validation succeeds; load failures must fail closed with no partial install state.
* `ERR_SVC_APP_*` is reserved for app service availability failures and maps to HTTP `503` per [04-error-model.md](04-error-model.md).

## 11. Forbidden behaviors

* Creating app identities or schemas outside the register endpoint.
* Enabling or disabling apps without [App Manager](../02-architecture/managers/08-app-manager.md) state transitions.
* Accepting package artifacts that declare node-local `app_id` values.
* Partially applying schema or ACL bundles after any register-stage failure.
