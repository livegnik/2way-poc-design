



# 02 Storage Manager

## 1. Purpose and scope

The Storage Manager is the authoritative component responsible for the scope described below. Storage Manager is the sole authority for durable persistence in the 2WAY backend. It owns the SQLite database lifecycle, schema materialization, per-app table provisioning, transactional boundaries, and persistence primitives consumed by all other managers and services.

This specification defines the complete responsibilities, internal structure, invariants, APIs, and failure posture of Storage Manager. It is an implementation-facing design specification. It does not define higher-level graph semantics, ACL logic, schema meaning, sync policy, or network behavior, except where storage guarantees are required to support them. Storage Manager is a passive subsystem. It never interprets protocol meaning. It persists state exactly as instructed by higher-level managers defined in [01-component-model.md](../01-component-model.md) and guarantees durability, ordering, isolation, and integrity. Storage Manager enforces the canonical data and sequencing rules defined by the protocol corpus; those references are listed explicitly below.

This specification consumes the protocol contracts defined in:

* [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md)
* [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md)
* [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md)

Those files remain normative for all behaviors described here.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Owning the single backend SQLite database file and its WAL lifecycle, keeping persistence centralized per the manager boundaries established in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Creating, migrating, and validating all global tables so canonical metadata defined in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) and [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) always has an authoritative store.
* Creating and maintaining per-app table families for every registered app, matching the namespace guarantees described in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md) and [App Manager](08-app-manager.md).
* Enforcing transactional isolation, atomicity, and write serialization.
* Persisting all graph objects exactly as provided by [Graph Manager](07-graph-manager.md).
* Persisting monotonic sequence counters, including `global_seq` and `domain_seq`.
* Persisting sync progress and peer replication state.
* Persisting system metadata such as settings, peers, and app registry data.
* Providing typed, constrained persistence helpers to all managers and services defined in [02-architecture/services-and-apps/**](../services-and-apps/).
* Guaranteeing that every stored graph row carries the immutable metadata fields required by [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) and that callers cannot mutate those fields post insert.
* Preserving the envelope transaction boundary described in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) so that each accepted envelope maps to exactly one SQLite transaction commit.
* Enforcing the strict `global_seq` and `domain_seq` ordering discipline mandated by [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) by co-locating sequence persistence with the data rows they gate.
* Preventing all raw database access outside this manager.
* Providing observability, maintenance, and integrity tooling hooks.
* Failing closed on corruption, partial initialization, or invariant violations.

This specification does not cover the following:

* Schema validation semantics, which belong to [Schema Manager](05-schema-manager.md) per [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* ACL evaluation or permission enforcement, which belong to [ACL Manager](06-acl-manager.md) per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Graph semantics, object meaning, or lifecycle interpretation.
* Network transport, peer connectivity, or message handling.
* Sync policy, domain logic, or replication strategy.
* Cryptographic key custody, signing, or encryption.
* Application-level business logic or service behavior.

## 3. Invariants and guarantees

Across all components and contexts defined in this file, the following invariants hold:

* There is exactly one writable SQLite connection per backend process.
* All graph writes are durable, atomic, and ordered, matching the envelope atomicity requirements in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Required metadata fields (`app_id`, `id`, `type_id`, `owner_identity`, `global_seq`, `sync_flags`) remain immutable once persisted, per [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* `global_seq` is strictly monotonic and never reused in accordance with [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* `domain_seq` and sync_state never advance when an operation fails, satisfying Section 3 of [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Graph rows are append only and never deleted, preserving the constraints in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* [Storage Manager](02-storage-manager.md) never interprets semantic meaning.
* No component bypasses [Storage Manager](02-storage-manager.md) for persistence.
* Failed writes leave no partial state or sequence movement, aligning with [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Startup either completes fully or aborts entirely, honoring the fail-closed posture in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Corruption is detected and causes fail closed behavior.

These guarantees hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 4. Internal structure

[Storage Manager](02-storage-manager.md) is internally divided into explicit engines. These engines are required for correctness and clarity.

### 4.1 Storage Engine

The Storage Engine owns:

* SQLite connection creation and teardown.
* Pragmas and connection configuration.
* Transaction primitives.
* Query execution.
* WAL management and checkpoints.

It exposes no raw SQL to callers.

### 4.2 Schema Provisioning Engine

The Schema Provisioning Engine owns:

* Creation of global tables.
* Creation of per-app table families.
* Index creation.
* Idempotent DDL execution.
* Migration application and version tracking.

It executes only during startup or app registration.

### 4.3 Sequence Engine

The Sequence Engine owns:

* Atomic persistence of `global_seq`.
* Persistence of per-(peer, sync_domain) `domain_seq` rows that track the highest accepted `global_seq`, as required by [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Persistence of peer `sync_state`, reflecting the exact ordering guarantees described in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).

It does not decide when sequences advance. It only persists values supplied by [Graph Manager](07-graph-manager.md) or [State Manager](09-state-manager.md).

### 4.4 Maintenance Engine

The Maintenance Engine owns:

* WAL checkpoints.
* VACUUM and ANALYZE operations.
* Integrity checks.
* Size and health metrics.
* Safe quiescing for backup operations.

It never runs automatically without coordination.

## 5. Database topology

### 5.1 Connection and pragmas

* SQLite database path is supplied by [Config Manager](01-config-manager.md).
* WAL mode is mandatory.
* Foreign keys are disabled at SQLite level.
* Busy timeout is enforced.
* Only [Storage Manager](02-storage-manager.md) holds the connection.

Failure to apply required pragmas aborts startup.

### 5.2 Global tables

Global tables exist exactly once per database and are created at bootstrap.

* identities
* apps
* peers
* settings
* sync_state
* domain_seq
* global_seq
* schema_migrations

These tables are durable system state. Some are caches. Authority remains in the graph as defined in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) where applicable.

### 5.3 Per-app tables

For each registered app, [Storage Manager](02-storage-manager.md) ensures the existence of the following tables:

* app_N_type
* app_N_parent
* app_N_attr
* app_N_edge
* app_N_rating
* app_N_log

All tables include `app_id` explicitly. All graph rows include `global_seq` and `sync_flags`.

No per-app table is dropped automatically.

These per-app tables correspond to the canonical Parent, Attribute, Edge, and Rating object categories in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md). ACL structures are persisted by composing Parent and Attribute rows per Section 10 of that same document; [Storage Manager](02-storage-manager.md) never introduces a dedicated ACL table.

Each per-app table stores the immutable metadata fields described in Section 5.1 of [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) (`app_id`, `id`, `type_id`, `owner_identity`, `global_seq`, `sync_flags`). Those fields are server assigned and never exposed for direct mutation, consistent with the operation constraints in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).

### 5.4 Indexing rules

Indexes are mandatory on:

* `global_seq`
* `sync_flags`
* parent ownership
* edge directionality
* type lookups

Indexes are created idempotently.

## 6. Initialization and startup behavior

Startup proceeds as follows:

1. [Config Manager](01-config-manager.md) resolves database path.
2. [Storage Manager](02-storage-manager.md) opens SQLite connection.
3. Pragmas are applied.
4. Bootstrap transaction begins.
5. Global tables are created if missing.
6. `global_seq` seed row is verified or created.
7. Schema migrations are applied.
8. Apps are enumerated.
9. Per-app schemas are ensured.
10. Bootstrap transaction commits.
11. [Storage Manager](02-storage-manager.md) becomes available.

Any failure aborts startup.

## 7. Shutdown behavior

Shutdown proceeds as follows:

1. New transactions are rejected.
2. Active transactions complete.
3. WAL checkpoint is attempted.
4. Connection is closed.

Partial shutdown is forbidden.

## 8. APIs and helper contracts

[Storage Manager](02-storage-manager.md) exposes typed helpers only.

These helpers mirror the operation categories defined in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and operate exclusively on the canonical graph objects from [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).

### 8.1 Transaction helpers

* read only context
* write transaction context
* savepoint support for nested calls

Callers never manage commits directly.

### 8.2 Graph persistence helpers

* insert parent
* insert attribute
* insert edge
* insert rating
* insert log

No update or delete helpers exist for graph objects.

### 8.3 Sequence helpers

* get global_seq
* next global_seq
* read domain_seq
* advance domain_seq
* update sync_state

Sequence helpers are atomic.

### 8.4 Query helpers

* select parents
* select attributes
* select edges
* select ratings
* select pending sync rows

All queries are constrained and parameterized.

Transaction helpers guarantee that the entire envelope defined in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) is processed atomically; partial application is forbidden.

## 9. Transactions and concurrency

* Only one writer at a time.
* Writes use immediate transactions to maintain the envelope atomicity described in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Reads use snapshot isolation.
* Savepoints are used for nested operations.
* Busy timeouts are enforced.
* Starvation is prevented by early locking.

[Storage Manager](02-storage-manager.md) never spins or retries silently.

## 10. Schema evolution and migrations

* Schema versions are tracked explicitly.
* Migrations are deterministic and must preserve the canonical object layout in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* Downgrades are unsupported.
* Failure aborts startup.
* App schema upgrades are coordinated with [App Manager](08-app-manager.md).

Migrations may add columns or tables only if they preserve the invariants defined in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md), and they must not introduce paths that could relax the ordering guarantees in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).

## 11. Observability and diagnostics

[Storage Manager](02-storage-manager.md) exposes:

* database size
* WAL size
* last checkpoint time
* last vacuum time
* integrity check results
* transaction latency metrics

Diagnostics never expose raw rows.

## 12. Security and trust boundaries

* Database file permissions are restricted.
* All SQL is parameterized.
* No raw SQL is exposed.
* [Storage Manager](02-storage-manager.md) assumes callers validated authorization.
* Binary payloads remain opaque.
* No cryptographic operations occur here.

## 13. Failure posture and recovery

[Storage Manager](02-storage-manager.md) fails closed on:

* open failure
* corruption
* missing global_seq
* migration failure
* invariant violation

Recovery requires operator intervention. Automatic repair is forbidden. Failures never advance `global_seq`, `domain_seq`, or peer `sync_state`, honoring the rejection guarantees defined in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).

## 14. Allowed and forbidden behaviors

### 14.1 Allowed

* Typed persistence via [Storage Manager](02-storage-manager.md).
* Batch inserts coordinated by [Graph Manager](07-graph-manager.md).
* Maintenance operations during quiescent windows.
* App schema provisioning via [App Manager](08-app-manager.md).

### 14.2 Forbidden

* Direct SQLite access by any other component.
* Deleting graph rows.
* Mutating sync_flags post insert.
* Fabricating or reusing global_seq.
* Treating [Storage Manager](02-storage-manager.md) as a queue.
* Silent repair or auto reset of corrupted state.
