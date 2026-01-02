



# 2WAY System PoC Design Repository

> Normative design documentation for the 2WAY proof of concept—a local-first platform that enforces security and correctness structurally rather than by convention.

---

## Contents

- **Orientation**
  - [1. 2WAY at a glance](#1-2way-at-a-glance)
  - [2. What 2WAY is](#2-what-2way-is)
  - [3. Why it exists](#3-why-it-exists)
  - [4. Core idea](#4-core-idea)
- **Security and correctness model**
  - [5. Security model and threat framing](#5-security-model-and-threat-framing)
  - [6. Structural impossibility](#6-structural-impossibility)
  - [7. Degrees of separation and influence limits](#7-degrees-of-separation-and-influence-limits)
  - [8. Sybil resistance through structure](#8-sybil-resistance-through-structure)
  - [9. Denial-of-service containment](#9-denial-of-service-containment)
  - [10. Failure behavior](#10-failure-behavior)
  - [11. What the system guarantees](#11-what-the-system-guarantees)
- **Building on 2WAY**
  - [12. What the system enables but does not define](#12-what-the-system-enables-but-does-not-define)
  - [13. Application model for developers](#13-application-model-for-developers)
    - [13.1 What applications do](#131-what-applications-do)
    - [13.2 What applications do not do](#132-what-applications-do-not-do)
  - [14. Application domains and environments](#14-application-domains-and-environments)
- **Repository scope and authority**
  - [15. What this repository deliberately does not decide](#15-what-this-repository-deliberately-does-not-decide)
  - [16. Who this repository is for](#16-who-this-repository-is-for)
  - [17. Repository structure and authority](#17-repository-structure-and-authority)
  - [18. Conformance](#18-conformance)
  - [19. Scope boundary](#19-scope-boundary)
  - [20. Status](#20-status)

---

## Orientation

### 1. 2WAY at a glance

A P2P platform that replaces central backends with locally enforced control over data and security.

* Each device keeps its own data and decides what it accepts
* Decisions are made using local rules and cryptographic keys
* All changes are signed, recorded, and cannot be silently altered
* Data from the network is never trusted by default
* Apps and unknown users are limited unless explicitly allowed
* Trust does not automatically spread through the system
* Compromise is contained instead of spreading
* Security is enforced by how the system is built, not by convention
* If permission is missing, the action is rejected
* There is no central backend or global coordination
* Invalid or unclear actions are refused

2WAY is designed to keep working correctly even when parts of the system fail or are compromised.

### 2. What 2WAY is

2WAY replaces the traditional application backend with a shared, local data and security layer that runs on every device.

Applications run on a common graph where identity, permissions, ordering, and history are enforced by the platform, not rebuilt per app. Each node is authoritative for its own state, synchronizes directly with peers, and treats all network data as untrusted.

This repository defines the normative design for the 2WAY proof of concept (PoC). It specifies required behavior at the protocol and architecture level and is not a production implementation.

### 3. Why it exists

Modern application architectures fail when trust is concentrated. Identity, permissions, data ownership, and synchronization are rebuilt by each application on top of centralized backends that assume networks and peers are trustworthy. When those assumptions fail, small bugs or breaches can silently escalate into broad access, corrupted data, or loss of control. The primary failure 2WAY is designed to prevent is silent escalation from local compromise to system-wide damage.

At the same time, existing systems connect poorly at scale. As users, devices, and applications grow, systems become either globally reachable or heavily siloed, with no structural way to limit reach based on real relationships. Every new connection increases the blast radius. 2WAY uses an explicit graph to connect identities, devices, applications, and data, where distance matters. Reach and influence can be bounded by degrees of separation rather than global rules or central coordination.

Finally, most systems do not age well. Data outlives applications, applications outlive teams, and access logic becomes tied to specific implementations. This makes reuse, migration, and interoperability fragile over time. 2WAY separates durable structure from changing software. Identities, relationships, ordering, and permissions remain stable, while applications evolve or disappear, allowing systems to remain usable and interoperable across long time spans.

### 4. Core idea

At the center of 2WAY is a shared, local-first graph.

The graph holds identities, devices, relationships, content, and application state. Ownership is explicit. History is never rewritten. Every change is checked, authorized, and ordered before it becomes part of the state.

Each node works on its own and can operate offline. Synchronization happens explicitly and in small steps. Consistency comes from clear ownership, strict ordering, and local validation, not from global agreement or central coordination.

The graph is more than a way to store data. It is where security, isolation, and authority are enforced. What an application can see or change is determined by the graph, not by application code or network trust.

Running locally is a security property. Correctness and control do not depend on being online or on trusting other nodes.

---

## Security and correctness model

### 5. Security model and threat framing

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

### 6. Structural impossibility

Many prohibited behaviors in 2WAY are not merely disallowed by policy, but structurally impossible.

Structural impossibility means that no valid execution path exists that would allow the behavior to occur, regardless of application intent, peer behavior, or network conditions.

This principle underlies application isolation, access control enforcement, graph mutation rules, and state ordering throughout the system.

### 7. Degrees of separation and influence limits

Visibility and influence are constrained through explicit graph distance.

* Relationships define degrees of separation between identities
* Services and applications may restrict reads, writes, and broadcasts based on maximum allowed distance
* Identities outside the permitted radius are structurally ignored

This bounds unsolicited reach and limits the impact of unknown or weakly anchored peers.

### 8. Sybil resistance through structure

2WAY does not attempt global Sybil prevention.

Instead, it limits Sybil impact through graph structure:

* Identities have no influence without meaningful graph anchoring
* Trust, ratings, and membership are app-scoped and typed
* Influence does not propagate across applications or domains by default
* Degrees of separation restrict unsolicited interaction

Large numbers of unanchored identities therefore remain inert.

The graph encodes relationships and constraints, not social truth or moral trust.

### 9. Denial-of-service containment

The PoC is designed to degrade predictably and fail closed under load or attack.

Structural mechanisms include:

* Early rejection of malformed or unverifiable input
* Schema validation before authorization
* Authorization before any state mutation
* A single serialized write path for ordered state
* Scoped synchronization to avoid unbounded scans
* Peer-level throttling using client puzzles with difficulty adjusted to load

These guarantees hold regardless of peer behavior.

---

### 10. Failure behavior

When violations occur, the system rejects input, preserves local integrity, and continues operating with reduced scope.

Recovery is explicit, never implicit.
No automatic reconciliation, overwrite, or trust escalation occurs as a side effect of failure.

### 11. What the system guarantees

Guaranteed by design:

* Identity-bound authorship
* Append-only, tamper-evident local history
* Structural application isolation
* Deterministic validation and ordering
* Explicit authority delegation
* Fail-closed behavior under ambiguity or attack

These properties are enforced structurally, not by convention or policy.

---

## Building on 2WAY

### 12. What the system enables but does not define

This section defines areas intentionally left to applications and users, rather than enforced by the platform.

The 2WAY platform enforces structure and limits.
What that structure means is decided by applications and users.

What can emerge from use, but is not defined by the system:

* Trust relationships that grow from direct connections, past interactions, and closeness in the graph, without the system deciding who to trust
* Reputation or credibility signals based on recorded actions, where each application decides how to interpret them
* Social, economic, or organizational meaning built on top of neutral, verifiable data
* Resistance to large-scale fake identities because reach is limited and relationships must be explicit
* Rules, moderation, and governance created by applications or communities, not baked into the platform
* Incentives, rewards, penalties, or markets that use stored data, but are not required by the system
* User interfaces and ways of interacting that differ by device, environment, and use case
* Ways of coordinating and working together that rely on shared state and clear authority, without a fixed process

The system decides what is allowed and what is not.
It does not decide what actions mean or why they matter.

Structure is guaranteed. Meaning is not.

### 13. Application model for developers

2WAY is not an application framework and not a runtime in the traditional sense.
It is a shared execution substrate that applications run on top of.

Applications built on 2WAY do not manage their own backends, databases, or trust models. Instead, they execute within an environment where identity, data ownership, permissions, synchronization, and auditability are already enforced by the platform.

From a developer's perspective:

* An application defines its own data types, schemas, and logic
* All application state is stored in the shared graph, under explicit ownership and access rules
* Reads and writes are validated, authorized, ordered, and persisted by the platform before the application observes them
* Synchronization with other devices or peers happens through the platform, not through application-managed networking
* Applications never receive raw, implicit trust over external input

This applies equally to backend services, frontend applications, background agents, embedded software, and headless systems.

#### 13.1 What applications do

Applications focus on domain logic:

* Defining what data exists and how it relates
* Defining who may read or modify that data
* Reacting to state changes and events
* Presenting, processing, or acting on data locally

Applications may expose user interfaces, provide services to other applications, control devices, or run autonomously. The platform does not assume a specific interaction model.

#### 13.2 What applications do not do

Applications do not:

* Run or trust a central backend
* Manage identity or key material directly
* Implement custom synchronization protocols
* Rebuild access control or trust logic
* Resolve conflicts by overwriting state
* Accept network input without validation

These concerns are handled once, consistently, by the platform.

### 14. Application domains and environments

2WAY applies to systems where local authority, explicit trust boundaries, and bounded failure matter, regardless of environment or scale.

Applications built on the platform rely on the same substrate everywhere. The same rules apply across online and offline operation, constrained and unconstrained hardware, and human-facing or autonomous systems. Applications inherit these guarantees automatically.

Applicable domains include:

* Web and multi-application platforms
* Mobile, desktop, and non-web applications
* User-facing and headless systems
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
* Resource-constrained devices and data centers
* Offline-first and intermittently connected systems
* Mesh networks and ad-hoc communication systems
* Defense, aerospace, and satellite-based systems
* Research, scientific, and field-deployed platforms
* Data-sharing platforms with strict isolation requirements

These domains share a common requirement: centralized trust, implicit coordination, and silent failure are unacceptable.

---

## Repository scope and authority

### 15. What this repository deliberately does not decide

The following are intentionally left undefined or application-specific:

* User interface and experience models
* Social interpretation of trust or reputation
* Economic incentives or token systems
* Moderation, governance, or content policy
* Peer discovery and bootstrap strategy

Absence of a feature is not an oversight unless explicitly marked as such.

The protocol constrains behavior. It does not impose policy.

### 16. Who this repository is for

* Systems engineers evaluating the protocol and architecture
* Implementers building the PoC exactly as specified
* Reviewers auditing correctness, isolation, and security properties

Recommended reading paths:

* **Conceptual orientation**: start with scope, then protocol
* **Security audit**: start with security, then protocol and architecture, do not skip protocol
* **Implementation**: read in numeric order, prioritizing the PoC definition
* **Operational behavior**: focus on end-to-end flows

The repository is structured to support all of these perspectives without reinterpretation.

### 17. Repository structure and authority

The repository is organized by conceptual dependency and authority level.
Lower-numbered folders define constraints that higher-numbered folders must not bypass or contradict.

The numbering is intentional and normative.

```
00-scope/
  - Defines the scope boundary of the system.
  - Goals, non-goals, terminology, assumptions, and hard constraints.
  - All other material is interpreted relative to this folder.

01-protocol/
  - Normative protocol definition.
  - Identity, object model, serialization, cryptography, access control,
  synchronization semantics, network assumptions, error handling,
  and compatibility rules.
  - This folder defines what the protocol is.

02-architecture/
  - Normative architectural design.
  - Component model, runtime topologies, trust boundaries, and data flow.
  - Includes the backend kernel, managers, services, application boundaries,
  and explicit denial-of-service guards.

03-data/
  - Normative persistence and data model.
  - Storage layout, system and per-application structures,
  indexing strategy, migrations, and explicit storage budgets.

04-interfaces/
  - Normative interface definitions.
  - Local APIs, event surfaces, internal component interfaces,
  and the system-wide error model.

05-security/
  - Normative security model.
  - Threat assumptions, identity and key handling, authentication and authorization,
  signed transport and synchronization integrity, encryption, rotation and recovery,
  privacy, selective synchronization, abuse controls, and auditability.

06-flows/
  - Normative end-to-end operational flows.
  - Includes success and failure paths for bootstrap, application installation,
  graph mutation, messaging, synchronization, conflict handling,
  key rotation, device lifecycle, and backup and restore.

07-poc/
  - Proof of concept definition and execution criteria.
  - Feature coverage, build and run expectations, testing strategy,
  demo scenarios, known limitations, and acceptance criteria.
  - This folder is authoritative for implementation scope.

08-decisions/
  - Architecture Decision Records.
  - Explicitly recorded tradeoffs, reversals, and resolved questions.
  - Decisions here override earlier design text within their scope.

09-appendix/
  - Reference material.
  - Glossary, reference configurations, open questions, and diagrams.
  - Informational unless explicitly stated otherwise.

10-examples/
  - Illustrative examples.
  - Non-normative demonstrations of how the protocol and architecture
  may be used. Examples never define required behavior.
```

Later folders must not introduce concepts that violate constraints defined earlier.

### 18. Conformance

An implementation conforms to the 2WAY proof of concept design if and only if:

* All defined invariants hold under all allowed operations
* Forbidden behaviors are structurally impossible
* Validation, authorization, and ordering rules are enforced exactly
* No state mutation bypasses defined architectural boundaries

Any deviation requires an explicit Architecture Decision Record.

### 19. Scope boundary

Only properties explicitly defined within this repository are claimed by the design.

No additional guarantees should be inferred from terminology, naming, or examples.

---

### 20. Status

This repository describes a proof of concept [WIP].

The design prioritizes correctness, clarity, and auditability over performance or scale.
The PoC exists to validate the protocol model and architectural boundaries before any production implementation.
ry are claimed by the design.

No additional guarantees should be inferred from terminology, naming, or examples.

---

### 20. Status

This repository describes a proof of concept [WIP].

The design prioritizes correctness, clarity, and auditability over performance or scale.
The PoC exists to validate the protocol model and architectural boundaries before any production implementation.
