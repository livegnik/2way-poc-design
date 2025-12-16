



# 2WAY System PoC Design Repository

## 2WAY at a glance

A P2P platform replacing central backends with locally enforced cryptographic data control.

* Each device keeps its own data and decides what is valid.
* Decisions are based on local rules and cryptographic keys.
* All changes are signed, recorded, and never silently rewritten.
* Network data is always treated as untrusted.
* Apps and unknown users are strictly limited by default.
* Trust does not spread automatically.
* Damage from compromise stays contained.
* Security rules are enforced by structure, not by convention.
* Missing permission means rejection, not fallback behavior.
* No central backend or global coordination.
* Unclear or invalid actions are rejected.

2WAY is designed to remain correct under compromise.

## What 2WAY is

2WAY is a local-first, peer-to-peer application substrate designed to operate correctly in hostile and unreliable environments.

It provides identity, data ownership, access control, synchronization, and trust semantics as shared infrastructure, enforced structurally rather than through centralized backends, implicit trust, or application-level convention.

Applications built on 2WAY do not own isolated databases or central servers. They operate on a shared, local-first graph where authorship is explicit, permissions are enforced before mutation, and history is append-only and verifiable.

Each node maintains its own authoritative state. Nodes synchronize directly with peers using signed, ordered envelopes. All incoming data is treated as untrusted and validated locally.

This repository contains the normative system design for the 2WAY proof of concept (PoC).
The design is complete at the protocol and architecture level [WIP].

It defines what must exist and how it must behave for a correct PoC.
It is a design specification, not a production implementation.

## Why it exists

Modern application architectures fail predictably under compromise.

Identity, authorization, ordering, synchronization, and abuse handling are repeatedly reimplemented as application-specific logic, often layered on top of centralized backends that implicitly trust infrastructure, networks, and peers. When those assumptions break, failure is silent, escalatory, and systemic.

The primary failure mode 2WAY is designed to prevent is silent escalation from local compromise to global control.

2WAY exists to make these properties non-optional by design. Identity, authorship, access control, and ordering are enforced structurally at the graph level. Local authority is treated as a security primitive, not a convenience. Synchronization does not imply trust. Absence of permission results in rejection, not fallback behavior.

The result is a system where compromise, abuse, and partial failure remain contained rather than systemic.

## Core idea

The core abstraction in 2WAY is a shared, local-first graph.

The graph represents identities, devices, relationships, content, and application-specific state. Ownership is explicit. History is append-only. All mutations are validated, authorized, and ordered before persistence.

Nodes operate independently and offline. Synchronization is incremental and explicit. Consistency emerges from deterministic validation, explicit ownership, strict ordering, and scoped synchronization rather than global consensus or coordination.

The graph is not merely a data structure. It is the primary enforcement surface for security, isolation, and authority.

Local-first operation is a security property, ensuring correctness and authority do not depend on network availability or remote honesty.

## Security model and threat framing

2WAY is designed under adversarial assumptions.

The proof of concept explicitly considers and constrains:

* Untrusted or malicious peers
* Sybil identity creation
* Unauthorized graph mutation
* Replay and reordering attacks
* Denial-of-service through malformed or excessive input
* Partial compromise of nodes, applications, or devices

Across the design, absence of permission, ambiguity, or incomplete context results in rejection rather than fallback behavior. The system fails closed by default.

Security properties are enforced structurally and locally. No global trust, centralized authority, or trusted transport is assumed.

## Structural impossibility

Many prohibited behaviors in 2WAY are not merely disallowed by policy, but structurally impossible.

Structural impossibility means that no valid execution path exists that would allow the behavior to occur, regardless of application intent, peer behavior, or network conditions.

This principle underlies application isolation, access control enforcement, graph mutation rules, and state ordering throughout the system.

## Degrees of separation and influence limits

Visibility and influence are constrained through explicit graph distance.

* Relationships define degrees of separation between identities
* Services and applications may restrict reads, writes, and broadcasts based on maximum allowed distance
* Identities outside the permitted radius are structurally ignored

This bounds unsolicited reach and limits the impact of unknown or weakly anchored peers.

## Sybil resistance through structure

2WAY does not attempt global Sybil prevention.

Instead, it limits Sybil impact through graph structure:

* Identities have no influence without meaningful graph anchoring
* Trust, ratings, and membership are app-scoped and typed
* Influence does not propagate across applications or domains by default
* Degrees of separation restrict unsolicited interaction

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

## Failure behavior

When violations occur, the system rejects input, preserves local integrity, and continues operating with reduced scope.

Recovery is explicit, never implicit.
No automatic reconciliation, overwrite, or trust escalation occurs as a side effect of failure.

## What the system guarantees

Guaranteed by design:

* Identity-bound authorship
* Append-only, tamper-evident local history
* Structural application isolation
* Deterministic validation and ordering
* Explicit authority delegation
* Fail-closed behavior under ambiguity or attack

These properties are enforced structurally, not by convention or policy.

## What the system enables but does not define

Emergent from usage:

* Trust graphs
* Reputation signals
* Social or economic meaning
* Resistance to large-scale Sybil influence

The system enforces structure, not meaning.

## Application model for developers

2WAY is not an application framework and not a runtime in the traditional sense.
It is a shared execution substrate that applications run on top of.

Applications built on 2WAY do not manage their own backends, databases, or trust models. Instead, they execute within an environment where identity, data ownership, permissions, synchronization, and auditability are already enforced by the platform.

From a developer's perspective:

* An application defines its own data types, schemas, and logic.
* All application state is stored in the shared graph, under explicit ownership and access rules.
* Reads and writes are validated, authorized, ordered, and persisted by the platform before the application observes them.
* Synchronization with other devices or peers happens through the platform, not through application-managed networking.
* Applications never receive raw, implicit trust over external input.

This applies equally to backend services, frontend applications, background agents, embedded software, and headless systems.

### What applications do

Applications focus on domain logic:

* Defining what data exists and how it relates
* Defining who may read or modify that data
* Reacting to state changes and events
* Presenting, processing, or acting on data locally

Applications may expose user interfaces, provide services to other applications, control devices, or run autonomously. The platform does not assume a specific interaction model.

### What applications do not do

Applications do not:

* Run or trust a central backend
* Manage identity or key material directly
* Implement custom synchronization protocols
* Rebuild access control or trust logic
* Resolve conflicts by overwriting state
* Accept network input without validation

These concerns are handled once, consistently, by the platform.

### Why this model exists

By moving security, identity, and data integrity below the application layer, 2WAY ensures that:

* Applications cannot accidentally bypass critical guarantees
* Compromise of one application does not compromise others
* Application logic remains portable across environments
* The same application can run on a single device, across peers, or in large deployments without changing its trust model

This makes the application model stable across vastly different environments, from embedded systems and edge devices to desktops, servers, and distributed deployments.

### Applicability across domains

Because applications rely on the same substrate regardless of environment, the model applies uniformly to:

* Web and non-web applications
* User-facing and headless systems
* Resource-constrained devices and data centers
* Online, offline, and intermittently connected environments

The platform enforces the same rules everywhere. Applications inherit those guarantees automatically.

## Application domains

The 2WAY design applies to systems that require local authority, explicit trust boundaries, and bounded failure under untrusted conditions, including but not limited to:

* Web and multi-application platforms
* Mobile and desktop applications
* Peer-to-peer and federated systems
* Messaging, contact, and social systems
* Collaborative and shared-workspace tools
* Enterprise and inter-organizational platforms
* Identity, credential, and access management systems
* Supply chain and inter-vendor coordination systems
* Financial, accounting, and audit-focused systems
* Regulated and compliance-driven environments
* Critical infrastructure and operational technology
* Industrial control and automation systems
* Internet of Things and edge device networks
* Embedded systems and firmware-managed devices
* Offline-first and intermittently connected systems
* Mesh networks and ad-hoc communication systems
* Defense, aerospace, and satellite-based systems
* Research, scientific, and field-deployed platforms
* Data-sharing platforms with strict isolation requirements

Each domain reflects environments where centralized trust, implicit coordination, or silent failure are unacceptable.

## What this repository deliberately does not decide

The following are intentionally left undefined or application-specific:

* User interface and experience models
* Social interpretation of trust or reputation
* Economic incentives or token systems
* Moderation, governance, or content policy
* Peer discovery and bootstrap strategy

Absence of a feature is not an oversight unless explicitly marked as such.

The protocol constrains behavior. It does not impose policy.

## Who this repository is for

* Systems engineers evaluating the protocol and architecture
* Implementers building the PoC exactly as specified
* Reviewers auditing correctness, isolation, and security properties

Recommended reading paths:

* **Conceptual orientation**: start with scope, then protocol
* **Security audit**: start with security, then protocol and architecture, do not skip protocol
* **Implementation**: read in numeric order, prioritizing the PoC definition
* **Operational behavior**: focus on end-to-end flows

The repository is structured to support all of these perspectives without reinterpretation.

## Repository structure and authority

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
  Includes the backend kernel, managers, services, application boundaries,
  and explicit denial-of-service guards.

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
  signed transport and synchronization integrity, encryption, rotation and recovery,
  privacy, selective synchronization, abuse controls, and auditability.

06-flows/
  Normative end-to-end operational flows.
  Includes success and failure paths for bootstrap, application installation,
  graph mutation, messaging, synchronization, conflict handling,
  key rotation, device lifecycle, and backup and restore.

07-poc/
  Proof of concept definition and execution criteria.
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

An implementation conforms to the 2WAY proof of concept design if and only if:

* All defined invariants hold under all allowed operations
* Forbidden behaviors are structurally impossible
* Validation, authorization, and ordering rules are enforced exactly
* No state mutation bypasses defined architectural boundaries

Any deviation requires an explicit Architecture Decision Record.

## Scope boundary

Only properties explicitly defined within this repository are claimed by the design.

No additional guarantees should be inferred from terminology, naming, or examples.

## Status

This repository describes a proof of concept [WIP].

The design prioritizes correctness, clarity, and auditability over performance or scale.
The PoC exists to validate the protocol model and architectural boundaries before any production implementation.
