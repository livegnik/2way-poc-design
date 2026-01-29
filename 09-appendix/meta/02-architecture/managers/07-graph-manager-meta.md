



# 07 Graph Manager

## 1. Purpose and scope

The Graph Manager is the authoritative component responsible for the scope described below. The Graph Manager is the authoritative coordinator for graph state access within the local node. It is the only permitted write path for graph objects, and it provides the canonical read surface for graph objects where access control, application context, traversal constraints, consistency guarantees, and default visibility filtering must be enforced.

This document defines responsibilities, boundaries, invariants, guarantees, allowed and forbidden behaviors, concurrency rules, component interactions, startup and shutdown behavior, internal execution engines, and failure handling for the Graph Manager. This file specifies graph level access behavior only. It does not define schema content, access control policy logic, synchronization protocol behavior, network transport, cryptographic verification, peer discovery, or storage internals, except where interaction boundaries are required.

This specification consumes the protocol contracts defined in:

* [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md)
* [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md)
* [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md)
* [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md)
* [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md)

Those files remain normative for all behaviors described here.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Acting as the single entry point for all persisted mutations of Parents, Attributes, Edges, Ratings, and ACL structures per [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md), matching the canonical object definitions in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md). ACL data is represented as Parent and Attribute objects exactly as defined there.
* Accepting graph envelopes only from trusted in process components, including local services and [State Manager](09-state-manager.md) for remote application after [Network Manager](10-network-manager.md) verification, exactly as allowed by [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and constrained by [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md).
* Validating envelope structure and operation shape at the graph layer, including supervised operation identifiers, the required `ops` array, `type_key` and `type_id` exclusivity, declared `owner_identity`, and rejection of forbidden fields such as `global_seq` or `sync_flags` per [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Enforcing namespace isolation and object reference rules defined in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md), as well as the single-app reference constraints in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* Delegating type resolution and schema validation to [Schema Manager](05-schema-manager.md) so that schemas remain authoritative per [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* Delegating authorization decisions for reads and writes to [ACL Manager](06-acl-manager.md) per the ordering defined in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) and the enforcement rules in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Enforcing application context for all operations so [OperationContext](../services-and-apps/05-operation-context.md) semantics and app isolation described in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) and [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md) remain intact.
* Enforcing serialized write ordering and global sequencing for all accepted mutations per [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Persisting accepted envelopes atomically through [Storage Manager](02-storage-manager.md), upholding the transactional guarantees described in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Publishing semantic graph events after commit through [Event Manager](11-event-manager.md) so downstream consumers see only committed state, matching the ordering posture in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Providing canonical read operations for graph objects, with authorization, application context, consistency guarantees, and default visibility filtering enforced per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Providing bounded traversal primitives required to support authorization checks that depend on graph distance, as required by [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Enforcing bounded read and traversal budgets consistent with the resource safety posture of [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Defining the concurrency contract for graph reads and writes at the manager boundary so sequencing and consistency guarantees in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) hold.
* Enforcing strict separation between graph access logic and storage implementation per the manager boundaries laid out in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Remaining cryptographically agnostic by never performing signing, verification, encryption, or decryption, and by rejecting any remote sourced envelope that bypasses the [Network Manager](10-network-manager.md) and [State Manager](09-state-manager.md) path, per [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md).
* Defining startup, readiness, and shutdown behavior for safe operation.
* Defining internal execution engines and their ownership of behavior.

This specification does not cover the following:

* Schema definition, migration, or versioning behavior.
* The meaning of types, fields, or application semantics beyond what is required to enforce visibility defaults defined in this file.
* The content of access control policies, rule evaluation, or policy storage.
* Construction of sync packages, per peer sync state, or inbound and outbound sync flows.
* Network transport, encryption, signature verification, or peer management.
* Storage schemas, SQL details, or indexing strategies.
* Application specific query engines, search, ranking, analytics, denormalized views, or aggregates.
