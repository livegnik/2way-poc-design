



# 02 WebSocket events

Defines the local WebSocket interface used for authenticated, stateful sessions and (future) event delivery. This interface is local-only and must not be exposed to untrusted networks.

For the meta specifications, see [02-websocket-events meta](../09-appendix/meta/04-interfaces/02-websocket-events-meta.md).

## 1. Purpose and scope

The WebSocket interface provides:

* Authenticated session establishment.
* A channel for future real-time event delivery.

The PoC currently focuses on explicit authentication gating and session creation.

## 2. Connection and authentication

A WebSocket connection must supply an authentication token during the handshake. The backend resolves the token via [Auth Manager](../02-architecture/managers/04-auth-manager.md). If authentication fails, the connection must be rejected.

Accepted token sources (implementation-defined):

* Query parameter (e.g., `?token=...`).
* Header-based token if the adapter exposes headers.
* Cookie `session_token` if available to the adapter.

The interface must map the token to an `AuthResult`. Unauthorized sessions must never be admitted.

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

Event names and payloads will be defined in later interface specs. Until then, the PoC only requires authentication and session establishment.

## 5. Forbidden behaviors

* Accepting unauthenticated connections.
* Emitting events without a bound identity.
* Using WebSocket transport for remote sync or inter-node replication.
