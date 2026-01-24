



# 01 SQLite layout

## 1. Purpose and scope

This document defines the complete SQLite storage layout for the 2WAY backend. It specifies database topology, table families, column contracts, sequencing state, and persistence guarantees required to store canonical graph objects and synchronization metadata. It is normative for [Storage Manager](../02-architecture/managers/02-storage-manager.md) behavior and is binding for [Graph Manager](../02-architecture/managers/07-graph-manager.md) persistence semantics. Terminology is defined in [00-scope/03-definitions-and-terminology.md](../00-scope/03-definitions-and-terminology.md).

Storage Manager owns the database lifecycle and is the only component permitted to issue SQL statements. Graph Manager remains the only write path for graph objects. Every accepted envelope results in exactly one committed SQLite transaction, with no partial acceptance, in accordance with the envelope rules defined by the protocol.

This document does not define schema semantics, ACL evaluation logic, sync policy decisions, cryptographic validation, or network behavior. Those responsibilities remain with their respective managers.

This specification consumes and is constrained by the protocol contracts defined in:

* [01-protocol/01-identifiers-and-namespaces.md](../01-protocol/01-identifiers-and-namespaces.md)
* [01-protocol/02-object-model.md](../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/05-keys-and-identity.md](../01-protocol/05-keys-and-identity.md)
* [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md)
* [01-protocol/10-errors-and-failure-modes.md](../01-protocol/10-errors-and-failure-modes.md)

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

## 3. Invariants and guarantees

Across all components and execution contexts defined in this file, the following invariants and guarantees hold:

* All graph object persistence is append-only.
* Immutable metadata fields are never mutated after insertion.
* Deletions of graph objects are forbidden at the storage layer.
* All graph writes are serialized and atomic.
* No partial envelope acceptance is possible.
* `global_seq` advances strictly monotonically and only after commit.
* Domain and peer sync cursors never advance on failure.
* Storage Manager never accepts caller supplied sequence values.
* Referential integrity is enforced by protocol validation, not SQLite foreign keys.
* Database corruption or invariant violation causes immediate fail-closed behavior.

These guarantees hold regardless of caller, execution context, input source, or peer behavior.

## 4. Database topology

### 4.1 Connection lifecycle and pragmas

The database path is supplied by [Config Manager](../02-architecture/managers/01-config-manager.md) and opened exactly once by [Storage Manager](../02-architecture/managers/02-storage-manager.md) during backend startup. Storage Manager applies mandatory SQLite pragmas before any table access:

* WAL mode is enabled.
* A busy timeout is enforced.
* Foreign key enforcement is disabled.
* Synchronous mode is set to ensure durability.

Failure to apply required pragmas aborts startup. Savepoints may be used internally by Storage Manager for composition but must never expose partial acceptance to callers or other managers.

### 4.2 Global tables

Global tables exist once per database and store system-wide state, sequencing metadata, and peer coordination data. These tables are created during bootstrap inside a single transaction. Startup fails closed if any required global table is missing, malformed, or inconsistent.

The required global tables are:

* `identities` stores system-wide identity records used for ownership, authorization, and peer association.
* `apps` stores application registrations and their assigned numeric `app_id` values.
* `peers` stores known peer records and metadata required for sync coordination.
* `settings` stores persisted configuration and runtime operating flags.
* `sync_state` stores per peer and per domain cursors required to resume incremental synchronization.
* `domain_seq` stores per domain high water marks used to advance sync eligibility.
* `global_seq` stores the single monotonic sequence cursor for the database.
* `schema_migrations` stores applied migration identifiers to ensure ordered, idempotent upgrades.

The initial `global_seq` row is seeded during bootstrap. Migrations are applied before any other manager becomes operational.

### 4.3 Per app table families

Each registered application owns a dedicated table family using the prefix `app_N_`, where `N` is the numeric app_id. `app_0` is reserved for system-owned graph data, including identities, schemas, ACL structures, and protocol-level metadata.

Per app table families are created on demand by Storage Manager at app registration time and must be created within the same registration transaction that inserts the app record. They are never dropped automatically. All per app tables include an explicit `app_id` column even when the table name already implies scope. Each app owns an independent `type_id` namespace and cannot observe or reference another app's object tables.

The per app table family includes:

* `app_N_type` stores deterministic `type_key` to `type_id` mappings for the app.
* `app_N_parent` stores Parent objects for the app.
* `app_N_attr` stores Attribute objects for the app.
* `app_N_edge` stores Edge objects for the app.
* `app_N_rating` stores Rating objects for the app.
* `app_N_log` stores Storage Manager owned operational records for the app.

### 4.4 Common graph metadata columns

Every graph object row includes the following immutable metadata columns:

* `app_id` is the owning application scope for the object.
* `id` is the stable object identifier within the app namespace.
* `type_id` is the resolved integer type mapping for the object kind.
* `owner_identity` is the identity that owns the object for ACL evaluation.
* `global_seq` is the commit ordered sequence assigned on acceptance.
* `sync_flags` stores protocol defined sync metadata for the object.

These values are assigned exclusively by [Graph Manager](../02-architecture/managers/07-graph-manager.md) and [Storage Manager](../02-architecture/managers/02-storage-manager.md). Callers must never supply or override them. Cross app references are forbidden and must be rejected before persistence.

### 4.5 Graph object tables

#### Parent table

`app_N_parent` stores Parent objects. Each row represents a single immutable Parent instance with optional JSON payload defined by schema.

#### Attribute table

`app_N_attr` stores Attribute objects. Each Attribute references exactly one source Parent via `src_parent_id` and carries a value payload. Value representation is schema-defined and stored in JSON.

#### Edge table

`app_N_edge` stores Edge objects. Each Edge references exactly one source Parent and exactly one destination selector. Only one of `dst_parent_id` or `dst_attr_id` may be populated. Enforcement occurs at the Graph Manager layer.

#### Rating table

`app_N_rating` stores Rating objects. Each Rating references exactly one target selector, either `target_parent_id` or `target_attr_id`, and stores its value payload in JSON.

ACL structures are persisted using Parents and Attributes within these tables. There is no dedicated ACL table.

### 4.6 Type registry tables

`app_N_type` stores deterministic mappings between `type_key` and integer `type_id` for each object kind. These rows are derived indices generated by [Schema Manager](../02-architecture/managers/05-schema-manager.md). Once assigned, a type mapping is immutable.

The authoritative schema source remains graph objects stored in `app_0`.

### 4.7 Log tables

`app_N_log` stores internal audit and operational records owned by Storage Manager. These rows are not graph objects and must not participate in sync, ACL evaluation, or schema interpretation.

## 5. Sequencing and sync state storage

### 5.1 Global sequence

`global_seq` stores the local monotonic sequence cursor. It advances only after a successful commit of a full envelope. Values are never reused or rolled back.

Graph Manager allocates the next `global_seq` value and Storage Manager persists it at commit time, writing it to every row persisted for the envelope. Sequence gaps may exist if a transaction fails before commit, but committed values remain strictly increasing.

### 5.2 Domain and peer sequencing

`domain_seq` stores per peer and per sync domain high water marks. `sync_state` stores per peer and per domain cursors required to resume incremental synchronization as defined by [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).

Sequence state advances only after full acceptance and persistence. Rejected envelopes do not advance any cursor.

## 6. Indexing posture

Indexes exist to support:

* Global sequence scans.
* Sync eligibility filtering.
* Type resolution.
* Ownership queries.
* Edge directionality traversal.

Index definitions are specified separately and applied idempotently by Storage Manager. This layout guarantees column stability required for indexing.

Indexes are advisory for performance only and must never be relied on for correctness. Storage Manager may create, rebuild, or drop indexes during maintenance as long as the column contracts in this document remain unchanged.

## 7. Startup responsibilities

On startup, Storage Manager must:

* Open the database with required pragmas.
* Verify presence and integrity of all global tables.
* Apply pending migrations.
* Verify the `global_seq` seed.
* Refuse startup on any inconsistency.

No other manager may access the database before Storage Manager signals readiness.

## 8. Shutdown responsibilities

On shutdown, Storage Manager must:

* Reject new write requests.
* Allow in-flight transactions to complete.
* Flush WAL state.
* Close the database cleanly.

Abrupt termination relies on SQLite WAL durability guarantees.

## 9. Failure handling and crash recovery

Any of the following conditions cause immediate fail-closed behavior:

* Missing or malformed tables.
* Sequence corruption.
* Migration failure.
* Detected invariant violation.
* SQLite I/O errors.

Recovery requires operator intervention. Automatic repair is forbidden. Crash recovery relies on SQLite WAL semantics and does not permit partial state exposure or partial acceptance of any envelope.

## 10. Forbidden behaviors

The following behaviors are explicitly forbidden:

* Direct SQL access by any component other than Storage Manager.
* Mutation or deletion of immutable graph metadata.
* Manual modification of sequencing tables.
* Cross app object references.
* Sync cursor advancement on rejection.
* Partial envelope persistence.

## 11. Manager interaction contracts

Storage Manager exposes persistence primitives only to [Graph Manager](../02-architecture/managers/07-graph-manager.md) and [State Manager](../02-architecture/managers/09-state-manager.md). It does not interpret schema, ACLs, or sync policy. All inputs are assumed pre-validated. Storage Manager enforces atomicity, ordering, and durability only.

## 12. Readiness and liveness signals

Storage Manager is considered ready when all startup checks complete successfully. Liveness is defined as continued ability to accept and commit transactions. Any loss of liveness transitions the system to degraded or failed state as reported by [Health Manager](../02-architecture/managers/13-health-manager.md).
