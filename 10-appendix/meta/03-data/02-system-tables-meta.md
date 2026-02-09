



# 02 System tables

## 1. Purpose and scope

This document defines the global system tables stored in the 2WAY backend SQLite database. These tables exist exactly once per node and are created during bootstrap before any application data is written. It does not define per-app graph tables or schema semantics. Terminology is defined in [00-scope/03-definitions-and-terminology.md](../../../00-scope/03-definitions-and-terminology.md).

This specification consumes and is constrained by the protocol contracts defined in:

- [01-protocol/01-identifiers-and-namespaces.md](../../../01-protocol/01-identifiers-and-namespaces.md)
- [01-protocol/02-object-model.md](../../../01-protocol/02-object-model.md)
- [01-protocol/03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)
- [01-protocol/05-keys-and-identity.md](../../../01-protocol/05-keys-and-identity.md)
- [01-protocol/06-access-control-model.md](../../../01-protocol/06-access-control-model.md)
- [01-protocol/07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
- [01-protocol/10-errors-and-failure-modes.md](../../../01-protocol/10-errors-and-failure-modes.md)
- [01-protocol/11-versioning-and-compatibility.md](../../../01-protocol/11-versioning-and-compatibility.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining all global system tables that exist outside app-scoped graph storage
* Defining invariants for identity, sequencing, sync tracking, configuration, peer state, and auth token storage
* Defining when tables may be written, updated, or read
* Defining fail-closed behavior for corruption or inconsistency
* Defining startup and shutdown expectations related to system tables

This specification does not cover the following:

* Graph object persistence, which is owned by [Graph Manager](../../../02-architecture/managers/07-graph-manager.md)
* Schema compilation and type mapping, which is owned by [Schema Manager](../../../02-architecture/managers/05-schema-manager.md)
* ACL rule evaluation, which is owned by [ACL Manager](../../../02-architecture/managers/06-acl-manager.md) and defined in [01-protocol/06-access-control-model.md](../../../01-protocol/06-access-control-model.md)
* Sync envelope construction or validation, which is owned by [State Manager](../../../02-architecture/managers/09-state-manager.md) and defined in [01-protocol/03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)
* Network connectivity and transport, which is owned by [Network Manager](../../../02-architecture/managers/10-network-manager.md)
