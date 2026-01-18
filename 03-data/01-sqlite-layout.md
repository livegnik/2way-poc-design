



# SQLite layout

## 1. Purpose and scope

This document defines the SQLite storage layout for the 2WAY backend. It is aligned with the protocol object model and the manager boundaries. Storage Manager owns the database lifecycle and is the only component allowed to issue SQL, while Graph Manager remains the only write path for graph objects. Every accepted envelope maps to exactly one committed SQLite transaction.

## 2. Responsibilities and boundaries

This specification covers the database topology, required tables, column conventions, and sequencing metadata necessary to persist canonical graph objects and sync state. It does not define schema semantics, ACL evaluation, sync policy, or network behavior, which remain in the protocol and manager specifications.

## 3. Invariants and guarantees

SQLite persistence is append only for graph objects, immutable metadata fields are never mutated after insert, and deletions are forbidden. All graph writes are serialized, atomic, and ordered, with no partial acceptance. Global sequencing and domain sequencing advance only after a successful commit, and failures never advance sequence state.

## 4. Database topology

### 4.1 Connection and pragmas

The database path is supplied by Config Manager and opened once by Storage Manager. WAL mode is mandatory, a busy timeout is enforced, and foreign key enforcement is disabled so referential integrity remains a protocol level concern. Failure to apply required pragmas aborts startup. Savepoints are used only for internal composition and never expose partial acceptance to callers.

### 4.2 Global tables

Global tables exist once per database and store system state and sequencing metadata. The required tables are `identities`, `apps`, `peers`, `settings`, `sync_state`, `domain_seq`, `global_seq`, and `schema_migrations`. These tables are created during bootstrap inside a single transaction that also seeds the initial `global_seq` row and applies any pending migrations. Startup fails closed if a global table is missing, if the sequence seed is absent, or if migrations fail.

### 4.3 Per app table families

Every registered application has a dedicated table family named with the `app_N_` prefix where `N` is the numeric app_id. app_0 is reserved for system owned graph data, including identities and schemas. Per app tables are never dropped automatically, and all rows include an explicit `app_id` column even when the table name is scoped.

The per app table family includes `app_N_type`, `app_N_parent`, `app_N_attr`, `app_N_edge`, `app_N_rating`, and `app_N_log`. These tables are append only, and Storage Manager does not expose update or delete helpers for graph rows. Updates to graph rows are limited to value bearing payload columns when the object model permits updates and higher level managers authorize them.

### 4.4 Common graph columns

Every graph object row stores the immutable metadata fields `app_id`, `id`, `type_id`, `owner_identity`, `global_seq`, and `sync_flags` as defined by the object model. These values are assigned by Graph Manager and Storage Manager and must never be supplied or modified by callers. `global_seq` is strictly monotonic for the local node and is used for sync ordering, while `sync_flags` records sync domain membership and is storage controlled. Object references are stored as explicit identifiers in the same app namespace, and cross app references or unresolved identifiers must be rejected before persistence.

### 4.5 Graph object tables

`app_N_parent` stores Parent objects and includes `value_json` for the schema defined payload. `app_N_attr` stores Attribute objects and includes `src_parent_id` plus `value_json`. `app_N_edge` stores Edge objects and includes `src_parent_id` and exactly one destination selector, either `dst_parent_id` or `dst_attr_id`, with Graph Manager enforcing that only one destination column is populated. `app_N_rating` stores Rating objects and includes exactly one target selector, either `target_parent_id` or `target_attr_id`, plus `value_json` for the rating payload.

ACL structures are represented using Parent and Attribute rows and are persisted in the same per app tables. There is no dedicated ACL table in the SQLite layout.

### 4.6 Type registry tables

`app_N_type` stores derived type mappings produced by Schema Manager so `type_key` and `type_id` resolution is deterministic for each object kind. These rows are indices only, the authoritative schema source remains the graph objects stored in app_0, and type mappings are immutable once assigned.

### 4.7 Log tables

`app_N_log` is reserved for internal per app bookkeeping and audit metadata owned by Storage Manager. It is not a graph object category and must not be written or read directly by other managers.

## 5. Sequencing and sync state storage

`global_seq` stores the local monotonic cursor used to order accepted envelopes and is never reused. `domain_seq` stores per peer and per domain ordering cursors, and `sync_state` stores the last accepted sequence and related acceptance metadata required by the sync protocol. These tables advance only when an envelope is fully accepted and persisted, and they never advance on rejection.

## 6. Indexing posture

Indexes exist to support global sequence scans, sync eligibility, type lookups, ownership queries, and edge directionality. Index definitions are specified in the indexing strategy document and created idempotently by Storage Manager, but the layout here guarantees that the indexed columns are present and stable.

## 7. Migrations and failure posture

Schema migrations are recorded in `schema_migrations` and run only during Storage Manager startup. Migrations must preserve the canonical object layout and downgrades are not supported. Any migration failure, corruption detection, or invariant violation causes the backend to fail closed without attempting repair, and recovery requires operator intervention.
