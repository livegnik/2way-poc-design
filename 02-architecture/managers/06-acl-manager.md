



# 06 ACL Manager

## 1. Purpose and scope

The ACL Manager is the sole authority for access control decisions over graph objects within the 2WAY system, implementing the normative behaviors defined in `01-protocol/06-access-control-model.md` and the pipeline positioning described in `01-protocol/00-protocol-overview.md`. It determines whether a requester may read or mutate graph state based on identity, app context, schema-defined defaults, ownership rules, group and relationship constraints, object-level ACL overrides, execution context, and sync constraints.

This specification defines the responsibilities, boundaries, internal engines, execution phases, invariants, guarantees, inputs, outputs, and failure behavior of the ACL Manager.

This specification defines authorization logic only. It does not define authentication, identity verification, graph mutation semantics, persistence, sync selection, transport behavior, encryption, signature verification, or logging implementation. Those concerns are handled by other protocol specifications such as [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md), [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md), and [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).

This specification references:

* [01-protocol/**](../../01-protocol/)
* [02-architecture/00-architecture-overview.md](../00-architecture-overview.md)
* [02-architecture/01-component-model.md](../01-component-model.md)
* [02-architecture/02-runtime-topologies.md](../02-runtime-topologies.md)
* [02-architecture/03-trust-boundaries.md](../03-trust-boundaries.md)
* [02-architecture/04-data-flow-overview.md](../04-data-flow-overview.md)
* [02-architecture/managers/**](../managers/)
* [02-architecture/services-and-apps/**](../services-and-apps/)
* [04-interfaces/**](../../04-interfaces/)

This specification consumes the protocol contracts defined in:

* [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md)
* [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md)
* [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md)
* [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md)

Those files remain normative for all behaviors described here.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Acting as the single authorization authority for all read and write access to graph objects, as mandated in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) and restated in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Evaluating access decisions for all graph operations, including create, read, update, and delete, matching the supervised operation ordering in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and the access layers in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Enforcing authorization consistently for:
  * Local frontend requests.
  * Backend system services.
  * Backend app extension services.
  * State Manager driven remote sync application.
* Evaluating authorization using only:
  * Identity context.
  * App context.
  * Domain and sync domain context.
  * Schema-defined defaults and prohibitions.
  * Ownership semantics.
  * Group and relationship constraints derived from the graph.
  * Object-level ACL overrides.
* Enforcing app isolation and domain isolation per [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md) and [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Enforcing remote execution restrictions during sync application, including the remote envelope rules in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Producing deterministic allow or deny decisions with stable rejection categories that map to [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).
* Failing closed on missing, ambiguous, malformed, or unsupported policy data, following the rejection posture in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md) and [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).
* Participating in every graph mutation path before any persistent write occurs, consistent with the sequencing in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Participating in every restricted read path where visibility is constrained by policy, as required by [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

This specification does not cover the following:

* Authentication or session resolution, owned by [Auth Manager](04-auth-manager.md) per [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Identity verification or signature validation, governed by [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Graph mutation ordering, sequencing, or persistence, which remain the responsibility of [Graph Manager](07-graph-manager.md) and [Storage Manager](02-storage-manager.md) per [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Schema definition, compilation, or validation defined in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* Sync domain selection or package construction described in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Network transport, encryption, or peer authentication, governed by [Network Manager](10-network-manager.md) and [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Event emission, logging storage, or audit pipelines.

## 3. Invariants and guarantees

Across all relevant components, boundaries, and contexts defined in this file, the following invariants and guarantees hold:

* All access control decisions occur exclusively through the ACL Manager, preserving the single-authority requirement in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* No other manager, service, or app may implement independent authorization logic, in accordance with the trust boundaries in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Authorization decisions are deterministic for identical inputs and identical graph state, mirroring [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Authorization decisions rely solely on:
  * Local graph state.
  * Compiled schema metadata.
  * ACL objects attached to graph Parents.
  These sources align with the allowed inputs described in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md), and no network metadata or transport hints are ever considered.
* Authorization evaluation has no side effects, per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Authorization evaluation completes before any graph mutation occurs, firmly positioned between schema validation and persistence in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Explicit deny rules always override allow rules, matching the precedence rules in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Schema-defined prohibitions cannot be overridden by ACL data, per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Authorization fails closed when correctness cannot be guaranteed, matching both [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md) and the rejection handling in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).
* These guarantees hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise, ensuring parity with [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

## 4. Internal structure and engines

The ACL Manager is internally structured as a set of deterministic engines executed in a strict order. These engines are logical components and do not imply separate processes or threads.

### 4.1 ACL Evaluation Engine

The core engine responsible for evaluating authorization decisions. It orchestrates all subordinate engines and produces the final allow or deny decision.

### 4.2 Schema Default Engine

Evaluates schema-defined default permissions, prohibitions, mutability rules, and creation rules for the target object type.

### 4.3 Ownership Resolution Engine

Resolves ownership semantics for the target object and determines owner privileges as defined by schema metadata.

### 4.4 Domain and App Boundary Engine

Enforces app isolation, domain isolation, and cross-context visibility rules.

### 4.5 Object ACL Engine

Parses, validates, and applies object-level ACL overrides attached to Parent objects.

### 4.6 Graph Constraint Engine

Evaluates schema-declared graph-derived constraints such as group membership, relationship existence, trust edges, degree-of-separation limits, or rating thresholds.

### 4.7 Remote Execution Constraint Engine

Applies additional hard constraints for operations originating from remote peers during sync application.

### 4.8 Cache Layer

An internal, optional cache used to accelerate repeated authorization decisions. Cache use must never affect correctness.

## 5. Authorization inputs and outputs

### 5.1 Inputs

The ACL Manager consumes the following inputs after the structural validation, signature verification, and schema validation stages described in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) and [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).

#### OperationContext

* requester_identity_id.
* delegated_key_id or device identifier, when present.
* app_id.
* domain identifier.
* operation type.
* execution context, local or remote.
* sync domain identifier, when invoked during sync.
* authenticated remote peer identity identifier, when applicable.

[OperationContext](../services-and-apps/05-operation-context.md) content and immutability follow the lifecycle detailed in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md), while remote fields originate from the sync submission flow in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).

#### Target object metadata

* Object kind, Parent, Attribute, Edge, or Rating.
* Target object identifier.
* Owner identity identifier.
* Associated app identifier.
* Associated domain identifier.
* Schema-resolved type identifier.
* Sync domain membership flags.

These values correspond to the canonical object structures in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).

#### Local graph state

* Parents, Attributes, Edges, Ratings, and ACL objects required for evaluation.
* Group membership relationships resolved through authorized manager interfaces.
* Other schema-declared graph relationships required for constraint evaluation.

Only locally persisted and authorized data sources listed in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md) may be queried; transport metadata or remote peer claims are ignored.

#### Policy material

* Compiled schema metadata supplied by Schema Manager.
* Schema-defined default ACL rules.
* Optional object-level ACL overrides attached to the Parent.

Overrides are stored using the ACL representation defined in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) and evaluated under the precedence rules from [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

### 5.2 Outputs

The ACL Manager returns:

* A binary authorization decision, allow or deny.
* A stable rejection category suitable for logging and audit.

Rejection categories map deterministically to the protocol errors in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md) (for example `ERR_AUTH_ACL_DENIED`), ensuring consistent telemetry across managers.

The ACL Manager does not emit events and does not mutate state, matching the side-effect restrictions in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

## 6. Evaluation order and execution model

Authorization is evaluated in a strict, linear sequence that mirrors the layers enumerated in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md). Failure at any stage results in immediate denial.

1. Ownership resolution.
2. Schema-defined defaults and prohibitions.
3. App and domain boundary enforcement.
4. Object-level ACL evaluation.
5. Graph-derived constraint evaluation.
6. Remote execution constraint enforcement.

No later stage may override a failure from an earlier stage, and earlier pipeline stages (structural validation, signature verification, and schema validation) must already have succeeded as described in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md) and enforced for remote envelopes by [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).

## 7. Ownership semantics

* Ownership is derived from Parent authorship, exactly as defined in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Ownership is immutable and cannot be reassigned.
* Owner privileges are defined exclusively by schema defaults, and only explicit ACL rules may extend those privileges within schema limits.
* Ownership does not bypass schema prohibitions declared in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Ownership does not bypass remote execution constraints defined for sync flows in [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Attempts to mutate objects owned by another identity are denied unless explicitly permitted by schema and ACL rules, honoring the remote mutation prohibition in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

## 8. Schema-defined defaults and prohibitions

Schema metadata defines, consistent with [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md):

* Whether an object type is mutable, append-only, or immutable.
* Which identities, apps, or domains may create objects of the type.
* Which operations are permitted or forbidden.
* Whether cross-app or cross-domain access is ever allowed.

Schema-defined prohibitions are absolute and cannot be overridden by ACL data, per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

If schema metadata is missing or incomplete, access is denied, producing the schema-related rejection described in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

## 9. App and domain boundary enforcement

* All authorization is evaluated within the requesting app_id and domain, preserving the isolation boundaries described in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Objects outside the app or domain are invisible unless explicitly permitted by schema.
* Cross-app reads or writes are denied by default.
* Cross-domain reads or writes are denied by default.
* App identity does not substitute for user identity.

These rules apply identically for local execution and remote sync application per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

## 10. Object-level ACL overrides

Object-level ACL overrides are attached as Attributes on Parent objects, following the ACL representation described in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).

Rules:

* Overrides must be well-formed and schema-compatible.
* Overrides may restrict or extend permissions within schema limits.
* Overrides cannot violate schema-defined prohibitions from [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Explicit deny rules override allow rules.
* Unsupported or malformed ACL data results in denial and produces the deterministic rejection outlined in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

## 11. Graph-derived constraints

Schema may declare graph-derived authorization constraints, including those enumerated in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md):

* Group membership requirements.
* Relationship existence requirements.
* Degree-of-separation limits.
* Trust or rating thresholds.

The ACL Manager evaluates these constraints using only local graph state. Unauthorized graph reads are not permitted during evaluation. If required state cannot be resolved safely, access is denied, matching the fail-closed rule in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

## 12. Local and remote execution constraints

### 12.1 Local execution

For local execution:

* Schema defaults apply.
* Object-level ACLs apply.
* Ownership semantics apply.
* App and domain boundaries apply.

These local behaviors align with the baseline model in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

### 12.2 Remote execution

For remote execution during sync application, inside the envelope pipeline defined in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md):

* Remote operations must not rewrite local history; rewrite attempts map to `ERR_SYNC_REWRITE_ATTEMPT` in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).
* Remote operations must not mutate objects owned by local identities unless explicitly permitted, per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Remote operations must respect sync domain rules enforced by State Manager, including per-domain acceptance gates.
* Remote operations must not access objects outside the permitted app and domain.

Any violation results in denial regardless of ACL content, and refusal reasons map to [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

## 13. Allowed and forbidden behavior

### 13.1 Allowed behavior

The ACL Manager may:

* Cache compiled ACL data and recent decisions, provided cache hits never contradict the evaluation rules in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Query group membership and relationships through authorized interfaces exposed by [Graph Manager](07-graph-manager.md), retaining the manager boundaries in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Use schema-precompiled metadata that originated from the authorization inputs defined in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

### 13.2 Forbidden behavior

The ACL Manager must not:

* Access the database directly, which would bypass [Graph Manager](07-graph-manager.md) and violate [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Mutate graph state, preserving the write-path exclusivity defined in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Perform network communication, so transport trust boundaries in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) remain intact.
* Authenticate identities, which is governed by [Auth Manager](04-auth-manager.md) and [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Infer permissions from transport metadata, which is explicitly forbidden in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Bypass Schema Manager, Graph Manager, or State Manager.
* Grant access based on incomplete or implicit data, ensuring fail-closed behavior per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

## 14. Manager interactions

### 14.1 Graph Manager

Graph Manager invokes ACL Manager for every mutation and restricted read, exactly as depicted in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).

The ACL Manager must return a decision before any write occurs to preserve the envelope validation order established in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).

### 14.2 Schema Manager

[Schema Manager](05-schema-manager.md) provides authoritative schema metadata compiled from the object model described in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).

ACL Manager treats schema metadata as final and immutable for the duration of any evaluation.

### 14.3 Auth Manager and App Manager

Identity and app context are resolved upstream via the [OperationContext](../services-and-apps/05-operation-context.md) construction process in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).

If required context is missing, access is denied because the protocol forbids substituting transport metadata for authenticated context.

### 14.4 State Manager

State Manager supplies sync domain and execution context per [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).

ACL Manager enforces remote constraints accordingly and denies access if State Manager inputs cannot be validated.

## 15. Failure and rejection behavior

### 15.1 General rule

Any ambiguity, missing data, or unsupported structure results in denial, matching the fail-closed requirement in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md) and the rejection handling defined in [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md). No partial evaluation or partial write is permitted.

### 15.2 Missing identity

If requester identity is missing:

* Deny all operations unless schema explicitly permits public access, following the requirements spelled out in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

### 15.3 Missing schema defaults

If schema-defined ACL metadata is missing:

* Deny access, generating the schema-related rejection code from [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

### 15.4 Malformed ACL data

If object-level ACL data is malformed or unsupported:

* Deny access, treating it as an authorization failure per [01-protocol/09-errors-and-failure-modes.md](../../01-protocol/09-errors-and-failure-modes.md).

### 15.5 Internal or cache failure

If internal evaluation fails:

* Deny access or bypass cache and re-evaluate.
* Correctness always takes precedence over availability.

## 16. Readiness and liveness guarantees

* ACL Manager is considered ready once schema metadata is loaded, mirroring the readiness expectations in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* ACL Manager has no long-running state.
* ACL Manager failure results in fail-closed behavior across the system, ensuring the guarantees described in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
