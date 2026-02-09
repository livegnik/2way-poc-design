



# 09 Device add/remove flow

This flow defines how devices are enrolled and removed for an identity.

For the meta specifications, see [09-device-add-remove-flow-meta.md](../10-appendix/meta/06-flows/09-device-add-remove-flow-meta.md).

## 1. Inputs

* Authenticated request from an identity owner or admin identity (`system.admin`).
* OperationContext with device management capability.

## 2. Add device flow

1) Admin (`system.admin`) or owner requests device enrollment.

2) Key Manager generates device key material.

3) Graph Manager applies envelope to create:

   * Device parent object.
   * Device ownership edge linking device -> identity.

4) Schema Manager validates device schema.

5) ACL Manager enforces owner rights or admin action bypass per the access control model.

6) Storage Manager persists device objects atomically.

## 3. Remove device flow

1) Owner requests device removal.

2) Graph Manager applies envelope that marks the device as inactive (Rating or attribute).

3) ACL Manager enforces ownership.

4) Storage Manager persists the change.

## 4. Allowed behavior

* Multiple devices per identity.
* Device removal without deleting historical data.

## 5. Forbidden behavior

* Removing devices without owner or admin (`system.admin`) authorization.
* Deleting device objects.

## 6. Failure behavior

* Failures do not change device state.
* Partial changes are rolled back.
* When surfaced to a transport that returns `ErrorDetail`, the following mappings apply:

| Condition | Owner | ErrorDetail.code | ErrorDetail.category | Transport status |
| --- | --- | --- | --- | --- |
| Malformed device request payload | Interface layer | `envelope_invalid` | `structural` | `400` |
| Malformed identity or device identifier | Interface layer | `identifier_invalid` | `structural` | `400` |
| Target identity or device not found | Graph Manager | `object_invalid` | `structural` | `400` |
| Unauthorized add/remove attempt | ACL Manager | `acl_denied` | `acl` | `400` |
| Persistence failure | Storage Manager | `storage_error` | `storage` | `400` |
| Unexpected internal failure | Owning manager | `internal_error` | `internal` | `500` |
