



# 04 Test plan

The PoC test plan ensures each protocol and manager requirement is covered by an executable test.

For the meta specifications, see [04-test-plan-meta.md](../09-appendix/meta/07-poc/04-test-plan-meta.md).

## 1. Test categories

* Unit tests for managers, protocol validation, and services.
* Integration tests for cross-manager flows.
* End-to-end acceptance placeholders for full PoC verification.

## 2. Required coverage

* Every manager has at least one unit and one negative test.
* Protocol rules have traceability entries in [TRACEABILITY.md](../../TRACEABILITY.md).
* Phase exit criteria are backed by runnable tests in the build plan.

## 3. Acceptance criteria alignment

The acceptance criteria are defined in [POC-ACCEPTANCE.md](../../POC-ACCEPTANCE.md). Tests that verify each criterion exist and are runnable.

## 4. Execution rules

All tests run under pytest. See [TEST-CONVENTIONS.md](../../TEST-CONVENTIONS.md) for markers and layout.
