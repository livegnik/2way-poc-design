# 02 Reference config

This file summarizes configuration namespaces and points to the authoritative configuration specs. It is non-normative.

Authoritative sources:

- `specs/02-architecture/managers/01-config-manager.md` (namespace ownership, invariants, and load/reload rules).
- `docs-build/CONFIG.md` (build-facing config checklist).

## Namespace index (non-normative)

- `node.*` boot identity and protocol version
- `storage.*` persistence settings
- `graph.*` graph engine settings
- `schema.*` schema compilation settings
- `auth.*` local authentication settings
- `key.*` key custody settings
- `network.*` transport settings
- `acl.*` authorization settings
- `dos.*` DoS guard settings
- `log.*` logging settings
- `event.*` event routing settings
- `health.*` readiness and liveness settings
- `state.*` sync settings
- `service.<service_name>.*` system service settings
- `app.<slug>.*` app scoped settings

The owning manager for each namespace is defined in `specs/02-architecture/managers/01-config-manager.md`.
