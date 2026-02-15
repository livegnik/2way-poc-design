



# 02 App install and permissions

This flow defines how an app is registered, its schema is introduced, and initial permissions are provisioned.

For the meta specifications, see [02-app-install-and-permissions-meta.md](../10-appendix/meta/06-flows/02-app-install-and-permissions-meta.md).

## 1. Inputs

* App install request from frontend or local admin surface.
* App package ZIP and detached signature file.
* App package metadata (slug, version, schema bundle, capability list) extracted from the ZIP.
* OperationContext representing an authorized installer identity.

## 1a. Interface contract (HTTP)

Endpoint:

* `POST /api/system/apps/register`

Request body (multipart/form-data):

* `package_zip` (file, required) - `<slug>_app.zip` containing `manifest.json`, `schema.json`, and optional `acl.json`.
* `package_sig` (file, required) - `<slug>_app_sig.txt` containing a detached signature for the ZIP bytes.
* `device_id` (int, optional)
* `enabled` (bool, optional)

Derived payload rules:

* `manifest` (object, required)
  * `slug` (string, required)
  * `version` (string, required)
  * `capabilities` (array of string)
  * `dependencies` (array of string)
  * `config_keys` (array of string)
* `schema` (object, required)
  * `objects` (array of graph objects)
* `acl` (object, optional)
  * `objects` (array of graph objects)

Rules:

* Objects in `schema.objects` and `acl.objects` MUST NOT include `global_seq` or `sync_flags` (assigned on commit).
* The ZIP payload MUST include `manifest.json` and `schema.json`. `acl.json` is optional.
* The signature file MUST be present and MUST verify against the raw ZIP bytes using public key material supplied with the package or a trusted publisher registry.
* The signature file MUST include a `signer_id` that resolves to a publisher identity in the graph, or a `publisher_public_key` that can be bound to a new publisher identity.
* App installation MUST be blocked unless the publisher identity exists in the graph and is marked trusted for app publication. If the publisher identity is missing or untrusted, the user MUST be prompted to add or trust the publisher before installation proceeds.

Publisher trust rules:

* The trusted publisher registry is the set of publisher identities that carry the `system.apps.publish` capability edge in `app_0`.
* Adding a publisher to the registry is a graph mutation handled by the Identity Service or Admin Service under a privileged [OperationContext](../02-architecture/services-and-apps/05-operation-context.md).

Response body (JSON):

* `app_id` (int)
* `slug` (string)
* `version` (string)
* `status` (string)
* `enabled` (bool)

Notes:

* Only the register flow is allowed to create app identities, manifests, and schemas.
* The response is minimal and non-authoritative; the backend graph remains the source of truth.

## 2. Preconditions

* Node bootstrap has completed.
* App slug is not already registered (or install is idempotent).
* Schema bundle passes structural validation.

## 3. Flow

1) Interface layer authenticates the caller and constructs OperationContext.

2) Interface layer verifies the ZIP signature and extracts `manifest.json`, `schema.json`, and optional `acl.json`.

3) Interface layer resolves the signature `signer_id` to a publisher identity in the graph (or binds `publisher_public_key` to a new publisher identity) and verifies the publisher is trusted for app publication. If the publisher is missing or untrusted, the install flow halts and requires user confirmation to add/trust the publisher.

4) App Manager registers the app slug and allocates app_id.

5) Key Manager generates the app identity keypair (app-scoped identity).

6) Graph Manager applies envelopes to:

   * Create app identity parent object.
   * Store app schema objects and version metadata.
   * Store app capability declarations (app-scoped attributes/edges).

7) Schema Manager validates the schema bundle.

8) ACL Manager establishes default app ACLs and capability bindings.

9) Storage Manager persists all writes atomically.

10) Event Manager emits app installation events after commit.

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

Failure mapping:

* Signature verification failure -> `ERR_APP_SIGNATURE_INVALID`.
* Missing or untrusted publisher -> `ERR_APP_PUBLISHER_UNTRUSTED`.
* Missing or invalid OperationContext -> `ERR_APP_SERVICE_CONTEXT`.
* Missing installer capability -> `ERR_APP_SERVICE_CAPABILITY`.
* Schema object validation failure -> `schema_validation_failed`.
* ACL object validation failure -> `schema_validation_failed`.
* ACL authorization failure -> `acl_denied`.
* Persistence failure -> `storage_error`.
* Transport status and error categories follow [04-error-model.md](../04-interfaces/04-error-model.md).
