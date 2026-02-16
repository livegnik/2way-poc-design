



# 06 App Lifecycle Interface

## 1. Purpose and scope

Defines the app lifecycle interface implied by App Manager and app service lifecycle rules.

This document references:

* [02-architecture/managers/08-app-manager.md](../../../02-architecture/managers/08-app-manager.md)
* [02-architecture/services-and-apps/03-app-services.md](../../../02-architecture/services-and-apps/03-app-services.md)
* [02-architecture/services-and-apps/05-operation-context.md](../../../02-architecture/services-and-apps/05-operation-context.md)
* [01-protocol/03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Declaring required lifecycle operations (install, list, enable, disable, uninstall, repair, open).
* Declaring canonical lifecycle state values and transition matrix rules.
* Declaring the canonical app artifact contract (ZIP layout, `manifest.json`, `schema.json`, optional `acl.json`, and `package_sig`).
* Declaring install payload fields for manifests, schema bundles, and ACL bundles.
* Declaring install payload constraints for schema/ACL objects (no `global_seq` or `sync_flags`).
* Declaring app package upload requirements (ZIP contents and detached signature).
* Declaring signature metadata schema (`publisher_public_key`, detached signature), local-graph publisher key resolution, and unknown-field rejection behavior for install artifacts.
* Declaring composition-specific app-service artifact requirements and post-validation service load/start ordering.
* Declaring slug-first package identity and forbidding node-local identifiers (for example, `manifest.app_id`) in package artifacts.
* Declaring publisher trust requirements for app installation.
* Stating validation, ordering, and fail-closed rules for lifecycle actions.
* Declaring lifecycle endpoint error responses.
* Declaring parent-scoped lifecycle error families (`ERR_SVC_APP_*`, `ERR_SVC_SYS_APP_*`) and rejecting legacy singleton roots.
* Declaring app service availability mappings for `ERR_SVC_APP_*` lifecycle failures.

This specification does not cover the following:

* App-specific frontend behavior.
