



# 02 System tables

## 1. Purpose and scope

This document defines the global system tables stored in the 2WAY backend SQLite database. These tables exist exactly once per node and are created during bootstrap before any application data is written. It does not define per-app graph tables or schema semantics. Terminology is defined in [00-scope/03-definitions-and-terminology.md](../00-scope/03-definitions-and-terminology.md).

This specification consumes and is constrained by the protocol contracts defined in:

- [01-protocol/01-identifiers-and-namespaces.md](../01-protocol/01-identifiers-and-namespaces.md)
- [01-protocol/02-object-model.md](../01-protocol/02-object-model.md)
- [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md)
- [01-protocol/05-keys-and-identity.md](../01-protocol/05-keys-and-identity.md)
- [01-protocol/06-access-control-model.md](../01-protocol/06-access-control-model.md)
- [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md)
- [01-protocol/09-errors-and-failure-modes.md](../01-protocol/09-errors-and-failure-modes.md)
- [01-protocol/10-versioning-and-compatibility.md](../01-protocol/10-versioning-and-compatibility.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining all global system tables that exist outside app-scoped graph storage
* Defining invariants for identity, sequencing, sync tracking, configuration, and peer state
* Defining when tables may be written, updated, or read
* Defining fail-closed behavior for corruption or inconsistency
* Defining startup and shutdown expectations related to system tables

This specification does not cover the following:

* Graph object persistence, which is owned by [Graph Manager](../02-architecture/managers/07-graph-manager.md)
* Schema compilation and type mapping, which is owned by [Schema Manager](../02-architecture/managers/05-schema-manager.md)
* ACL rule evaluation, which is owned by [ACL Manager](../02-architecture/managers/06-acl-manager.md) and defined in [01-protocol/06-access-control-model.md](../01-protocol/06-access-control-model.md)
* Sync envelope construction or validation, which is owned by [State Manager](../02-architecture/managers/09-state-manager.md) and defined in [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md)
* Network connectivity and transport, which is owned by [Network Manager](../02-architecture/managers/10-network-manager.md)

All tables defined here are owned exclusively by [Storage Manager](../02-architecture/managers/02-storage-manager.md). No other manager or service may access them directly.

## 3. Invariants and guarantees

Across all system tables defined in this file, the following invariants and guarantees hold:

* All system tables are created during bootstrap in a single transaction
* Startup fails closed if any required system table is missing
* Startup fails closed if required seed rows are missing
* No system table permits silent repair or auto reconstruction
* Sequence values advance only on successful commit
* Sequence values never regress
* Identifiers are never reused, matching [01-protocol/01-identifiers-and-namespaces.md](../01-protocol/01-identifiers-and-namespaces.md)
* System tables are not synced to peers per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md)
* System tables are node-local state and never part of the graph defined in [01-protocol/02-object-model.md](../01-protocol/02-object-model.md)

These guarantees hold regardless of caller, execution context, input source, or peer behavior.

## 4. Table ownership and access rules

* [Storage Manager](../02-architecture/managers/02-storage-manager.md) is the sole owner of all system tables
* [Graph Manager](../02-architecture/managers/07-graph-manager.md) may request sequence values but may not update tables directly
* [State Manager](../02-architecture/managers/09-state-manager.md) may request read and write access to sync tracking state
* [Config Manager](../02-architecture/managers/01-config-manager.md) may request read and write access to settings
* [Network Manager](../02-architecture/managers/10-network-manager.md) may request read access to peers
* No service, app, or extension may access system tables directly
* Direct SQL access outside Storage Manager is forbidden

Violation of these rules is a fatal implementation error.

## 5. System table catalog

System tables are not graph objects. They exist outside the graph to store node-local state that must be available before graph access is possible, or state that must never be replicated to peers. Graph objects are the source of truth for application data and identities, while system tables are operational registries, counters, and local policy state owned by Storage Manager. Each table below exists only because its data is required for startup, sequencing, sync tracking, or configuration, and because storing it in the graph would either violate the protocol boundaries or create circular dependencies during bootstrap.

### 5.1 identities

#### Purpose

Stores the durable identity registry that binds identity identifiers to cryptographic material and graph representation. It lives outside the graph because it is required to resolve identities during startup and sync validation before graph reads are permitted. The graph remains the authoritative identity model, while this table provides fast, local lookup for bootstrapping and verification.

This table exists to support:

* authentication
* signature verification
* sync trust decisions
* identity resolution

The canonical identity representation remains in the graph under `app_0` per [01-protocol/05-keys-and-identity.md](../01-protocol/05-keys-and-identity.md). This table is a registry, not the source of truth for identity attributes.

#### Expected contents

Each row represents a stable identity known to the node.

Typical fields include:

* identity_id
* public_key material
* creation timestamp
* optional status metadata

#### Rules and guarantees

* identity_id values are globally unique within the node
* identity_id values are never reused
* identity rows are append only
* identity rows are never deleted
* updates are limited to status or metadata fields if present
* identity rows must correspond to a valid identity Parent in app_0

Failure to resolve an identity registry entry to a graph identity is fatal.

### 5.2 apps

#### Purpose

Stores the application registry owned by [App Manager](../02-architecture/managers/08-app-manager.md). It lives outside the graph because app identifiers must be declared before any graph objects can reference them, and because the registry is local node state rather than syncable graph data.

This table defines which applications exist and assigns stable app_id values.

#### Expected contents

Each row includes:

* app_id
* slug
* version
* creation timestamp

This table is the authoritative source of app existence.

#### Rules and guarantees

* app_id values are strictly monotonic
* app_id values are never reused
* app rows are append only
* app rows are not deleted when apps are disabled or removed
* app existence must be verified before any graph operation using an app_id

If an envelope references an unknown app_id, it is rejected per [01-protocol/01-identifiers-and-namespaces.md](../01-protocol/01-identifiers-and-namespaces.md) and [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md).

### 5.3 peers

#### Purpose

Stores peer metadata required for network connectivity, trust evaluation, and sync coordination. It lives outside the graph because peer state is local policy and transport metadata that must not be replicated as graph data.

This table represents local node knowledge and is not part of the graph.

#### Expected contents

Each row may include:

* peer identifier
* associated identity_id
* endpoint or transport address
* metadata describing peer capabilities
* timestamps for last contact or handshake

#### Rules and guarantees

* peer identity must resolve to a valid identity registry entry
* peer rows may be updated to reflect state changes
* peer rows are not deleted automatically
* removal requires explicit operator action or policy decision
* peers table is never synced

### 5.4 settings

#### Purpose

Stores durable runtime configuration managed by [Config Manager](../02-architecture/managers/01-config-manager.md). It lives outside the graph because configuration is node-local state and must be available before graph services are initialized.

This table persists operational configuration across restarts.

#### Expected contents

Each row includes:

* setting key
* serialized value

Values are opaque to Storage Manager.

#### Rules and guarantees

* only Config Manager may write settings
* settings are validated before commit
* arbitrary writes by other managers are forbidden
* settings may be updated
* settings keys are unique

Invalid settings cause Config Manager to signal degraded health.

### 5.5 sync_state

#### Purpose

Tracks per peer and per sync domain acceptance state. It lives outside the graph because it is local node sync bookkeeping and must never be replicated as graph data.

This table enforces ordering, replay protection, and incremental sync correctness per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).

#### Expected contents

Each row tracks:

* peer_id
* sync domain
* last accepted global sequence
* optional state flags

#### Rules and guarantees

* sync_state advances only after full envelope acceptance
* rejected envelopes do not update sync_state
* values are monotonic per peer and domain
* values never regress
* rows may be updated during normal operation

This table is authoritative for sync replay protection.

### 5.6 domain_seq

#### Purpose

Tracks per peer and per sync domain high water marks used for ordered replication. It lives outside the graph because it is local sequencing state tied to peer sync and must advance only on local acceptance.

This table supports ordered replication per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md).

#### Expected contents

Each row includes:

* peer_id
* sync domain
* last accepted global sequence

#### Rules and guarantees

* values are strictly monotonic per peer and domain
* values advance only on successful commit
* values never regress
* rows are updated during normal operation

Domain sequence inconsistency is a fatal error.

### 5.7 global_seq

#### Purpose

Stores the local monotonic sequence counter used to order all accepted operations per [01-protocol/07-sync-and-consistency.md](../01-protocol/07-sync-and-consistency.md). It lives outside the graph because it must be available during write acceptance and cannot be influenced by graph mutations.

This is the root ordering primitive of the system.

#### Expected contents

The table contains exactly one row.

Typical fields:

* id, fixed to a single value
* seq, current sequence value

#### Rules and guarantees

* exactly one row must exist
* sequence starts at zero or one depending on bootstrap
* sequence increments only within a transaction that writes graph data
* sequence increments only after all validation passes
* sequence never advances on failure
* sequence values are never reused

Violation of these rules invalidates sync correctness.

### 5.8 schema_migrations

#### Purpose

Tracks executed storage migrations. It lives outside the graph because migrations are a storage concern executed before graph access is available and must not be synced or modeled as graph objects.

This table prevents partial or repeated migrations.

#### Expected contents

Each row records:

* migration identifier
* execution timestamp

#### Rules and guarantees

* rows are append only
* migrations are never removed
* downgrades are unsupported per [01-protocol/10-versioning-and-compatibility.md](../01-protocol/10-versioning-and-compatibility.md)
* partial migration execution causes startup failure
* migration failure results in fail-closed behavior

## 6. Startup behavior

During startup:

1. [Storage Manager](../02-architecture/managers/02-storage-manager.md) opens the database
2. All system tables are verified to exist
3. Required seed rows are verified
4. schema_migrations are checked
5. global_seq row is verified
6. Startup aborts on any inconsistency

No manager may proceed until system tables are validated.

## 7. Shutdown behavior

During shutdown:

* no system table mutations occur
* pending transactions are completed or rolled back
* WAL is flushed
* database is closed cleanly

No best effort repair occurs on shutdown.

## 8. Failure posture

The system fails closed under the following conditions:

* missing system table
* missing required seed row
* global_seq inconsistency
* domain_seq regression
* sync_state regression
* migration inconsistency
* identity registry mismatch

Recovery requires operator intervention.

Automatic repair is forbidden per [01-protocol/09-errors-and-failure-modes.md](../01-protocol/09-errors-and-failure-modes.md).

## 9. Explicitly forbidden behavior

The following behavior is forbidden:

* direct SQL access outside Storage Manager
* deleting identity rows
* reusing identity_id values
* reusing app_id values
* modifying global_seq outside a graph write transaction
* advancing sequence on failed validation
* syncing system tables to peers
* reconstructing system tables implicitly

Any implementation performing these actions is incorrect.
