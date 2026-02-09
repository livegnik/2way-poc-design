



# 05 Schema Manager

## 1. Purpose and scope

The Schema Manager is the authoritative component responsible for the scope described below. This specification defines the Schema Manager within the 2WAY architecture and implements the schema validation stage that `01-protocol/00-protocol-overview.md` requires between structural verification and ACL evaluation.

The Schema Manager is responsible for loading, validating, compiling, indexing, and exposing schema definitions stored in the graph so that the `type_key`/`type_id` constructs defined in [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md) and the sync domains described in [01-protocol/07-sync-and-consistency.md](../../../../01-protocol/07-sync-and-consistency.md) remain authoritative across the node. Schemas are stored as graph objects per the canonical Parent/Attribute representation in [01-protocol/02-object-model.md](../../../../01-protocol/02-object-model.md) so they are ordered, replicated, validated, and audited using the same mechanisms as all other graph state. Any compiled or indexed representation is strictly derived and non-authoritative. This file specifies Schema Manager behavior only. It does not define schema authoring, schema mutation flows, envelope formats, ACL semantics, sync execution logic, or storage internals beyond what is required to implement this manager correctly.

This specification consumes the protocol contracts defined in:

* [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md)
* [01-protocol/01-identifiers-and-namespaces.md](../../../../01-protocol/01-identifiers-and-namespaces.md)
* [01-protocol/02-object-model.md](../../../../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/10-errors-and-failure-modes.md](../../../../01-protocol/10-errors-and-failure-modes.md)
* [01-protocol/11-versioning-and-compatibility.md](../../../../01-protocol/11-versioning-and-compatibility.md)

Those files remain normative for all behaviors described here.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Loading all schema definitions from graph objects stored in app_0 so application-owned type metadata referenced by [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md) has one authoritative source.
* Enforcing that exactly one schema exists per app_id, preserving the namespace boundaries defined in [01-protocol/01-identifiers-and-namespaces.md](../../../../01-protocol/01-identifiers-and-namespaces.md).
* Validating schema structure, cardinality, and internal consistency before those rules can shape the `value_json` payloads described in [01-protocol/02-object-model.md](../../../../01-protocol/02-object-model.md).
* Rejecting malformed, incomplete, ambiguous, or conflicting schemas in the same failure class as `ERR_SCHEMA_*` outcomes from [01-protocol/10-errors-and-failure-modes.md](../../../../01-protocol/10-errors-and-failure-modes.md).
* Compiling schemas into immutable in-memory structures so downstream managers can rely on stable metadata per [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md).
* Maintaining per-app and per-kind mappings from type_key to numeric type_id so operations that choose either identifier form in [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md) can be processed deterministically.
* Ensuring type_id stability across restarts and reloads, matching the immutability guarantees on `type_id` in [01-protocol/02-object-model.md](../../../../01-protocol/02-object-model.md).
* Exposing schema metadata to other managers through a read-only interface, including the ACL inputs identified in [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md).
* Providing schema-based validation helpers to [Graph Manager](../../../../02-architecture/managers/07-graph-manager.md), which must run schema checks before persistence per [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md).
* Compiling and exposing sync domain configuration metadata to [State Manager](../../../../02-architecture/managers/09-state-manager.md) so the domain-scoped sync described in [01-protocol/07-sync-and-consistency.md](../../../../01-protocol/07-sync-and-consistency.md) can be enforced.
* Detecting and failing closed on schema integrity violations, surfacing the schema-specific failures enumerated in [01-protocol/10-errors-and-failure-modes.md](../../../../01-protocol/10-errors-and-failure-modes.md).
* Participating in startup readiness determination as part of the manager lifecycle described in [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md).
* Participating in controlled schema reload operations without violating the compatibility posture of [01-protocol/11-versioning-and-compatibility.md](../../../../01-protocol/11-versioning-and-compatibility.md).
* Declaring the `schema.*` configuration surface and its bounds for schema limits.

This specification does not cover the following:

* Creating, updating, or deleting schema graph objects, which belong to general graph mutation flows enforced by [Graph Manager](../../../../02-architecture/managers/07-graph-manager.md).
* Defining schema lifecycle policy beyond validation and reload semantics; those policies are governed by [01-protocol/11-versioning-and-compatibility.md](../../../../01-protocol/11-versioning-and-compatibility.md).
* Evaluating ACLs, ownership, or visibility rules, which are defined solely in [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md).
* Performing graph writes except permitted creation of type_id mappings, and even those must honor the immutability rules in [01-protocol/02-object-model.md](../../../../01-protocol/02-object-model.md).
* Executing sync, reconciliation, or conflict resolution, which stay within [State Manager](../../../../02-architecture/managers/09-state-manager.md) per [01-protocol/07-sync-and-consistency.md](../../../../01-protocol/07-sync-and-consistency.md).
* Network transport, cryptographic verification, or peer negotiation ([01-protocol/04-cryptography.md](../../../../01-protocol/04-cryptography.md), [01-protocol/08-network-transport-requirements.md](../../../../01-protocol/08-network-transport-requirements.md)).
* Schema migration, backward compatibility handling, or data transformation ([01-protocol/11-versioning-and-compatibility.md](../../../../01-protocol/11-versioning-and-compatibility.md)).
* Application-level interpretation of schema semantics.

## 3. References

* Graph object model and envelopes are defined in [01-protocol/02-object-model.md](../../../../01-protocol/02-object-model.md) and [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md).
* Storage layout and app_N_type tables are defined in [03-data/**](../../03-data/).
* Sync behavior is defined in [01-protocol/07-sync-and-consistency.md](../../../../01-protocol/07-sync-and-consistency.md) and [02-architecture/managers/09-state-manager.md](../../../../02-architecture/managers/09-state-manager.md).
* Authorization behavior is defined in [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md) and [02-architecture/managers/06-acl-manager.md](../../../../02-architecture/managers/06-acl-manager.md).
