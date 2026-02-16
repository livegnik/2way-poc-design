



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

## 1.1 Canonical suite matrix

The following suite matrix is authoritative for generated test-conventions references:

| Suite | Canonical marker | Scope |
| --- | --- | --- |
| Unit tests | `unit` | Single manager/module behavior and local invariants. |
| Property-based tests | `property` | Invariants across generated/randomized inputs. |
| Protocol conformance tests | `conformance` | Protocol rules, canonical bytes, and deterministic behavior. |
| Integration tests | `integration` | Cross-manager flows and interface wiring. |
| System-level black-box tests | `system` | End-to-end behavior against public interfaces. |
| Replay tests | `replay` | Re-application of accepted history. |
| Fork and conflict tests | `fork_conflict` | Conflict detection/rejection behavior. |
| Crash and restart tests | `crash_restart` | Recovery, restart replay, readiness gating. |
| Negative/adversarial tests | `adversarial` | Malformed inputs, policy bypass, boundary violations. |
| Fuzz tests | `fuzz` | Bounded parser/validation random input exploration. |
| Soak tests | `soak` | Long-run stability and invariant retention. |
| Smoke tests | `smoke` | Minimal boot/readiness and basic route checks. |
| Regression tests | `regression` | Bugfix lock-in and policy assertions. |

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

## 4.1 Canonical bounds matrix

| Variable | Default | Applies to |
| --- | --- | --- |
| `FUZZ_SEED` | `0` | Fuzz suites |
| `FUZZ_MAX_CASES` | `1000` | Fuzz suites |
| `FUZZ_MAX_SECONDS` | `10` | Fuzz suites |
| `SOAK_DURATION_MIN` | `30` | Soak suites |
| `SOAK_DURATION_MAX` | `120` | Soak suites |
| `SOAK_MIN_ENVELOPES` | `10000` | Soak suites |
| `SOAK_MAX_INVARIANT_VIOLATIONS` | `0` | Soak suites |

## 4.2 Performance sanity workload defaults (authoritative)

The Build Plan 3.5 perf sanity checks use the following deterministic workload:

* Database: isolated temp DB per test run.
* Commit case: first successful local `POST /graph/envelope` write on an empty DB, no warmup operation.
* Read fixture: insert exactly 200 Parent rows for `app_id=1` and `parent_type=perf.parent` before timing.
* Read query: `GraphReadRequest` with `app_id=1`, `target=parent`, `parent_type=perf.parent`, `limit=200`, `offset=0`, `order_by=global_seq`, `order_dir=asc`.
* Timing method: monotonic timer (`time.perf_counter` or equivalent).
* Warmup policy: exactly one unmeasured read before one measured read.
* Measurement scope: excludes fixture creation and process startup.
* Thresholds: commit under 2 seconds, measured read under 1 second.
* Logs: each check emits `PERF_SANITY` prefix.

## 5. CI suite command registry (authoritative)

Required CI-oriented pytest suite commands are:

| Suite | Command | Expected use |
| --- | --- | --- |
| Fast verification | `pytest -m fast` | Required PR/merge gate. |
| Full verification | `pytest -m "not soak and not fuzz"` | Required pre-release verification. |
| All tests | `pytest` | Optional full run when broad drift checks are needed. |
| Backend-only verification | `pytest backend/tests` | Backend-focused validation. |
| Frontend-only verification | `pytest frontend/tests` | Frontend-focused validation. |
| Fuzz verification | `pytest -m fuzz` | Scheduled or manual bounded fuzz runs. |
| Soak verification | `pytest -m soak` | Scheduled or manual long-run stability checks. |

## 6. Regression policy

Every fixed bug MUST add a regression test in `backend/tests/regression/` (or `frontend/tests/regression/` for frontend defects) that references the bug or issue ID.
