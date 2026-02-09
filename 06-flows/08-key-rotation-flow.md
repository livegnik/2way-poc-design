



# 08 Key rotation flow

This flow defines how identities rotate keys without rewriting history.

For the meta specifications, see [08-key-rotation-flow-meta.md](../10-appendix/meta/06-flows/08-key-rotation-flow-meta.md).

## 1. Inputs

* Authenticated request from an identity owner.
* OperationContext with appropriate capability (identity management).
* Key rotation request containing the new public key material.

## 2. Flow

1) Auth Manager validates the requester identity.

2) Key Manager generates a new keypair or imports a new public key, depending on flow.

3) Graph Manager applies an envelope that:

   * Adds a new key object or key attribute under the identity.
   * Marks the old key as retired or revoked (Rating or attribute).

4) Schema Manager validates the key object schema.

5) ACL Manager enforces that only the identity owner may rotate keys.

6) Storage Manager persists the key changes atomically.

## 3. Allowed behavior

* Multiple active keys during a transition window.
* Explicit revocation of old keys after rotation.

## 4. Forbidden behavior

* Rotating keys without an authenticated owner.
* Overwriting historical signatures.

## 5. Failure behavior

* Rotation failures do not change existing keys.
* Partially applied rotations are not persisted.
* When surfaced to a transport that returns `ErrorDetail`, the following mappings apply:

| Condition | Owner | ErrorDetail.code | ErrorDetail.category | Transport status |
| --- | --- | --- | --- | --- |
| Malformed rotation request payload | Interface layer | `envelope_invalid` | `structural` | `400` |
| Invalid key material or schema violation | Schema Manager | `schema_validation_failed` | `schema` | `400` |
| Unauthorized rotation attempt | ACL Manager | `acl_denied` | `acl` | `400` |
| Persistence failure | Storage Manager | `storage_error` | `storage` | `400` |
| Unexpected internal failure | Owning manager | `internal_error` | `internal` | `500` |
