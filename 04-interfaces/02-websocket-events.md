



# 02 WebSocket events

Defines the local WebSocket interface used for authenticated, stateful sessions and (future) event delivery. This interface is local-only and must not be exposed to untrusted networks.

For the meta specifications, see [02-websocket-events meta](../10-appendix/meta/04-interfaces/02-websocket-events-meta.md).

## 1. Purpose and scope

The WebSocket interface provides:

* Authenticated session establishment.
* A channel for future real-time event delivery.

The PoC currently focuses on explicit authentication gating and session creation.

## 2. Connection and authentication

### 2.1 Endpoint path

A WebSocket connection is accepted only on the local endpoint path:

* `GET /ws`

Requests that are not `GET /ws` MUST be rejected with HTTP `404` and no `ErrorDetail` payload.

A WebSocket connection must supply an authentication token during the handshake. The backend resolves the token via [Auth Manager](../02-architecture/managers/04-auth-manager.md). If authentication fails, the connection must be rejected.

Errors:

* Authentication failures reject the connection (`auth_required`, `auth_invalid`).
* Expired or revoked tokens reject the connection (`ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`).
* The WebSocket upgrade MUST be rejected with HTTP `401` and an `ErrorDetail` payload; no session is created.

### 2.2 Accepted token sources

Accepted token sources:

* Query parameter `?token=...`.
* `Authorization: Bearer <token>`.
* `X-Auth-Token: <token>`.
* Cookie `auth_token=<token>`.

The interface must map the token to an `AuthResult`. Unauthorized sessions must never be admitted.

If multiple token sources are present and do not match, the upgrade MUST be rejected with `auth_invalid`.

### 2.3 Post-connection token expiry or revocation

If a session token expires or is revoked after the WebSocket connection is established:

* The connection MUST be closed.
* The server MUST emit an `error` event with `ErrorDetail.code=ERR_AUTH_TOKEN_EXPIRED` or `ERR_AUTH_TOKEN_REVOKED` before closing when event delivery is available.
* The close reason MUST be `auth_failed` (see [14-events-interface.md](14-events-interface.md) close reason mapping).

## 3. Session model

A successful connection creates a session record:

* `requester_identity_id` (required)

The session is the authoritative binding between the WebSocket connection and the caller identity. It is used for any downstream event authorization.

## 4. Event envelope (reserved)

Event delivery is reserved for a later phase. When implemented, events will be delivered using a consistent envelope:

```
{
  "event": "<event_name>",
  "trace_id": "<trace_id>",
  "payload": { ... }
}
```

Rules:

* Unknown fields are rejected at the envelope level.
* `payload` is an opaque JSON object; only a size bound is enforced (max 8192 bytes UTF-8). Unknown fields inside `payload` are allowed.

Event names and payloads will be defined in later interface specs. Until then, the PoC only requires authentication and session establishment.

Client subscription frame:

```
{
  "type": "subscribe",
  "channels": ["<string>"]
}
```

Rules:

* Unknown fields are rejected.
* `channels` is 1-32 entries.
* Each channel must match a family defined in [14-events-interface.md](14-events-interface.md).
* Invalid subscription frames MUST emit an `error` event with `ErrorDetail.code=network_rejected` before the connection closes.
* Unauthorized or admin-only channel subscriptions MUST emit an `error` event with `ErrorDetail.code=acl_denied` and close the connection with reason `permission_denied`.

## 5. Forbidden behaviors

* Accepting unauthenticated connections.
* Emitting events without a bound identity.
* Using WebSocket transport for remote sync or inter-node replication.
