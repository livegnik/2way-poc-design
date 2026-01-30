



# 03 Per-app tables

## 1. Purpose and scope

This document defines the per-app table families stored in the 2WAY backend SQLite database. These tables store canonical graph objects for a single application domain and are created once per registered app under the `app_N_` prefix. It does not define global system tables or storage engine behavior outside app-scoped graph data. Terminology is defined in [00-scope/03-definitions-and-terminology.md](../00-scope/03-definitions-and-terminology.md).

This specification consumes and is constrained by the protocol contracts defined in:

- [01-protocol/01-identifiers-and-namespaces.md](../01-protocol/01-identifiers-and-namespaces.md)
- [01-protocol/02-object-model.md](../01-protocol/02-object-model.md)
- [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md)
- [01-protocol/05-keys-and-identity.md](../01-protocol/05-keys-and-identity.md)
- [01-protocol/06-access-control-model.md](../01-protocol/06-access-control-model.md)
- [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md)
- [01-protocol/10-errors-and-failure-modes.md](../01-protocol/10-errors-and-failure-modes.md)
- [01-protocol/11-versioning-and-compatibility.md](../01-protocol/11-versioning-and-compatibility.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining the per-app table family naming scheme and lifecycle
* Defining all per-app tables used to store graph objects and derived indices
* Defining shared metadata columns and immutability constraints
* Defining app-scoped isolation rules and reference constraints
* Defining failure posture for per app table corruption or inconsistency

This specification does not cover the following:

* Global system tables, which are defined in [03-data/02-system-tables.md](02-system-tables.md)
* Schema compilation and type mapping semantics, which are owned by [Schema Manager](../02-architecture/managers/05-schema-manager.md)
* ACL rule evaluation, which is owned by [ACL Manager](../02-architecture/managers/06-acl-manager.md) and defined in [01-protocol/06-access-control-model.md](../01-protocol/06-access-control-model.md)
* Envelope validation and acceptance rules, which are owned by [Graph Manager](../02-architecture/managers/07-graph-manager.md)
* Sync envelope construction or validation, which is owned by [State Manager](../02-architecture/managers/09-state-manager.md)
* Network transport behavior, which is owned by [Network Manager](../02-architecture/managers/10-network-manager.md)
