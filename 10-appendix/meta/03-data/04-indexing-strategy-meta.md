



# 04 Indexing strategy

## 1. Purpose and scope

This document defines the indexing strategy for the 2WAY backend SQLite database. It specifies which indexes Storage Manager must provide to support protocol and manager guarantees, and which query patterns those indexes exist to accelerate. It does not define SQL schemas, query plans, or application-specific optimizations. Terminology is defined in [00-scope/03-definitions-and-terminology.md](../../../00-scope/03-definitions-and-terminology.md).

This specification consumes and is constrained by the protocol contracts defined in:

- [01-protocol/01-identifiers-and-namespaces.md](../../../01-protocol/01-identifiers-and-namespaces.md)
- [01-protocol/02-object-model.md](../../../01-protocol/02-object-model.md)
- [01-protocol/03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)
- [01-protocol/06-access-control-model.md](../../../01-protocol/06-access-control-model.md)
- [01-protocol/07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
- [01-protocol/10-errors-and-failure-modes.md](../../../01-protocol/10-errors-and-failure-modes.md)
- [01-protocol/11-versioning-and-compatibility.md](../../../01-protocol/11-versioning-and-compatibility.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining the mandatory index families required for manager SLAs
* Defining index scope across global tables and per-app table families
* Defining index stability requirements during upgrades and maintenance
* Defining failure posture for index corruption or mismatch

This specification does not cover the following:

* Table schemas or column definitions, which are defined in [03-data/01-sqlite-layout.md](../../../03-data/01-sqlite-layout.md)
* Graph validation or query semantics, which are owned by [Graph Manager](../../../02-architecture/managers/07-graph-manager.md)
* Schema compilation or type mapping, which are owned by [Schema Manager](../../../02-architecture/managers/05-schema-manager.md)
* ACL rule evaluation, which is owned by [ACL Manager](../../../02-architecture/managers/06-acl-manager.md) and defined in [01-protocol/06-access-control-model.md](../../../01-protocol/06-access-control-model.md)
* Sync policy and peer eligibility, which are owned by [State Manager](../../../02-architecture/managers/09-state-manager.md)
