



# 04 Indexing strategy

Defines required index families and access patterns for backend SQLite tables. Specifies indexing guarantees, ownership, and operational constraints. Defines index maintenance expectations for query performance.

For the meta specifications, see [04-indexing-strategy meta](../10-appendix/meta/03-data/04-indexing-strategy-meta.md).

## 1. Invariants and guarantees

Across all indexes defined in this file, the following invariants and guarantees hold:

* Indexes are advisory for performance only and must never be relied on for correctness
* Missing or degraded indexes must never change query results or acceptance decisions
* Index creation and rebuild operations are idempotent and safe to rerun
* Index definitions are stable across compatible versions per [01-protocol/11-versioning-and-compatibility.md](../01-protocol/11-versioning-and-compatibility.md)
* Indexes never change the authoritative data model defined in [01-protocol/02-object-model.md](../01-protocol/02-object-model.md)
* Index maintenance must never advance `global_seq` or any sync cursor per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md)

These guarantees hold regardless of caller, execution context, input source, or peer behavior.

## 2. Ownership and access rules

All indexes defined here are owned exclusively by [Storage Manager](../02-architecture/managers/02-storage-manager.md). No other manager or service may create, drop, or modify indexes directly.

* [Storage Manager](../02-architecture/managers/02-storage-manager.md) is the sole owner of all indexes
* [Graph Manager](../02-architecture/managers/07-graph-manager.md) may request index presence checks but may not create or drop indexes
* [State Manager](../02-architecture/managers/09-state-manager.md) may request index health diagnostics for sync performance only
* No system service, app, or app service may access SQLite index definitions directly
* Direct SQL access outside Storage Manager is forbidden

Violation of these rules is a fatal implementation error.

## 3. Index catalog

Indexes are grouped by table family. All index names and SQL definitions are implementation details managed by [Storage Manager](../02-architecture/managers/02-storage-manager.md). This catalog defines required index purposes, not explicit DDL.

### 3.1 Global table indexes

#### identities

Indexes must support:

* lookup by `identity_id` for identity resolution
* fast validation of identity existence for envelope and ACL checks

#### apps

Indexes must support:

* lookup by `app_id`
* lookup by `slug`

#### peers

Indexes must support:

* lookup by peer identifier
* lookup by associated identity_id
* fast scans by last contact or handshake time for scheduling

#### settings

Indexes must support:

* lookup by setting key

#### sync_state

Indexes must support:

* lookup by `(peer_id, sync_domain)`
* monotonic cursor reads for replay protection per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md)

#### domain_seq

Indexes must support:

* lookup by `(peer_id, sync_domain)`
* efficient reads for sync eligibility decisions per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md)

#### global_seq

Indexes must support:

* fast access to the single sequence row

#### schema_migrations

Indexes must support:

* lookup by migration identifier

### 3.2 Per app graph object indexes

For every `app_N_` family, indexes must support the following access patterns on the graph object tables.

#### `app_N_parent`

Indexes must support:

* lookup by `(app_id, id)`
* lookup by `type_id` for type-scoped scans
* lookup by `owner_identity` for ACL evaluation
* lookup by `global_seq` for ordered sync scans

#### `app_N_attr`

Indexes must support:

* lookup by `(app_id, id)`
* lookup by `src_parent_id` for adjacency traversal
* lookup by `type_id` for type-scoped scans
* lookup by `owner_identity` for ACL evaluation
* lookup by `global_seq` for ordered sync scans

#### `app_N_edge`

Indexes must support:

* lookup by `(app_id, id)`
* lookup by `src_parent_id` for outbound traversal
* lookup by `dst_parent_id` and `dst_attr_id` for inbound traversal
* lookup by `type_id` for type-scoped scans
* lookup by `owner_identity` for ACL evaluation
* lookup by `global_seq` for ordered sync scans

#### `app_N_rating`

Indexes must support:

* lookup by `(app_id, id)`
* lookup by `target_parent_id` and `target_attr_id` for inbound traversal
* lookup by `type_id` for type-scoped scans
* lookup by `owner_identity` for ACL evaluation
* lookup by `global_seq` for ordered sync scans

### 3.3 Per app derived and operational indexes

#### `app_N_type`

Indexes must support:

* lookup by `(object_kind, type_key)`
* lookup by `(object_kind, type_id)`

These indexes are required for deterministic type resolution per [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md).

#### `app_N_log`

Indexes must support:

* lookup by log category
* lookup by timestamp for bounded scans

These indexes are operational only and must not be relied on for protocol correctness.

## 4. Indexing posture and correctness

Indexes exist solely to accelerate read and sync scan workloads. All correctness constraints remain enforced by the protocol and manager layers, not by index presence or SQL constraints.

* Referential integrity is enforced by protocol validation, not indexes or foreign keys.
* Cross-app references are rejected by [Graph Manager](../02-architecture/managers/07-graph-manager.md) per [01-protocol/01-identifiers-and-namespaces.md](../01-protocol/01-identifiers-and-namespaces.md).
* Sync ordering and replay protection are enforced by [State Manager](../02-architecture/managers/09-state-manager.md) per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).

## 5. Creation, rebuild, and migration

* Index creation is owned by [Storage Manager](../02-architecture/managers/02-storage-manager.md) and occurs idempotently during startup or maintenance windows.
* Index rebuilds may be triggered after migrations or detected corruption.
* Index changes must preserve column contracts defined in [03-data/01-sqlite-layout.md](01-sqlite-layout.md).
* Index creation or rebuild must never expose partial acceptance or advance any sequence cursor.

## 6. Failure posture

The system fails closed under the following conditions:

* index corruption that produces inconsistent query behavior
* index definitions that do not match the expected column contracts
* missing required index that prevents mandatory read paths from meeting resource constraints and cannot be rebuilt

Automatic repair is permitted only for index rebuilds. Any detected corruption in base tables remains a fatal error per [01-protocol/10-errors-and-failure-modes.md](../01-protocol/10-errors-and-failure-modes.md).

## 7. Explicitly forbidden behavior

The following behavior is forbidden:

* direct SQL access or index manipulation outside Storage Manager
* relying on index presence for correctness or validation
* creating custom indexes that alter or reinterpret protocol-defined fields or violate column contracts
* index rebuilds that run during active graph write transactions
* index changes that alter or reinterpret protocol-defined fields

Any implementation performing these actions is incorrect.
