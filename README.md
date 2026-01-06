# 2WAY PoC Design Repository

Normative design documentation for a decentralized, fully open source (MIT-licensed), local-first application substrate that enforces security and correctness structurally rather than by convention.

---

## Table of Contents

* [Introduction](#introduction)
* [1. 2WAY at a glance](#1-2way-at-a-glance)
* [2. Repository guide](#2-repository-guide)
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
* [17. Scope boundary and status](#17-scope-boundary-and-status)

---

## Introduction

2WAY defines a fully open source and decentralized application substrate that separates identity, permissions, ordering, and history from fast-changing application code. This repository is the normative specification for the proof of concept; every invariant, guarantee, and constraint discussed elsewhere in the project is rooted here.

Modern software stacks depend on centralized backends to decide who users are, which actions are permitted, how data is ordered, and how long any of that survives. Those backends become single points of incentive, fragility, and failure. When operators change priorities, infrastructure disappears, or multiple deployments must cooperate, users inherit migration debt and policy churn they never consented to.

2WAY relocates authority to the edge. Each node owns its cryptographic identity, evaluates permissions locally, orders the changes it accepts, and stores its own durable history. Correctness derives from structure, not from a continuously available coordinator or a trusted transport.

Applications do not mutate storage directly. They describe schemas, propose graph mutations, and react to the ordered stream of accepted state. Every proposal must clear schema checks, authorization, deterministic ordering, and append-only commit on the device that receives it. Unsigned, ambiguous, or context-free input never leaves the network buffer.

This repository does not ship a finished product. It records the design intent, boundaries, guarantees, and failure behavior required for a proof of concept that multiple independent implementations could build against. Performance tuning, UI polish, and production bootstrapping are out of scope. The following sections explain how the substrate works, why it exists, how it contains adversaries, and what obligations any conformant build must meet.

## 1. 2WAY at a glance

2WAY replaces central backends with locally enforced structure. The platform guarantees:

- **Local authority and durability**: every device persists its own append-only log, owns its cryptographic keys, and decides what it accepts. Nothing depends on a remote operator.
- **Guarded inputs**: network data is untrusted by default. Schema checks, capability validation, and deterministic ordering all occur before commits, so malformed or replayed input dies at the boundary.
- **Bounded trust**: identities remain inert until explicitly anchored in the shared graph. Unknown applications and peers cannot borrow privilege or spread influence implicitly.
- **Structural containment**: applications cannot cross authority boundaries because the substrate enforces graph ownership, permission edges, and ordering rules that cannot be bypassed by configuration.
- **Deterministic rejection**: missing permission, ambiguous context, or invalid ancestry yields the same error everywhere, preventing silent divergence or opportunistic escalation.
- **Progressive failure**: compromise or outage reduces capability instead of destroying state. Nodes isolate the fault, keep good history intact, and continue serving trusted peers.

## 2. Repository guide

This repository is the normative design source for the 2WAY proof of concept. It exists to define structure (scope, invariants, architecture, data, security, flows, and proof-of-concept acceptance criteria) so multiple implementations can be judged against the same rules, not to provide runnable code or UI polish.

It intentionally excludes deployment guidance, performance promises, reference UX, governance or economic policy, and any shortcut that bypasses structural guarantees. Everything here answers a single question: If identity, permissions, ordering, and synchronization are enforced structurally and locally, what systems become possible that centralized backends cannot deliver reliably?

Lower-numbered directories carry higher authority, so scope constrains protocol, protocol constrains architecture, and so on; when conflicts appear, an Architecture Decision Record must document any override.

| Folder | Authority focus | Typical questions it answers |
| --- | --- | --- |
| `00-scope` | System boundary and vocabulary | What is in or out of scope? Which assumptions are mandatory? |
| `01-protocol` | Wire format and invariants | How are identities, objects, and signatures encoded? |
| `02-architecture` | Runtime composition | Which managers exist and how do they interact? |
| `03-data` | Persistence model | How is state stored, versioned, and migrated locally? |
| `04-interfaces` | APIs and event surfaces | How do components and applications integrate? |
| `05-security` | Threat framing and controls | Which adversaries are assumed and how are they contained? |
| `06-flows` | End-to-end operations | How do bootstrap, sync, and recovery behave? |
| `07-poc` | Execution scope | What must the proof of concept build, demo, and test? |
| `08-decisions` | Recorded trade-offs | Which ADRs modify previous rules and why? |
| `09-appendix` / `10-examples` | Reference material | What supporting context or illustrations exist? |

Place new material in the folder that matches its authority, ensure higher folders never contradict lower ones, and use the ADR process for any intentional exception.

## 3. What 2WAY is

2WAY is a shared, local-first application substrate that replaces the traditional backend. Every participating device runs the same authority stack (identity, permissions, ordering, and durability) so availability and policy never hinge on a central service.

Each node maintains its own append-only log, validates every proposed change against local rules, and syncs only the data it is willing to accept. Nodes can operate offline for extended periods, then reconcile when peers are available without ever ceding control over history or policy.

All domain data lives in a single structured graph that spans identities, relationships, capabilities, and application records. Ownership is explicit down to individual edges, so every mutation states whose authority governs it. The substrate enforces graph rules, checks signatures, orders accepted writes, and persists the result locally.

Applications run beside, not inside, the substrate. They describe schemas, react to the ordered feed of accepted changes, and propose new mutations through deterministic interfaces. They never own storage, manage keys, or bypass validation; they simply interpret and influence the shared graph according to the permissions they hold.

Because these guarantees apply on every device, network input and peer behavior remain untrusted until proven valid. Unsigned, ambiguous, or out-of-order data is rejected before it reaches durable state, so compromise on one node cannot coerce another into rewriting history or leaking authority.

### Layered authority model

Authority flows downward. Each layer relies on the guarantees of the one below it and cannot bypass them.

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

| Layer | Responsibilities | It cannot bypass |
| --- | --- | --- |
| Applications | Interpret ordered state, run UI and domain logic, compose new proposals | Substrate validation, ordering, or authority rules |
| 2WAY Substrate | Own identity, permissions, ordering, synchronization, and graph invariants | Storage guarantees or transport constraints |
| Storage & Transport | Persist append-only history and exchange messages with peers | Local authority of the substrate or per-device policy |

## 4. Why 2WAY exists

Centralized systems accumulate implicit trust: operators hold root keys, rewrite history silently, and change access rules without recourse. A single breach or policy shift can revoke products, orphan data, or force mass migrations. Secrets, ACLs, and business logic share the same blast radius.

They also connect poorly. Either everything is globally reachable, or everything is siloed. Complex federation agreements rarely survive organizational change, and every bridge increases the damage an attacker can inflict. Data outlives software, yet ownership remains entangled with whichever backend happens to be running today.

2WAY separates durable structure from transient deployment. Identities, relationships, ordering, and permissions remain stable, portable, and inspectable even as applications evolve or disappear. Because authority is local and structural, compromise is contained to the device or trust radius that granted it, and systems can reconnect or extend without inheriting the liabilities of a central backend.

## 5. Core idea: a shared, local-first graph

The heart of 2WAY is a typed graph that every node materializes locally. It is not a central database; it is a set of nodes, edges, and append-only histories that each device maintains, signs, and synchronizes on its own schedule.

The graph stores identities, devices, relationships, content, capabilities, and application records. Ownership is explicit, down to individual edges, so any mutation clearly states whose authority governs it. History is append-only and rooted in per-node logs. Every change carries cryptographic authorship, parent references, and schema-bound payloads before it enters committed state.

Nodes function independently and offline. Writes land locally, then propagate as signed deltas to peers that re-validate them against their own context. Synchronization is incremental and bounded by trust: peers only request segments they are willing to accept, check ordering deterministically, and merge when invariants hold. Consistency emerges from ownership and validation, not from global consensus.

The proposal lifecycle is deterministic everywhere:

1. Application proposes a change using domain schemas.
2. Schema validation ensures payload shape and references exist.
3. Authorization checks verify keys, capabilities, and graph ownership.
4. Deterministic ordering resolves conflicts relative to other accepted writes.
5. The mutation commits to the local append-only log and, optionally, syncs to peers that repeat the same process.

If any prerequisite is missing, the proposal is rejected before it touches shared state.

## 6. Security model and threat framing

2WAY assumes hostile transports, adversarial peers, and compromised applications. Every node acts as if the network is malicious, every application is untrusted until proven otherwise, and every identity is suspect unless anchored with explicit authority in the graph.

The design constrains:

* Untrusted peers attempting to inject invalid data, replay stale history, or impersonate devices
* Mass identity fabrication (Sybil attempts) that lacks graph anchoring
* Unauthorized graph mutations that try to bypass ownership or escalate permissions
* Replay and reordering attacks aimed at confusing deterministic state machines
* Denial-of-service via malformed, excessive, or computationally expensive input
* Partial compromise of nodes, including stolen keys, tampered binaries, or misbehaving applications

Validation precedes authorization, authorization precedes ordering, ordering precedes commit. Missing context always yields rejection, so the default posture is fail-closed rather than best-effort.

## 7. Structural impossibility

Many behaviors are not merely disallowed, they cannot occur because no valid execution path exists. Authority boundaries, graph schemas, ownership edges, and ordering rules are encoded so that an operation either satisfies every prerequisite or never reaches commit.

Structural impossibility underpins:

* Application isolation: proposals cannot target foreign state without explicit delegation edges.
* Access control enforcement: capabilities are graph objects that must exist before any write is considered.
* Graph mutation rules: only the owning device can author changes for its portion of the graph.
* State ordering guarantees: ancestry and deterministic ordering prevent retroactive edits or inconsistent histories.

Even a compromised application can only issue invalid proposals that the substrate rejects; it cannot manufacture privilege, rewrite history, or create the structural hooks it would need to cross authority boundaries.

## 8. Degrees of separation and influence limits

Reach and visibility are bounded through explicit graph distance. Edges record direction, ownership, and purpose, enabling policies that describe not only who may act but how far their influence travels.

* Relationships establish degrees of separation, allowing different rules for first-degree collaborators versus distant observers.
* Reads, writes, and broadcasts can specify maximum hop counts, limiting unsolicited proposals or data exposure.
* Identities beyond the permitted radius are structurally ignored: without a path, their messages never enter validation pipelines.

These limits prevent trust from spreading automatically, keep unsolicited reach narrow, and force influence to flow through intentional, inspectable relationships.

## 9. Sybil resistance through structure

2WAY does not assume global Sybil prevention. Instead, it makes large-scale identity floods unproductive.

* Identities without anchors have no influence. Until new keys form explicit relationships with trusted anchors, their writes remain invisible.
* Trust and reputation live inside applications and derive from the shared graph, so acceptance in one domain never auto-grants privileges elsewhere.
* Delegation is explicit: edges carry bounded authority, and both parties must record the relationship before it takes effect.
* Degree limits cap unsolicited interaction, preventing Sybils from spamming nodes that never opted into a path toward them.

Attackers can generate traffic, but without the structural prerequisites they cannot mutate state, expand reach, or coerce attention.

## 10. Denial-of-service containment

The PoC is designed to degrade predictably under load or attack. Throughput may fall, but correctness and isolation remain intact. Every expensive operation has a gatekeeper so that malicious traffic consumes the attacker's resources, not the defender's.

| Mechanism | Result when under attack |
| --- | --- |
| Early rejection and schema enforcement | Invalid input dies before consuming CPU, memory, or disk |
| Authorization-before-mutation | Unauthorized writes never trigger domain logic or persistence |
| Serialized write path | Only one ordered stream progresses, preventing write amplification |
| Scoped sync windows | Synchronization cost scales with trust radius, not global network size |
| Adaptive client puzzles | Attackers must spend CPU to continue, giving defenders leverage |

Compromised nodes cannot force well-behaved peers into expensive retries or global coordination; damage remains localized.

## 11. Failure behavior

When violations occur, the system fails closed:

* Input that breaks schema, authority, or ordering rules is rejected before it touches shared state.
* Local integrity holds because every write requires explicit ownership and a serialized commit path.
* Operation continues with reduced scope: nodes quarantine the faulty actor, isolate incomplete state, and keep serving trusted peers.

Recovery is explicit. Administrators or applications must craft corrective actions (revocations, replays, migrations) that pass the same validation pipeline as any other write. No automatic reconciliation or implicit trust escalation occurs, keeping audit trails deterministic.

## 12. What the system guarantees

The substrate guarantees:

* Identity-bound authorship: every mutation is cryptographically tied to the device and identity that proposed it.
* Append-only, tamper-evident local history with parent references and durable digests suitable for independent replay or audit.
* Structural application isolation: applications consume the same ordered feed but cannot touch each other's state without explicit delegation.
* Deterministic validation and ordering across nodes, ensuring well-formed inputs produce identical outcomes everywhere.
* Explicit authority delegation: permissions are granted through recorded graph edges, never through environment configuration or implied roles.
* Fail-closed behavior under ambiguity or attack, so missing context or conflicting data yields rejection rather than guesswork.

These guarantees are structural, testable, and auditable without procedural controls.

## 13. What the system enables but does not define

2WAY enforces structure but deliberately avoids prescribing meaning. The substrate guarantees how data is stored, validated, and authorized; interpretation belongs to applications, communities, and operators.

What can emerge without being hard-coded:

* Trust relationships derived from shared edges without the platform declaring global trust.
* Reputation signals interpreted per application, allowing different scoring models for the same identity.
* Social, economic, or organizational semantics layered on neutral data structures.
* Governance and moderation tailored by applications, including sanction lists, appeals processes, or quorum rules.
* Incentives and markets, such as credits for resource sharing or bids for scarce namespaces.
* Diverse user interfaces that consume the same ordered state but present different experiences.

Structure is guaranteed; meaning is intentionally left open.

## 14. Application model for developers

Developers treat applications as deterministic state machines that react to the ordered graph feed and emit new proposals. A typical workflow is:

1. Define schemas, domain logic, and validation rules that describe the objects the application cares about.
2. Subscribe to the ordered feed that the substrate maintains locally, updating caches, UI state, or side effects purely from accepted events.
3. Let users interact with local data (every node already stores the relevant graph slice) without waiting on a remote backend.
4. Propose mutations through substrate interfaces; the platform enforces authority, ordering, and durability uniformly across peers.

Implications for developer experience:

* Applications never run central backends or maintain authoritative copies of shared state.
* Identity and key management stay inside the device and identity managers; applications rely on provided abstractions.
* Custom sync protocols, reconciliation loops, or ACL rebuilds are unnecessary because the substrate already enforces them structurally.
* All network input visible to applications has already passed validation, so application logic sees deterministic, trustworthy events.

## 15. Application domains

Any workflow that requires verifiable history, local survivability, bounded influence, or offline-first guarantees benefits from 2WAY's structure. Examples include:

* Web, mobile, desktop, and embedded software that must behave consistently on- and offline without bespoke sync engines.
* Messaging, collaboration, and shared workspaces where every edit, mention, or invitation needs provenance and bounded reach.
* Identity, credential, and access management stacks that require distributed issuance, revocation, and auditability without a single CA.
* Supply-chain and inter-vendor coordination where mutually distrustful parties must share state while retaining local authority.
* Regulated or audit-heavy environments such as finance, healthcare, or government that require append-only histories and explicit authority.
* Offline-first, mesh, and edge networks that must keep operating securely despite intermittent connectivity or hostile transports.
* Critical infrastructure and defense systems that cannot tolerate centralized control planes or silent compromise.

## 16. Conformance

An implementation conforms to the 2WAY PoC design only if it satisfies every normative requirement in this repository. Passing tests or interoperability checks is insufficient when core invariants are weakened.

Conformance requires:

* All defined invariants hold under every supported operating condition, including hostile peers and offline operation.
* Forbidden behaviors remain structurally impossible; policy alone is not acceptable.
* Validation, authorization, and ordering rules execute exactly as specified, with no fast paths that bypass structural guards.
* No state mutation bypasses defined boundaries; every write flows through the same serialized authority path regardless of origin.

Any deviation must be documented with an Architecture Decision Record (ADR) that explains scope, reasoning, and compensating controls. Without that ADR, an implementation cannot claim conformance.

## 17. Scope boundary and status

Only properties explicitly defined in this repository are claimed. Terms such as "secure," "trusted," or "verified" have meaning only where the accompanying section spells out conditions. Examples show possibility, not obligation; code fragments in appendices are non-normative unless referenced by a normative section.

This is a work-in-progress proof of concept. Clarity, auditability, and structural correctness take priority over performance or scale, and some trade-offs remain intentionally unresolved until validated. Treat this repository as authoritative for design intent, but not as evidence that all future choices have been finalized.
