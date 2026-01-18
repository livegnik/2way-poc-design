



# SQLite layout

This document describes the SQLite layout used by the 2WAY backend. It follows the protocol object model and the backend manager boundaries. Storage Manager owns the database lifecycle and is the only component allowed to issue SQL. Graph objects are persisted only through Graph Manager, and every accepted envelope maps to exactly one transaction commit.

## Database file and connection rules

The database path is supplied by Config Manager and opened once by Storage Manager. The connection runs in WAL mode with a single writer at a time. Foreign key enforcement is disabled at the SQLite level, so referential integrity is enforced by Graph Manager and Schema Manager before persistence. All graph writes are serialized, atomic, and ordered, and immutable metadata fields are never modified after insert.

## Global tables

Global tables exist once per database and store system state and sequencing metadata. The tables are `identities` for identity registry data anchored in app_0, `apps` for the application registry, `peers` for known peer metadata, `settings` for node configuration snapshots, `sync_state` for per peer and per domain acceptance state, `domain_seq` for per peer and per domain ordering cursors, `global_seq` for the local monotonic sequence cursor, and `schema_migrations` for applied migration tracking.

## Per app table families

Every registered application has a dedicated table family named with the `app_N_` prefix where `N` is the numeric app_id. app_0 is reserved for system owned graph data, including identities and schemas. Per app tables are never dropped automatically, and all rows include an explicit `app_id` column even when the table name is scoped.

The per app table family includes `app_N_type`, `app_N_parent`, `app_N_attr`, `app_N_edge`, `app_N_rating`, and `app_N_log`. These tables are append only. Deletion is forbidden, and Storage Manager does not expose update or delete helpers for graph rows.

## Common graph columns

Every graph object row stores the immutable metadata fields `app_id`, `id`, `type_id`, `owner_identity`, `global_seq`, and `sync_flags` as defined by the object model. These values are assigned by Graph Manager and Storage Manager and must never be supplied or modified by callers. `global_seq` is strictly monotonic for the local node and is used for sync ordering. `sync_flags` records sync domain membership and is storage controlled.

## Graph object tables

`app_N_parent` stores Parent objects. In addition to the common metadata columns it stores `value_json`, which holds the schema defined payload for the parent.

`app_N_attr` stores Attribute objects. In addition to the common metadata columns it stores `src_parent_id` to bind the attribute to its source Parent and `value_json` for the schema defined payload.

`app_N_edge` stores Edge objects. In addition to the common metadata columns it stores `src_parent_id` and exactly one destination selector, `dst_parent_id` or `dst_attr_id`, with Graph Manager enforcing that only one destination column is populated.

`app_N_rating` stores Rating objects. In addition to the common metadata columns it stores exactly one target selector, `target_parent_id` or `target_attr_id`, and a `value_json` payload for the schema defined rating data.

ACL structures are represented using Parent and Attribute rows and are persisted in the same per app tables. There is no dedicated ACL table in the SQLite layout.

## Type registry tables

`app_N_type` stores derived type mappings produced by Schema Manager so `type_key` and `type_id` resolution is deterministic for each object kind. These rows are indices only. The authoritative schema source remains the graph objects stored in app_0, and type mappings are immutable once assigned.

## Log tables

`app_N_log` is reserved for internal per app bookkeeping and audit metadata owned by Storage Manager. It is not a graph object category and must not be written or read directly by other managers.
