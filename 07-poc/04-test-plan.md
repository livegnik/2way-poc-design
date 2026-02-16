



# 04 Test plan

The PoC test plan ensures each protocol and manager requirement is covered by an executable test.

For the meta specifications, see [04-test-plan-meta.md](../10-appendix/meta/07-poc/04-test-plan-meta.md).

## 1. Test categories

Required categories are defined in [08-testing/00-testing-and-conformance.md](../08-testing/00-testing-and-conformance.md).

## 2. Required coverage

* Every manager has at least one unit and one negative test.
* Protocol rules have traceability entries in [TRACEABILITY.md](../../docs-build/hybrid/TRACEABILITY.md).
* Phase exit criteria are backed by runnable tests in the build plan.
* System-level black-box tests map to [POC-ACCEPTANCE.md](../../docs-build/hybrid/POC-ACCEPTANCE.md) criteria.

## 3. System-level black-box alignment

The acceptance criteria are defined in [POC-ACCEPTANCE.md](../../docs-build/hybrid/POC-ACCEPTANCE.md). System-level black-box tests that verify each criterion exist and are runnable.

## 4. Execution rules

All tests run under pytest. See [TEST-CONVENTIONS.md](../../docs-build/hybrid/TEST-CONVENTIONS.md) for markers and layout.
