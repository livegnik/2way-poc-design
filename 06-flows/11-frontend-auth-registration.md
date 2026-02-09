



# 11 Frontend auth registration flow

Defines the frontend registration flow for PoC identity binding and token issuance. Passwords are local-only and never sent to the backend.

For the meta specifications, see [11-frontend-auth-registration-meta.md](../10-appendix/meta/06-flows/11-frontend-auth-registration-meta.md).

## 1. Inputs

* Username + password provided in the frontend UI (handled by the frontend Account Manager).
* Generated secp256k1 keypair for the frontend user.
* Registration payload per [13-auth-session.md](../04-interfaces/13-auth-session.md).

## 2. Flow

1) Frontend Account Manager stores `bcrypt(password)` in the local frontend DB.

2) Frontend Account Manager generates a per-user secp256k1 keypair and stores:
   * Public key in the frontend DB.
   * Private key at `frontend/keys/<frontend_user_id>.pem` with owner-only permissions.

3) Frontend Account Manager constructs the registration payload and signs the canonical JCS bytes.

4) Frontend submits `POST /auth/identity/register` with `{ payload, signature }`, including `nonce` and `timestamp`.

5) Backend Auth Manager verifies the signature and binds identity to the submitted public key.

6) Backend registers a new identity if the public key is new, or reuses the existing identity if already registered.

7) Backend issues an opaque auth token bound to `identity_id` and signs the response using the node key.

8) Frontend verifies the backend response signature and verifies that `server_public_key` matches `FRONTEND_BACKEND_PUBLIC_KEY`, then stores `identity_id`, `token`, and `expires_at` locally.

9) Subsequent requests use the auth token; the backend Auth Manager resolves it to `requester_identity_id` for OperationContext. If the token expires or is revoked, the frontend re-registers to obtain a fresh token.

## 3. Failure behavior

* Invalid registration signature results in `ERR_AUTH_SIGNATURE_INVALID` and no identity creation.
* Duplicate public key registration is idempotent and returns the existing identity id.
* Replayed payloads are rejected with `ERR_AUTH_REPLAY`.
* If the backend response signature fails verification, the frontend discards the token and treats the response as invalid.
* If the backend public key does not match `FRONTEND_BACKEND_PUBLIC_KEY`, the frontend discards the response and treats it as invalid.
* When surfaced to a transport that returns `ErrorDetail`, the following mappings apply:

| Condition | Owner | ErrorDetail.code | ErrorDetail.category | Transport status |
| --- | --- | --- | --- | --- |
| Malformed registration payload | Auth Manager | `envelope_invalid` | `structural` | `400` |
| Registration signature invalid | Auth Manager | `ERR_AUTH_SIGNATURE_INVALID` | `auth` | `401` |
| Replay detected or timestamp skew | Auth Manager | `ERR_AUTH_REPLAY` | `auth` | `401` |
| Nonce or token persistence failure | Auth Manager | `storage_error` | `storage` | `400` |
| Unexpected internal failure | Auth Manager | `internal_error` | `internal` | `500` |
* Backend response signature or pinned key mismatch is a client-side rejection and does not emit a backend `ErrorDetail`.

## 4. Forbidden behaviors

* Sending passwords to the backend.
* Treating device metadata as identity binding input.
* Accepting backend responses without signature verification.
* Registering or revoking devices via the auth registration flow.
