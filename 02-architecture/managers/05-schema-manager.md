



# 05 Schema Manager

## 1. Purpose and scope

This specification defines the Schema Manager within the 2WAY architecture and implements the schema validation stage that `01-protocol/00-protocol-overview.md` requires between structural verification and ACL evaluation.

The Schema Manager is responsible for loading, validating, compiling, indexing, and exposing schema definitions stored in the graph so that the `type_key`/`type_id` constructs defined in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and the sync domains described in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) remain authoritative across the node.

Schemas are stored as graph objects per the canonical Parent/Attribute representation in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) so they are ordered, replicated, validated, and audited using the same mechanisms as all other graph state. Any compiled or indexed representation is strictly derived and non-authoritative.

This file specifies Schema Manager behavior only. It does not define schema authoring, schema mutation flows, envelope formats, ACL semantics, sync execution logic, or storage internals beyond what is required to implement this manager correctly.

This specification consumes the protocol contracts defined in:

* [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md)
* [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md)
* [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md)
* [01-protocol/10-versioning-and-compatibility.md](../../01-protocol/10-versioning-and-compatibility.md)

Those files remain normative for all behaviors described here.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Loading all schema definitions from graph objects stored in app_0 so application-owned type metadata referenced by [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) has one authoritative source.
* Enforcing that exactly one schema exists per app_id, preserving the namespace boundaries defined in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Validating schema structure, cardinality, and internal consistency before those rules can shape the `value_json` payloads described in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* Rejecting malformed, incomplete, ambiguous, or conflicting schemas in the same failure class as `ERR_SCHEMA_*` outcomes from [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).
* Compiling schemas into immutable in-memory structures so downstream managers can rely on stable metadata per [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Maintaining per-app and per-kind mappings from type_key to numeric type_id so operations that choose either identifier form in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) can be processed deterministically.
* Ensuring type_id stability across restarts and reloads, matching the immutability guarantees on `type_id` in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* Exposing schema metadata to other managers through a read-only interface, including the ACL inputs identified in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Providing schema-based validation helpers to [Graph Manager](07-graph-manager.md), which must run schema checks before persistence per [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Compiling and exposing sync domain configuration metadata to [State Manager](09-state-manager.md) so the domain-scoped sync described in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) can be enforced.
* Detecting and failing closed on schema integrity violations, surfacing the schema-specific failures enumerated in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).
* Participating in startup readiness determination as part of the manager lifecycle described in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Participating in controlled schema reload operations without violating the compatibility posture of [01-protocol/10-versioning-and-compatibility.md](../../01-protocol/10-versioning-and-compatibility.md).

This specification does not cover the following:

* Creating, updating, or deleting schema graph objects, which belong to general graph mutation flows enforced by Graph Manager.
* Defining schema lifecycle policy beyond validation and reload semantics; those policies are governed by [01-protocol/10-versioning-and-compatibility.md](../../01-protocol/10-versioning-and-compatibility.md).
* Evaluating ACLs, ownership, or visibility rules, which are defined solely in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Performing graph writes except permitted creation of type_id mappings, and even those must honor the immutability rules in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* Executing sync, reconciliation, or conflict resolution, which stay within [State Manager](09-state-manager.md) per [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Network transport, cryptographic verification, or peer negotiation ([01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md), [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md)).
* Schema migration, backward compatibility handling, or data transformation ([01-protocol/10-versioning-and-compatibility.md](../../01-protocol/10-versioning-and-compatibility.md)).
* Application-level interpretation of schema semantics.

## 3. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* Schemas stored in the graph are the only authoritative schema source, matching the expectation that Schema Manager supplies the type metadata omitted from [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* app_N_type tables are derived indices and are never authoritative.
* Exactly one schema exists per app_id, preserving the application namespaces defined in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Multiple schemas or versions for the same app_id are forbidden.
* Schema data is treated as untrusted input and is fully validated before use, in line with [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* A type_key resolves to a numeric type_id only if declared in the loaded schema, which is how callers may supply either identifier in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* A numeric type_id, once assigned, is stable and never remapped, matching the immutability guarantees in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* Schema validation and type resolution are deterministic given the same inputs.
* Compiled schemas are immutable during normal operation.
* Schema-dependent operations fail closed if schema loading or validation fails, surfacing the schema error class defined in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).
* Disagreement between compiled schema state and persisted indices is fatal.
* Sync domain metadata reflects exactly what is declared in schemas, because domain-scoped sync in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) relies on deterministic membership.
* Schema validation does not imply authorization; ACL evaluation remains the scope of [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* No manager may bypass Schema Manager for schema knowledge; [Graph Manager](07-graph-manager.md) must honor the validation ordering defined in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).

These guarantees hold regardless of caller, execution context, input source, or peer behavior.

## 4. Inputs, outputs, and trust boundaries

### 4.1 Inputs

The Schema Manager consumes the following inputs:

* Schema Parents and Attributes stored in app_0, encoded using the canonical structures in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* app_id values used to scope schema lookup and type resolution, honoring the namespace rules in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Validation and lookup requests from [Graph Manager](07-graph-manager.md) for operations defined in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Sync domain lookup requests from [State Manager](09-state-manager.md) so it can enforce the per-domain sync rules in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Administrative reload requests from control surfaces.

### 4.2 Outputs

The Schema Manager produces the following outputs:

* A compiled, in-memory schema registry keyed by app_id.
* Deterministic mappings from type_key to numeric type_id per app and kind so either identifier permitted by [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) can be serviced.
* Compiled sync domain configurations keyed by domain_name, enabling the invariants documented in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Validation results for schema-based checks.
* Readiness and health signals.

### 4.3 Trust boundaries

* Schema input from the graph is untrusted, matching the failure posture in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Callers trust the Schema Manager to enforce schema correctness.
* The Schema Manager does not enforce ACLs and must not be used as an authorization oracle; that responsibility is defined separately in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* The Schema Manager does not trust storage indices without verification.

## 5. Schema representation and constraints

### 5.1 Storage location

* All schemas are stored as graph objects in app_0 and use the canonical object structures defined in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* Schemas are represented as Parents with structured Attributes containing schema definitions, mirroring the Parent/Attribute composition in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* No schema information is loaded from configuration files or code.

### 5.2 Cardinality and uniqueness

* Exactly one schema per app_id is permitted.
* Duplicate schemas for the same app_id cause startup failure.
* Multiple schema versions for the same app_id are forbidden.
* Schema version fields are required but informational only.

### 5.3 Required schema structure

A schema is structurally valid only if it declares:

* app_slug.
* version.
* parent_types.
* attribute_types per parent type.
* relationship constraints, if applicable.
* sync_schema with at least one domain.

Each sync domain must declare at minimum (to satisfy the per-domain replication rules in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)):

* domain_name.
* parent_types.
* mode.

Missing required fields cause schema rejection.

### 5.4 Scoping rules

* Schemas define types only within their own app_id namespace, as required by [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Cross-app type references are forbidden unless future protocol revisions define linking semantics in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Duplicate type_key definitions within the same app and kind are forbidden.
* Kind namespaces are isolated (Parent, Attribute, Edge, Rating) to match the independent `type_id` fields for each category in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).

## 6. Internal structure and engines

### 6.1 Schema Loading Engine

The Schema Loading Engine is responsible for:

* Querying the graph for schema Parents in app_0.
* Extracting and decoding schema Attribute payloads.
* Grouping schema definitions by app_id.
* Detecting duplicate or missing schemas.

### 6.2 Schema Validation Engine

The Schema Validation Engine is responsible for:

* Structural validation of schema payloads.
* Validation of required fields and data types.
* Validation of parent and attribute type declarations.
* Validation of relationship constraints.
* Validation of sync domain declarations ([01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)).
* Detection of internal contradictions or ambiguity.

Validation failures are fatal.

### 6.3 Schema Compilation Engine

The Schema Compilation Engine is responsible for:

* Building immutable in-memory representations of schemas.
* Normalizing type declarations.
* Preparing lookup tables for fast validation.
* Emitting compiled schema objects for runtime use.

Compiled schemas must not retain references to mutable input data.

### 6.4 Type Registry Engine

The Type Registry Engine is responsible for:

* Resolving type_key to numeric type_id mappings for the operation formats defined in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Creating missing mappings where permitted.
* Verifying stability and consistency of existing mappings.
* Detecting conflicts between schema declarations and stored mappings.

### 6.5 Sync Domain Compilation Engine

The Sync Domain Compilation Engine is responsible for:

* Compiling sync domain declarations into efficient structures required by [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Resolving domain membership to app_ids and type_ids.
* Exposing domain metadata to State Manager.

## 7. Startup and shutdown behavior

### 7.1 Startup

On startup, the Schema Manager must:

* Initialize internal state.
* Load all schemas from the graph.
* Validate all schemas.
* Compile schemas and domains.
* Verify type_id mappings.
* Enter ready state only if all steps succeed.

This sequence preserves the validation ordering mandated by [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md), where schema validation must succeed before [Graph Manager](07-graph-manager.md) persists any mutation.

If any step fails, the Schema Manager must fail closed and report degraded health.

### 7.2 Shutdown

On shutdown, the Schema Manager must:

* Reject new schema-dependent requests.
* Release in-memory structures.
* Perform no persistence operations.

No special shutdown ordering is required beyond normal manager teardown.

## 8. Reload semantics

### 8.1 Controlled reload

Schema reload is an explicit administrative operation.

During reload:

* All schema-dependent operations must be rejected.
* Existing compiled schema state remains active until reload succeeds.
* Reload is atomic.

### 8.2 Reload failure

If reload fails:

* The previous compiled schema remains active.
* Failure is reported to [Health Manager](13-health-manager.md).
* No partial state is permitted.

Automatic or incremental reload is forbidden.

## 9. Type identifier management

### 9.1 Mapping rules

* type_key to type_id mappings are per app_id and per kind so either identifier in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) resolves without ambiguity.
* type_id assignment is monotonic, keeping the immutable `type_id` fields defined in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) stable.
* type_ids are never reused.
* type_ids are never remapped.

### 9.2 Creation constraints

The Schema Manager may create missing mappings only if:

* The app_id exists.
* The type_key exists in the loaded schema and matches a declaration that callers could reference via `type_key` in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* No existing mapping exists.

Mappings for undeclared type_keys are forbidden.

### 9.3 Determinism

Given identical schema definitions and unchanged storage, type resolution must be identical across restarts. Conflicts cause startup failure.

## 10. Validation helpers for Graph Manager

### 10.1 Parent validation

Validation must confirm:

* app_id exists and has a loaded schema, preserving the namespace guarantees in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* parent type_key exists and matches a declaration referenced by `type_key` or `type_id` in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* parent creation rules declared by the schema are satisfied.

### 10.2 Attribute validation

Validation must confirm:

* parent type exists.
* attribute type exists for that parent.
* value representation matches schema constraints for the `value_json` payload defined in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* cardinality constraints are satisfied.

### 10.3 Edge and rating validation

Validation must confirm:

* referenced types exist.
* relationships are permitted, matching the schema-derived rules consumed by ACL evaluation in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* domain constraints are respected so objects remain eligible for the per-domain sync model in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).

No inferred constraints are permitted.

## 11. Sync domain compilation and exposure

### 11.1 Domain compilation

The Schema Manager must compile domain configurations such that [State Manager](09-state-manager.md) can resolve the sync invariants required by [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md):

* domain_name to configuration.
* configuration to app_ids, parent_type_ids, and attribute_type_ids.

### 11.2 Domain constraints

* Domain names are scoped to app_id ([01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md)).
* Duplicate domain names within an app_id are forbidden.
* Cross-app domain merging is forbidden unless explicitly defined by protocol ([01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)).

### 11.3 Domain modes

Domain mode is treated as metadata only. Enforcement is performed by [State Manager](09-state-manager.md) per [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).

## 12. Allowed behaviors

The Schema Manager explicitly allows:

* Multiple apps with independent schemas, matching the isolation rules in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Deterministic type resolution so operations defined in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) can choose either identifier form.
* Schema-declared sync domains, enabling the state machine described in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Read-only schema access by other managers, preserving the manager responsibilities in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Controlled administrative reload that does not bypass the compatibility guarantees documented in [01-protocol/10-versioning-and-compatibility.md](../../01-protocol/10-versioning-and-compatibility.md).

## 13. Forbidden behaviors

The Schema Manager explicitly forbids:

* Multiple schemas per app_id, which would violate [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Runtime mutation of compiled schemas outside explicit reloads.
* Cross-app schema references ([01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md)).
* Silent type_id remapping, which would contradict the immutability guarantees in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* Schema inference from data, disallowed by the declaration-before-use posture in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Authorization decisions ([01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md)).
* Automatic migration or compatibility heuristics.

## 14. Failure handling

### 14.1 Startup failures

If startup fails:

* The Schema Manager enters failed state.
* Schema-dependent operations are rejected.
* Health Manager must surface the failure.

All such failures are reported using the schema error class defined in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

### 14.2 Runtime failures

At runtime, operations referencing unknown or invalid schema elements must be rejected immediately, preserving the precedence rules (structural before schema before authorization) in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

### 14.3 Integrity failures

Any detected inconsistency between schema declarations and persisted indices is fatal and must block schema-dependent operations, even if the caller would otherwise succeed per [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

## 15. Security constraints

* Schema input is untrusted.
* Payload size and nesting must be bounded.
* Parsing and compilation must be resource bounded.
* No remote input may trigger schema reload.

## 16. Manager interactions

* [Graph Manager](07-graph-manager.md) depends on Schema Manager for validation only, matching the processing order in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* [State Manager](09-state-manager.md) depends on Schema Manager for domain metadata only, consistent with [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* [Storage Manager](02-storage-manager.md) is used only for type_id persistence and must uphold the immutability constraints in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* [Health Manager](13-health-manager.md) consumes readiness and failure signals so system posture matches [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

No cyclic dependencies are permitted.

## 17. References

* Graph object model and envelopes are defined in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) and [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Storage layout and app_N_type tables are defined in [03-data/**](../../03-data/).
* Sync behavior is defined in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) and [02-architecture/managers/09-state-manager.md](09-state-manager.md).
* Authorization behavior is defined in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md) and [02-architecture/managers/06-acl-manager.md](06-acl-manager.md).
