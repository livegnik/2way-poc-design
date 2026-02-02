



# 03 Build and run

This document describes the minimal environment and commands for building and testing the PoC.

For the meta specifications, see [03-build-and-run-meta.md](../09-appendix/meta/07-poc/03-build-and-run-meta.md).

## 1. Environment

* Python 3.13
* Local virtual environment
* Dependencies in [requirements.txt](../../requirements.txt)

## 2. Build steps (minimal)

1) Create and activate a virtual environment.
2) Install dependencies from requirements.txt.
3) Run the test suite with pytest.

## 3. Test execution

* Run all tests: `pytest`
* Backend only: `pytest backend/tests`
* Frontend only: `pytest frontend/tests`

Tor-dependent or network-coupled tests support skipping if the runtime is unavailable, per [TEST-CONVENTIONS.md](../../TEST-CONVENTIONS.md).
