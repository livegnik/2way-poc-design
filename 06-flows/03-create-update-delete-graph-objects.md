



# 03 Create, update, and delete graph objects

This flow defines local write operations over graph objects. Deletion is expressed through Rating-based suppression; physical deletes are forbidden.

For the meta specifications, see [03-create-update-delete-graph-objects-meta.md](../10-appendix/meta/06-flows/03-create-update-delete-graph-objects-meta.md).

## 1. Inputs

* Write request from frontend app or backend service.
* Graph message envelope containing one or more operations.
* OperationContext with requester identity, app_id, and capability.

## 2. Flow

1) Interface layer validates authentication and constructs OperationContext.

2) Envelope is structurally validated.

3) Schema Manager validates type keys and constraints.

4) ACL Manager authorizes the write against the OperationContext.

5) Graph Manager acquires exclusive write access.

6) Storage Manager persists all operations atomically and assigns global_seq.

7) Graph Manager releases write access.

8) Event Manager emits domain events after commit.

## 3. Update semantics

* Updates must specify the target object id.
* Updates are append-only; new rows are written, prior state is retained.
* Ordering is defined by global_seq, not wall clock.

## 4. Delete semantics

* Deletes are not supported.
* Visibility suppression is represented by Rating objects with app-defined meaning.

## 5. Failure behavior

* Any validation failure rejects the envelope.
* Storage errors roll back the entire envelope.
* No partial writes are allowed.
* When surfaced to a transport that returns `ErrorDetail`, the following mappings apply:

| Failure stage | Owner | ErrorDetail.code | ErrorDetail.category | Transport status |
| --- | --- | --- | --- | --- |
| Missing auth token | Auth Manager | `auth_required` | `auth` | `401` |
| Invalid auth token | Auth Manager | `auth_invalid` | `auth` | `401` |
| Expired auth token | Auth Manager | `ERR_AUTH_TOKEN_EXPIRED` | `auth` | `401` |
| Revoked auth token | Auth Manager | `ERR_AUTH_TOKEN_REVOKED` | `auth` | `401` |
| Structural validation failure | Interface layer | `envelope_invalid` | `structural` | `400` |
| Identifier validation failure | Interface layer | `identifier_invalid` | `structural` | `400` |
| Schema type or constraint failure | Schema Manager | `schema_unknown_type` or `schema_validation_failed` | `schema` | `400` |
| ACL denial | ACL Manager | `acl_denied` | `acl` | `400` |
| Ordering or sequence violation | State Manager | `sequence_error` | `storage` | `400` |
| Persistence failure | Storage Manager | `storage_error` | `storage` | `400` |
| Unexpected internal failure | Owning manager | `internal_error` | `internal` | `500` |
