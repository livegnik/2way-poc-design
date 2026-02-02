



# 01 Local HTTP API

Defines the local HTTP interface exposed by the 2WAY backend. This API is local-only and framework-agnostic; handlers are designed to run under any HTTP server adapter.

For the meta specifications, see [01-local-http-api meta](../09-appendix/meta/04-interfaces/01-local-http-api-meta.md).

## 1. Purpose and scope

The local HTTP API provides a minimal surface for PoC interaction:

* Health checks for readiness and liveness.
* Submission of graph message envelopes for local writes.

This API does not cover remote peer sync, which uses [Network Manager](../02-architecture/managers/10-network-manager.md) and the sync protocol.

## 2. Transport posture

* **Local only.** This interface must be bound to a local transport (loopback or IPC) and not exposed to untrusted networks.
* **No framework requirement.** Implementations may use Flask, FastAPI, or a custom adapter, but must preserve the handler semantics defined here.

## 3. Authentication

Authentication is mandatory for write paths. The handler uses [Auth Manager](../02-architecture/managers/04-auth-manager.md) to validate tokens.

Accepted token sources:

* `Authorization: Bearer <token>`
* `X-Session-Token: <token>`
* `Cookie: session_token=<token>`

Missing or invalid tokens result in a `401` response.

## 4. Headers

### 4.1 Required

None.

### 4.2 Optional

* `X-Trace-Id`: If present, propagated into OperationContext. If absent, the server must mint a trace id.

## 5. Endpoints

### 5.1 GET /health

**Purpose:** health probe for local supervision.

**Response:**

```
200 OK
{
  "ok": true
}
```

### 5.2 POST /graph/envelope

**Purpose:** Submit a graph message envelope for local mutation.

**Request body:**

```
{
  "app_id": <int>,
  "envelope": {
    "trace_id": "<string>",
    "ops": [ ... ]
  }
}
```

The envelope must conform to [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md).

**Response (success):**

```
200 OK
{
  "global_seq": <int>
}
```

**Response (errors):**

* `400` if JSON is malformed, payload is missing required fields, or Graph Manager rejects the envelope.
* `401` if authentication fails.
* `500` for internal failures.

Error payloads follow [04-error-model.md](04-error-model.md).

## 6. Validation and ordering

The HTTP handler must:

1. Authenticate the request and resolve the identity.
2. Validate body structure (`app_id` integer and `envelope` object).
3. Construct a complete [OperationContext](../02-architecture/services-and-apps/05-operation-context.md).
4. Submit to [Graph Manager](../02-architecture/managers/07-graph-manager.md).

No persistence is permitted before schema validation and ACL checks succeed.

## 7. Forbidden behaviors

* Accepting requests without authentication for write paths.
* Accepting envelopes that target multiple apps.
* Returning partial results after rejection.
