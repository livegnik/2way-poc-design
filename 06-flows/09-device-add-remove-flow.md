



# 09 Device add/remove flow

This flow defines how devices are enrolled and removed for an identity.

For the meta specifications, see [09-device-add-remove-flow-meta.md](../09-appendix/meta/06-flows/09-device-add-remove-flow-meta.md).

## 1. Inputs

* Authenticated request from an identity owner or bootstrap admin.
* OperationContext with device management capability.

## 2. Add device flow

1) Admin or owner requests device enrollment.
2) Key Manager generates device key material.
3) Graph Manager applies envelope to create:
   * Device parent object.
   * Device ownership edge linking device -> identity.
4) Schema Manager validates device schema.
5) ACL Manager enforces owner or admin rights.
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

* Removing devices without owner or admin authorization.
* Deleting device objects.

## 6. Failure behavior

* Failures do not change device state.
* Partial changes are rolled back.
