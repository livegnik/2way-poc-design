



# 14 Events Interface

Defines the event delivery surfaces referenced by system services and frontend requirements.

For the meta specifications, see [14-events-interface meta](../10-appendix/meta/04-interfaces/14-events-interface-meta.md).

## 1. Purpose and scope

This specification defines the event envelope and channel families delivered over the local WebSocket interface. It does not replace the detailed Event Manager behavior in [02-architecture/managers/11-event-manager.md](../02-architecture/managers/11-event-manager.md).

## 2. Event envelope

Events delivered to clients use the following envelope:

```
{
  "event": "<event_type>",
  "trace_id": "<string>",
  "payload": { ... }
}
```

Rules:

* Unknown fields are rejected at the envelope level.
* `payload` is an opaque JSON object; only a size bound is enforced (max 8192 bytes UTF-8). Unknown fields inside `payload` are allowed.

Errors:

* Event delivery failures use `ErrorDetail` and MUST use one of: `auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`, `acl_denied`, `network_rejected`, `internal_error`.

Client frames:

* `subscribe` frame:
  ```
  {
    "type": "subscribe",
    "channels": ["<string>"]
  }
  ```
* `ack` frame:
  ```
  {
    "type": "ack",
    "resume_token": "<string>"
  }
  ```
* `resume` frame:
  ```
  {
    "type": "resume",
    "resume_token": "<string>"
  }
  ```

Rules:

* Unknown fields are rejected.
* `channels` is 1-32 entries.
* Each channel must match a family defined in Section 3.
* `resume_token` must be a non-empty string.
* Invalid or malformed client frames MUST emit an `error` event with `ErrorDetail.code=network_rejected` before the connection closes.
* Unauthorized or admin-only channel subscriptions MUST emit an `error` event with `ErrorDetail.code=acl_denied` and close the connection with reason `permission_denied`.
* Invalid or expired `resume_token` values MUST emit an `error` event with `ErrorDetail.code=network_rejected` and close the connection with reason `resume_invalid`.
* `ack` frames that reference unknown or out-of-order `resume_token` values MUST emit an `error` event with `ErrorDetail.code=network_rejected` and close the connection with reason `frame_invalid`.

Error event envelope:

```
{
  "event": "error",
  "trace_id": "<string>",
  "payload": {
    "error": { ... ErrorDetail ... }
  }
}
```

Close reason mapping:

* `permission_denied` -> `acl_denied`
* `auth_failed` -> `auth_required`, `auth_invalid`, `ERR_AUTH_TOKEN_EXPIRED`, or `ERR_AUTH_TOKEN_REVOKED`
* `buffer_overflow`, `queue_full`, `heartbeat_timeout`, `resume_invalid`, `frame_invalid`, `filter_invalid`, `subscription_rejected` -> `network_rejected`
* unexpected internal failure -> `internal_error`

When possible, an `error` event is emitted before the connection closes.

## 3. Channel families

Channel families are derived from the Event Manager and system services specs:

* `graph.*` for graph commit notifications.
* `system.*` for lifecycle and readiness events.
* `network.*` for transport lifecycle events.
* `security.*` for abuse and audit signals.
* `app.<slug>.*` for app service events.

Examples of system events include:

* `system.bootstrap.completed`
* `system.identity.invite.accepted`
* `system.sync.plan.failed`
* `system.ops.health_toggle`

Admin-only channels (`system.*`, `security.*`) require admin gating as described in [11-event-manager.md](../02-architecture/managers/11-event-manager.md).

## 4. Forbidden behaviors

* Emitting events without an authenticated session.
* Delivering admin channels to non-admin identities.
