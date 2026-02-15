



# 01 Scope and goals

Defines system-level scope, goals, and required guarantees for the 2WAY PoC. Specifies global invariants, trust boundaries, and failure handling requirements. Defines allowed and forbidden behaviors at the system level.

For the meta specifications, see [01-scope-and-goals meta](../10-appendix/meta/00-scope/01-scope-and-goals-meta.md).

## 1. System scope

2WAY is a local-first, graph-based system for identity-anchored data ownership, access control, incentive-mediated interaction, and peer-to-peer synchronization over untrusted networks.

This repository defines the complete design required to build and evaluate a single 2WAY proof-of-concept node and its interactions with peers.

Within scope:

- A graph-based object model with explicit identity, ownership, and ordering.
- Cryptographically anchored identity and authorship.
- A deterministic validation and enforcement pipeline for all state mutations.
- A modular backend composed of Managers and Services with strict trust boundaries.
- A local API surface for frontend applications.
- A peer-to-peer synchronization model with explicit scoping, sequencing, and rejection rules.
- App-defined domains with isolated semantics enforced by schema and access control.
- Economic and incentive mechanisms expressed as graph structures and enforced locally.
- Protocol-level envelope and sync semantics as defined in [01-protocol](../01-protocol/).
- Storage layout and indexing strategies for the PoC node as defined in [03-data](../03-data/).

Out of scope:

- Centralized coordination, global consensus, or shared ledgers.
- Externally enforced monetary policy or global settlement.
- User interface or experience design beyond API boundary requirements.
- Operational deployment strategies beyond a single-node PoC.
- Any behavior that requires implicit trust in peers, transports, or infrastructure.
- Production-scale multi-node consensus or cluster management.

## 2. Design goals

The goals in this section are mandatory constraints on the design.

### 2.1 Correctness

- All persistent state mutations are validated before storage.
- Unauthorized mutations are structurally impossible.
- Historical state cannot be silently rewritten.
- Invalid input is rejected deterministically.

### 2.2 Security

- Every operation is attributable to exactly one cryptographic identity.
- Identity verification is explicit and never inferred from context.
- Authorization is enforced before persistence.
- Sync inputs are validated for integrity, ordering, and authorization.
- Key compromise is recoverable without rewriting history.

### 2.3 Local authority and autonomy

- Each node enforces its own validation and authorization rules.
- Nodes do not depend on external services to remain correct.
- Nodes can operate offline without losing consistency.
- Peer participation is optional and explicitly scoped.

### 2.4 Isolation and containment

- App domains are isolated by schema and access control rules.
- App-specific logic cannot mutate foreign domains without explicit authorization.
- Backend core logic is isolated from app logic.
- Frontend code cannot directly access backend Managers.

### 2.5 Incentive enforcement

- Incentive mechanisms are represented as graph objects.
- Incentive enforcement occurs locally through schema and access control.
- Incentives do not bypass ownership, validation, or authorization rules.
- Incentives do not require global agreement to be meaningful.

## 3. Invariants and guarantees

The following invariants apply globally:

- All backend code consists of Managers and Services.
- Frontend applications run outside the backend.
- Apps may include app service Services, but never bypass Managers.
- All graph writes occur through [Graph Manager](../02-architecture/managers/07-graph-manager.md).
- All authorization decisions occur through [ACL Manager](../02-architecture/managers/06-acl-manager.md).
- All schemas are sourced from the graph and validated by [Schema Manager](../02-architecture/managers/05-schema-manager.md).
- All synchronization state transitions occur through [State Manager](../02-architecture/managers/09-state-manager.md).
- All network traffic is mediated by [Network Manager](../02-architecture/managers/10-network-manager.md).
- All event emission is mediated by [Event Manager](../02-architecture/managers/11-event-manager.md).
- All authentication and requester resolution is mediated by [Auth Manager](../02-architecture/managers/04-auth-manager.md).
- All audit logging is mediated by [Log Manager](../02-architecture/managers/12-log-manager.md).
- All request-scoped work is bound to a complete [OperationContext](../02-architecture/services-and-apps/05-operation-context.md).

The system guarantees that:

- Unauthorized operations cannot reach persistent storage.
- Persisted objects have verifiable authorship.
- Sync cannot introduce out of order or replayed state.
- Partial compromise does not imply total compromise.
- State evolution is auditable from local data alone.

## 4. Allowed behaviors

The following behaviors are explicitly allowed:

- Multiple independent nodes operating without coordination.
- Selective synchronization with peers based on explicit rules.
- Multiple apps with isolated schemas and semantics.
- App-defined economic and incentive models within enforced boundaries.
- Delegation of limited authority encoded in graph structure.

## 5. Forbidden behaviors

The following behaviors are explicitly forbidden:

- Direct database access outside Graph Manager.
- Authorization outside ACL Manager.
- Implicit trust based on network or transport metadata.
- Cross-domain mutation without explicit authorization.
- Silent mutation or deletion of historical state.
- Bypassing validation for performance or convenience.

## 6. Trust boundaries and interactions

This document defines trust boundaries without defining interfaces.

Untrusted inputs:

- All network input.
- All frontend input prior to authentication.
- All app-provided input.

Trusted outputs only after validation:

- Persisted graph objects.
- Events emitted as a result of accepted operations.

Trust boundaries:

- Frontend to backend is mediated by authentication and OperationContext resolution.
- Network to persistence is mediated by network handling, sync logic, and graph validation.
- App logic to core state is mediated exclusively by Managers.

## 7. Failure and rejection behavior

On failure or invalid input:

- Operations are rejected explicitly.
- Rejected operations produce no persistent side effects.
- Rejected sync inputs do not advance synchronization state.
- Components fail closed at trust boundaries.
- Partial failures do not create ambiguous or intermediate state.

Silent acceptance, partial mutation, or best-effort processing are not permitted.

## 8. Non-goals

The following are explicitly not goals:

- Universal consensus.
- Global identity uniqueness.
- Anonymous mutation without identity.
- Automatic trust inference.
- Enforcement of policy outside graph-encoded rules.
