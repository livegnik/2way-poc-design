



# 03 Build and run

## 1. Purpose and scope

Defines the minimal build and run guidance for the PoC.

This specification references:

* [07-poc/03-build-and-run.md](../../../07-poc/03-build-and-run.md)
* [IMPLEMENTATION-CHOICES.md](../../../../docs-build/manual/IMPLEMENTATION-CHOICES.md)
* [CI.md](../../../../docs-build/hybrid/CI.md)
* [TEST-CONVENTIONS.md](../../../../docs-build/hybrid/TEST-CONVENTIONS.md)
* [DOC-CHECKLIST.md](../../../../docs-build/automated/DOC-CHECKLIST.md)

## 2. Responsibilities and boundaries

This specification is responsible for:

* Defining the required environment, dependency source list, dependency lockfile posture, and minimal test execution steps.
* Defining launcher readiness default inputs used by local build-and-run workflows.
* Defining canonical checklist inputs used to generate documentation consistency checks.
* Defining that hybrid API-example skeleton regeneration inputs are tracked through the same checklist-input source section.
* Defining that hybrid CI required-suite command regeneration inputs are tracked through the same checklist-input source section.
* Defining that hybrid PoC acceptance ledger regeneration inputs are tracked through the same checklist-input source section.
* Defining that hybrid test-conventions suite/bounds matrix regeneration inputs are tracked through the same checklist-input source section.

This specification does not cover:

* Deployment tooling or production runtime concerns.
