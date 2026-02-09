



# 12 Upload HTTP Interfaces

Defines attachment upload and download flows referenced by frontend requirements.

For the meta specifications, see [12-upload-http meta](../10-appendix/meta/04-interfaces/12-upload-http-meta.md).

## 1. Purpose and scope

This document specifies the local upload contract used for large payloads and attachments. Uploads are local-only and must follow the authorization and OperationContext requirements defined elsewhere.

Upload endpoints MUST NOT be exposed to untrusted networks.

## 2. Endpoint index

| Route | Method | Auth | Summary |
| --- | --- | --- | --- |
| `/uploads/initiate` | POST | Required | Initiate an upload session. |
| `/uploads/chunk` | POST | Required | Upload a chunk for an active session. |
| `/uploads/complete` | POST | Required | Finalize an upload and return a handle. |

## 3. POST /uploads/initiate

Request body:

```
{
  "content_type": "<string>",
  "byte_length": <int>,
  "digest": "<string>"
}
```

Response:

```
{
  "upload_id": "<string>",
  "chunk_size": <int>,
  "expires_at": "<rfc3339>"
}
```

Rules:

* Unknown fields are rejected.
* `content_type` is 1-128 chars.
* `byte_length` is 1-104857600 bytes.
* `digest` is lowercase hex SHA-256 (64 chars).
* `chunk_size` is 1024-1048576 bytes.

Errors:

* `401` (`auth_required`, `auth_invalid`) if authentication fails.
* `401` (`ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) if auth token is expired or revoked.
* `400` (`envelope_invalid`) for malformed payloads or invalid digest format.
* `400` (`storage_error`) for upload session persistence failures.
* `500` (`internal_error`) for internal failures.

## 4. POST /uploads/chunk

Request body:

```
{
  "upload_id": "<string>",
  "offset": <int>,
  "data": "<base64>"
}
```

Rules:

* Unknown fields are rejected.
* `upload_id` is 1-128 chars.
* `offset` is a non-negative integer and must be a multiple of `chunk_size`, except for the final chunk.
* `data` is base64-encoded bytes, 1-1048576 bytes decoded, and MUST be a full chunk except for the final chunk.
* `upload_id` MUST refer to an active, unexpired upload session.
* Chunks submitted after completion are rejected.

Response:

```
{"ok": true}
```

Errors:

* `401` (`auth_required`, `auth_invalid`) if authentication fails.
* `401` (`ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) if auth token is expired or revoked.
* `400` (`sequence_error`, `envelope_invalid`) for invalid offsets, unknown or expired `upload_id`, or chunks submitted after completion.
* `400` (`envelope_invalid`) for invalid base64 encoding or data size violations.
* `400` (`storage_error`) for persistence failures.
* `500` (`internal_error`) for internal failures.

## 5. POST /uploads/complete

Request body:

```
{
  "upload_id": "<string>",
  "digest": "<string>"
}
```

Rules:

* Unknown fields are rejected.
* `upload_id` is 1-128 chars.
* `digest` is lowercase hex SHA-256 (64 chars).
* `upload_id` MUST refer to an active, unexpired upload session.

Response:

```
{
  "handle": "<string>",
  "byte_length": <int>
}
```

Errors:

* `401` (`auth_required`, `auth_invalid`) if authentication fails.
* `401` (`ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) if auth token is expired or revoked.
* `400` (`sequence_error`, `storage_error`, `envelope_invalid`) for digest or ordering failures, or unknown/expired `upload_id`.
* `500` (`internal_error`) for internal failures.

## 6. Validation and ordering

* Uploads MUST be authorized by the caller's [OperationContext](../02-architecture/services-and-apps/05-operation-context.md).
* Chunk ordering MUST be validated by `offset` and `chunk_size`.
* `digest` MUST be the lowercase hex-encoded SHA-256 of the full upload payload bytes (exactly 64 hex chars).
* Finalization MUST verify the declared digest before issuing a handle.

## 7. Forbidden behaviors

* Accepting uploads without authentication.
* Returning a handle without digest verification.
