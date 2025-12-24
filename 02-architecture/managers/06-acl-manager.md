



# 06 ACL Manager

## 1. Purpose and scope

The ACL Manager is the sole authority for access control decisions over graph objects. It determines whether a requester may read or mutate graph state based on identity, app context, schema defaults, ownership, group membership, and object-level overrides.

This file defines the responsibilities, boundaries, invariants, guarantees, inputs, outputs, and failure behavior of the ACL Manager.

This file does not define schema structure, graph mutation semantics, sync selection logic, transport behavior, or identity authentication. Those concerns are owned by other components and are referenced only where required for correctness.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Acting as the single authorization authority for all read and write access to graph objects.
* Evaluating access decisions using:
  * Identity-based rules.
  * App-based rules.
  * Domain-based isolation rules.
  * Group-based rules.
  * Owner privileges.
  * Schema-defined default access rules.
  * Object-level ACL overrides.
  * Execution context constraints (local versus remote).
* Enforcing app and domain isolation by rejecting cross-context operations unless schema metadata explicitly allows them.
* Deriving authorization decisions solely from local graph state, compiled schema metadata, and ACL objects provided through trusted manager interfaces.
* Participating in every write path through Graph Manager.
* Participating in every read path where visibility is restricted.
* Producing a deterministic allow or deny decision for a given operation context.
* Enforcing access control uniformly across:
  * System services.
  * App backend extension services.
  * Frontend app requests.
  * Local operations.
  * Remote sync application.
* Denying access by default when policy data is missing, malformed, ambiguous, or unsupported.

This specification does not cover the following:

* Authentication, session handling, or identity verification.
* Graph mutation ordering, sequencing, or persistence.
* Schema definition, validation, or compilation.
* Sync domain selection or envelope construction.
* Network transport, encryption, or signature verification.
* Event emission, logging, or auditing beyond returning structured denial metadata to callers.

## 3. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* All access control decisions occur exclusively through the ACL Manager.
* No service, manager, app, or extension may implement ad hoc authorization logic.
* Authorization semantics are uniform and predictable across all apps and sync domains.
* Authorization decisions are deterministic for identical inputs and graph state.
* Authorization decisions rely solely on local graph state, ACL objects, and compiled schema metadata. Network metadata, transport characteristics, or implicit context are ignored.
* Authorization evaluation has no side effects on graph state.
* Authorization evaluation must complete before any graph mutation is applied.
* Explicit deny rules from schema or ACL data take precedence over grant rules.
* Deny-by-default behavior applies whenever correctness cannot be guaranteed.
* These guarantees hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 4. Authorization inputs and outputs

### 4.1 Inputs

The ACL Manager consumes the following inputs.

OperationContext:

* requester_identity_id.
* delegated_key_id or device identifier when provided.
* app_id.
* domain_id.
* operation type (create, read, update, delete, or other graph verbs surfaced by Graph Manager).
* execution context, local or remote.
* sync domain identifier when invoked during sync apply.
* authenticated remote peer identity when applicable.

Target metadata:

* Object kind, Parent, Attribute, Edge, or Rating.
* Target object identifier.
* Owner identity identifier.
* Associated app identifier.
* Associated domain identifier.
* Schema-resolved type identifier.
* Sync domain membership flags as resolved by Schema Manager.

Local graph state snapshot:

* Parents, Attributes, Edges, Ratings, and ACL objects referenced by the target, scoped to local storage.
* Group membership edges and indices surfaced via authorized manager interfaces.
* Other graph-derived relationships declared in schema as part of authorization constraints.

Policy material:

* Compiled schema definitions covering mutability, creation permissions, allowed relations, cross-app/domain visibility, and graph-derived constraints for the object type.
* Schema-defined default ACL rules for the object type and app.
* Optional object-level ACL overrides attached to the target Parent.

### 4.2 Outputs

The ACL Manager returns:

* A binary decision, allow or deny.
* A stable denial reason category suitable for logging and audit.

The ACL Manager does not emit events, write logs, or mutate state.

## 5. Policy composition and evaluation model

### 5.1 Evaluation order

Authorization executes as a strict sequence of checks. Failure at any stage results in denial:

1. Ownership rules.
2. Schema-defined defaults and prohibitions.
3. App and domain boundary enforcement.
4. Object-level ACL evaluation.
5. Schema-declared graph-derived constraints, including group membership.

No subsequent rule may override a failure from an earlier stage.

### 5.2 Ownership semantics

The owner of a Parent object is granted implicit privileges as defined by schema defaults. Ownership is derived from Parent authorship and is immutable. Remote and local operations attempting to mutate objects owned by another identity are denied unless schema defaults and ACL data explicitly permit the action. Ownership does not bypass schema constraints or remote execution constraints.

### 5.3 Schema-defined defaults

Schema metadata establishes the baseline authorization properties for each object type:

* Mutability (mutable, append only, immutable) for each object type.
* Which identities, apps, or domains may create instances of the type.
* Allowed relations between object types.
* Whether cross-app or cross-domain access is ever permitted.

Schema validation occurs before ACL evaluation. No ACL may override schema-defined prohibitions or structural requirements.

### 5.4 App and domain boundaries

Operations are evaluated strictly within the requesting app_id and domain_id. Objects from other apps or domains are invisible unless schema metadata explicitly whitelists the relation. Cross-app or cross-domain reads and writes are denied by default, including during remote sync application. App identity never substitutes for user identity and cannot expand scope without schema approval.

### 5.5 Object-level overrides

Object-level ACLs may further restrict or extend access relative to schema defaults, subject to the following constraints:

* Overrides must be structurally valid, schema-compatible, and version-supported.
* Overrides may not violate hard constraints imposed by schema, execution context, or sync domain rules.
* Overrides are applied after schema defaults and merged deterministically.
* Explicit deny rules in overrides take precedence over grant rules.

Invalid or unsupported object-level ACL data results in denial.

### 5.6 Graph-derived constraints

Schema may declare graph-derived constraints, such as membership edges, degree-of-separation limits, trust or rating thresholds, or other deterministic graph conditions, that must be satisfied before authorization succeeds. The ACL Manager evaluates these constraints using only locally available graph state. Group membership resolution must not require unauthorized graph reads, and derived constraints cannot contradict schema prohibitions.

## 6. Local and remote execution constraints

### 6.1 Local execution

For local execution:

* Schema defaults and object-level ACLs apply normally.
* Ownership privileges apply as defined by schema.
* App and domain boundary enforcement applies identically.
* App identity constraints apply.

### 6.2 Remote execution

For remote execution, additional hard constraints apply:

* Remote operations must not rewrite or corrupt local history.
* Remote operations must not mutate objects owned by local identities unless explicitly permitted by schema and ACL rules.
* Remote operations must respect app, domain, and sync domain rules enforced by State Manager.
* Remote operations must not access objects that are not visible within the targeted app_id and domain_id.

Any violation of remote execution constraints results in denial regardless of ACL content.

## 7. Explicitly allowed and forbidden behavior

### 7.1 Explicitly allowed

The ACL Manager may:

* Cache compiled ACL rules and recent authorization decisions.
* Query group membership through authorized manager interfaces.
* Use schema-precompiled metadata provided by Schema Manager.

### 7.2 Explicitly forbidden

The ACL Manager must not:

* Perform direct database access.
* Mutate graph state.
* Perform network communication.
* Authenticate identities.
* Infer permissions from peer identity, network origin, transport context, or other implicit metadata.
* Bypass Schema Manager, Graph Manager, or State Manager boundaries.
* Grant access based on incomplete, implicit, or partially parsed policy data.

## 8. Interaction with other components

### 8.1 Graph Manager

Graph Manager invokes the ACL Manager for every graph mutation and for restricted reads.

The ACL Manager returns allow or deny prior to any mutation.

### 8.2 Schema Manager

Schema Manager supplies precompiled default ACL rules and type metadata.

The ACL Manager treats schema metadata as authoritative.

### 8.3 App Manager and Auth Manager

Identity and app context are resolved upstream.

The ACL Manager assumes identity context is trusted or denies access if missing.

### 8.4 State Manager

State Manager determines sync domains and execution context.

The ACL Manager enforces domain and remote constraints based on State Manager inputs.

## 9. Failure and rejection behavior

### 9.1 General rule

Any ambiguity, missing data, or unsupported structure results in denial before any persistent write occurs. No partial writes are ever attempted after a denial.

### 9.2 Missing identity

If requester identity is absent:

* Deny all operations unless explicitly permitted by schema-defined public access rules.

### 9.3 Missing schema defaults

If no schema-defined ACL exists for the target type:

* Deny access.

### 9.4 Malformed or unsupported ACL data

If object-level ACL data is malformed or version-unsupported:

* Deny access.

### 9.5 Cache or internal failure

Cache failures or internal evaluation errors must not affect correctness.

Authorization proceeds without cache or denies if correctness cannot be guaranteed.

## 10. Minimum correctness requirements

* Authorization decisions must be deterministic.
* Authorization must be enforced uniformly across all entry points.
* Authorization must complete before any graph mutation.
* No alternative authorization path may exist.
