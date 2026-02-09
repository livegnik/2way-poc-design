



# 00 Testing and conformance

Defines required test categories and conformance criteria for the PoC.

For the meta specifications, see [00-testing-and-conformance-meta.md](../10-appendix/meta/08-testing/00-testing-and-conformance-meta.md).

## 1. Test categories (required)

The PoC test plan MUST include:

* unit tests
* property-based tests
* protocol conformance tests
* integration tests
* system-level black-box tests
* replay tests
* fork and conflict tests
* crash and restart tests
* negative/adversarial tests
* fuzz tests
* soak tests
* smoke tests
* regression tests

LLM-aware invariant regression tests MUST NOT be used.

## 2. Conformance criteria (testable)

Conformance tests MUST verify:

* deterministic serialization of the signed portion ([01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md))
* structural rejection before persistence ([01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md), [01-protocol/10-errors-and-failure-modes.md](../01-protocol/10-errors-and-failure-modes.md))
* replay and ordering rejections ([01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md))

## 3. Coverage expectations

Every validation or rejection path MUST have at least one negative test.

System-level black-box tests MUST be runnable in CI using documented commands and environment variables.

## 4. Fuzz and soak bounds (authoritative defaults)

Fuzz suites MUST be bounded and deterministic by default:

* `FUZZ_SEED=0` unless overridden.
* `FUZZ_MAX_CASES=1000` per test.
* `FUZZ_MAX_SECONDS=10` per test.

Soak suites MUST be bounded and declare completion criteria:

* `SOAK_DURATION_MIN=30` minutes.
* `SOAK_DURATION_MAX=120` minutes.
* `SOAK_MIN_ENVELOPES=10000` across the run.
* `SOAK_MAX_INVARIANT_VIOLATIONS=0`.

## 5. Regression policy

Every fixed bug MUST add a regression test in `backend/tests/regression/` (or `frontend/tests/regression/` for frontend defects) that references the bug or issue ID.
