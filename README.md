



# 2WAY PoC Design Repository

Normative design documentation for a decentralized, local-first application substrate that enforces security and correctness structurally rather than by convention.

---

## Table of Contents

* [Abstract](#abstract)
* [1. 2WAY at a glance](#1-2way-at-a-glance)
* [2. What this repository is and how to read it](#2-what-this-repository-is-and-how-to-read-it)
* [3. What 2WAY is](#3-what-2way-is)
* [4. Why 2WAY exists](#4-why-2way-exists)
* [5. Core idea: a shared, local-first graph](#5-core-idea-a-shared-local-first-graph)
* [6. Security model and threat framing](#6-security-model-and-threat-framing)
* [7. Structural impossibility](#7-structural-impossibility)
* [8. Degrees of separation and influence limits](#8-degrees-of-separation-and-influence-limits)
* [9. Sybil resistance through structure](#9-sybil-resistance-through-structure)
* [10. Denial-of-service containment](#10-denial-of-service-containment)
* [11. Failure behavior](#11-failure-behavior)
* [12. What the system guarantees](#12-what-the-system-guarantees)
* [13. What the system enables but does not define](#13-what-the-system-enables-but-does-not-define)
* [14. Application model for developers](#14-application-model-for-developers)
* [15. Application domains](#15-application-domains)
* [16. Conformance](#16-conformance)
* [17. Repository structure and authority](#17-repository-structure-and-authority)
* [18. Scope boundary and status](#18-scope-boundary-and-status)

---

## Overview

Most modern applications depend on centralized backends to provide identity, access control, ordering, and persistence. While effective in the short term, this architecture makes systems fragile over time. When operators change incentives, infrastructure disappears, or systems need to interoperate, users and data are forced to migrate, fork, or vanish.

This repository defines 2WAY, a decentralized application substrate that separates application logic from authority over identity, permissions, and history*. By enforcing these concerns structurally rather than procedurally, 2WAY enables applications that remain coherent across failure, can interoperate without federation, and do not depend on the continued operation of a single provider.

This repository is not an implementation. It is the authoritative design specification for a proof of concept (PoC). Its purpose is to define the structure, guarantees, limits, and failure behavior of the system precisely enough that multiple independent implementations could be built, tested, and audited against the same criteria.

## 1. 2WAY at a glance

2WAY is a peer-to-peer platform that replaces central backends with locally enforced control over data and security.

The following properties are enforced by design:

* Each device keeps its own data and decides what it accepts
* Decisions are made using local rules and cryptographic keys
* All changes are signed, recorded, and cannot be silently altered
* Data from the network is never trusted by default
* Applications and unknown identities are limited unless explicitly allowed
* Trust does not automatically propagate through the system
* Compromise is contained instead of spreading
* Security is enforced by structure, not convention
* If permission is missing, the action is rejected
* There is no central backend and no global coordination
* Invalid, ambiguous, or incomplete actions are refused
* Failure reduces capability rather than destroying state

2WAY is designed to continue operating correctly even when parts of the system are offline, compromised, or malicious.

## 2. What this repository is and how to read it

This repository is the normative design source for the 2WAY proof of concept.

It defines:

* System scope and non-goals
* Protocol-level invariants and guarantees
* Architectural components and authority boundaries
* The persistence and data model
* Security assumptions and threat framing
* End-to-end operational flows
* PoC execution criteria and acceptance rules

It does not define:

* A production deployment
* Performance targets
* A reference UI
* An economic or governance model
* A fixed peer discovery or bootstrap strategy

The PoC exists to answer a specific question:

> If identity, permissions, ordering, and synchronization are enforced structurally and locally, what classes of systems become possible that cannot be reliably built on centralized backends?

All material in this repository should be read in service of that question.

## 3. What 2WAY is

2WAY replaces the traditional application backend with a shared, local-first data and security substrate that runs on every node. Each device carries the full authority stack - identity, permissions, ordering, and durability - so availability and policy never depend on a remote operator or cloud service.

Applications operate on a single, structured graph where identities, relationships, capabilities, and application records live side by side. The substrate enforces graph invariants, filters untrusted network input, and ensures that every node remains authoritative for its own portion of state while synchronizing with peers opportunistically.

Applications do not own state. They describe schemas and propose mutations against the graph. The substrate deterministically validates every proposal, orders it relative to other writes, and either commits or rejects it; application logic reacts to the ordered feed rather than mutating storage directly.

### Layered authority model

```
┌──────────────────────────────────────────┐
│              Applications                │
│  Interpretation · UI · Domain logic      │
└──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│            2WAY Substrate                │
│  Identity · Permissions · Ordering       │
│  Graph state · Sync · Structural guards  │
└──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│        Storage and Transport             │
│  Local persistence · Networking          │
└──────────────────────────────────────────┘
```

Authority flows downward. No layer may bypass the one below it.

| Layer | Responsibilities | It cannot bypass |
| --- | --- | --- |
| Applications | Interpret ordered state, run UI/domain logic, propose new mutations | Substrate validation or ordering rules |
| 2WAY Substrate | Own identity, permissions, ordering, structural guards, graph synchronization | Storage guarantees or transport constraints |
| Storage & Transport | Persist append-only history, exchange messages with peers | Local authority of the substrate or per-device policy |

## 4. Why 2WAY exists

Modern systems fail when trust is concentrated. Operators end up controlling root keys, rewrite history at will, and silently change the rules that govern identity or data ownership. When a single breach or policy shift can revoke an entire product line, customers inherit the operator’s fragility.

Identity, permissions, and data ownership are rebuilt repeatedly on top of centralized backends that assume networks and peers are trustworthy. Secrets and ACLs are stored in the same place as business logic, so any compromise bypasses application intent entirely. Local failure escalates to global damage because nothing structurally prevents inappropriate writes or replay of stale authority.

At the same time, centralized systems connect poorly at scale. Systems become either globally reachable or heavily siloed, with no structural way to bound reach based on real relationships. Every new connection increases blast radius, and every federation bridge demands bespoke trust agreements that rarely survive organizational change.

Centralized systems also do not age well. Data outlives applications. Applications outlive teams. Access logic becomes tied to specific implementations, migrations require freeze-and-cutover events, and interoperability degrades over time because structure is entangled with software delivery.

2WAY separates durable structure from changing software. Identities, relationships, ordering, and permissions remain stable, portable, and inspectable. Applications evolve or disappear while authority, provenance, and history remain intact, so the system can be redeployed, audited, or extended without inheriting the liabilities of a central backend.

## 5. Core idea: a shared, local-first graph

At the center of 2WAY is a shared graph that every node materializes locally. The graph is not a central database; it is a set of typed nodes, edges, and append-only histories that each device maintains, signs, and syncs on its own schedule.

The graph holds identities, devices, relationships, content, and application state. Ownership is explicit down to individual edges, so it is always clear whose authority governs a mutation. History is append-only and anchored in per-node logs; every change carries cryptographic authorship, parent references, and schema-bound payloads before it becomes part of committed state.

Each node operates independently and can function offline. Writes land locally first, then propagate as signed deltas to peers that verify them against their own view. Synchronization is explicit, incremental, and bounded by authority: peers request the segments they trust, validate ordering deterministically, and merge only when invariants hold. Consistency arises from ownership, ordering, and validation, not from global agreement or best-effort replication.

Running locally is a security property. Correctness does not depend on being online or on trusting peers, because the substrate refuses to apply mutations that lack the required keys, context, or ordering proofs regardless of where they originate.

Flow of a single mutation:

```
Application proposal
        |
        v
[Schema validation]
        |
        v
[Authorization + capability checks]
        |
        v
[Deterministic ordering]
        |
        v
[Commit to local log] --> [Optional sync to peers]
```

Every stage emits deterministic errors if prerequisites are missing, so peers observing the same proposal either commit it identically or reject it identically, keeping replicas aligned without a coordinator.

## 6. Security model and threat framing

2WAY is designed under adversarial assumptions. Every node treats the network as a hostile transport, every application as untrusted until proven otherwise, and every identity as potentially malicious unless anchored in the graph with explicit authority.

The PoC explicitly considers and constrains:

* Untrusted or malicious peers that attempt to inject invalid data, replay stale state, or impersonate known devices
* Sybil identity creation at scale without corresponding trust anchors
* Unauthorized graph mutation, including attempts to bypass ownership or escalate permissions across authority boundaries
* Replay and reordering attacks aimed at confusing state machines or re-executing previously rejected actions
* Denial-of-service via malformed, excessive, or computationally expensive input
* Partial compromise of nodes, applications, or devices, including stolen keys and tampered binaries

Across the design, absence of permission, ambiguity, or incomplete context results in rejection. Validation occurs before authorization, authorization before ordering, and ordering before commit, so the system fails closed at multiple layers instead of relying on a final guard.

Security is enforced structurally and locally. No global trust, centralized authority, or trusted transport is assumed; each node must be able to withstand hostile peers indefinitely with only the guarantees encoded in the substrate.

## 7. Structural impossibility

Many prohibited behaviors in 2WAY are not merely disallowed by policy, but structurally impossible. The substrate encodes authority boundaries, graph schema rules, and ordering invariants so that an operation either satisfies every prerequisite or it never reaches commit.

Structural impossibility means that no valid execution path exists that would allow the behavior to occur, regardless of application intent, peer behavior, or network conditions. Attempted bypasses fail early because required edges, keys, or predecessors simply do not exist; the system cannot be coerced into creating them on demand.

This principle underlies:

* Application isolation
* Access control enforcement
* Graph mutation rules
* State ordering guarantees

These guarantees mean a compromised application can at worst issue invalid proposals that are rejected; it cannot retroactively grant itself privileges, rewrite history, or cross authority boundaries because the necessary structural hooks never exist in the first place.

## 8. Degrees of separation and influence limits

Visibility and influence are constrained through explicit graph distance. Every edge has direction, ownership, and purpose, allowing policies to express not just “who” but “how far.”

* Relationships define degrees of separation between identities, so an application can reason about first-degree collaborators differently from distant observers
* Reads, writes, and broadcasts may be restricted by maximum allowed distance, limiting how far proposals can travel or who can observe sensitive data
* Identities outside the permitted radius are structurally ignored: their messages never enter validation pipelines because no path authorizes them

This bounds unsolicited reach, limits the impact of unknown or weakly anchored peers, and forces influence to flow through explicit, inspectable relationships instead of global fan-out.

## 9. Sybil resistance through structure

2WAY does not attempt global Sybil prevention. Large networks cannot reliably distinguish real people from automated actors, so the design focuses on making Sybil floods structurally unproductive.

Instead, it limits Sybil impact:

* Identities have no influence without graph anchoring, so new keys must form explicit relationships with existing anchors before their writes become visible
* Trust and reputation are application-scoped and derived from the shared graph, preventing one application’s trust model from auto-granting privileges elsewhere
* Influence does not propagate automatically: edges have bounded authority, and delegation must be explicitly recorded and accepted by both parties
* Degrees of separation restrict unsolicited interaction, preventing Sybils from spamming nodes that never opted into a relationship path

Large numbers of unanchored identities therefore remain inert - they can generate traffic, but they cannot mutate state, gain reach, or drain attention without first satisfying the same structural requirements as legitimate participants.

## 10. Denial-of-service containment

The PoC is designed to degrade predictably and fail closed under load or attack. Throughput may drop, but correctness and isolation do not. Every expensive operation has a bounded scope and an obvious gatekeeper so that malicious traffic consumes the attacker’s resources, not the defender’s.

Structural mechanisms include:

| Mechanism | Result when under attack |
| --- | --- |
| Early rejection + schema enforcement | Invalid input is discarded before consuming CPU or I/O |
| Authorization-before-mutation | Unauthorized writes never trigger business logic or disk usage |
| Serialized write path | Only one ordered stream can progress, preventing write amplification |
| Scoped sync windows | Synchronization cost grows with trust radius, not network size |
| Adaptive client puzzles | Attackers must spend CPU to continue, giving defenders leverage |

These guarantees hold regardless of peer behavior and keep denial attempts localized: compromised nodes cannot coerce well-behaved nodes into global coordination or expensive retries.

## 11. Failure behavior

When violations occur, the system fails closed by design:

* Input is rejected as soon as it violates schema, authority, or ordering rules; nothing speculative leaks into shared state
* Local integrity is preserved because every write requires explicit ownership and a serialized commit path
* Operation continues with reduced scope: nodes isolate the faulty actor, quarantine incomplete state, and continue serving known-good peers

Recovery is explicit, never implicit. Administrators or applications must produce corrective actions - revocations, replays, or migrations - that pass the same validation pipeline as any other write. No automatic reconciliation, overwrite, or trust escalation occurs, so debugging and audit trails remain deterministic.

## 12. What the system guarantees

Guaranteed by design:

* Identity-bound authorship, so every mutation is cryptographically tied to the device and identity that proposed it
* Append-only, tamper-evident local history with parent references and durable digests, enabling independent audit and replay
* Structural application isolation: applications observe the same ordered feed but cannot touch one another’s state without explicit delegation
* Deterministic validation and ordering across nodes, ensuring that well-formed inputs produce the same result everywhere regardless of timing
* Explicit authority delegation where permissions are granted through recorded graph edges, never through implicit roles or environment configuration
* Fail-closed behavior under ambiguity or attack, so missing context or conflicting data results in rejection rather than guesswork

These properties are enforced structurally, not by convention, making them testable and auditable without relying on procedural controls.

## 13. What the system enables but does not define

2WAY enforces structure and limits. It does not define meaning. The substrate guarantees how data is stored, validated, and authorized, but it never dictates why a relationship exists or how a domain interprets it. That interpretive layer belongs to applications, communities, and operators.

What can emerge without being defined:

* Trust relationships without the system deciding trust: applications can derive confidence scores or circles of trust from shared edges without the platform imposing policy
* Reputation signals interpreted per application, allowing different domains to score the same identity based on their own criteria
* Social, economic, or organizational meaning layered on neutral data structures, enabling everything from collaborative workspaces to supply chains
* Governance and moderation defined by applications, including custom sanction lists, appeals processes, or quorum requirements
* Incentives and markets layered on neutral data, such as credits for resource sharing or bids for scarce graph namespaces
* Diverse user interfaces and interaction models that consume the same ordered state but present radically different experiences

Structure is guaranteed. Meaning is not, which keeps the substrate general-purpose while still enabling high-trust workflows.

## 14. Application model for developers

Applications run on the substrate, not as the substrate. They resemble deterministic state machines that respond to graph events and emit new proposals rather than long-lived services that mediate every interaction.

Applications:

* Define schemas and domain logic, including validation rules for their objects and the invariants they expect the substrate to enforce
* React to validated, ordered state by processing the append-only feed and updating local caches or user interfaces
* Present or act on local data, leveraging the fact that every node already stores the relevant slice of the graph
* Propose mutations through well-defined interfaces, trusting the substrate to apply authority and ordering rules uniformly across peers

Applications do not:

* Run central backends or maintain authoritative copies of shared state
* Manage identity or keys directly; those responsibilities sit in the substrate’s device and identity managers
* Implement custom sync protocols or reconciliation loops
* Rebuild access control logic, since delegation and enforcement already live in the graph
* Accept unvalidated network input - every event they see has already passed structural validation and authorization

## 15. Application domains

2WAY applies wherever centralized trust, silent failure, or unbounded blast radius are unacceptable. Any workflow that requires verifiable history, local survivability, or bounded influence stands to benefit from structural enforcement rather than operational controls.

Applicable domains include, but are not limited to:

* Web, mobile, desktop, and embedded systems that need consistent behavior on and offline without shipping bespoke sync engines
* Messaging, collaboration, and shared workspaces where every edit, mention, or invitation must carry provenance and bounded reach
* Identity, credential, and access management stacks that require distributed issuance, revocation, and auditability without a single CA
* Supply chain and inter-vendor coordination, where mutually distrustful parties need to share state while retaining local authority
* Regulated and audit-heavy environments such as finance, healthcare, or government, where append-only histories and explicit authority are legal requirements
* Offline-first, mesh, and edge networks that must continue operating securely despite intermittent connectivity or hostile transports
* Critical infrastructure and defense systems that cannot afford centralized control planes or silent compromise

## 16. Conformance

An implementation conforms to the 2WAY PoC design if and only if it satisfies every normative requirement in this repository. Passing tests or interoperability checks is insufficient if core invariants are weakened.

Conformance requires:

* All defined invariants hold under all supported operating conditions, including offline operation and hostile peers
* Forbidden behaviors are structurally impossible, not merely unlikely or prevented by policy
* Validation, authorization, and ordering rules are enforced exactly as specified, with no fast paths or shortcuts that bypass structural guards
* No state mutation bypasses defined boundaries; every write crosses the same serialized authority path regardless of origin

Any deviation requires an explicit Architecture Decision Record that documents the reasoning, scope, and compensating controls. Without that ADR, the implementation cannot claim conformance.

## 17. Repository structure and authority

Lower-numbered folders define constraints that higher-numbered folders must not violate. Each directory is normative within its scope; when conflicts arise, the numerically lower folder wins unless an Architecture Decision Record explicitly overrides it. This ordering keeps foundational assumptions ahead of protocol, protocol ahead of architecture, and so on.

| Folder | Authority focus | Typical questions it answers |
| --- | --- | --- |
| `00-scope` | System boundary and vocabulary | What is in/out of scope? What assumptions are mandatory? |
| `01-protocol` | Wire format and invariants | How are identities, objects, and signatures encoded? |
| `02-architecture` | Runtime composition | Which managers exist and how do they interact? |
| `03-data` | Persistence model | How is state stored, versioned, and migrated locally? |
| `04-interfaces` | APIs and event surfaces | How do components and applications integrate? |
| `05-security` | Threat framing and controls | What adversaries are assumed and how are they contained? |
| `06-flows` | End-to-end operations | How do bootstrap, sync, and recovery behave? |
| `07-poc` | Execution scope | What must the proof of concept build, demo, and test? |
| `08-decisions` | Recorded tradeoffs | Which ADRs modify previous rules and why? |
| `09-appendix` / `10-examples` | Reference and non-normative guidance | What supporting material or illustrations exist? |

This structure is normative. When extending or modifying the repository, new material must be placed in the folder whose authority matches the change, and any cross-cutting updates must respect lower-folder constraints. Deviations require the ADR process described above.

## 18. Scope boundary and status

Only properties explicitly defined in this repository are claimed. Terms such as “secure,” “trusted,” or “verified” have meaning only where the accompanying section spells out the conditions. Everything else is illustrative.

No additional guarantees should be inferred from naming, examples, or terminology. Example flows show possibility, not obligation; code fragments in appendices are non-normative unless referenced from a normative section.

This repository describes a work-in-progress proof of concept. Correctness, clarity, and auditability take priority over performance or scale, and open questions remain intentionally unresolved until validated through the PoC. Readers should treat the content as authoritative for design intent, but not as evidence that all tradeoffs have been finalized.
