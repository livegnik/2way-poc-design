



# 01 First-run and identity bootstrap

## 1. Purpose and scope

Defines the first-run bootstrap flow that initializes the Server Graph and first admin identity. This flow runs once per node.

This specification references:

* [06-flows/01-first-run-and-identity-bootstrap.md](../../../06-flows/01-first-run-and-identity-bootstrap.md)
* [02-architecture/04-data-flow-overview.md](../../../02-architecture/04-data-flow-overview.md)
* [02-architecture/services-and-apps/02-system-services.md](../../../02-architecture/services-and-apps/02-system-services.md)
* [01-protocol/05-keys-and-identity.md](../../../01-protocol/05-keys-and-identity.md)

## 2. Responsibilities and boundaries

This specification is responsible for:

* Defining the required ordering of bootstrap steps.
* Declaring allowed and forbidden behavior during bootstrap.
* Defining fail-closed semantics for bootstrap failures.

This specification does not cover:

* Production installation UX or deployment tooling.
* UI workflows for onboarding or recovery.
