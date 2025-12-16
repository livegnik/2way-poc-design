



# 2WAY System PoC Design Repository

## What this repository is

This repository contains the normative system design for the 2WAY proof of concept (PoC).

2WAY is a local-first, peer-to-peer application substrate that provides identity, data ownership, access control, synchronization, and trust semantics as shared infrastructure rather than application-specific backend logic.

The design defined here is complete at the protocol and architecture level. All major data models, security properties, failure modes, operational flows, and implementation constraints required for a correct PoC are explicitly specified.

This repository defines what must exist and how it must behave.
It is a design specification, not a production implementation.

## What this repository is not

* Not an SDK
* Not a reference or demo implementation
* Not a deployment, orchestration, or operations guide
* Not a UI or product specification
* Not a performance-optimized or horizontally scaled system

Anything not explicitly defined within the scope of this repository is out of bounds and must not be assumed.

## Who this repository is for

* Systems engineers evaluating the protocol and architecture
* Implementers building the PoC exactly as specified
* Reviewers auditing correctness, isolation, and security properties

Suggested reading paths:

* **Conceptual orientation:** start with `00-scope`, then `01-protocol`
* **Security audit:** start with `05-security`, then `01-protocol` and `02-architecture`
* **Implementation:** read in numeric order, prioritizing `07-poc`
* **Operational behavior:** focus on `06-flows`

The repository is designed to support all of these perspectives without reinterpretation.

## Design posture and threat framing

2WAY is designed under the assumption of adversarial and unreliable environments.

The PoC explicitly considers and constrains:

* Untrusted or malicious peers
* Sybil identity creation
* Unauthorized graph mutation
* Replay and reordering attacks
* Denial-of-service through malformed or excessive input
* Partial compromise of nodes, applications, or devices

Across the design, absence of permission, ambiguity, or incomplete context results in rejection rather than fallback behavior. The system fails closed by default.

All containment mechanisms are structural and enforced locally. No global coordination or external trust is assumed.

## Core idea

Applications built on 2WAY do not own isolated databases or central backends. They operate on a shared, local-first graph representing identities, devices, relationships, content, and app-specific state under a single authorship and permission model.

Each node maintains its own authoritative state. Nodes synchronize directly with peers using signed, ordered envelopes. Incoming data is always treated as untrusted and validated locally. Consistency emerges from deterministic validation, explicit ownership, strict ordering, and scoped synchronization rather than global consensus.

## Design guarantees

The following properties are guaranteed by design and enforced structurally.

### Identity-bound authorship

Every operation is bound to a cryptographic identity.
Ownership is explicit and immutable for the lifetime of an object.

### Append-only, tamper-evident history

Accepted history is never rewritten or retroactively altered.
Ordering is explicit, monotonic, and locally authoritative.

### Structural application isolation

Applications are isolated by schema and domain boundaries.
Cross-application reinterpretation or mutation is structurally impossible, not merely disallowed by policy.

### Offline-first correctness

Nodes operate with full local authority and reconcile incrementally.
Remote coordination is never required for correctness.

### No implicit trust

Synchronization does not imply trust.
All network input is untrusted and validated against local state, schema, and authorization rules.

## Degrees of separation and influence limits

Visibility and influence are constrained through explicit graph distance.

* Relationships define degrees of separation between identities.
* Services and applications may restrict reads, writes, and broadcasts based on maximum allowed distance.
* Identities outside the permitted radius are structurally ignored.

This bounds unsolicited reach and limits the impact of unknown or weakly anchored peers.

## Sybil resistance model

2WAY does not attempt global Sybil prevention.

Instead, it limits Sybil impact through graph structure:

* Identities have no influence without meaningful graph anchoring.
* Trust, ratings, and membership are app-scoped and typed.
* Influence does not propagate across applications or domains by default.
* Degrees of separation restrict unsolicited interaction.

Large numbers of unanchored identities therefore remain inert.

The graph encodes relationships and constraints, not social truth or moral trust.

## Denial-of-service containment

The PoC is designed to degrade predictably and fail closed under load or attack.

Structural mechanisms include:

* Early rejection of malformed or unverifiable input
* Schema validation before authorization
* Authorization before any state mutation
* A single serialized write path for ordered state
* Scoped synchronization to avoid unbounded scans
* Peer-level throttling and rate limiting

These guarantees hold regardless of peer behavior.

## Guarantees vs emergent properties

Guaranteed by design:

* Identity-bound authorship
* Append-only local history
* Structural application isolation
* Deterministic validation and ordering
* Explicit authority delegation
* Fail-closed behavior

Emergent from usage:

* Trust graphs
* Reputation signals
* Social or economic meaning
* Resistance to large-scale Sybil influence

The system enforces structure, not meaning.

## What this repository deliberately does not decide

The following are intentionally left undefined or application-specific:

* User interface and experience models
* Social interpretation of trust or reputation
* Economic incentives or token systems
* Moderation, governance, or content policy
* Peer discovery and bootstrap strategy

The protocol constrains behavior. It does not impose policy.

## Repository authority model

This repository is internally self-consistent.

Authority rules:

* Documents marked as normative define required behavior.
* More specific material overrides more general material.
* Architecture Decision Records override prior text within their scope.
* In case of ambiguity or omission, behavior is considered undefined and must not be assumed.

The PoC definition is authoritative for what must be implemented.

## Repository structure

The repository is organized by conceptual dependency and authority level.
Lower-numbered folders define constraints that higher-numbered folders must not bypass or contradict.

The numbering is intentional and normative.

```
00-scope/
  Defines the scope boundary of the system.
  Goals, non-goals, terminology, assumptions, and hard constraints.
  All other material is interpreted relative to this folder.

01-protocol/
  Normative protocol definition.
  Identity, object model, serialization, cryptography, access control,
  synchronization semantics, network assumptions, error handling,
  and compatibility rules.
  This folder defines what the protocol is.

02-architecture/
  Normative architectural design.
  Component model, runtime topologies, trust boundaries, and data flow.
  Includes the backend kernel, managers, services, and app boundaries,
  as well as explicit denial-of-service guards.

03-data/
  Normative persistence and data model.
  Storage layout, system and per-application structures,
  indexing strategy, migrations, and explicit storage budgets.

04-interfaces/
  Normative interface definitions.
  Local APIs, event surfaces, internal component interfaces,
  and the system-wide error model.

05-security/
  Normative security model.
  Threat assumptions, identity and key handling, authentication and authorization,
  signed transport and sync integrity, encryption, rotation and recovery,
  privacy, selective synchronization, abuse controls, and auditability.

06-flows/
  Normative end-to-end operational flows.
  Includes success and failure paths for bootstrap, app installation,
  graph mutation, messaging, synchronization, conflict handling,
  key rotation, device lifecycle, and backup and restore.

07-poc/
  Proof of Concept definition and execution criteria.
  Feature coverage, build and run expectations, testing strategy,
  demo scenarios, known limitations, and acceptance criteria.
  This folder is authoritative for implementation scope.

08-decisions/
  Architecture Decision Records.
  Explicitly recorded tradeoffs, reversals, and resolved questions.
  Decisions here override earlier design text within their scope.

09-appendix/
  Reference material.
  Glossary, reference configurations, open questions, and diagrams.
  Informational unless explicitly stated otherwise.

10-examples/
  Illustrative examples.
  Non-normative demonstrations of how the protocol and architecture
  may be used. Examples never define required behavior.
```

Later folders must not introduce concepts that violate constraints defined earlier.

## Conformance

An implementation conforms to the 2WAY PoC design if and only if:

* All defined invariants hold under all allowed operations
* Forbidden behaviors are structurally impossible
* Validation, authorization, and ordering rules are enforced exactly
* No state mutation bypasses defined architectural boundaries

Any deviation requires an explicit Architecture Decision Record.

## Scope boundary

Only properties explicitly defined within this repository are claimed by the design.

No additional guarantees should be inferred from terminology, naming, or examples.

## Status

This repository describes a Proof of Concept.

The design prioritizes correctness, clarity, and auditability over performance or scale.
The PoC exists to validate the protocol model and architectural boundaries before any production implementation.
