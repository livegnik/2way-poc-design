



# 05. Schema Manager

## 1. Purpose and scope

This file defines the Schema Manager component within the 2WAY architecture.  
The Schema Manager is responsible for loading, validating, compiling, and exposing schema definitions stored in the graph. These schemas define the allowed object types, attribute representations, and sync domain membership used by other components for validation and routing.

Schemas are stored as graph objects so they are ordered, replicated, validated, and audited using the same mechanisms as all other graph state. Any compiled or indexed representation is strictly derived and non-authoritative.

This file specifies Schema Manager behavior only. It does not define schema authoring, graph mutation semantics, envelope formats, access control decisions, storage schemas, or sync execution.

Schema Manager validates/compiles. Schema authoring and lifecycle are defined in flows + protocol versioning.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Loading schema definitions from graph objects stored in app_0.
* Enforcing that exactly one schema exists per app_id.
* Validating schema structure, cardinality, and internal consistency.
* Compiling schemas into immutable in-memory structures.
* Maintaining per-app, per-kind mappings from type_key to numeric type_id.
* Exposing schema and type metadata to other managers.
* Providing schema-based validation helpers for Graph Manager.
* Compiling and exposing sync domain configuration metadata to State Manager.
* Rejecting schema configurations that violate invariants defined in this file.

This specification does not cover the following:

* Creating, updating, or deleting schema graph objects.
* Defining schema lifecycle policy beyond validation and reload semantics.
* Evaluating permissions, ownership, or visibility rules.
* Performing graph writes other than permitted type_id mapping creation.
* Executing sync, conflict resolution, or peer reconciliation.
* Network transport, cryptographic verification, or peer negotiation.
* Schema migration, backward compatibility handling, or data transformation.

## 3. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* Schemas stored in the graph are the only authoritative schema source.
* app_N_type tables are derived indices and are never authoritative.
* Exactly one schema exists per app_id. Multiple schemas or versions for the same app_id are forbidden.
* Schema data is treated as untrusted input and is fully validated before use.
* A type_key resolves to a numeric type_id only if declared in the loaded schema.
* A numeric type_id, once assigned, is stable and never remapped to a different type_key.
* Schema validation and type resolution are deterministic given the same schema and storage state.
* Compiled schemas are immutable at runtime unless an explicit reload occurs.
* Schema-dependent operations fail closed if schema loading or validation fails.
* If compiled indices and schema objects disagree, schema-dependent operations must be blocked.
* Domain configuration reflects exactly what is declared in loaded schemas.
* Schema validation is necessary but not sufficient for authorization.

These guarantees hold regardless of caller, execution context, input source, or peer behavior.

## 4. Inputs, outputs, and trust boundaries

### 4.1 Inputs

The Schema Manager consumes the following inputs:

* Schema Parents and Attributes stored in app_0, containing schema definitions as structured JSON values.
* app_id values used to scope schema lookup and type resolution.
* Validation and lookup requests from Graph Manager.
* Sync domain lookup requests from State Manager.

### 4.2 Outputs

The Schema Manager produces the following outputs:

* A compiled, in-memory schema registry keyed by app_id.
* Deterministic mappings from type_key to numeric type_id per app and kind.
* Compiled sync domain configuration objects keyed by domain_name.
* Validation results for schema-based checks.

### 4.3 Trust boundaries

* The Schema Manager does not trust callers to provide valid type keys, domain names, or value representations.
* Callers trust the Schema Manager to enforce schema correctness.
* The Schema Manager does not enforce access control and must not be used as an authorization oracle.

## 5. Schema representation and constraints

### 5.1 Storage location

* All schemas are stored as graph objects in app_0.
* Schemas are represented as Parents with associated Attributes that contain the schema definition.
* No schema information is loaded from configuration files or code.

### 5.2 Cardinality and version rules

* Exactly one schema per app_id is permitted.
* Multiple schemas for the same app_id must be rejected.
* The schema version field is required but informational only.
* Multiple versions for the same app_id must be rejected.
* Version comparison, upgrade, or migration logic is explicitly out of scope.

### 5.3 Required schema fields

A schema is structurally valid only if it declares:

* app_slug.
* version.
* parent_types.
* sync_schema with domains.

Each parent type must declare its attribute types.  
Each sync domain must declare at least:

* parent_types.
* mode.

Missing required fields cause schema rejection.

### 5.4 Scoping rules

* A schema defines types only within its own app_id namespace.
* Cross-app type references are forbidden.
* Duplicate type_key definitions within the same app and kind are forbidden.

## 6. Compilation and lifecycle

### 6.1 Startup compilation

On startup, the Schema Manager must:

* Load all schema objects from app_0.
* Parse schema definitions.
* Validate structure, cardinality, and internal consistency.
* Detect and reject duplicate app_id schemas.
* Compile schemas into immutable in-memory registries.
* Ensure all declared type_keys have corresponding type_id mappings.

If any step fails, the schema subsystem must be considered failed.

### 6.2 Runtime characteristics

* Compiled schemas must be fully resident in memory.
* No schema eviction or partial unloading is permitted.
* Schema lookup and validation must not require parsing schema JSON.

### 6.3 Reload semantics

* Schema reload is a controlled administrative operation.
* Reload is atomic.
* During reload, schema-dependent operations must be rejected.
* Reload failure leaves the previously loaded schema active.
* Automatic or incremental reload is forbidden.

## 7. Type identifier management

### 7.1 Mapping rules

* type_key to type_id mappings are per app_id and per kind.
* type_id assignment is monotonic and stable.
* Existing mappings must never be modified or reused.

### 7.2 Creation constraints

The Schema Manager may create missing type mappings only if:

* The app_id exists.
* The type_key exists in the loaded schema.
* No existing mapping exists for that type_key and kind.

Type mappings for undeclared type_keys must never be created.

### 7.3 Determinism across restarts

* Given identical schema definitions and unchanged storage, type resolution must be identical across restarts.
* If schema definitions change in a way that conflicts with existing mappings, startup must fail.

## 8. Validation helpers for Graph Manager

The Schema Manager provides schema-based validation helpers used by Graph Manager.

### 8.1 Parent validation

Validation must confirm:

* The app_id has a loaded schema.
* The parent type_key exists in that schema.

### 8.2 Attribute validation

Validation must confirm:

* The parent type exists.
* The attribute type exists under that parent type.
* The value representation matches the declared schema representation.

### 8.3 Edge and rating validation

Validation must confirm:

* Referenced type_keys exist.
* Declared relationships are permitted by the schema.
* Domain constraints declared in the schema are not violated.

The Schema Manager must not invent constraints not declared in the schema.

## 9. Sync domain compilation and exposure

### 9.1 Domain compilation

The Schema Manager must compile sync domain configurations that allow State Manager to resolve:

* domain_name to domain configuration.
* domain configuration to app_ids, parent_type_ids, and attr_type_ids.

### 9.2 Domain name constraints

* Domain names are global across all schemas.
* Domain name collisions are forbidden.
* Any collision causes startup failure.

### 9.3 Domain modes

* Domain mode is treated as declared metadata.
* The Schema Manager exposes mode but does not enforce its semantics.

## 10. Allowed behaviors

The Schema Manager explicitly allows:

* Multiple apps with independent schemas.
* Deterministic type resolution per app and kind.
* Schema-declared sync domains shared across apps.
* Read-only schema access by other managers.

## 11. Forbidden behaviors

The Schema Manager explicitly forbids:

* Multiple schemas or versions per app_id.
* Schema inference from data or runtime behavior.
* Runtime mutation of compiled schemas.
* Cross-app schema references.
* Silent remapping of existing type_ids.
* Authorization or permission evaluation.
* Automatic schema migration or compatibility heuristics.

## 12. Failure handling

### 12.1 Startup failures

If schema loading or compilation fails:

* The Schema Manager must enter a failed state.
* Schema-dependent operations must be rejected.
* Health Manager must be able to surface the failure.

### 12.2 Runtime failures

At runtime, operations must be rejected if they reference:

* Unknown app_id.
* Unknown type_key or kind.
* Invalid attribute representations.
* Unknown or invalid domain_name.

No fallback or coercion is permitted.

### 12.3 Integrity failures

If inconsistencies are detected between compiled schemas and persisted type mappings:

* The system must treat this as a fatal integrity failure.
* Schema-dependent operations must be blocked.

## 13. Security constraints

* Schema data is treated as untrusted input.
* Oversized schema payloads must be rejected.
* Excessive nesting or pathological structures must be rejected.
* Schema parsing and compilation must be bounded in time and memory.

## 14. References

* Graph object model and envelopes are defined in the protocol specifications.
* Storage layout and app_N_type tables are defined in the data specifications.
* Sync behavior is defined in the State Manager specification.
* Authorization behavior is defined in the ACL Manager specification.
