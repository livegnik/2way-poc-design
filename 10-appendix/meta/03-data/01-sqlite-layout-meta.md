



# 01 SQLite layout

## 1. Purpose and scope

This document defines the complete SQLite storage layout for the 2WAY backend. It specifies database topology, table families, column contracts, sequencing state, and persistence guarantees required to store canonical graph objects and synchronization metadata. It is normative for [Storage Manager](../../../02-architecture/managers/02-storage-manager.md) behavior and is binding for [Graph Manager](../../../02-architecture/managers/07-graph-manager.md) persistence semantics. Terminology is defined in [00-scope/03-definitions-and-terminology.md](../../../00-scope/03-definitions-and-terminology.md).

This document does not define schema semantics, ACL evaluation logic, sync policy decisions, cryptographic validation, or network behavior. Those responsibilities remain with their respective managers.

This specification consumes and is constrained by the protocol contracts defined in:

* [01-protocol/01-identifiers-and-namespaces.md](../../../01-protocol/01-identifiers-and-namespaces.md)
* [01-protocol/02-object-model.md](../../../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/05-keys-and-identity.md](../../../01-protocol/05-keys-and-identity.md)
* [01-protocol/07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/10-errors-and-failure-modes.md](../../../01-protocol/10-errors-and-failure-modes.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining the SQLite database topology used by the backend.
* Defining all required global tables and per app table families.
* Defining mandatory columns, immutability rules, and value domains.
* Defining sequencing and sync state persistence structures.
* Defining startup, migration, shutdown, and crash recovery expectations for persistence.
* Defining indexing posture requirements without embedding index definitions.
* Defining failure and fail-closed behavior for persistence operations.

This specification does not cover the following:

* Graph object validation rules.
* Schema compilation or interpretation.
* ACL rule evaluation or merging logic.
* Sync policy, filtering logic, or peer eligibility.
* Network transport or cryptographic operations.
* Application domain semantics.
