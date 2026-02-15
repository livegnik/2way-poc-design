



# 09 Derived cache tables

Defines the data model for service derived cache tables referenced by system service and app service specifications.

For the meta specifications, see [09-derived-cache-tables meta](../10-appendix/meta/03-data/09-derived-cache-tables-meta.md).

## 1. Purpose and scope

Derived cache tables provide non-authoritative, rebuildable indices for system services and app services. They exist solely for performance and are never part of sync or authoritative state.

## 2. Invariants and guarantees

Across all derived cache tables, the following invariants hold:

* Derived caches are optional and non-authoritative.
* Cache tables are rebuildable from graph reads and may be dropped at any time without affecting correctness.
* Cache contents must not include secrets or ACL-protected data unless authorization is rechecked on every read.
* Cache corruption or mismatch forces a drop-and-rebuild sequence.
* Cache writes never bypass [Graph Manager](../02-architecture/managers/07-graph-manager.md) or [ACL Manager](../02-architecture/managers/06-acl-manager.md).

## 3. Ownership and access rules

* [Storage Manager](../02-architecture/managers/02-storage-manager.md) owns cache table creation and access.
* Services must register cache tables and use Storage Manager APIs to read or write them.
* Direct SQL access outside Storage Manager is forbidden.

## 4. Table schema requirements

Each cache table MUST include, at minimum:

* `cache_key` (TEXT, primary key)
* `value` (TEXT, serialized JSON)
* `source_global_seq` (INTEGER)
* `updated_at` (INTEGER, epoch ms)

Services may add additional columns required for their indices, but must keep the table non-authoritative and rebuildable.

## 5. Naming and scoping

* Cache table names MUST include the owning service or app identifier to avoid collisions.
* System service cache tables are scoped to `app_0`.
* App service cache tables are scoped to the owning `app_id`.

## 6. Failure posture

* Any cache write or read failure MUST fail closed for that request and must not alter authoritative state.
* Cache rebuild failures mark the owning service degraded and emit corresponding events.

## 7. Forbidden behaviors

* Treating cache tables as authoritative state.
* Storing secrets or unredacted ACL-protected data in caches.
* Syncing cache tables to peers.
