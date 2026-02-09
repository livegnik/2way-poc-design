



# 09 System Services HTTP Interfaces

Defines the HTTP interfaces for mandatory system services. This document formalizes the routes enumerated in system service specifications and the required payload shapes for PoC implementation.

For the meta specifications, see [09-system-services-http meta](../10-appendix/meta/04-interfaces/09-system-services-http-meta.md).

## 1. Purpose and scope

This document specifies local-only HTTP contracts for system services under `/system/*`. All endpoints require a complete [OperationContext](../02-architecture/services-and-apps/05-operation-context.md) and must follow the manager ordering and fail-closed rules defined in [02-architecture/services-and-apps/02-system-services.md](../02-architecture/services-and-apps/02-system-services.md).

## 2. Endpoint index

| Service | Route | Method | Auth | Summary |
| --- | --- | --- | --- | --- |
| SBPS | `/system/bootstrap/install` | POST | Required | First-run installation and bootstrap. |
| SBPS | `/system/bootstrap/invites` | POST | Required | Issue a bootstrap invite token. |
| SBPS | `/system/bootstrap/devices` | POST | Required | Enroll a device using an invite. |
| SBPS | `/system/bootstrap/recover` | POST | Required | Rotate bootstrap secrets or reset ACL templates. |
| IRS | `/system/identity/identities` | POST | Required | Create or update an identity. |
| IRS | `/system/identity/devices` | POST | Required | Link a device to an identity. |
| IRS | `/system/identity/invites` | POST | Required | Issue a contact invite. |
| IRS | `/system/identity/invites/accept` | POST | Required | Accept a contact invite. |
| IRS | `/system/identity/capabilities/grant` | POST | Required | Grant a capability to an identity. |
| IRS | `/system/identity/capabilities/revoke` | POST | Required | Revoke a capability from an identity. |
| IRS | `/system/identity/directory` | GET | Required | Directory query by handle/capability/trust. |
| BFS | `/system/feed/threads` | POST | Required | Create a feed thread. |
| BFS | `/system/feed/messages` | POST | Required | Append a message to a thread. |
| BFS | `/system/feed/reactions` | POST | Required | Add a reaction rating. |
| BFS | `/system/feed/moderations` | POST | Required | Submit a moderation rating. |
| BFS | `/system/feed/threads` | GET | Required | Read aggregated feed threads. |
| SOS | `/system/sync/peers` | GET | Required | List peers with sync status. |
| SOS | `/system/sync/plans` | POST | Required | Submit or update a sync plan. |
| SOS | `/system/sync/peers/{peer_id}/pause` | POST | Required | Pause peer sync. |
| SOS | `/system/sync/peers/{peer_id}/resume` | POST | Required | Resume peer sync. |
| SOS | `/system/sync/diagnostics` | POST | Required | Trigger sync diagnostics package. |
| OCS | `/system/ops/health` | GET | Required (admin) | Aggregated readiness/liveness snapshot. |
| OCS | `/system/ops/config` | GET | Required (admin) | Export sanitized configuration. |
| OCS | `/system/ops/service-toggles` | POST | Required (admin) | Enable or disable services. |
| OCS | `/system/ops/capabilities` | POST | Required (admin) | Delegate capabilities via IRS. |
| OCS | `/system/ops/audit/logs` | GET | Required (admin) | Query structured logs. |
| OCS | `/system/ops/extensions/{slug}/diagnostics` | POST | Required (admin) | Extension diagnostics dump. |
| OCS | `/system/ops/clients/telemetry` | POST | Required (admin) | Ingest client telemetry aggregates. |

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
* `500` (`internal_error`) for internal failures.

## 4. SBPS endpoints

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

* `ERR_BOOTSTRAP_SCHEMA`, `ERR_BOOTSTRAP_ACL`, `ERR_BOOTSTRAP_DEVICE_ATTESTATION`.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for persistence failures.

Additional rules:

* Invalid or expired `bootstrap_token` MUST return `ERR_BOOTSTRAP_ACL`.
* `storage_path_confirmation` mismatch MUST return `ERR_BOOTSTRAP_SCHEMA`.
* If the node is already installed, the request MUST return `ERR_BOOTSTRAP_ACL`.

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

* `ERR_BOOTSTRAP_ACL` when the caller lacks bootstrap invite capability.
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
* `ERR_BOOTSTRAP_DEVICE_ATTESTATION` on attestation failure.
* `ERR_INVITE_EXPIRED` with `ErrorDetail.category` `auth` when invite is expired.
* `ERR_BOOTSTRAP_ACL` when the invite lacks `system.bootstrap.device`.
* `400` (`object_invalid`) when `invite_token` does not resolve to a pending invite.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for persistence failures.

Rules:

* `device_attestation.proof` is required and unknown fields are rejected.
* `payload_b64` is base64 with 32-4096 bytes decoded.
* `issued_at` and `expires_at` must be RFC3339; expired proofs are rejected with `ERR_BOOTSTRAP_DEVICE_ATTESTATION`.

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

* `ERR_BOOTSTRAP_ACL` when the caller lacks bootstrap recovery capability.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for persistence failures.

## 5. IRS endpoints

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

* `ERR_IDENTITY_CONTACT_LIMIT`
* `ERR_IDENTITY_CAPABILITY`
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

* `ERR_IDENTITY_CAPABILITY`
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

* `ERR_IDENTITY_CAPABILITY`
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

* `ERR_IDENTITY_CAPABILITY`
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`object_invalid`) when `invite_token` does not resolve to an invite.
* `410 Gone` when invite is expired.
* `ERR_INVITE_EXPIRED` with `ErrorDetail.category` `auth` when invite is expired.
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
* `ERR_IDENTITY_CAPABILITY`
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

* `ERR_IDENTITY_CAPABILITY`
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

* `ERR_IDENTITY_CAPABILITY`
* `400` (`envelope_invalid`) for malformed query parameters.
* `400` (`storage_error`) for directory read failures.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

## 6. BFS endpoints

### 6.1 POST /system/feed/threads

Request body:

```
{
  "app_id": <int>,
  "thread": {
    "title": "<string>",
    "body": "<string>"
  }
}
```

Rules:

* `thread.title` is required (1-120 chars).
* `thread.body` is optional (1-2000 chars).
* Unknown fields are rejected.

Errors:

* `ERR_FEED_CAPABILITY`
* `acl_denied`
* `storage_error`
* `config_invalid` when `service.feed.max_threads_per_app` is exceeded.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`identifier_invalid`) for malformed `app_id`.
* `400` (`schema_validation_failed`) when `app_id` does not resolve to a feed-enabled app.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

Response:

```
{
  "thread_id": "<parent_id>",
  "global_seq": <int>
}
```

Errors:

* `ERR_FEED_CAPABILITY`

### 6.2 POST /system/feed/messages

Request body:

```
{
  "app_id": <int>,
  "thread_id": "<parent_id>",
  "message": {
    "body": "<string>"
  }
}
```

Rules:

* `message.body` is required (1-2000 chars).
* Unknown fields are rejected.

Errors:

* `ERR_FEED_CAPABILITY`
* `acl_denied`
* `storage_error`
* `config_invalid` when `service.feed.max_replies_per_thread` is exceeded.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`identifier_invalid`) for malformed `app_id` or `thread_id`.
* `400` (`object_invalid`) when `thread_id` does not resolve to a thread.
* `400` (`schema_validation_failed`) when `app_id` does not resolve to a feed-enabled app.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

Response:

```
{
  "message_id": "<attr_id>",
  "global_seq": <int>
}
```

### 6.3 POST /system/feed/reactions

Request body:

```
{
  "app_id": <int>,
  "target_parent_id": "<parent_id>",
  "reaction": {
    "value": <int>
  }
}
```

Rules:

* `reaction.value` is required and must be -1, 0, or 1.
* Unknown fields are rejected.

Errors:

* `ERR_FEED_CAPABILITY`
* `acl_denied`
* `storage_error`
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`identifier_invalid`) for malformed `app_id` or `target_parent_id`.
* `400` (`object_invalid`) when `target_parent_id` does not resolve to a target.
* `400` (`schema_validation_failed`) when `app_id` does not resolve to a feed-enabled app.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

Response:

```
{
  "reaction_id": "<rating_id>",
  "global_seq": <int>
}
```

### 6.4 POST /system/feed/moderations

Request body:

```
{
  "app_id": <int>,
  "target_parent_id": "<parent_id>",
  "moderation": {
    "value": <int>,
    "reason": "<string>"
  }
}
```

Rules:

* `moderation.value` is required and must be -1, 0, or 1.
* `moderation.reason` is optional (1-256 chars).
* Unknown fields are rejected.

Errors:

* `ERR_FEED_CAPABILITY`
* `acl_denied`
* `storage_error`
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`identifier_invalid`) for malformed `app_id` or `target_parent_id`.
* `400` (`object_invalid`) when `target_parent_id` does not resolve to a target.
* `400` (`schema_validation_failed`) when `app_id` does not resolve to a feed-enabled app.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

Response:

```
{
  "moderation_id": "<rating_id>",
  "global_seq": <int>
}
```

### 6.5 GET /system/feed/threads

Query parameters:

* `app_id` (required)
* `cursor` (optional)
* `limit` (optional)

Response:

```
{
  "items": [
    {
      "thread_id": "<parent_id>",
      "title": "<string>",
      "last_updated_at": "<rfc3339>"
    }
  ],
  "next_cursor": "<string>"
}
```

Rules:

* `items` entries include `thread_id`, `title`, `last_updated_at`.
* `next_cursor` is optional.

Errors:

* `ERR_FEED_CAPABILITY`
* `acl_denied`
* `storage_error`
* `400` (`envelope_invalid`) for malformed query parameters.
* `400` (`identifier_invalid`) for malformed `app_id`.
* `400` (`schema_validation_failed`) when `app_id` does not resolve to a feed-enabled app.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

## 7. SOS endpoints

### 7.1 GET /system/sync/peers

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

### 7.2 POST /system/sync/plans

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

* `ERR_SYNC_PLAN_INVALID`
* `400` (`identifier_invalid`) for malformed `peer_id`.
* `400` (`object_invalid`) when `peer_id` does not resolve to a peer.
* `400` (`acl_denied`) when the caller lacks sync permissions for the peer or domain.
* `400` (`sequence_error`) for ordering or range violations.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for State Manager persistence failures.

### 7.3 POST /system/sync/peers/{peer_id}/pause

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

### 7.4 POST /system/sync/peers/{peer_id}/resume

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

### 7.5 POST /system/sync/diagnostics

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

* `ERR_SYNC_PLAN_INVALID` for structural plan validation failures.
* `400` (`identifier_invalid`) for malformed `peer_id`.
* `400` (`object_invalid`) when `peer_id` does not resolve to a peer.
* `400` (`acl_denied`) when the caller lacks sync permissions for the peer or domain.
* `400` (`sequence_error`) for ordering or range violations.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for State Manager persistence failures.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

## 8. OCS endpoints

OCS routes are exposed only when `service.ops.admin_routes_enabled` is true. When disabled, all `/system/ops/*` routes MUST reject requests.
When disabled, all `/system/ops/*` routes return `400` with `config_invalid`.

### 8.1 GET /system/ops/health

Response schema: see [11-ops-http.md](11-ops-http.md).

Errors:

* `ERR_OPS_CAPABILITY`
* `401` (`auth_required`, `auth_invalid`) for authentication failures.
* `500` (`internal_error`) when Health Manager is unavailable or the snapshot cannot be served.

### 8.2 GET /system/ops/config

Response schema: see [11-ops-http.md](11-ops-http.md).

Errors:

* `ERR_OPS_CAPABILITY`
* `ERR_OPS_CONFIG_ACCESS`
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

### 8.3 POST /system/ops/service-toggles

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

* `ERR_OPS_CAPABILITY`
* `400` (`envelope_invalid`) when `service` does not resolve to a known service.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`config_invalid`) for Config Manager validation failures, vetoes, or queue overflow.
* `400` (`storage_error`) for Config Manager persistence failures.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

### 8.4 POST /system/ops/capabilities

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

* `ERR_OPS_CAPABILITY`
* `ERR_IDENTITY_CAPABILITY`
* `400` (`identifier_invalid`) for malformed `target_identity_id`.
* `400` (`object_invalid`) when `target_identity_id` does not resolve to an identity.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for IRS persistence failures.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

### 8.5 GET /system/ops/audit/logs

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

* `ERR_OPS_CAPABILITY`
* `ERR_OPS_CONFIG_ACCESS`
* `400` (`envelope_invalid`) for malformed query parameters or missing/invalid `class`.
* `400` (`storage_error`) for log read failures.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

### 8.6 POST /system/ops/extensions/{slug}/diagnostics

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

* `ERR_OPS_CAPABILITY`
* `404` (`app_not_found`) when `slug` does not resolve to an installed extension.
* `400` (`envelope_invalid`) for malformed payloads.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.

### 8.7 POST /system/ops/clients/telemetry

Request/response schema: see [11-ops-http.md](11-ops-http.md).

Errors:

* `ERR_OPS_CAPABILITY`
* `400` (`storage_error`) for ingestion or persistence failures.
* `400` (`envelope_invalid`) for malformed payloads.
* `401` (`auth_required`, `auth_invalid`) for authentication failures.
* `500` (`internal_error`) for internal failures.

## 9. Validation and ordering

* Structural validation occurs before schema, ACL, or persistence.
* Schema validation occurs before ACL evaluation.
* ACL evaluation occurs before persistence.
* All failures are returned without partial state changes.

## 10. Forbidden behaviors

* Accepting requests without a valid [OperationContext](../02-architecture/services-and-apps/05-operation-context.md).
* Bypassing [Graph Manager](../02-architecture/managers/07-graph-manager.md) for any mutation.
