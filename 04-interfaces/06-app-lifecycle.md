



# 06 App Lifecycle Interface

Defines application lifecycle endpoints for app installation, enable/disable, open, uninstall, and repair. These endpoints are local-only and require authenticated admin or installer identities per [03-app-backend-extensions.md](../02-architecture/services-and-apps/03-app-backend-extensions.md) and [06-flows/02-app-install-and-permissions.md](../06-flows/02-app-install-and-permissions.md).

For the meta specifications, see [06-app-lifecycle meta](../10-appendix/meta/04-interfaces/06-app-lifecycle-meta.md).

## 1. Purpose and scope

This document specifies the lifecycle operations required for app installation and management. It formalizes the register flow defined in [06-flows/02-app-install-and-permissions.md](../06-flows/02-app-install-and-permissions.md) and adds explicit lifecycle endpoints implied by App Manager state transitions. All endpoints are local-only.

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

## 3. POST /api/system/apps/register

Request body (multipart/form-data):

* `package_zip` (file, required) - `<slug>_app.zip` containing `manifest.json`, `schema.json`, and optional `acl.json`.
* `package_sig` (file, required) - `<slug>_app_sig.txt` containing a detached signature for the ZIP bytes.
* `device_id` (int, optional) - installer device id.
* `enabled` (bool, optional) - enable after install.

Package contents (derived from ZIP):

```
{
  "manifest": {
    "slug": "<string>",
    "version": "<string>",
    "capabilities": ["<string>"],
    "dependencies": ["<string>"],
    "config_keys": ["<string>"]
  },
  "schema": {
    "objects": [ { ... graph object ... } ]
  },
  "acl": {
    "objects": [ { ... graph object ... } ]
  }
}
```

Graph object bundle schema:

* `schema.objects` and `acl.objects` are arrays of operation objects conforming to [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md) Section 6.
* Only create operations are allowed (`parent_create`, `attr_create`, `edge_create`, `rating_create`).
* Exactly one of `type_key` or `type_id` MUST be present per operation.
* `global_seq` and `sync_flags` are forbidden fields on all objects.
* Unknown fields are rejected.

Rules:

* `manifest` and `schema` are required.
* `device_id` is optional and represents the installer device.
* Installation MUST be idempotent for the same slug and version.
* `manifest.slug` and `manifest.version` are required.
* `schema.objects` and `acl.objects` carry graph objects expressed using the canonical Parent/Attribute forms defined in [01-protocol/02-object-model.md](../01-protocol/02-object-model.md).
* Objects in `schema.objects` and `acl.objects` MUST NOT include `global_seq` or `sync_flags` (assigned on commit).
* The ZIP payload MUST include `manifest.json` and `schema.json`. `acl.json` is optional.
* The signature file MUST be present and MUST verify against the raw ZIP bytes using public key material supplied with the package or a trusted publisher registry.
* The signature file MUST include a `signer_id` that resolves to a publisher identity in the graph, or a `publisher_public_key` that can be bound to a new publisher identity.
* App installation MUST be blocked unless the publisher identity exists in the graph and is marked trusted for app publication. If the publisher identity is missing or untrusted, the caller MUST be prompted to add or trust the publisher before installation proceeds.
* A publisher is trusted when its identity carries the `system.apps.publish` capability edge in `app_0`.
* Signature file structure follows [02-architecture/services-and-apps/03-app-backend-extensions.md](../02-architecture/services-and-apps/03-app-backend-extensions.md).
* Filenames are informational; the manifest contents are authoritative.

Response:

```
{
  "app_id": <int>,
  "slug": "<string>",
  "version": "<string>",
  "status": "<string>",
  "enabled": true
}
```

Errors:

* `ERR_APP_EXTENSION_CONTEXT`
* `ERR_APP_EXTENSION_CAPABILITY`
* `ERR_APP_SIGNATURE_INVALID`
* `ERR_APP_PUBLISHER_UNTRUSTED`
* `schema_validation_failed`
* `acl_denied`
* `storage_error`
* `auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`
* `envelope_invalid` (malformed multipart or missing required parts)
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
      "status": "<string>",
      "enabled": true
    }
  ]
}
```

Errors:

* `ERR_APP_EXTENSION_CAPABILITY`
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

* `ERR_APP_EXTENSION_CAPABILITY`
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

* `ERR_APP_EXTENSION_CAPABILITY`
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

* `ERR_APP_EXTENSION_CAPABILITY`
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

* `ERR_APP_EXTENSION_CAPABILITY`
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
  "status": "<string>",
  "enabled": true
}
```

Errors:

* `ERR_APP_EXTENSION_CAPABILITY`
* `storage_error`
* `auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`
* `404` (`app_not_found`) when `slug` is unknown.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`object_invalid`) for invalid lifecycle transitions.
* `internal_error`

## 10. Validation and ordering

* All lifecycle endpoints MUST construct a complete [OperationContext](../02-architecture/services-and-apps/05-operation-context.md) before invoking managers.
* Missing or invalid payloads MUST be rejected before any manager mutation.
* App Manager MUST enforce the lifecycle transitions described in [03-app-backend-extensions.md](../02-architecture/services-and-apps/03-app-backend-extensions.md).

## 11. Forbidden behaviors

* Creating app identities or schemas outside the register endpoint.
* Enabling or disabling apps without App Manager state transitions.
