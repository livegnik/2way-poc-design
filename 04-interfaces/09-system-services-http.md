



# 09 System Services HTTP Interfaces

Defines the HTTP interfaces for mandatory system services. This document formalizes the routes enumerated in system service specifications and the required payload shapes for PoC implementation.

For the meta specifications, see [09-system-services-http meta](../10-appendix/meta/04-interfaces/09-system-services-http-meta.md).

## 1. Purpose and scope

This document specifies local-only HTTP contracts for system services under `/system/*`. All endpoints require a complete [OperationContext](../02-architecture/services-and-apps/05-operation-context.md) and must follow the manager ordering and fail-closed rules defined in [02-architecture/services-and-apps/02-system-services.md](../02-architecture/services-and-apps/02-system-services.md).

## 2. Endpoint index

| Service | Route | Method | Auth | Summary |
| --- | --- | --- | --- | --- |
| Setup Service | `/system/bootstrap/install` | POST | Required | First-run installation and bootstrap. |
| Setup Service | `/system/bootstrap/invites` | POST | Required | Issue a bootstrap invite token. |
| Setup Service | `/system/bootstrap/devices` | POST | Required | Enroll a device using an invite. |
| Setup Service | `/system/bootstrap/recover` | POST | Required | Rotate bootstrap secrets or reset ACL templates. |
| Identity Service | `/system/identity/identities` | POST | Required | Create or update an identity. |
| Identity Service | `/system/identity/devices` | POST | Required | Link a device to an identity. |
| Identity Service | `/system/identity/invites` | POST | Required | Issue a contact invite. |
| Identity Service | `/system/identity/invites/accept` | POST | Required | Accept a contact invite. |
| Identity Service | `/system/identity/capabilities/grant` | POST | Required | Grant a capability to an identity. |
| Identity Service | `/system/identity/capabilities/revoke` | POST | Required | Revoke a capability from an identity. |
| Identity Service | `/system/identity/directory` | GET | Required | Directory query by handle/capability/trust. |
| Sync Service | `/system/sync/peers` | GET | Required | List peers with sync status. |
| Sync Service | `/system/sync/plans` | POST | Required | Submit or update a sync plan. |
| Sync Service | `/system/sync/peers/{peer_id}/pause` | POST | Required | Pause peer sync. |
| Sync Service | `/system/sync/peers/{peer_id}/resume` | POST | Required | Resume peer sync. |
| Sync Service | `/system/sync/diagnostics` | POST | Required | Trigger sync diagnostics package. |
| Admin Service | `/system/ops/health` | GET | Required (admin) | Aggregated readiness/liveness snapshot. |
| Admin Service | `/system/ops/config` | GET | Required (admin) | Export sanitized configuration. |
| Admin Service | `/system/ops/service-toggles` | POST | Required (admin) | Enable or disable services. |
| Admin Service | `/system/ops/capabilities` | POST | Required (admin) | Delegate capabilities via Identity Service. |
| Admin Service | `/system/ops/audit/logs` | GET | Required (admin) | Query structured logs. |
| Admin Service | `/system/ops/app-services/{slug}/diagnostics` | POST | Required (admin) | app service diagnostics dump. |
| Admin Service | `/system/ops/clients/telemetry` | POST | Required (admin) | Ingest client telemetry aggregates. |

## 2.1 System service error-family legend

System service routes MUST emit parent-scoped codes. Legacy singleton roots such as `ERR_APP_SYS_*` are forbidden.

| Family | Parent owner | Meaning |
| --- | --- | --- |
| `ERR_SVC_SYS_SETUP_*` | Setup Service | Bootstrap/install/invite/device/recovery checks rejected by Setup Service. |
| `ERR_SVC_SYS_IDENTITY_*` | Identity Service | Identity/contact/capability policy checks rejected by Identity Service. |
| `ERR_SVC_SYS_SYNC_*` | Sync Service | Sync plan or sync service-specific validation rejected by Sync Service. |
| `ERR_SVC_SYS_OPS_*` | Admin/Ops Service | Admin operations or ops config/capability checks rejected by Ops Service. |
| `ERR_SVC_SYS_*` availability codes | Any system service | Service exists but is unavailable (`disabled`, `not_ready`, `dependency_unavailable`, `draining`, `load_failed`). |
| `ERR_MNG_<MANAGER>_*` | Manager layer | Manager-owned errors; typically normalized unless an interface contract exposes them directly. |

## 3. Common requirements

* All endpoints MUST construct a complete [OperationContext](../02-architecture/services-and-apps/05-operation-context.md) before invoking managers.
* Missing required fields MUST be rejected before any manager mutation.
* All responses MUST use the canonical `ErrorDetail` shape from [04-error-model.md](04-error-model.md).
* All endpoints are local-only and MUST NOT be exposed to untrusted networks.

Common errors (all endpoints):

* `401` (`auth_required`, `auth_invalid`) when authentication fails.
* `401` (`ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) when auth token is expired or revoked.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`envelope_invalid`) when required [OperationContext](../02-architecture/services-and-apps/05-operation-context.md) fields are missing.
* `400` (`network_rejected`) when [Network Manager](../02-architecture/managers/10-network-manager.md) is not ready for network-coupled work.
* `503` with one of `ERR_SVC_SYS_NOT_READY`, `ERR_SVC_SYS_DISABLED`, `ERR_SVC_SYS_DEPENDENCY_UNAVAILABLE`, `ERR_SVC_SYS_DRAINING`, `ERR_SVC_SYS_LOAD_FAILED` when the targeted system service is unavailable.
* DoS Guard challenges are not issued on these local HTTP endpoints; admission failures are surfaced as `network_rejected`.
* `500` (`internal_error`) for internal failures.

## 4. Setup Service endpoints

### 4.1 POST /system/bootstrap/install

Request body:

```
{
  "bootstrap_token": "<string>",
  "node": {
    "name": "<string>",
    "metadata": {"environment": "<string>"},
    "storage_path_confirmation": "<string>"
  },
  "admin": {
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
    },
    "recovery": {
      "recovery_key_fingerprint": "<hex>",
      "recovery_public_key": "<base64>",
      "recovery_hint": "<string>"
    }
  }
}
```

Rules:

* `bootstrap_token` MUST be present and valid.
* `node.name` MUST be present.
* `admin.identity` and `admin.device` payloads MUST be present; their internal schemas are defined in [02-system-services.md](../02-architecture/services-and-apps/02-system-services.md#721-Bootstrap-install-payload-schemas-app_0).
* Payloads are signed locally and MUST NOT be accepted from remote transport.
* Unknown fields are rejected at all levels except `node.metadata`, which is an opaque JSON object (max 4096 bytes when UTF-8 encoded).

Response (success):

```
{
  "node_id": "<parent_id>",
  "admin_identity_id": "<parent_id>",
  "admin_device_id": "<parent_id>",
  "global_seq": <int>
}
```

Errors:

* `ERR_SVC_SYS_SETUP_SCHEMA`, `ERR_SVC_SYS_SETUP_ACL`, `ERR_SVC_SYS_SETUP_DEVICE_ATTESTATION`.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for persistence failures.

Additional rules:

* Invalid or expired `bootstrap_token` MUST return `ERR_SVC_SYS_SETUP_ACL`.
* `storage_path_confirmation` mismatch MUST return `ERR_SVC_SYS_SETUP_SCHEMA`.
* If the node is already installed, the request MUST return `ERR_SVC_SYS_SETUP_ACL`.

### 4.2 POST /system/bootstrap/invites

Request body:

```
{
  "capabilities": ["system.bootstrap.device"],
  "expires_at": "<rfc3339>",
  "metadata": {"note": "<string>"}
}
```

Rules:

* `identity` and `device` schemas are defined in [07-identity-service.md](07-identity-service.md#22-Identity-object-schema).
* Unknown fields are rejected.

Response:

```
{
  "invite_token": "<string>",
  "expires_at": "<rfc3339>"
}
```

Rules:

* `capabilities` is a non-empty array of strings (1-64 chars each, max 32 entries).
* `expires_at` is required and must be RFC3339.
* `metadata` is optional, opaque JSON object (max 2048 bytes UTF-8); unknown fields rejected outside `metadata`.

Errors:

* `ERR_SVC_SYS_SETUP_ACL` when the caller lacks bootstrap invite capability.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for persistence failures.
* `400` (`config_invalid`) when `service.bootstrap.max_pending_invites` is exceeded.

### 4.3 POST /system/bootstrap/devices

Request body:

```
{
  "invite_token": "<string>",
  "capabilities": ["system.bootstrap.device"],
  "device_attestation": {
    "device_fingerprint": "<string>",
    "key_fingerprint": "<string>",
    "proof": {
      "proof_type": "device_signature_v1",
      "payload_b64": "<base64>",
      "issued_at": "<rfc3339>",
      "expires_at": "<rfc3339>"
    }
  }
}
```

Rules:

* `device_attestation` schema is defined in [07-identity-service.md](07-identity-service.md#24-Device-attestation-schema).
* Unknown fields are rejected.

Response:

```
{
  "device_id": "<parent_id>",
  "identity_id": "<parent_id>",
  "global_seq": <int>
}
```

Errors:

* `410 Gone` when invite is expired.
* `ERR_SVC_SYS_SETUP_DEVICE_ATTESTATION` on attestation failure.
* `ERR_AUTH_INVITE_EXPIRED` with `ErrorDetail.category` `auth` when invite is expired.
* `ERR_SVC_SYS_SETUP_ACL` when the invite lacks `system.bootstrap.device`.
* `400` (`object_invalid`) when `invite_token` does not resolve to a pending invite.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for persistence failures.

Rules:

* `device_attestation.proof` is required and unknown fields are rejected.
* `payload_b64` is base64 with 32-4096 bytes decoded.
* `issued_at` and `expires_at` must be RFC3339; expired proofs are rejected with `ERR_SVC_SYS_SETUP_DEVICE_ATTESTATION`.

### 4.4 POST /system/bootstrap/recover

Request body:

```
{
  "rotate_bootstrap_secrets": true,
  "reset_acl_templates": true,
  "revoke_invites": true
}
```

Response:

```
{"ok": true}
```

Errors:

* `ERR_SVC_SYS_SETUP_ACL` when the caller lacks bootstrap recovery capability.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for persistence failures.

## 5. Identity Service endpoints

### 5.1 POST /system/identity/identities

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

* `ERR_SVC_SYS_IDENTITY_CONTACT_LIMIT`
* `ERR_SVC_SYS_IDENTITY_CAPABILITY`
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for persistence failures.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

### 5.2 POST /system/identity/devices

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

* `ERR_SVC_SYS_IDENTITY_CAPABILITY`
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`identifier_invalid`) for malformed `identity_id`.
* `400` (`object_invalid`) when `identity_id` does not resolve to an identity.
* `400` (`storage_error`) for persistence failures.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.
* `auth_invalid` for invalid or expired attestation proof.

### 5.3 POST /system/identity/invites

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

Rules:

* `target` schema is defined in [07-identity-service.md](07-identity-service.md#25-Invite-target-schema).
* `capabilities` is a non-empty array of strings (1-64 chars each, max 32 entries).
* `expires_at` is required and must be RFC3339.
* Unknown fields are rejected.

Errors:

* `ERR_SVC_SYS_IDENTITY_CAPABILITY`
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for persistence failures.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

### 5.4 POST /system/identity/invites/accept

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

Rules:

* `proof` schema is defined in [07-identity-service.md](07-identity-service.md#26-Invite-proof-schema).
* Unknown fields are rejected.

Errors:

* `ERR_SVC_SYS_IDENTITY_CAPABILITY`
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`object_invalid`) when `invite_token` does not resolve to an invite.
* `410 Gone` when invite is expired.
* `ERR_AUTH_INVITE_EXPIRED` with `ErrorDetail.category` `auth` when invite is expired.
* `400` (`storage_error`) for persistence failures.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.
* `auth_invalid` for invalid or expired invite proof.

### 5.5 POST /system/identity/capabilities/grant

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
* `ERR_SVC_SYS_IDENTITY_CAPABILITY`
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`identifier_invalid`) for malformed `target_identity_id`.
* `400` (`object_invalid`) when `target_identity_id` does not resolve to an identity.
* `400` (`storage_error`) for persistence failures.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

### 5.6 POST /system/identity/capabilities/revoke

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

* `ERR_SVC_SYS_IDENTITY_CAPABILITY`
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`identifier_invalid`) for malformed `target_identity_id`.
* `400` (`object_invalid`) when `target_identity_id` does not resolve to an identity.
* `400` (`storage_error`) for persistence failures.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

### 5.7 GET /system/identity/directory

Query parameters:

* `handle`
* `capability`
* `trust_state`
* `device_status`

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

Rules:

* `results` entries follow the schema in [07-identity-service.md](07-identity-service.md#27-Directory-result-schema).
* `next_cursor` is optional.
* All parameters are optional; unknown parameters are rejected.
* `handle` is 1-64 chars; `capability` is 1-64 chars; `trust_state` and `device_status` are 1-32 chars.

Errors:

* `ERR_SVC_SYS_IDENTITY_CAPABILITY`
* `400` (`envelope_invalid`) for malformed query parameters.
* `400` (`storage_error`) for directory read failures.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

## 6. Sync Service endpoints

### 6.1 GET /system/sync/peers

Response:

```
{
  "peers": [
    {
      "peer_id": "<string>",
      "status": "<string>",
      "last_success_seq": <int>
    }
  ]
}
```

Errors:

* `400` (`acl_denied`) when the caller lacks sync permissions.
* `400` (`storage_error`) for State Manager read failures.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

### 6.2 POST /system/sync/plans

Request body:

```
{
  "peer_id": "<string>",
  "domains": ["<domain_id>"],
  "from_seq": <int>,
  "to_seq": <int>
}
```

Response:

```
{"ok": true}
```

Errors:

* `ERR_SVC_SYS_SYNC_PLAN_INVALID`
* `400` (`identifier_invalid`) for malformed `peer_id`.
* `400` (`object_invalid`) when `peer_id` does not resolve to a peer.
* `400` (`acl_denied`) when the caller lacks sync permissions for the peer or domain.
* `400` (`sequence_error`) for ordering or range violations.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for State Manager persistence failures.

### 6.3 POST /system/sync/peers/{peer_id}/pause

Response:

```
{"ok": true}
```

Errors:

* `400` (`identifier_invalid`) for malformed `peer_id`.
* `400` (`object_invalid`) when `peer_id` does not resolve to a peer.
* `400` (`sequence_error`) for invalid pause transitions.
* `400` (`acl_denied`) when the caller lacks sync permissions.
* `400` (`storage_error`) for State Manager persistence failures.

### 6.4 POST /system/sync/peers/{peer_id}/resume

Response:

```
{"ok": true}
```

Errors:

* `400` (`identifier_invalid`) for malformed `peer_id`.
* `400` (`object_invalid`) when `peer_id` does not resolve to a peer.
* `400` (`sequence_error`) for invalid resume transitions.
* `400` (`acl_denied`) when the caller lacks sync permissions.
* `400` (`storage_error`) for State Manager persistence failures.

### 6.5 POST /system/sync/diagnostics

Request body:

```
{
  "peer_id": "<string>",
  "include_failures": true
}
```

Response:

```
{
  "diagnostics_id": "<string>"
}
```

Rules:

* Unknown fields are rejected.
* `peer_id` is 1-64 chars.
* `include_failures` is optional boolean; if omitted, it is treated as `false`.

Errors:

* `ERR_SVC_SYS_SYNC_PLAN_INVALID` for structural plan validation failures.
* `400` (`identifier_invalid`) for malformed `peer_id`.
* `400` (`object_invalid`) when `peer_id` does not resolve to a peer.
* `400` (`acl_denied`) when the caller lacks sync permissions for the peer or domain.
* `400` (`sequence_error`) for ordering or range violations.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for State Manager persistence failures.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

## 7. Admin Service endpoints

Admin Service routes are exposed only when `service.ops.admin_routes_enabled` is true. When disabled, all `/system/ops/*` routes MUST reject requests.
When disabled, all `/system/ops/*` routes return `503` with `ERR_SVC_SYS_DISABLED`.

### 7.1 GET /system/ops/health

Response schema: see [11-ops-http.md](11-ops-http.md).

Errors:

* `ERR_SVC_SYS_OPS_CAPABILITY`
* `401` (`auth_required`, `auth_invalid`) for authentication failures.
* `500` (`internal_error`) when Health Manager is unavailable or the snapshot cannot be served.

### 7.2 GET /system/ops/config

Response schema: see [11-ops-http.md](11-ops-http.md).

Errors:

* `ERR_SVC_SYS_OPS_CAPABILITY`
* `ERR_SVC_SYS_OPS_CONFIG_ACCESS`
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

### 7.3 POST /system/ops/service-toggles

Request body:

```
{
  "service": "<string>",
  "enabled": true
}
```

Response:

```
{"ok": true}
```

Rules:

* Unknown fields are rejected.
* `service` is 1-64 chars, lowercase `[a-z0-9_]+`.
* `enabled` is boolean.
* Unknown `service` values are rejected.

Errors:

* `ERR_SVC_SYS_OPS_CAPABILITY`
* `400` (`envelope_invalid`) when `service` does not resolve to a known service.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`config_invalid`) for Config Manager validation failures, vetoes, or queue overflow.
* `400` (`storage_error`) for Config Manager persistence failures.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

### 7.4 POST /system/ops/capabilities

Request body:

```
{
  "target_identity_id": "<parent_id>",
  "capability": "<string>",
  "action": "grant|revoke"
}
```

Response:

```
{"ok": true}
```

Rules:

* Unknown fields are rejected.
* `target_identity_id` is a parent id.
* `capability` is 1-64 chars.
* `action` must be `grant` or `revoke`.

Errors:

* `ERR_SVC_SYS_OPS_CAPABILITY`
* `ERR_SVC_SYS_IDENTITY_CAPABILITY`
* `400` (`identifier_invalid`) for malformed `target_identity_id`.
* `400` (`object_invalid`) when `target_identity_id` does not resolve to an identity.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for Identity Service persistence failures.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

### 7.5 GET /system/ops/audit/logs

Query parameters:

* `class` (required): `audit`, `security`, `operational`, or `diagnostic`
* `limit`
* `cursor`
* `since`

Response:

```
{
  "records": [
    {
      "timestamp": "<rfc3339>",
      "severity": "<string>",
      "class": "<string>",
      "component": "<string>",
      "message": "<string>",
      "trace_id": "<string>",
      "data": { },
      "global_seq": <int>,
      "actor_identity_id": "<parent_id>"
    }
  ],
  "next_cursor": "<string>"
}
```

Rules:

* Unknown fields are rejected.
* `severity` is one of `debug`, `info`, `warn`, `error`, `critical`.
* `data` is an opaque JSON object (max 4096 bytes UTF-8).
* `trace_id`, `global_seq`, and `actor_identity_id` are optional.
* Records are ordered newest-first.

Errors:

* `ERR_SVC_SYS_OPS_CAPABILITY`
* `ERR_SVC_SYS_OPS_CONFIG_ACCESS`
* `400` (`envelope_invalid`) for malformed query parameters or missing/invalid `class`.
* `400` (`storage_error`) for log read failures.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

### 7.6 POST /system/ops/app-services/{slug}/diagnostics

Response:

```
{
  "snapshot": {
    "slug": "<string>",
    "generated_at": "<rfc3339>",
    "status": "<string>",
    "checks": [
      {
        "name": "<string>",
        "status": "<string>",
        "message": "<string>"
      }
    ]
  }
}
```

Rules:

* Unknown fields are rejected.
* `slug` is 1-64 chars, lowercase `[a-z0-9_]+`.
* `generated_at` is RFC3339.
* `status` is one of `ok`, `warning`, `failed`.
* `checks` is 0-128 entries.
* Each `checks[].name` is 1-64 chars; `checks[].status` is one of `ok`, `warning`, `failed`; `checks[].message` is 0-256 chars.

Errors:

* `ERR_SVC_SYS_OPS_CAPABILITY`
* `404` (`app_not_found`) when `slug` does not resolve to an installed app service.
* `400` (`envelope_invalid`) for malformed payloads.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

### 7.7 POST /system/ops/clients/telemetry

Request/response schema: see [11-ops-http.md](11-ops-http.md).

Errors:

* `ERR_SVC_SYS_OPS_CAPABILITY`
* `400` (`storage_error`) for ingestion or persistence failures.
* `400` (`envelope_invalid`) for malformed payloads.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.
* `500` (`internal_error`) for internal failures.

## 8. Validation and ordering

* Structural validation occurs before schema, ACL, or persistence.
* Schema validation occurs before ACL evaluation.
* ACL evaluation occurs before persistence.
* All failures are returned without partial state changes.

## 9. Forbidden behaviors

* Accepting requests without a valid [OperationContext](../02-architecture/services-and-apps/05-operation-context.md).
* Bypassing [Graph Manager](../02-architecture/managers/07-graph-manager.md) for any mutation.
