



# 05 Migrations and upgrades

## 1. Purpose and scope

This document defines the migration and upgrade posture for the 2WAY backend SQLite database. It specifies ordering, idempotency, and failure handling for schema changes applied by Storage Manager. It does not define table schemas or SQL contents. Terminology is defined in [00-scope/03-definitions-and-terminology.md](../00-scope/03-definitions-and-terminology.md).

This specification consumes and is constrained by the protocol contracts defined in:

- [01-protocol/01-identifiers-and-namespaces.md](../01-protocol/01-identifiers-and-namespaces.md)
- [01-protocol/02-object-model.md](../01-protocol/02-object-model.md)
- [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md)
- [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md)
- [01-protocol/10-errors-and-failure-modes.md](../01-protocol/10-errors-and-failure-modes.md)
- [01-protocol/11-versioning-and-compatibility.md](../01-protocol/11-versioning-and-compatibility.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining migration identifier format and strict ordering guarantees
* Defining idempotent migration application rules
* Defining forward-only upgrade posture and failure handling
* Defining Storage Manager ownership of migration execution

This specification does not cover the following:

* Table schemas or column definitions, which are defined in [03-data/01-sqlite-layout.md](01-sqlite-layout.md)
* Per-app data modeling, which is defined in [03-data/03-per-app-tables.md](03-per-app-tables.md)
* Index requirements, which are defined in [03-data/04-indexing-strategy.md](04-indexing-strategy.md)
* Runtime graph validation, which is owned by [Graph Manager](../02-architecture/managers/07-graph-manager.md)
