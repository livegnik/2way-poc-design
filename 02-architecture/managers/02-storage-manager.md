# 02 Storage Manager

## 1. Purpose and scope

Storage Manager is the sole owner of durable state for the 2WAY backend runtime. It manages the SQLite database lifecycle, schema creation, per-app table provisioning, and transactional helpers used by every manager and service. This specification defines the data model, APIs, invariants, and operational behaviors that Storage Manager must uphold. The scope includes the global tables shared by all apps, the per-app table families, global sequence persistence primitives, synchronization helpers, indexing rules, maintenance routines, and trust boundaries. It does not re-specify higher level business logic, graph semantics, or sync algorithms beyond the storage responsibilities required to support them.

## 2. Responsibilities and boundaries

Storage Manager is responsible for:

* Owning a single SQLite connection (and its WAL file) for the backend runtime, including opening, migrations, pragmas, and shutdown.
* Creating and upgrading the global schema plus per-app table sets on demand.
* Providing typed helper methods for managers and services to insert, update, and query rows without bypassing schema constraints, plus narrowly-scoped deletion hooks limited to maintenance tasks or Graph Manager flows that policy permits.
* Supplying atomic persistence primitives for the monotonic `global_seq` counter plus `domain_seq` and `sync_state`; Graph Manager and State Manager decide when sequences are consumed and what they mean.
* Acting as the persistence layer for configuration (`settings`), peer metadata, App Manager metadata, and application graphs while recognizing that graph tables remain the source of truth (e.g., identities are authoritative in app_0 and only cached elsewhere).
* Enforcing transactional consistency, locking rules, and write batching so that higher-level managers remain free of SQLite details.
* Exposing observability (metrics, pragmas, vacuum stats) to Health and Log Managers.

Storage Manager explicitly does not:

* Perform application-specific validation beyond referential integrity and schema constraints. Services own semantic validation of their domain objects.
* Implement ACL checks or OperationContext filtering. Callers must already possess authorization to read or mutate records.
* Expose raw SQLite connections or allow arbitrary SQL execution from other managers. All access flows through typed helpers or vetted query builders.
* Handle cryptographic material; blobs and key references are stored, but actual key custody belongs to Key Manager.
* Replicate data to peers. Sync services leverage the sequences and query helpers provided here, but networking is handled by Network and Sync managers.

## 3. Storage topology and schema

### 3.1 Database connection and pragmas

* Storage Manager opens a single SQLite database file (default `backend/instance/backend.db`) discovered via Config Manager.
* Connection is opened with WAL mode enabled for concurrent reads and crash resilience: `PRAGMA journal_mode=WAL;`.
* Additional pragmas enforced at open: `synchronous=NORMAL`, `foreign_keys=ON`, `temp_store=MEMORY`, `busy_timeout=5000`.
* Storage Manager serializes schema creation and migrations inside a bootstrap transaction so that concurrent startups cannot trample the file.
* Managers never hold the connection directly; they receive transactional handles (context managers) that enforce timeouts and wrap statements with logging.

### 3.2 Global tables

The following tables exist in every database and are created on first boot. Storage Manager maintains them and exposes CRUD helpers.

```sql
CREATE TABLE IF NOT EXISTS identities (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    pubkey     TEXT NOT NULL,
    label      TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS apps (
    app_id     INTEGER PRIMARY KEY,
    slug       TEXT UNIQUE NOT NULL,
    title      TEXT NOT NULL,
    version    INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_state (
    peer_id  INTEGER,
    domain   TEXT,
    last_seq INTEGER NOT NULL,
    PRIMARY KEY (peer_id, domain)
);

CREATE TABLE IF NOT EXISTS domain_seq (
    domain   TEXT PRIMARY KEY,
    last_seq INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS peers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    identity_id INTEGER NOT NULL,
    endpoint    TEXT NOT NULL,
    meta_json   TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS global_seq (
    id   INTEGER PRIMARY KEY CHECK (id = 1),
    seq  INTEGER NOT NULL
);
```

* `global_seq` is initialized with a single row `(id=1, seq=0)` on the first run. Storage Manager advances it atomically but does not decide when logical operations should claim the counter; Graph Manager determines sequencing policy.
* `settings` belongs to Config Manager, but Storage Manager enforces its persistence guarantees and transactions.
* `sync_state` and `domain_seq` persist sync watermarks. Storage Manager only records the numbers provided by sync or State Manager flows, while State Manager defines what a "flush complete" event means before requesting an increment.
* `identities` acts only as a local cache/registry (e.g., for peer metadata). The authoritative identity records live in the graph (app_0 parents/attributes); Storage Manager must not treat this cache as the source of truth and sync logic may choose to rebuild it from the graph.
* SQLite-level foreign keys are not declared in this schema; Graph Manager and Schema Manager enforce referential integrity in validation logic to preserve append-only behaviors and cross-app referencing rules.

### 3.3 Per-app tables

For every app registered in `apps`, Storage Manager ensures the following table family exists. The placeholder `N` below is the numeric `app_id`.

```sql
CREATE TABLE IF NOT EXISTS app_N_type (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    kind     TEXT NOT NULL,           -- 'parent' | 'attr' | 'edge' | 'rating'
    type_key TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS app_N_parent (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    type_id        INTEGER NOT NULL,
    owner_identity INTEGER NOT NULL,
    global_seq     INTEGER NOT NULL,
    sync_flags     INTEGER NOT NULL,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_N_attr (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id      INTEGER NOT NULL,
    type_id        INTEGER NOT NULL,
    owner_identity INTEGER NOT NULL,
    global_seq     INTEGER NOT NULL,
    sync_flags     INTEGER NOT NULL,
    value_text     TEXT,
    value_number   REAL,
    value_blob     BLOB,
    value_json     TEXT
);

CREATE TABLE IF NOT EXISTS app_N_edge (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    src_parent_id  INTEGER NOT NULL,
    dst_parent_id  INTEGER,
    dst_attr_id    INTEGER,
    type_id        INTEGER NOT NULL,
    owner_identity INTEGER NOT NULL,
    global_seq     INTEGER NOT NULL,
    sync_flags     INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS app_N_rating (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    target_parent_id INTEGER,
    target_attr_id   INTEGER,
    type_id          INTEGER NOT NULL,
    owner_identity   INTEGER NOT NULL,
    global_seq       INTEGER NOT NULL,
    sync_flags       INTEGER NOT NULL,
    value_text       TEXT,
    value_number     REAL,
    value_json       TEXT
);

CREATE TABLE IF NOT EXISTS app_N_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    level        TEXT NOT NULL,
    event_type   TEXT NOT NULL,
    context_json TEXT NOT NULL,
    created_at   TEXT NOT NULL
);
```

* `app_N_type` serves as a registry of semantic types per app, partitioned by `kind`. Storage Manager enforces uniqueness of `type_key` but defers semantic meaning to Schema Manager.
* `sync_flags` is a bit-set consumed by sync services for queueing/purge semantics. Storage Manager treats it opaquely yet indexes it for range scans (see below).
* `value_*` columns provide sparse storage for heterogenous attribute payloads. Only one of the columns should be populated per row, but Storage Manager does not enforce mutual exclusivity beyond optional helper assertions.

### 3.4 Indexes and naming conventions

* Indexes are materialized per app:
  * `CREATE INDEX IF NOT EXISTS app_N_parent_type_owner ON app_N_parent (type_id, owner_identity);`
  * `CREATE INDEX IF NOT EXISTS app_N_parent_sync ON app_N_parent (sync_flags, global_seq);`
  * `CREATE INDEX IF NOT EXISTS app_N_attr_parent_type ON app_N_attr (parent_id, type_id);`
  * `CREATE INDEX IF NOT EXISTS app_N_edge_src_type ON app_N_edge (src_parent_id, type_id);`
  * `CREATE INDEX IF NOT EXISTS app_N_edge_dst_type ON app_N_edge (dst_parent_id, type_id);`
* Index DDL is idempotent and runs inside the same transaction that creates the tables to avoid race conditions.
* Table names always follow `app_<id>_<noun>` pattern to simplify programmatic creation and introspection.
* Storage Manager exposes helper methods such as `ensure_app_schema(app_id)` and caches which tables already exist to reduce redundant DDL.

## 4. Initialization and lifecycle

1. During backend startup, Config Manager hands Storage Manager the resolved database path plus runtime pragmas.
2. Storage Manager opens the connection, applies pragmas, verifies WAL files, and begins a bootstrap transaction.
3. Global tables (section 3.2) are created if missing. `global_seq` row is inserted when absent.
4. Any pending migrations are applied (section 8). Migrations are versioned and deterministic; failure aborts startup.
5. Storage Manager scans the `apps` table and ensures each app schema exists by invoking `ensure_app_schema`.
6. After bootstrap, Storage Manager exposes transactional helpers (`with_txn`, `read_only`, `write_batch`) to other managers. Each helper attaches metadata for logging and debugging.
7. Shutdown closes the connection gracefully, checkpointing WAL files to avoid leaking disk usage.

## 5. APIs and helper methods

The manager exposes typed methods rather than raw SQL. Examples:

* `with_read_only(do_work)` / `with_transaction(do_work)` - executes a callable with a cursor, automatically commits or rolls back.
* `get_global_seq()` - returns current sequence without incrementing.
* `next_global_seq()` - atomically increments and returns the new sequence inside a write transaction.
* `insert_parent(app_id, parent_row)` -> `parent_id`.
* `insert_attr(app_id, attr_row)` -> `attr_id`.
* `insert_edge`, `insert_rating`, `insert_log` similar to above.
* `select_parents(app_id, *, type_ids=None, owner=None, since_seq=None, limit=None)` -> list of dict rows.
* `select_attrs(app_id, parent_ids=None, type_ids=None, since_seq=None)`.
* `select_edges`, `select_ratings` with directional filters.
* `update_sync_flags(app_id, table, row_ids, flags)` - bulk updates for sync scheduling.
* `record_sync_progress(peer_id, domain, last_seq)` - updates `sync_state`.
* `load_domain_seq(domain)` / `increment_domain_seq(domain)` - helpers used by State Manager to persist per-domain watermarks once it decides a flush completed.
* `upsert_setting(key, value)` and `list_settings()` - used only by Config Manager but enforced here.

APIs follow these rules:

* All write helpers accept already-validated DTOs. Storage Manager trusts the inputs for schema correctness but still enforces required columns.
* Graph Manager orchestrates `global_seq` assignment. Storage Manager simply persists the integer attached to each write request and does not enforce reuse/skipping semantics beyond requiring a non-null value.
* Caller-provided timestamps are validated to be ISO8601 strings before insertion when feasible, mainly in tests.
* Query helpers always return immutable structures (tuples or frozen dataclasses) so callers cannot mutate shared caches.
* Deletion helpers are restricted to internal maintenance routines or explicit Graph Manager code paths for domains where policy allows removal; other managers cannot delete graph objects directly.

## 6. Global sequence and synchronization support

`global_seq` provides a monotonic sequence number for graph mutations. Storage Manager guarantees atomic persistence, while Graph Manager determines when a logical batch should claim and reuse a sequence. Guarantees:

* `next_global_seq()` runs inside a single-row `UPDATE global_seq SET seq = seq + 1 WHERE id = 1 RETURNING seq` (or a select + update under transaction) to ensure atomicity, but callers choose when to invoke it.
* Callers may reuse a claimed sequence for multiple rows in a single logical mutation batch only when Graph Manager authorizes that pattern; Storage Manager simply records the supplied value.
* `sync_flags` plus `global_seq` indexes allow efficient scanning of mutations pending sync. Storage Manager provides `select_pending_rows(app_id, table, flag_mask, limit, after_seq)` for sync services without interpreting the semantics.
* `domain_seq` persists per-domain replication watermarks (e.g., `app`, `acl`, `schema`). State Manager defines the lifecycle of each domain and signals when Storage Manager should atomically advance the corresponding counter.
* `sync_state` records remote peers' progress. Helpers ensure the `(peer_id, domain)` composite key exists and is updated atomically based on inputs from sync services.

## 7. Transactions, batching, and concurrency

* Write helpers default to running inside `BEGIN IMMEDIATE` transactions to acquire a reserved lock early and prevent writer starvation.
* Bulk inserts support `insert_many_*` variants that accept iterables; Storage Manager chunks statements to keep SQLite parameter limits intact.
* Long-running read operations use `BEGIN DEFERRED` transactions combined with `PRAGMA read_uncommitted=0` to guarantee snapshot isolation.
* Storage Manager enforces timeouts using the `busy_timeout` pragma plus manual deadline checks to avoid stuck writes. Overdue transactions log warnings.
* Higher-level managers may compose multi-step workflows by passing a transaction handle to nested helper calls. SQLite has no true nested transactions, so Storage Manager either reuses the existing handle or creates explicit SAVEPOINT scopes when re-entrancy is required, never opening implicit top-level transactions.
* WAL checkpoints occur periodically (configurable) or when WAL size exceeds thresholds. Storage Manager exposes `checkpoint(mode='PASSIVE')` to Log/Health managers for maintenance.

## 8. Schema evolution and migrations

* Schema versions are tracked in a dedicated meta table `schema_migrations(version INTEGER PRIMARY KEY)`. Each migration file increments the version.
* Bootstrapping creates all baseline tables if the database is empty, then seeds the migrations table with the baseline version number.
* Migrations run inside a single transaction; failure rolls back to the prior version and aborts startup.
* App-specific migrations are versioned alongside the app record. When App Manager upgrades `apps.version`, it invokes Storage Manager to execute the per-app DDL necessary for that version (e.g., new indexes, columns).
* Storage Manager keeps migration code idempotent and backward-compatible. Downgrades are unsupported; operators must restore from backup.

## 9. Observability and maintenance

* Storage Manager exposes metrics: `db_size_bytes`, `wal_size_bytes`, `open_connections` (always 1), `pending_checkpoint`, `last_vacuum_ts`, `last_backup_ts`, `txn_latency_ms`, and the raw `global_seq` counter value strictly as a storage-level sanity check.
* Log Manager receives structured entries for slow queries (> configurable threshold), failed transactions, and migrations.
* `VACUUM` and `ANALYZE` operations run in maintenance windows triggered manually or by Health Manager once per day. Storage Manager coordinates with other managers to ensure no long-running readers before executing.
* `PRAGMA integrity_check` is exposed through diagnostic APIs that higher-level services gate via ACL Manager; Storage Manager merely honors capability tokens handed to it and logs the results for Health Manager.
* Observability APIs never expose raw SQL or row data beyond aggregated metrics and do not attempt to interpret protocol or sync semantics.

## 10. Security and trust boundaries

* The SQLite file resides under a path controlled by Config Manager; Storage Manager ensures directories exist and restricts permissions to the backend user.
* No other component reads or writes the database files directly. Even backup routines must call Storage Manager to quiesce the database before copying files.
* Inputs to Storage Manager are considered untrusted until validated by the caller. However, Storage Manager still performs basic sanity checks (non-null, type normalization) to mitigate misuse.
* Binary blobs stored in `value_blob` are not decrypted inside Storage Manager; they remain opaque payloads. Key Manager handles sensitive operations.
* Sync and export operations must go through ACL Manager; Storage Manager expects callers to present a pre-validated OperationContext or capability and does not evaluate authorization policy itself.
* SQL injection is prevented by using parameterized statements exclusively. Storage Manager never concatenates user input into SQL fragments.

## 11. Failure posture and recovery

* If SQLite cannot be opened (IO error, permissions), Storage Manager halts startup and surfaces the error via Health Manager. Partial startup is forbidden.
* Schema initialization failures (missing migrations, corrupt tables) abort startup; operators must restore from backup or run repair tooling.
* Runtime write failures roll back their transaction, emit structured errors, and propagate exceptions to callers. Callers decide whether to retry.
* If `global_seq` row disappears or becomes corrupted, Storage Manager refuses to proceed and directs operators to restore from backup; automatically re-seeding would risk sequence reuse.
* WAL corruption triggers a forced checkpoint and optional rebuild (backup + restore). Storage Manager exposes tooling hooks for ops teams but never silently rebuilds data.
* Health Manager monitors database metrics; thresholds trigger degradation states (e.g., WAL > configured size, repeated `SQLITE_BUSY`, failing integrity checks).

## 12. Allowed and forbidden behaviors

### 12.1 Allowed

* Managers invoking typed Storage Manager helpers for all persistence needs.
* Batch inserts and updates that reuse `global_seq` within a single logical mutation under Graph Manager coordination.
* Creating new apps via App Manager, which triggers Storage Manager to provision per-app tables automatically.
* Running maintenance commands (checkpoint, vacuum) via authorized operational tooling.

### 12.2 Forbidden

* Direct SQL execution by managers/services without going through Storage Manager.
* Mutating the SQLite files outside the process (manual `sqlite3` session) while the backend is running.
* Writing graph rows without going through Graph Manager sequencing primitives (e.g., fabricating `global_seq` values or skipping assignment).
* Allowing external callers to read tables without upstream ACL/OperationContext validation enforced by higher layers.
* Treating Storage Manager as a general queue or event bus; it stores durable state, not transient work items.
* Deleting graph rows outside maintenance routines or Graph Manager pathways explicitly authorized by policy.

Storage Manager enforces these boundaries to keep the backend's persistent state consistent, auditable, and ready for synchronization across distributed peers.
