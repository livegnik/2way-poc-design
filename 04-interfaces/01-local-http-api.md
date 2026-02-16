



# 01 Local HTTP API

Defines the local HTTP interface exposed by the 2WAY backend. This API is local-only and framework-agnostic; handlers are designed to run under any HTTP server adapter.

For the meta specifications, see [01-local-http-api meta](../10-appendix/meta/04-interfaces/01-local-http-api-meta.md).

## 1. Purpose and scope

The local HTTP API provides a minimal surface for PoC interaction:

* Health checks for readiness and liveness.
* Submission of graph message envelopes for local writes.

## 2. Transport posture

* **Local only.** This interface must be bound to a local transport (loopback or IPC) and not exposed to untrusted networks.
* **No framework requirement.** Implementations may use Flask, FastAPI, or a custom adapter, but must preserve the handler semantics defined here.
* **No DoS challenges.** DoS Guard challenges are not issued on local HTTP routes; `dos_challenge_required` is not emitted on this interface.

## 3. Authentication

Authentication is mandatory for write paths. The handler uses [Auth Manager](../02-architecture/managers/04-auth-manager.md) to validate tokens.

Accepted token sources:

* `Authorization: Bearer <token>`
* `X-Auth-Token: <token>`
* `Cookie: auth_token=<token>`

Missing or invalid tokens result in a `401` response.
Expired or revoked tokens result in a `401` response with `ERR_AUTH_TOKEN_EXPIRED` or `ERR_AUTH_TOKEN_REVOKED`.

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
  "status": "ok",
  "ready": false,
  "version": "<string>",
  "git_commit": "<string>",
  "schema_version": <int>,
  "cfg_seq": <int>,
  "global_seq": <int>,
  "manager_states": [
    {
      "manager": "<string>",
      "state": "<string>"
    }
  ]
}
```

Rules:

* `status` MUST be `ok` when the probe is served.
* `ready` reflects runtime readiness; `ready=false` is a valid success response and does not change HTTP status.
* `git_commit` MAY be `unknown` when commit metadata is unavailable.
* `schema_version`, `cfg_seq`, and `global_seq` are non-negative integers.
* `manager_states` is a deterministic list of manager readiness entries ordered by manager name.
* Each `manager_states` entry uses `state` values `healthy`, `degraded`, `failed`, or `unknown`.

**Response (errors):**
* `500` (`internal_error`) only when the health snapshot cannot be produced.

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
* `400` on structural or validation errors (`envelope_invalid`, `object_invalid`, `identifier_invalid`, `schema_unknown_type`, `schema_validation_failed`, `acl_denied`, `sequence_error`, `storage_error`).
* `401` if authentication fails (`auth_required`, `auth_invalid`).
* `401` if auth token is expired or revoked (`ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`).
* `500` for internal failures (`internal_error`).

Error payloads follow [04-error-model.md](04-error-model.md).

### 5.2.1 Temporary minimal commit mode contract (Build Plan 3.4 only)

When minimal commit mode is enabled (Build Plan step 3.4), `POST /graph/envelope` is constrained to one deterministic request shape:

```
{
  "app_id": <int>,
  "envelope": {
    "trace_id": "<string>",
    "ops": [
      {
        "op": "parent_create",
        "app_id": <int>,
        "type_key": "<string>" | "type_id": <int>,
        "owner_identity": <int>,
        "payload": {
          "value": { ... }
        }
      }
    ]
  }
}
```

Rules:

* `envelope.ops` length must be exactly `1`.
* `request.app_id` must equal `envelope.ops[0].app_id`.
* `payload` must contain only `value`.
* Any payload fields representing Attribute/Edge/Rating targets or inline ACL data are forbidden.
* On rejection, no persistence is allowed and `global_seq` must not change.

Errors in minimal commit mode:

* `400` (`envelope_invalid`) for any violation of this temporary contract.
* Other error codes remain mapped per Section 5.2 for auth, identifier/schema/ACL, and internal failures.

### 5.3 POST /graph/read

**Purpose:** Submit a local graph read request and return authorized results.
**Authentication:** Required.
**Request body:**

```
{
  "read_request": { ... }
}
```

`read_request` MUST conform to `GraphReadRequest` in [03-internal-apis-between-components.md](03-internal-apis-between-components.md#5.2.1-GraphReadRequest-Graph-Manager-inputs).

**Response (success):**

```
200 OK
{
  "result": { ... }
}
```

`result` MUST conform to `GraphReadResult` in [03-internal-apis-between-components.md](03-internal-apis-between-components.md#5.2.2-GraphReadResult-Graph-Manager-outputs).

**Response (errors):**
* `400` on structural or validation errors (`envelope_invalid`, `identifier_invalid`, `schema_unknown_type`, `schema_validation_failed`, `acl_denied`, `storage_error`).
* `401` if authentication fails (`auth_required`, `auth_invalid`).
* `401` if auth token is expired or revoked (`ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`).
* `500` for internal failures (`internal_error`).

### 5.4 GET /admin/health

**Purpose:** Admin health snapshot with optional component filters.
**Authentication:** Required. Caller identity must carry the admin capability defined by `health.admin_capability`.
**Response:**

```
200 OK
{
  "snapshot": { ... }
}
```

Snapshot schema (unknown fields rejected, see [13-health-manager.md](../02-architecture/managers/13-health-manager.md) Section 2.3):

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `health_seq` | Yes | int | Monotonic, non-negative. |
| `published_at` | Yes | string | RFC3339 timestamp. |
| `readiness` | Yes | string | `ready` or `not_ready`. |
| `liveness` | Yes | string | `alive` or `dead`. |
| `components` | Yes | object | Map of component -> `ComponentHealth`. |
| `last_transition` | Yes | object | `Transition` object. |
| `outputs` | Yes | array | List of sink identifiers (0-16). |

ComponentHealth:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `state` | Yes | string | `healthy`, `degraded`, `failed`, or `unknown`. |
| `reason_code` | No | string | 1-64 chars. |
| `last_reported_at` | No | string | RFC3339 timestamp. |

Transition:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `from` | Yes | object | `{ readiness, liveness }`. |
| `to` | Yes | object | `{ readiness, liveness }`. |
| `cause` | Yes | string | 1-128 chars. |

**Response (errors):**
* `401` if authentication fails (`auth_required`, `auth_invalid`).
* `401` if auth token is expired or revoked (`ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`).
* `400` for authorization or validation failures (`acl_denied`, `config_invalid`).
* `400` (`envelope_invalid`) for malformed or unknown component filter parameters.
* `500` for internal failures (`internal_error`).

### 5.5 POST /apps/{slug}/list

**Purpose:** List objects for PoC app domains using a constrained graph read.
**Authentication:** Required.
**Path params:**

* `slug`: one of `contacts`, `messaging`, `social`, `market`.

**Request body:**

```
{
  "read_request": { ... }
}
```

`read_request` MUST conform to `GraphReadRequest` in [03-internal-apis-between-components.md](03-internal-apis-between-components.md#5.2.1-GraphReadRequest-Graph-Manager-inputs).

Rules:

* The server resolves `slug` to an `app_id` via the app registry.
* If `read_request.app_id` is present, it MUST match the resolved `app_id`.
* The request MUST target schema types defined in the corresponding PoC app schemas (`specs/07-poc/02-feature-matrix.md`).

**Response (success):**

```
200 OK
{
  "result": { ... }
}
```

`result` MUST conform to `GraphReadResult` in [03-internal-apis-between-components.md](03-internal-apis-between-components.md#5.2.2-GraphReadResult-Graph-Manager-outputs).

**Response (errors):**
* `400` on structural or validation errors (`envelope_invalid`, `identifier_invalid`, `schema_unknown_type`, `schema_validation_failed`, `acl_denied`, `storage_error`).
* `400` (`schema_validation_failed`) when `read_request.app_id` mismatches the slug-resolved `app_id` or targets non-PoC schema types.
* `401` if authentication fails (`auth_required`, `auth_invalid`).
* `401` if auth token is expired or revoked (`ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`).
* `404` if `slug` is unknown or the app registry has no entry for the resolved app (`app_not_found`).
* `503` with one of `ERR_SVC_APP_NOT_READY`, `ERR_SVC_APP_DISABLED`, `ERR_SVC_APP_DEPENDENCY_UNAVAILABLE`, `ERR_SVC_APP_DRAINING`, `ERR_SVC_APP_LOAD_FAILED` if the app service for `slug` is installed but unavailable.
* `500` for internal failures (`internal_error`).

### 5.6 POST /apps/{slug}/read

**Purpose:** Read a specific object set for PoC app domains using a constrained graph read.
**Authentication:** Required.
**Path params:**

* `slug`: one of `contacts`, `messaging`, `social`, `market`.

**Request body:**

```
{
  "read_request": { ... }
}
```

`read_request` MUST conform to `GraphReadRequest` in [03-internal-apis-between-components.md](03-internal-apis-between-components.md#5.2.1-GraphReadRequest-Graph-Manager-inputs).

Rules:

* The server resolves `slug` to an `app_id` via the app registry.
* If `read_request.app_id` is present, it MUST match the resolved `app_id`.
* The request MUST target schema types defined in the corresponding PoC app schemas (`specs/07-poc/02-feature-matrix.md`).

**Response (success):**

```
200 OK
{
  "result": { ... }
}
```

`result` MUST conform to `GraphReadResult` in [03-internal-apis-between-components.md](03-internal-apis-between-components.md#5.2.2-GraphReadResult-Graph-Manager-outputs).

**Response (errors):**
* `400` on structural or validation errors (`envelope_invalid`, `identifier_invalid`, `schema_unknown_type`, `schema_validation_failed`, `acl_denied`, `storage_error`).
* `400` (`schema_validation_failed`) when `read_request.app_id` mismatches the slug-resolved `app_id` or targets non-PoC schema types.
* `401` if authentication fails (`auth_required`, `auth_invalid`).
* `401` if auth token is expired or revoked (`ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`).
* `404` if `slug` is unknown or the app registry has no entry for the resolved app (`app_not_found`).
* `503` with one of `ERR_SVC_APP_NOT_READY`, `ERR_SVC_APP_DISABLED`, `ERR_SVC_APP_DEPENDENCY_UNAVAILABLE`, `ERR_SVC_APP_DRAINING`, `ERR_SVC_APP_LOAD_FAILED` if the app service for `slug` is installed but unavailable.
* `500` for internal failures (`internal_error`).

## 6. Validation and ordering

The HTTP handler must:

1. Authenticate the request and resolve the identity.
2. Validate body structure (`app_id` integer and `envelope` object) for writes, or `read_request` object for reads.
3. Construct a complete [OperationContext](../02-architecture/services-and-apps/05-operation-context.md).
4. Submit to [Graph Manager](../02-architecture/managers/07-graph-manager.md).

No persistence is permitted before schema validation and ACL checks succeed.

## 7. Forbidden behaviors

* Accepting requests without authentication for write paths.
* Accepting envelopes that target multiple apps.
* Returning partial results after rejection.
