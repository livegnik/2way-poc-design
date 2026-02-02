



# 04 Error model

Defines canonical error shapes, categories, and transport mapping for 2WAY. Errors are fail-closed and must not cause partial persistence.

For the meta specifications, see [04-error-model meta](../09-appendix/meta/04-interfaces/04-error-model-meta.md).

## 1. Purpose and scope

The error model provides a unified representation for failures across the backend, including protocol validation, schema enforcement, ACL denial, storage failures, and network admission. It does not define UI behavior; it defines payload shapes and manager-level semantics.

## 2. Error representation

All errors emitted by managers use `ErrorDetail`:

```
{
  "code": "<error_code>",
  "category": "<category>",
  "message": "<human readable message>",
  "data": { ... }
}
```

`ErrorDetail` is created via the `error_detail` helper and must include a canonical `code` and derived `category`.

## 3. Categories

Categories reflect the earliest failure stage:

* `structural`
* `schema`
* `acl`
* `storage`
* `config`
* `auth`
* `network`
* `dos`
* `internal`

## 4. Error codes (canonical)

The following codes are defined for the PoC:

* `envelope_invalid`
* `object_invalid`
* `identifier_invalid`
* `schema_unknown_type`
* `schema_validation_failed`
* `acl_denied`
* `storage_error`
* `sequence_error`
* `config_invalid`
* `auth_required`
* `auth_invalid`
* `network_rejected`
* `dos_challenge_required`
* `internal_error`

Implementations must not invent ad-hoc codes without updating this file.

## 5. Failure precedence

Failure precedence is strict:

1. Structural validation failures
2. Cryptographic/authentication failures
3. Schema validation failures
4. ACL failures
5. Storage failures

The first failure encountered must be returned and later stages must not execute.

## 6. Transport mapping

### 6.1 Local HTTP

* `401` for authentication failures (`auth_required`, `auth_invalid`).
* `400` for other `ErrorDetail` failures.
* `500` for unexpected internal errors without an `ErrorDetail`.

Response payloads use the `ErrorDetail` shape.

### 6.2 WebSocket

Authentication failures result in immediate connection rejection (no session). When events are added, error events must use the `ErrorDetail` shape.

### 6.3 Internal manager APIs

Manager errors are raised as exceptions that carry `ErrorDetail`. Interface layers translate them into transport responses.

## 7. Forbidden behaviors

* Returning partial success when a failure occurs.
* Emitting non-canonical error shapes.
* Leaking stack traces or internal errors over external interfaces.
