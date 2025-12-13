



# 00. Scope and goals

## 1. Purpose and scope of this document

This document defines the scope, goals, and boundaries of the 2WAY system proof of concept (PoC) design repository. It specifies what the repository is intended to describe, what guarantees it aims to establish at the design level, and what is explicitly out of scope. It does not define implementation details, deployment practices, or operational policy unless those are required to preserve correctness or security.

This document applies to the entire repository. All other documents are interpreted as refinements within the scope and constraints defined here.

## 2. System scope

The 2WAY system is a local first, graph based system for identity, data ownership, access control, peer to peer synchronization, and incentive mediated interaction. The scope of this repository is limited to the design required to build and evaluate a proof of concept implementation of that system.

Within scope:

- A formal protocol level model for identity, authorship, ownership, and mutation.
- A graph based data model with explicit typing, ownership, and ordering.
- A validation and enforcement pipeline that ensures structural correctness, authorization, and integrity.
- A decentralized synchronization model with explicit trust boundaries and replay protection.
- A modular backend architecture composed of strictly defined managers and services.
- A local API surface for frontend applications and backend extensions.
- Security properties derived from cryptographic identity, immutability, and constrained authority.
- Economic and incentive mechanisms encoded as first class graph structures and app level logic.

Out of scope:

- Production scalability guarantees beyond what is implied by the PoC design.
- Centralized economic coordination, global settlement, or external token infrastructure.
- User interface design, UX decisions, or frontend implementation details.
- Centralized infrastructure assumptions or mandatory service dependencies.
- Non local data custody or externally enforced state.

## 3. Design goals

The design goals stated here are normative constraints on all components described in this repository.

#### 3.1 Correctness and integrity

The system must ensure that:

- All persisted state changes are attributable to a cryptographic identity.
- Unauthorized mutations are structurally impossible, not merely discouraged.
- Historical state cannot be rewritten or silently corrupted.
- Invalid or malformed operations are rejected before persistence.

#### 3.2 Local authority and autonomy

Each node must be able to:

- Operate independently without reliance on a central coordinator.
- Enforce its own validation, authorization, and visibility rules.
- Select which peers, domains, and identities it interacts with.
- Maintain a consistent local state while offline.

#### 3.3 Explicit trust boundaries

Trust relationships must be explicit and inspectable:

- Identities are bound to keys represented in the graph.
- Permissions are derived from schema rules and ACLs, not implicit roles.
- Sync behavior is constrained by declared domains and sequence ordering.
- No component may infer trust from transport context or network position.

#### 3.4 Minimal trusted surface

The design must minimize the amount of logic that is implicitly trusted:

- All writes flow through a single validation pipeline.
- Managers form a closed backend kernel with no external mutation access.
- Apps and services operate with explicitly scoped authority.
- Transport security is not relied upon for correctness or integrity.

#### 3.5 Incentive alignment and local enforcement

The system must support incentive structures that:

- Are encoded as graph objects with explicit ownership and authorship.
- Are enforced locally by schema rules and ACL evaluation.
- Do not require global consensus to be meaningful.
- Remain interpretable and enforceable even under partial network participation.

## 4. Responsibilities

At the repository level, this design is responsible for defining:

- The abstract protocol and data model used by all compliant implementations.
- The invariants that must hold for graph state, identity, ownership, and incentives.
- The interfaces and trust boundaries between major system components.
- The conditions under which operations are accepted, rejected, or ignored.

The design is not responsible for:

- Market pricing, valuation, or external economic policy.
- Guaranteeing liquidity or participation.
- Resolving disputes outside the defined graph semantics.

## 5. Invariants and guarantees

The following invariants apply globally and must not be violated by any component:

- Every operation has exactly one author identity.
- Every identity is anchored to at least one verifiable public key.
- Ownership of graph Parents is immutable.
- All persistent mutations are totally ordered by a local sequence.
- Authorization is evaluated before any persistent write.
- No component may bypass Graph Manager to write state.

The system guarantees that:

- Unauthorized operations do not reach persistent storage.
- Authorship and provenance are verifiable from stored state alone.
- Incentive structures cannot bypass authorization or ownership rules.
- Partial compromise does not imply total system compromise.
- State evolution is auditable, reproducible, and can be rolled back.

## 6. Allowed behaviors

The following behaviors are explicitly allowed within this scope:

- Multiple independent implementations adhering to the same protocol.
- Application specific schemas that define domain local semantics.
- Selective synchronization based on explicit trust and visibility rules.
- Delegation of limited authority via graph encoded relationships.
- App defined incentive models operating within schema and ACL constraints.

## 7. Forbidden behaviors

The following behaviors are explicitly forbidden:

- Implicit trust based on network origin or transport layer identity.
- Direct database access by apps or frontend components.
- Mutation of objects without passing full validation and ACL checks.
- Cross app interpretation or mutation of foreign domain objects.
- Incentive mechanisms that require rewriting or bypassing ownership rules.
- Silent rewriting or deletion of historical state.

## 8. Interactions with other components

This document defines no direct interfaces. It constrains other components as follows:

- Protocol documents must conform to the invariants defined here.
- Architecture documents must respect the stated trust boundaries.
- Security documents must not weaken or bypass the guarantees listed.
- Incentive mechanisms must be expressible using the core graph model.
- PoC specific documents may narrow scope but may not expand authority.

All interactions between components are assumed to be adversarial by default and must be validated explicitly.

## 9. Failure and rejection behavior

At the scope level, the system must behave as follows on failure:

- Invalid input results in explicit rejection.
- Unauthorized operations are rejected without side effects.
- Malformed data does not propagate beyond validation boundaries.
- Partial failures do not result in undefined or ambiguous state.

Silent failure, implicit acceptance, or best effort mutation are not permitted within this design.

## 10. Non goals

The following are explicitly not goals of this design:

- Universal global consensus.
- Globally enforced monetary policy.
- Anonymous computation without identity.
- Automatic trust or reputation inference outside schema rules.
- Enforcement of social or legal policy outside the graph.

Any extension that introduces these properties must be treated as a separate design effort and is not covered by this repository.
