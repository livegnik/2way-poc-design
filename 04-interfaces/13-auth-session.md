



# 13 Auth Identity Registration Interface

Defines the local authentication surface used to register an identity and obtain an opaque backend token consumed by [Auth Manager](../02-architecture/managers/04-auth-manager.md).

For the meta specifications, see [13-auth-session meta](../10-appendix/meta/04-interfaces/13-auth-session-meta.md).

## 1. Purpose and scope

This document specifies the local-only auth endpoint for identity registration and token issuance. Passwords are frontend-local credentials and MUST NOT be sent to the backend. Backend authentication is exclusively:

1. Signature-based identity registration (public key + signed payload).
2. Opaque token on subsequent requests.

Auth endpoints MUST NOT be exposed to untrusted networks.

## 2. Endpoint index

| Route | Method | Auth | Summary |
| --- | --- | --- | --- |
| `/auth/identity/register` | POST | Optional | Register an identity by public key and obtain an auth token. |

## 2.1 Registration payload schema

Unknown fields are rejected.

Top-level request fields:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `payload` | Yes | object | Must match the payload fields below. |
| `signature` | Yes | string | base64, 64 bytes decoded (secp256k1 `r || s`). |

Payload fields (these fields are signed):

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `public_key` | Yes | string | base64, 32-512 bytes decoded. |
| `nonce` | Yes | string | base64, 16-64 bytes decoded. |
| `timestamp` | Yes | string | RFC3339 timestamp. |
| `frontend_user_id` | No | string | 1-64 chars, client metadata only. |
| `device_metadata` | No | object | Client metadata only; keys 1-64 chars, values 0-1024 chars. |

Notes:

* `frontend_user_id` and `device_metadata` are client metadata only and MUST NOT affect identity binding decisions.
* Device registration and device revocation are out of scope for PoC auth registration; no device identity is created or bound by this interface.
* Replay protection is mandatory: the backend MUST reject registration payloads with timestamps outside `auth.registration.max_skew_ms` and MUST reject any `(public_key, nonce)` reuse within `auth.registration.nonce_ttl_ms`.

Signature field (not part of the signed payload):

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `signature` | Yes | string | base64, 64 bytes decoded (secp256k1 `r || s`). |

## 2.2 Canonical signing rules

The bytes to sign for registration are the UTF-8 JCS canonical serialization of the `payload` object only (excluding the `signature` field), per [01-protocol/04-cryptography.md](../01-protocol/04-cryptography.md#1112-canonical-serialization-for-signing).

Signature verification uses the submitted `public_key`.

## 3. POST /auth/identity/register

Request body:

```
{
  "payload": {
    "public_key": "<base64>",
    "nonce": "<base64>",
    "timestamp": "<rfc3339>",
    "frontend_user_id": "<string>",
    "device_metadata": { "device_name": "<string>" }
  },
  "signature": "<base64>"
}
```

Response (success):

```
{
  "identity_id": "<parent_id>",
  "token": "<opaque>",
  "issued_at": "<rfc3339>",
  "expires_at": "<rfc3339>",
  "server_identity_id": "<parent_id>",
  "server_public_key": "<base64>",
  "server_signature": "<base64>"
}
```

Response fields:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `identity_id` | Yes | string | Parent id. |
| `token` | Yes | string | 16-4096 chars, opaque. |
| `issued_at` | Yes | string | RFC3339 timestamp. |
| `expires_at` | Yes | string | RFC3339 timestamp. |
| `server_identity_id` | Yes | string | Parent id. |
| `server_public_key` | Yes | string | base64, 32-512 bytes decoded. |
| `server_signature` | Yes | string | base64, 64 bytes decoded (secp256k1 `r || s`). |

Response signature:

* `server_signature` is a secp256k1 signature (base64, 64 bytes decoded) over the canonical JSON serialization of the response object excluding `server_signature`.
* The backend signs using its node key.
* Frontends MUST verify the response signature using `server_public_key` and MUST treat a signature failure as an authentication failure.
* Frontends MUST verify that `server_public_key` matches the locally configured backend public key (`FRONTEND_BACKEND_PUBLIC_KEY`). A mismatch is a hard authentication failure.
* The backend MUST include `server_identity_id`, `server_public_key`, and `server_signature` in every successful response.

Idempotency semantics:

* If `public_key` is not yet registered, the backend creates a new identity and returns `201 Created`.
* If `public_key` is already registered, the backend returns `200 OK` with the same `identity_id` and a fresh token.
* Duplicate registration MUST NOT create additional identities.

Errors:

* `400` (`envelope_invalid`) for malformed payloads.
* `401` (`ERR_AUTH_SIGNATURE_INVALID`) when signature verification fails.
* `401` (`ERR_AUTH_SIGNATURE_INVALID`) when the public key cannot be parsed or is unsupported.
* `401` (`ERR_AUTH_REPLAY`) when a replayed registration payload is detected or when timestamp skew exceeds `auth.registration.max_skew_ms`.
* `400` (`storage_error`) when nonce storage or token persistence fails.
* `500` (`internal_error`) for internal failures.

## 4. Validation and ordering

* Auth Manager MUST verify the registration signature before issuing a token.
* Auth Manager MUST bind the backend identity solely to the `public_key` in the signed payload.
* Auth Manager MUST enforce replay protection using `nonce` and `timestamp` as defined in Section 2.1.
* Auth Manager MUST store the token as an opaque server-validated value bound to `identity_id`.
* Nonce storage or token persistence failures MUST return `storage_error` and MUST NOT return a token.
* The backend MUST return both `identity_id` and `token` to the frontend.
* Tokens MUST NOT be self-contained claims (no JWT semantics).
* Tokens MUST include an expiry timestamp and MUST be rejected after expiry.
* `expires_at` MUST be computed from `issued_at` plus `auth.token.ttl_ms`.
* Issuing a new token for an identity MUST revoke any previously issued tokens for that identity.
* The auth registration endpoint MUST fail closed on missing or invalid payloads and signatures.

## 5. Forbidden behaviors

* Accepting username/password as a backend authentication mechanism.
* Sending frontend passwords to the backend.
* Issuing a token without validating the registration signature.
* Treating a token as an authorization decision.
