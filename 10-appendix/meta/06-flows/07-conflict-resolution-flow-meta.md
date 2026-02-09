



# 07 Conflict resolution flow

## 1. Purpose and scope

Defines how conflicting operations are handled in the PoC, using deterministic ordering and rejection rather than merging.

This specification references:

* [06-flows/07-conflict-resolution-flow.md](../../../06-flows/07-conflict-resolution-flow.md)
* [01-protocol/07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/10-errors-and-failure-modes.md](../../../01-protocol/10-errors-and-failure-modes.md)

## 2. Responsibilities and boundaries

This specification is responsible for:

* Declaring ordering guarantees for conflicting data.
* Defining rejection behavior for invalid or out-of-order operations.
* Mapping conflict rejection conditions to error codes and transport outcomes.

This specification does not cover:

* App-specific merge strategies.
* UI conflict resolution workflows.
