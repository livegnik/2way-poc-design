



# 00 Flows overview

## 1. Purpose and scope

This document defines the flow catalog for the 2WAY PoC. It enumerates the only allowed flow categories and establishes the invariants shared by all flows. It does not define schemas or implementation details beyond those required for flow correctness.

This specification references:

* [06-flows/**](../../../06-flows/)
* [02-architecture/04-data-flow-overview.md](../../../02-architecture/04-data-flow-overview.md)
* [01-protocol/00-protocol-overview.md](../../../01-protocol/00-protocol-overview.md)

## 2. Responsibilities and boundaries

This specification is responsible for:

* Defining the canonical list of flows implemented by the PoC.
* Stating shared invariants that apply to all flows.
* Pointing to the authoritative flow documents under `06-flows/`.

This specification does not cover:

* Graph object schemas or type definitions.
* Interface shapes or transport formats.
* UI or frontend behavior.
