



# Notes app package (v1.0.0)

Example install artifact set for `POST /api/system/apps/register`.

Canonical contract reference:

* `specs/04-interfaces/06-app-lifecycle.md` Section 2.3.

Expected ZIP layout:

* `manifest.json` (required)
* `schema.json` (required)
* `acl.json` (optional)
* `app-service/main.py` (required when `manifest.composition` is `service` or `hybrid`)

Detached signature payload:

* `package_sig.json` (shape equivalent to uploaded `package_sig` file content)
