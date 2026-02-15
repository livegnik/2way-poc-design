



# 00 Scope Overview

Defines repository-wide scope boundary, invariants, and trust boundaries for 2WAY implementations. Specifies mandatory enforcement boundaries, sequencing and persistence constraints, and deterministic rejection behavior across all interaction surfaces.

For the meta specifications, see [00-scope-overview meta](../10-appendix/meta/00-scope/00-scope-overview-meta.md).

## 1. Purpose, authority, and scope

This document defines the top-level scope boundary and repository-wide invariants for the 2WAY PoC design. It is normative for all other specifications in this repository and for implementations derived from them.

This document defines:

* Repository-wide invariants and enforcement boundaries.
* Trust boundaries and mandatory interaction constraints.
* PoC runtime and persistence constraints that apply regardless of topology.
* Failure and rejection requirements that apply to all interaction surfaces.
* Document authority and conflict resolution rules.

This document does not define:

* Protocol wire formats, envelopes, or cryptographic primitives beyond naming and boundary constraints.
* Component APIs, storage schemas, or interface request and response shapes.
* Application-specific semantics, UI behavior, or deployment operations.

Details live in [01-protocol](../01-protocol/), [02-architecture](../02-architecture/), [03-data](../03-data/), [04-interfaces](../04-interfaces/), [05-security](../05-security/), and [06-flows](../06-flows/). Terminology is defined in [03-definitions-and-terminology.md](03-definitions-and-terminology.md).

## 2. Document authority and conflict resolution

* This repository is internally authoritative. Any conflict between documents is a correctness failure until resolved.
* More specific documents may refine or override more general ones only if they do not weaken invariants defined here.
* If a conflict cannot be resolved, record the exception in an ADR under [09-decisions](../09-decisions/) and update documents to restore consistency.

## 3. Repository-wide invariants and enforcement boundaries

### 3.1 Manager and pipeline invariants

Across all interaction surfaces, including local HTTP, WebSocket, app services, and remote sync, the following invariants hold:

* All request-scoped work is bound to a complete [OperationContext](../02-architecture/services-and-apps/05-operation-context.md) constructed once and treated as immutable.
* Services, frontend apps, and remote peers are untrusted and must not bypass manager enforcement.
* Client-side signing does not bypass backend validation or authorization.

Summary table (normative):

| Manager | Invariant | Notes |
| --- | --- | --- |
| <span style="white-space:nowrap;">[Graph Manager](../02-architecture/managers/07-graph-manager.md)</span> | Only permitted write path for persistent state. | Serializes writes and assigns `global_seq` on commit. |
| <span style="white-space:nowrap;">[Storage Manager](../02-architecture/managers/02-storage-manager.md)</span> | Only component permitted to issue raw database operations. | Owns SQLite connections and transactions. |
| <span style="white-space:nowrap;">[Schema Manager](../02-architecture/managers/05-schema-manager.md)</span> | Only component permitted to interpret schema and validate schema constraints. | Structural validation precedes schema validation. |
| <span style="white-space:nowrap;">[ACL Manager](../02-architecture/managers/06-acl-manager.md)</span> | Only component permitted to make authorization decisions. | Applies capability and ownership rules. |
| <span style="white-space:nowrap;">[Auth Manager](../02-architecture/managers/04-auth-manager.md)</span> | Only component permitted to resolve requester identity and session context. | Local OperationContext construction is gated on auth success. |
| <span style="white-space:nowrap;">[Key Manager](../02-architecture/managers/03-key-manager.md)</span> | Only component permitted to access private key material or perform private-key operations. | Private keys never leave this manager. |
| <span style="white-space:nowrap;">[State Manager](../02-architecture/managers/09-state-manager.md)</span> | Only component permitted to manage sync state transitions and construct remote `OperationContext`. | Applies per-peer and per-domain ordering. |
| <span style="white-space:nowrap;">[Network Manager](../02-architecture/managers/10-network-manager.md)</span> | Only component permitted to perform network I/O. | Admission enforced by DoS Guard; readiness gated by Health. |
| <span style="white-space:nowrap;">[Config Manager](../02-architecture/managers/01-config-manager.md)</span> | Only component permitted to load, validate, and publish runtime configuration snapshots. | No direct `.env` or table reads by other components. |
| <span style="white-space:nowrap;">[App Manager](../02-architecture/managers/08-app-manager.md)</span> | Only component permitted to register and bind apps and app services. | Assigns app identity and binding. |
| <span style="white-space:nowrap;">[Event Manager](../02-architecture/managers/11-event-manager.md)</span> | Only component permitted to emit backend events. | State-changing events emitted post-commit only. |
| <span style="white-space:nowrap;">[Log Manager](../02-architecture/managers/12-log-manager.md)</span> | Only component permitted to emit audit and diagnostic logs. | Logging must not imply commit on failure. |
| <span style="white-space:nowrap;">[Health Manager](../02-architecture/managers/13-health-manager.md)</span> | Only component permitted to aggregate readiness and liveness signals. | Gates admission readiness. |
| <span style="white-space:nowrap;">[DoS Guard Manager](../02-architecture/managers/14-dos-guard-manager.md)</span> | Only component permitted to enforce rate limiting and abuse controls. | Issues challenges and admission decisions. |

### 3.2 State, sequencing, and object invariants

* All persistent state is representable as graph objects defined in [02-object-model.md](../01-protocol/02-object-model.md).
* All write intents are submitted as [graph message envelopes](../01-protocol/03-serialization-and-envelopes.md), including local writes.
* Structural validation occurs before schema validation and ACL evaluation, and all validation completes before persistence.
* [Graph Manager](../02-architecture/managers/07-graph-manager.md) serializes writes and assigns `global_seq` only on successful commit.
* `global_seq` is strictly monotonic for accepted writes and is never advanced on rejection.
* Rejected operations produce no persistent state changes, no sync cursor advances, and no state-changing events.
* Sync ordering is monotonic per peer and per domain; replayed or out-of-order inputs are rejected before persistence.
* Ratings provide the only suppression mechanism; there is no delete path and historical state is not rewritten.
* Derived data and caches are non-authoritative, rebuildable, and never synced.

### 3.3 Context, configuration, and observability invariants

* Local `OperationContext` is constructed only after [Auth Manager](../02-architecture/managers/04-auth-manager.md) success.
* Remote `OperationContext` is constructed only by [State Manager](../02-architecture/managers/09-state-manager.md) after cryptographic verification and sync ordering checks.
* Runtime configuration and policy inputs flow only through [Config Manager](../02-architecture/managers/01-config-manager.md); no component reads `.env` or storage tables directly.
* State-changing events are emitted only after successful commit. Operational events may be emitted without a commit but must not imply persistence. Logs may be emitted for success or rejection but must not imply a commit on failure.
* Debug and inspection interfaces are administrative, read-only, and subject to explicit authorization.

## 4. PoC runtime and persistence constraints

The PoC design requires the following constraints:

* The backend executes as a single long-running process hosting all managers and services.
* SQLite is used with a single serialized writer path mediated by [Graph Manager](../02-architecture/managers/07-graph-manager.md) and [Storage Manager](../02-architecture/managers/02-storage-manager.md).
* Local HTTP and WebSocket interfaces are local-only and treated as untrusted inputs.
* Remote sync uses untrusted transport; cryptographic verification and ordering enforcement are required before any state mutation.
* The PoC transport operates over Tor as defined in [04-assumptions-and-constraints.md](04-assumptions-and-constraints.md); transport security is not a correctness dependency.
* Signatures and encryption follow the PoC cryptography requirements in [04-assumptions-and-constraints.md](04-assumptions-and-constraints.md) and [04-cryptography.md](../01-protocol/04-cryptography.md).
* Private keys remain local and are owned by [Key Manager](../02-architecture/managers/03-key-manager.md).
* Local correctness is independent of network availability; nodes may operate offline indefinitely.
* Runtime topologies defined in [02-runtime-topologies.md](../02-architecture/02-runtime-topologies.md) are allowed only if they preserve all invariants in this document.

## 5. Trust boundaries and interaction constraints

Trust boundaries are enforced as defined in [03-trust-boundaries.md](../02-architecture/03-trust-boundaries.md). At minimum:

* Frontend to backend input is untrusted until authenticated and validated.
* App logic and app services are untrusted relative to manager invariants.
* Services are untrusted by managers and cannot bypass manager enforcement.
* Storage is untrusted for correctness; validation and authorization happen above it.
* Remote peers and network transport are untrusted; no trust is inferred from transport metadata.

All boundaries fail closed. If a boundary cannot be enforced, the operation is rejected.

## 6. Failure, rejection, and invalid input handling

This repository requires deterministic rejection behavior for invalid or unauthorized input.

Scope level requirements:

* Invalid structure, invalid schema meaning, or unauthorized actions are rejected before any persistent write occurs.
* Rejection produces no persistent state changes and does not allocate or advance `global_seq`.
* Rejection does not emit state-changing events and does not advance sync state.
* Remote sync inputs that are malformed, replayed, unauthorized, or inconsistent with expected sync state are rejected without altering local state.

Error representation and transport specific signaling are defined elsewhere. This document constrains effects only.

## 7. Allowed and forbidden behaviors

### 7.1 Allowed behaviors

* Multiple independent nodes operating without centralized coordination.
* Selective and asymmetric sync with peers based on explicit domain rules.
* Multiple apps with isolated schemas and semantics enforced by schema and ACL rules.
* App services that remain within app boundaries and manager APIs.
* Offline operation without loss of local correctness.

### 7.2 Forbidden behaviors

* Any mutation path that bypasses Graph Manager, Schema Manager, ACL Manager, or Storage Manager.
* Any authorization decision based on transport metadata, network location, or UI context.
* Direct database or key access by system services, apps, or app services.
* Partial envelope application, implicit retries that break ordering, or advancing sync state after rejection.
* Physical deletion or rewriting of accepted history outside the defined suppression mechanisms.

## 8. Relationship to other scope documents

This file defines repository-level scope and invariants. Additional scope detail lives in:

* [01-scope-and-goals.md](01-scope-and-goals.md)
* [02-non-goals-and-out-of-scope.md](02-non-goals-and-out-of-scope.md)
* [03-definitions-and-terminology.md](03-definitions-and-terminology.md)
* [04-assumptions-and-constraints.md](04-assumptions-and-constraints.md)

If a more specific scope document conflicts with this file, the conflict must be resolved by aligning with the invariants defined here.
