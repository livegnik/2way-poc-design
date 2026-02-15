



# 11 Ops HTTP Interfaces

Defines the Admin Service HTTP endpoints used by administrators and authorized tooling.

For the meta specifications, see [11-ops-http meta](../10-appendix/meta/04-interfaces/11-ops-http-meta.md).

## 1. Purpose and scope

This document defines the `/system/ops/*` endpoints and the optional client telemetry endpoint referenced by frontend requirements. These routes are admin-only and require `system.ops.manage` capability unless explicitly stated otherwise.

Ops endpoints MUST be local-only.

## 2. Endpoint index

| Route | Method | Auth | Summary |
| --- | --- | --- | --- |
| `/system/ops/health` | GET | Required (admin) | Read readiness/liveness snapshot. |
| `/system/ops/config` | GET | Required (admin) | Export sanitized configuration. |
| `/system/ops/service-toggles` | POST | Required (admin) | Enable/disable services. |
| `/system/ops/capabilities` | POST | Required (admin) | Capability grant/revoke via Identity Service. |
| `/system/ops/audit/logs` | GET | Required (admin) | Query structured logs. |
| `/system/ops/app-services/{slug}/diagnostics` | POST | Required (admin) | app service diagnostics snapshot. |
| `/system/ops/clients/telemetry` | POST | Required (admin) | Ingest client telemetry aggregates. |

Ops routes are exposed only when `service.ops.admin_routes_enabled` is true. When disabled, all `/system/ops/*` routes return `503` with `ERR_SVC_SYS_DISABLED`.

## 3. GET /system/ops/health

Response:

```
{
  "snapshot": {
    "health_seq": <int>,
    "published_at": "<rfc3339>",
    "readiness": "<ready|not_ready>",
    "liveness": "<alive|dead>",
    "components": {
      "<component>": {
        "state": "<healthy|degraded|failed|unknown>",
        "reason_code": "<string>",
        "last_reported_at": "<rfc3339>"
      }
    },
    "last_transition": {
      "from": {"readiness": "<string>", "liveness": "<string>"},
      "to": {"readiness": "<string>", "liveness": "<string>"},
      "cause": "<string>"
    },
    "outputs": ["<string>"]
  }
}
```

Rules:

* Unknown fields are rejected.
* Snapshot fields follow the Health Manager structure in [13-health-manager.md](../02-architecture/managers/13-health-manager.md) Section 2.3.

Errors:

* `ERR_SVC_SYS_OPS_CAPABILITY`
* `401` (`auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) for authentication failures.
* `500` (`internal_error`) when Health Manager is unavailable or the snapshot cannot be served.

## 4. GET /system/ops/config

Response:

```
{
  "config": [
    {
      "key": "<string>",
      "value": "<string>",
      "source": "<string>",
      "redacted": <bool>
    }
  ]
}
```

Rules:

* Unknown fields are rejected.
* `key` is 1-128 chars.
* `value` is 0-2048 chars; if `redacted` is true, value MUST be `REDACTED`.
* `source` is one of `default`, `env`, `settings`, `override`.
* Export is deny-by-default; only keys explicitly marked exportable by Config Manager may appear. Secrets are redacted per export policy.

Errors:

* `ERR_SVC_SYS_OPS_CAPABILITY`
* `ERR_SVC_SYS_OPS_CONFIG_ACCESS`
* `401` (`auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) for authentication failures.
* `500` (`internal_error`) for internal failures.

## 4.1 POST /system/ops/service-toggles

Request/response schema: see [09-system-services-http.md](09-system-services-http.md).

Errors:

* `ERR_SVC_SYS_OPS_CAPABILITY`
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`config_invalid`) for Config Manager validation failures, vetoes, or queue overflow.
* `400` (`storage_error`) for Config Manager persistence failures.
* `401` (`auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) for authentication failures.
* `500` (`internal_error`) for internal failures.

## 4.2 POST /system/ops/capabilities

Request/response schema: see [09-system-services-http.md](09-system-services-http.md).

Errors:

* `ERR_SVC_SYS_OPS_CAPABILITY`
* `ERR_SVC_SYS_IDENTITY_CAPABILITY`
* `400` (`identifier_invalid`) for malformed `target_identity_id`.
* `400` (`object_invalid`) when `target_identity_id` does not resolve to an identity.
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for Identity Service persistence failures.
* `401` (`auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) for authentication failures.
* `500` (`internal_error`) for internal failures.

## 5. GET /system/ops/audit/logs

Query parameters:

* `class` (required): `audit`, `security`, `operational`, or `diagnostic`
* `limit` (optional): 1-1000
* `cursor` (optional): opaque paging token
* `since` (optional): RFC3339 timestamp

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
* `401` (`auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) for authentication failures.
* `500` (`internal_error`) for internal failures.

## 6. POST /system/ops/clients/telemetry

Request body:

```
{
  "client_id": "<string>",
  "app_id": <int>,
  "metrics": {
    "counters": { "<string>": <int> },
    "gauges": { "<string>": <number> }
  },
  "timestamp": "<rfc3339>"
}
```

Response:

```
{"ok": true}
```

Rules:

* Telemetry is advisory only and must not mutate graph state.
* Payloads are bounded and validated before ingestion.
* Unknown fields are rejected.
* `client_id` is 1-64 chars.
* `app_id` is a positive integer.
* `metrics.counters` and `metrics.gauges` keys are 1-64 chars; values are non-negative.
* At least one of `metrics.counters` or `metrics.gauges` MUST be present.

Errors:

* `ERR_SVC_SYS_OPS_CAPABILITY`
* `400` (`envelope_invalid`) for malformed payloads.
* `400` (`storage_error`) for ingestion or persistence failures.
* `401` (`auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) for authentication failures.
* `500` (`internal_error`) for internal failures.

## 6.1 POST /system/ops/app-services/{slug}/diagnostics

Response:

```
{
  "snapshot": { ... }
}
```

Errors:

* `ERR_SVC_SYS_OPS_CAPABILITY`
* `404` (`app_not_found`) when `slug` does not resolve to an installed app service.
* `400` (`envelope_invalid`) for malformed payloads.
* `401` (`auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) for authentication failures.
* `500` (`internal_error`) for internal failures.

## 7. Error handling

Errors are returned using the canonical `ErrorDetail` shape in [04-error-model.md](04-error-model.md).

Service-specific errors include:

* `ERR_SVC_SYS_OPS_CAPABILITY`
* `ERR_SVC_SYS_OPS_CONFIG_ACCESS`

Authentication failures include `auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, and `ERR_AUTH_TOKEN_REVOKED`, mapped to HTTP `401`.
