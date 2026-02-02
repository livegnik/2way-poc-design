



# 02 App install and permissions

This flow defines how an app is registered, its schema is introduced, and initial permissions are provisioned.

For the meta specifications, see [02-app-install-and-permissions-meta.md](../09-appendix/meta/06-flows/02-app-install-and-permissions-meta.md).

## 1. Inputs

* App install request from frontend or local admin surface.
* App package metadata (slug, version, schema bundle, capability list).
* OperationContext representing an authorized installer identity.

## 2. Preconditions

* Node bootstrap has completed.
* App slug is not already registered (or install is idempotent).
* Schema bundle passes structural validation.

## 3. Flow

1) Interface layer authenticates the caller and constructs OperationContext.
2) App Manager registers the app slug and allocates app_id.
3) Key Manager generates the app identity keypair (app-scoped identity).
4) Graph Manager applies envelopes to:
   * Create app identity parent object.
   * Store app schema objects and version metadata.
   * Store app capability declarations (app-scoped attributes/edges).
5) Schema Manager validates the schema bundle.
6) ACL Manager establishes default app ACLs and capability bindings.
7) Storage Manager persists all writes atomically.
8) Event Manager emits app installation events after commit.

## 4. Allowed behavior

* Idempotent re-installation for the same slug and version.
* Upgrades that introduce new schema versions only through Schema Manager.

## 5. Forbidden behavior

* Installing apps without App Manager registration.
* Using unvalidated schemas.
* Assigning app capabilities outside ACL Manager decisions.

## 6. Failure behavior

* Any failure aborts the install; no partial state persists.
* Rejections are returned to the caller with deterministic errors.
