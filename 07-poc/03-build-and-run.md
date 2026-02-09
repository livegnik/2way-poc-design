



# 03 Build and run

This document describes the minimal environment and commands for building and testing the PoC.

For the meta specifications, see [03-build-and-run-meta.md](../10-appendix/meta/07-poc/03-build-and-run-meta.md).

## 1. Environment

* Python 3.13
* Local virtual environment
* Dependencies documented in this spec and enforced in CI.

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
coincurve
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

Tor-dependent or network-coupled tests support skipping if the runtime is unavailable, per [TEST-CONVENTIONS.md](../../docs-build/TEST-CONVENTIONS.md).

