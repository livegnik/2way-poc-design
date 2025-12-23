



# 06 ACL Manager

## 1. Purpose and scope

The ACL Manager is the sole authority for access control decisions over graph objects. It determines whether a requester may read or mutate graph state based on identity, app context, schema defaults, ownership, group membership, and object-level overrides.

This file defines the responsibilities, boundaries, invariants, guarantees, inputs, outputs, and failure behavior of the ACL Manager.

This file does not define schema structure, graph mutation semantics, sync selection logic, transport behavior, or identity authentication. Those concerns are owned by other components and are referenced only where required for correctness.

## 2. Responsibilities and boundaries

### 2.1 Responsibilities and boundaries

This specification is responsible for the following:

* Acting as the single authorization authority for all read and write access to graph objects.
* Evaluating access decisions using:

  * Identity-based rules.
  * App-based rules.
  * Group-based rules.
  * Owner privileges.
  * Schema-defined default access rules.
  * Object-level ACL overrides.
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
* Authorization evaluation has no side effects on graph state.
* Authorization evaluation must complete before any graph mutation is applied.
* Deny-by-default behavior applies whenever correctness cannot be guaranteed.
* These guarantees hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 4. Authorization inputs and outputs

### 4.1 Inputs

The ACL Manager consumes the following inputs.

OperationContext:

* requester_identity_id.
* app_id.
* execution context, local or remote.
* sync domain identifier when invoked during sync apply.
* authenticated remote peer identity when applicable.

Target metadata:

* Object kind, Parent, Attribute, Edge, or Rating.
* Target object identifier.
* Owner identity identifier.
* Associated app identifier.
* Schema-resolved type identifier.
* Sync domain membership flags as resolved by Schema Manager.

Policy material:

* Schema-defined default ACL rules for the object type and app.
* Optional object-level ACL override attached to the target Parent.

### 4.2 Outputs

The ACL Manager returns:

* A binary decision, allow or deny.
* A stable denial reason category suitable for logging and audit.

The ACL Manager does not emit events, write logs, or mutate state.

## 5. Policy composition and evaluation model

### 5.1 Policy sources

Authorization decisions are derived from the following sources, evaluated together:

* Schema-defined default ACL rules.
* Object-level ACL overrides.
* Ownership semantics.
* Group membership semantics.
* App identity constraints.
* Execution context constraints, local versus remote.

### 5.2 Ownership semantics

The owner of a Parent object is granted implicit privileges as defined by schema defaults. Ownership does not bypass schema constraints or remote execution constraints.

### 5.3 Object-level overrides

Object-level ACLs may further restrict or extend access relative to schema defaults, subject to the following constraints:

* Overrides must be structurally valid and schema-compatible.
* Overrides may not violate hard constraints imposed by execution context or sync domain rules.
* Overrides are applied after schema defaults and merged deterministically.

Invalid or unsupported object-level ACL data results in denial.

### 5.4 App identity constraints

Authorization decisions may include app-level restrictions:

* Operations are evaluated in the context of the requesting app.
* App identity does not substitute for user identity.
* App-based allowances must be explicitly defined in schema defaults or object-level ACLs.

### 5.5 Group membership

Group-based permissions are evaluated using group membership as defined in the graph and exposed through trusted manager interfaces.

Group resolution must not require unauthorized graph reads.

## 6. Local and remote execution constraints

### 6.1 Local execution

For local execution:

* Schema defaults and object-level ACLs apply normally.
* Ownership privileges apply as defined by schema.
* App identity constraints apply.

### 6.2 Remote execution

For remote execution, additional hard constraints apply:

* Remote operations must not rewrite or corrupt local history.
* Remote operations must not mutate objects owned by local identities unless explicitly permitted by schema and ACL rules.
* Remote operations must respect sync domain rules enforced by State Manager.

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

Any ambiguity, missing data, or unsupported structure results in denial.

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

## Change Summary

* Added explicit enforcement that all access control occurs exclusively through ACL Manager.
* Removed speculative or UI-facing ACL concepts not present in the PoC build guide.
* Corrected emphasis to include both read and write authorization paths.
* Clarified interaction boundaries with Graph Manager, Schema Manager, and State Manager.
* Tightened remote execution constraints to match PoC sync and history integrity rules.
* Retained ownership, group-based, app-based, schema-default, and object-level ACL concepts from older design documents because they remain explicitly referenced and required by the PoC build guide.
