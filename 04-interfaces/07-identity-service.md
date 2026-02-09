



# 07 Identity Service Interface

Defines identity and relationship service surfaces implied by the Identity & Relationship Service (IRS) specification. This document formalizes required routes and payload shapes.

For the meta specifications, see [07-identity-service meta](../10-appendix/meta/04-interfaces/07-identity-service-meta.md).

## 1. Purpose and scope

IRS provides identity lifecycle, contact invitations, and capability delegation within `app_0`. All endpoints require authenticated [OperationContext](../02-architecture/services-and-apps/05-operation-context.md) and capability intent as described in [02-system-services.md](../02-architecture/services-and-apps/02-system-services.md). Endpoints are local-only.

## 2. Endpoint index

| Route | Method | Auth | Summary |
| --- | --- | --- | --- |
| `/system/identity/identities` | POST | Required | Create or update an identity. |
| `/system/identity/devices` | POST | Required | Link a device to an identity. |
| `/system/identity/invites` | POST | Required | Issue a contact invite. |
| `/system/identity/invites/accept` | POST | Required | Accept a contact invite. |
| `/system/identity/capabilities/grant` | POST | Required | Grant a capability edge. |
| `/system/identity/capabilities/revoke` | POST | Required | Revoke a capability edge. |
| `/system/identity/directory` | GET | Required | Query directory entries. |

## 2.1 Identity object schema

Unknown fields are rejected.

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `handle` | Yes | string | 1-64 chars, lowercase `[a-z0-9_]+`. |
| `display_name` | No | string | 1-128 chars. |
| `public_key` | Yes | string | base64, 32-512 bytes decoded. |

## 2.2 Device object schema

Unknown fields are rejected.

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `device_name` | Yes | string | 1-64 chars. |
| `device_fingerprint` | Yes | string | hex string, 16-128 chars. |
| `key_fingerprint` | Yes | string | hex string, 16-128 chars. |
| `device_type` | No | string | 1-32 chars. |

## 2.3 Device attestation schema

Unknown fields are rejected.

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `device_fingerprint` | Yes | string | hex string, 16-128 chars. |
| `key_fingerprint` | Yes | string | hex string, 16-128 chars. |
| `proof` | Yes | object | See invite proof schema (2.5). |

## 2.4 Invite target schema

Unknown fields are rejected.

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `handle` | Yes | string | 1-64 chars, lowercase `[a-z0-9_]+`. |
| `public_key` | Yes | string | base64, 32-512 bytes decoded. |

## 2.5 Invite proof schema

Unknown fields are rejected.

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `proof_type` | Yes | string | Must equal `device_signature_v1`. |
| `payload_b64` | Yes | string | base64, 32-4096 bytes decoded. |
| `issued_at` | Yes | string | RFC3339 timestamp. |
| `expires_at` | Yes | string | RFC3339 timestamp. |

## 2.6 Directory result schema

Unknown fields are rejected.

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `identity_id` | Yes | string | Parent id. |
| `handle` | Yes | string | 1-64 chars. |
| `display_name` | No | string | 1-128 chars. |

## 3. POST /system/identity/identities

Request body:

```
{
  "identity": {
    "handle": "<string>",
    "display_name": "<string>",
    "public_key": "<base64>"
  },
  "device": {
    "device_name": "<string>",
    "device_fingerprint": "<hex>",
    "key_fingerprint": "<hex>",
    "device_type": "<string>"
  }
}
```

Response:

```
{
  "identity_id": "<parent_id>",
  "device_id": "<parent_id>",
  "global_seq": <int>
}
```

Errors:

* `ERR_IDENTITY_CONTACT_LIMIT`
* `ERR_IDENTITY_CAPABILITY`
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for persistence failures.
* `401` (`auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) for authentication failures.

## 4. POST /system/identity/devices

Request body:

```
{
  "identity_id": "<parent_id>",
  "device_attestation": {
    "device_fingerprint": "<hex>",
    "key_fingerprint": "<hex>",
    "proof": {
      "proof_type": "device_signature_v1",
      "payload_b64": "<base64>",
      "issued_at": "<rfc3339>",
      "expires_at": "<rfc3339>"
    }
  }
}
```

Response:

```
{
  "device_id": "<parent_id>",
  "global_seq": <int>
}
```

Errors:

* `ERR_IDENTITY_CAPABILITY`
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`identifier_invalid`) for malformed `identity_id`.
* `400` (`object_invalid`) when `identity_id` does not resolve to an identity.
* `400` (`storage_error`) for persistence failures.
* `401` (`auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) for authentication failures.
* `auth_invalid` for invalid or expired attestation proof.

## 5. POST /system/identity/invites

Request body:

```
{
  "target": {
    "handle": "<string>",
    "public_key": "<base64>"
  },
  "capabilities": ["system.identity.contact"],
  "expires_at": "<rfc3339>"
}
```

Response:

```
{
  "invite_token": "<string>",
  "expires_at": "<rfc3339>"
}
```

Errors:

* `ERR_IDENTITY_CAPABILITY`
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for persistence failures.
* `401` (`auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) for authentication failures.

## 6. POST /system/identity/invites/accept

Request body:

```
{
  "invite_token": "<string>",
  "proof": {
    "proof_type": "device_signature_v1",
    "payload_b64": "<base64>",
    "issued_at": "<rfc3339>",
    "expires_at": "<rfc3339>"
  }
}
```

Response:

```
{"ok": true}
```

Errors:

* `ERR_IDENTITY_CAPABILITY`
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`object_invalid`) when `invite_token` does not resolve to an invite.
* `410 Gone` when invite is expired.
* `ERR_INVITE_EXPIRED` with `ErrorDetail.category` `auth` when invite is expired.
* `400` (`storage_error`) for persistence failures.
* `401` (`auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) for authentication failures.
* `auth_invalid` for invalid or expired invite proof.

## 7. POST /system/identity/capabilities/grant

Request body:

```
{
  "target_identity_id": "<parent_id>",
  "capability": "<string>",
  "expires_at": "<rfc3339>"
}
```

Response:

```
{"ok": true}
```

Errors:

* `ERR_IDENTITY_CAPABILITY`
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`identifier_invalid`) for malformed `target_identity_id`.
* `400` (`object_invalid`) when `target_identity_id` does not resolve to an identity.
* `400` (`storage_error`) for persistence failures.
* `401` (`auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) for authentication failures.

## 8. POST /system/identity/capabilities/revoke

Request body:

```
{
  "target_identity_id": "<parent_id>",
  "capability": "<string>"
}
```

Response:

```
{"ok": true}
```

Errors:

* `ERR_IDENTITY_CAPABILITY`
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`identifier_invalid`) for malformed `target_identity_id`.
* `400` (`object_invalid`) when `target_identity_id` does not resolve to an identity.
* `400` (`storage_error`) for persistence failures.
* `401` (`auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) for authentication failures.

## 9. GET /system/identity/directory

Query parameters:

* `handle`
* `capability`
* `trust_state`
* `device_status`

Rules:

* All parameters are optional; unknown parameters are rejected.
* `handle` is 1-64 chars; `capability` is 1-64 chars; `trust_state` and `device_status` are 1-32 chars.

Response:

```
{
  "results": [
    {
      "identity_id": "<parent_id>",
      "handle": "<string>",
      "display_name": "<string>"
    }
  ],
  "next_cursor": "<string>"
}
```

Errors:

* `ERR_IDENTITY_CAPABILITY`
* `400` (`envelope_invalid`) for malformed query parameters.
* `400` (`storage_error`) for directory read failures.
* `401` (`auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) for authentication failures.

## 10. Validation and ordering

* Every endpoint MUST construct a complete [OperationContext](../02-architecture/services-and-apps/05-operation-context.md).
* Missing capability MUST reject with `ERR_IDENTITY_CAPABILITY`.
* Contact limits MUST reject with `ERR_IDENTITY_CONTACT_LIMIT`.

## 11. Forbidden behaviors

* Creating identities without schema validation.
* Delegating capabilities without ACL authorization.
