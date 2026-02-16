



# 03 Build and run

This document describes the minimal environment and commands for building and testing the PoC.

For the meta specifications, see [03-build-and-run-meta.md](../10-appendix/meta/07-poc/03-build-and-run-meta.md).

## 1. Environment

* Python 3.13
* Local virtual environment
* Dependencies documented in this spec and enforced in CI.

### 1.1 Launcher readiness defaults (when using `python -m launcher.app`)

* `LAUNCHER_READY_MARKER=BACKEND_READY`
* `LAUNCHER_BACKEND_READY_TIMEOUT_MS=15000`

## 2. Dependency management

Dependency sources and lockfiles are authoritative for the PoC build:

* `requirements.in` is the human-edited dependency source list.
* `requirements.txt` is the lockfile generated from `requirements.in` and MUST include hashes for every resolved artifact.
* CI and local builds MUST install dependencies from `requirements.txt` only.
* The lockfile is generated with `pip-compile --generate-hashes` (pip-tools) and committed to the repo.

## 2.1 Dependency source list (requirements.in)

The `requirements.in` contents are authoritative and MUST match this list exactly:

```
flask
sqlalchemy
bcrypt
ecdsa
cryptography
requests
websockets
pytest
hypothesis
pip-tools
```

## 3. Build steps (minimal)

1) Create and activate a virtual environment.

2) Install dependencies from `requirements.txt`.
3) Run the test suite with pytest.

## 4. Test execution

* Run all tests: `pytest`
* Backend only: `pytest backend/tests`
* Frontend only: `pytest frontend/tests`

Tor-dependent or network-coupled tests support skipping if the runtime is unavailable, per [TEST-CONVENTIONS.md](../../docs-build/hybrid/TEST-CONVENTIONS.md).

## 5. Documentation consistency checklist inputs

This section is the canonical source for the generated documentation checklist at `docs-build/automated/DOC-CHECKLIST.md`.

### 5.1 Manual docs checks

* Every `BP` step in [docs-build/manual/BUILD-PLAN.md](../../docs-build/manual/BUILD-PLAN.md) lists at least one `Rxxx`.
* Every route/config/error referenced in [docs-build/manual/BUILD-PLAN.md](../../docs-build/manual/BUILD-PLAN.md) exists in [docs-build/automated/ROUTES.md](../../docs-build/automated/ROUTES.md), [docs-build/automated/CONFIG.md](../../docs-build/automated/CONFIG.md), or [docs-build/automated/ERROR-CODES.md](../../docs-build/automated/ERROR-CODES.md).
* No `TODO` entries without an `Rxxx`.
* [docs-build/manual/DEFERRED.md](../../docs-build/manual/DEFERRED.md) contains all deferred IDs (if any are deferred).

### 5.2 Hybrid-generated docs checks

Operational checks:

* Every `Rxxx` appears exactly once in [docs-build/hybrid/TRACEABILITY.md](../../docs-build/hybrid/TRACEABILITY.md).
* Every `Rxxx` in [docs-build/hybrid/TRACEABILITY.md](../../docs-build/hybrid/TRACEABILITY.md) appears in [docs-build/hybrid/REQUIREMENTS-LEDGER.md](../../docs-build/hybrid/REQUIREMENTS-LEDGER.md).
* Every generated endpoint skeleton in [docs-build/hybrid/API-EXAMPLES.md](../../docs-build/hybrid/API-EXAMPLES.md) maps to canonical interface routes, and route/error skeletons are regenerated from interface specs.
* Every generated required-suite command in [docs-build/hybrid/CI.md](../../docs-build/hybrid/CI.md) maps to canonical test specs and Phase 9 build-plan suites.
* Every generated AC ledger row in [docs-build/hybrid/POC-ACCEPTANCE.md](../../docs-build/hybrid/POC-ACCEPTANCE.md) maps to canonical acceptance IDs and build-plan test references.
* Every generated canonical suite/bounds matrix in [docs-build/hybrid/TEST-CONVENTIONS.md](../../docs-build/hybrid/TEST-CONVENTIONS.md) maps to canonical testing spec matrices.

Regeneration checks:

| Artifact | Regenerate command | Regenerate after source changes |
| --- | --- | --- |
| `docs-build/hybrid/API-EXAMPLES.md` | `python docs-build/scripts/hybrid/generate_api_examples.py` | Interface endpoint/error contract changes under `specs/04-interfaces/01-local-http-api.md`, `specs/04-interfaces/09-system-services-http.md`, `specs/04-interfaces/05-sync-transport.md`, `specs/04-interfaces/06-app-lifecycle.md`, `specs/04-interfaces/13-auth-session.md`, `specs/04-interfaces/12-upload-http.md`, `specs/04-interfaces/02-websocket-events.md`, and `specs/04-interfaces/14-events-interface.md`. |
| `docs-build/hybrid/CI.md` | `python docs-build/scripts/hybrid/generate_ci.py` | CI-suite command or run-policy changes in `specs/08-testing/00-testing-and-conformance.md`, `specs/07-poc/03-build-and-run.md`, `specs/07-poc/04-test-plan.md`, and `docs-build/manual/BUILD-PLAN.md`. |
| `docs-build/hybrid/POC-ACCEPTANCE.md` | `python docs-build/scripts/hybrid/generate_poc_acceptance.py` | Acceptance criteria changes in `specs/07-poc/07-acceptance-criteria.md` or acceptance suite mapping changes in `docs-build/manual/BUILD-PLAN.md` (Phase 9). |
| `docs-build/hybrid/TEST-CONVENTIONS.md` | `python docs-build/scripts/hybrid/generate_test_conventions.py` | Testing suite matrix/bounds/command changes in `specs/08-testing/00-testing-and-conformance.md` or test-plan linkage changes in `specs/07-poc/04-test-plan.md`. |
| `docs-build/hybrid/REQUIREMENTS-LEDGER.md` | `python docs-build/scripts/hybrid/generate_requirements_ledger.py` | Requirement-anchor changes in canonical `/specs/**` (excluding meta specs). |
| `docs-build/hybrid/TRACEABILITY.md` | `python docs-build/scripts/hybrid/generate_traceability.py` | Requirement-anchor changes in canonical `/specs/**` (excluding meta specs). |

### 5.3 Auto-generated docs checks

| Artifact | Regenerate command | Regenerate after source changes |
| --- | --- | --- |
| `docs-build/automated/CONFIG.md` | `python docs-build/scripts/automated/generate_config.py` | Configuration-spec changes under `specs/02-architecture/managers/**`, `specs/02-architecture/services-and-apps/**`, and `specs/02-architecture/15-debug-logger.md`. |
| `docs-build/automated/DATA-MODEL.md` | `python docs-build/scripts/automated/generate_data_model.py` | Data/storage/frontend-auth spec changes under `specs/03-data/**`, `specs/02-architecture/managers/02-storage-manager.md`, `specs/02-architecture/managers/09-state-manager.md`, `specs/02-architecture/managers/04-auth-manager.md`, `specs/02-architecture/services-and-apps/04-frontend-apps.md`, and `specs/01-protocol/02-object-model.md`. |
| `docs-build/automated/DATAFLOW.md` | `python docs-build/scripts/automated/generate_dataflow.py` | Dataflow/flow/error-model/state/internal-api/auth spec changes under `specs/02-architecture/04-data-flow-overview.md`, `specs/06-flows/00-flows-overview.md`, `specs/04-interfaces/04-error-model.md`, `specs/02-architecture/managers/09-state-manager.md`, `specs/04-interfaces/03-internal-apis-between-components.md`, and `specs/02-architecture/managers/04-auth-manager.md`. |
| `docs-build/automated/DOC-CHECKLIST.md` | `python docs-build/scripts/automated/generate_doc_checklist.py` | Checklist input changes in `specs/07-poc/03-build-and-run.md` and `specs/10-appendix/meta/07-poc/03-build-and-run-meta.md`. |
| `docs-build/automated/ERROR-CODES.md` | `python docs-build/scripts/automated/generate_error_codes.py` | `specs/04-interfaces/04-error-model.md` and `specs/01-protocol/10-errors-and-failure-modes.md`. |
| `docs-build/automated/POC-APPS.md` | `python docs-build/scripts/automated/generate_poc_apps.py` | PoC app-spec changes under `specs/07-poc/00-poc-overview.md`, `specs/07-poc/02-feature-matrix.md`, `specs/02-architecture/managers/08-app-manager.md`, `specs/02-architecture/services-and-apps/03-app-services.md`, `specs/04-interfaces/06-app-lifecycle.md`, `specs/06-flows/02-app-install-and-permissions.md`, `specs/01-protocol/01-identifiers-and-namespaces.md`, `specs/01-protocol/02-object-model.md`, and `specs/01-protocol/03-serialization-and-envelopes.md`. |
| `docs-build/automated/ROUTES.md` | `python docs-build/scripts/automated/generate_routes.py` | Interface route-spec changes under `specs/04-interfaces/**`. |
| `docs-build/automated/SECURITY.md` | `python docs-build/scripts/automated/generate_security.py` | Security/auth/frontend/scope/error/data-boundary spec changes under `specs/05-security/00-security-overview.md`, `specs/05-security/01-threat-model-poc.md`, `specs/05-security/06-encryption-at-rest-and-key-storage.md`, `specs/05-security/09-privacy-selective-sync-and-domain-scoping.md`, `specs/00-scope/00-scope-overview.md`, `specs/04-interfaces/13-auth-session.md`, `specs/02-architecture/services-and-apps/04-frontend-apps.md`, `specs/01-protocol/04-cryptography.md`, `specs/01-protocol/03-serialization-and-envelopes.md`, `specs/03-data/02-system-tables.md`, and `specs/04-interfaces/04-error-model.md`. |
