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

---

## 1. 2WAY at a glance

2WAY replaces central backends with locally enforced structure. The platform guarantees:

- **Local authority and durability**: every device persists its own append-only log, owns its cryptographic keys, and decides what it accepts. Nothing depends on a remote operator.
- **Guarded inputs**: network data is untrusted by default. Schema checks, capability validation, and deterministic ordering all occur before commits, so malformed or replayed input dies at the boundary.
- **Bounded trust**: identities remain inert until explicitly anchored in the shared graph. Unknown applications and peers cannot borrow privilege or spread influence implicitly.
- **Structural containment**: applications cannot cross authority boundaries because the substrate enforces graph ownership, permission edges, and ordering rules that cannot be bypassed by configuration.
- **Deterministic rejection**: missing permission, ambiguous context, or invalid ancestry yields the same error everywhere, preventing silent divergence or opportunistic escalation.
- **Progressive failure**: compromise or outage reduces capability instead of destroying state. Nodes isolate the fault, keep good history intact, and continue serving trusted peers.

---

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

---

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

---

## 4. Why 2WAY exists

Modern systems fail because they concentrate authority. Root keys, ACLs, and data ownership sit next to business logic in a single backend, so the operator can silently rewrite history, change rules, or disappear entirely. A breach, policy swing, or acquisition can revoke an entire product overnight, leaving customers with no trustworthy path to recover their data or prove their rights.

Even when the backend behaves, it does not connect cleanly with others. Organizations either make every service globally reachable or silo everything behind brittle federation bridges. Each new integration expands the blast radius of a compromise, and every org change breaks the bespoke trust deals those bridges rely on. Meanwhile data always outlives the software that wrote it, yet migrations still require freeze-and-cutover events because authority and storage are welded to a specific deployment.

2WAY exists to decouple durable structure from transient software. Identities, relationships, ordering, and permissions live in a shared, inspectable graph that every device enforces locally. Applications and operators can evolve or go offline without dragging authority with them. Compromise is contained to the device or trust radius that granted access, and when systems reconnect they do so by replaying signed, auditable history rather than trusting a central coordinator. This lets multiple implementations cooperate without inheriting one another's incentives or liabilities.

---

## 5. Core idea: a shared, local-first graph

2WAY revolves around a single typed graph that every node materializes on its own hardware. There is no upstream database to query or replica set to join. Each device keeps its portion of the graph, signs the history it authors, and exchanges only the changes it is willing to accept.

The graph is the fact store for the entire system. It holds identities, devices, relationships, capabilities, application records, and the permissions that bind them together. Every node or edge has a clear owner, so a mutation always states which identity is responsible and which part of the structure it may influence.

All history is append-only and rooted in per-device logs. Every change carries authorship, parent references, schema identifiers, and payload hashes. Peers can replay another device's log and independently decide whether that sequence satisfies the same invariants they enforce locally; no opaque coordinator is required.

Because the graph lives on every node, the system is truly local-first. Writes land on the originating device, then propagate as signed deltas when peers come into contact. Synchronization is incremental and scoped by trust: peers request ranges they explicitly want, verify ordering deterministically, and merge only when every prerequisite holds. Long periods offline are normal; reconnection is just another validation and merge pass.

The proposal lifecycle is identical everywhere:

1. An application proposes a change with a schema that states what must exist and how it may evolve.
2. Schema validation ensures references exist, types match, and the payload respects domain-specific invariants.
3. Authorization checks verify that the signer owns the relevant nodes or holds capabilities that grant the mutation.
4. Deterministic ordering selects where the proposal fits relative to other accepted writes, preventing race conditions.
5. The mutation commits to the local append-only log and, if desired, streams to peers, which replay the exact same pipeline.

If any step fails (missing reference, stale capability, conflicting order), the proposal never touches durable state. Rejection is deterministic, so well-behaved nodes converge without negotiating with one another or trusting the network.

---

## 6. Security model and threat framing

2WAY treats the environment as adversarial by default. The network is assumed hostile, peers may be malicious or misconfigured, and applications are untrusted until the graph explicitly grants them authority. Every device must be able to withstand long-term exposure to anonymous traffic without relying on a perimeter, VPN, or trusted transport.

This posture covers:

* **Untrusted peers and transports** that inject invalid data, replay stale history, tamper with ordering, or impersonate devices.
* **Mass identity fabrication (Sybil attempts)** that flood the network with new keys hoping to borrow reputation or trigger expensive work.
* **Unauthorized graph mutation** that tries to cross ownership boundaries, escalate permissions, or tamper with schema-defined rules.
* **Replay and reordering attacks** aimed at confusing deterministic state machines or resurrecting revoked authority.
* **Denial-of-service** delivered through malformed payloads, unbounded fan-out, or resource-intensive validation paths.
* **Partial compromise of nodes or applications**, including stolen keys, tampered binaries, misbehaving plugins, or insider abuse.

Protection comes from structure rather than heuristics. Validation always happens before authorization, authorization before ordering, and ordering before commit. Each gate is deterministic and stateful, so missing context, ambiguous ownership, or conflicting history produces an immediate rejection. No shortcut allows a message to skip ahead “just this once.”

Because every node enforces the same rules locally, an attacker who compromises one device cannot coerce its peers into accepting poisoned input. The worst-case outcome is isolation: honest nodes refuse the traffic, quarantine the faulty identity, and continue serving known-good relationships while preserving their own history.

---

## 7. Structural impossibility

2WAY does not rely on policy or best effort to block dangerous behavior. It encodes the rules of the system so tightly that many attacks have no valid execution path. If the graph lacks the required edges, ownership, or ancestry, the mutation cannot even be expressed, let alone committed.

This structural approach covers:

* **Application isolation**: proposals cannot point at foreign state unless the graph already records a delegation that allows it.
* **Access control enforcement**: capabilities are first-class graph objects that must exist before any write is considered; without them the proposal is malformed.
* **Graph mutation rules**: only the owning device can author changes for its portion of the graph because no other key can form the required parent references.
* **State ordering guarantees**: ancestry links and deterministic ordering ensure history remains append-only; retroactive edits simply have nowhere to land.

As a result, even a compromised application or stolen key can only emit proposals that fail validation. It cannot fabricate privilege, rewrite history, or manufacture the structural hooks it would need to cross authority boundaries. Rejection is automatic and deterministic, not a matter of luck or operator vigilance.

---

## 8. Degrees of separation and influence limits

Authority in 2WAY is not global. Relationships in the graph include direction, ownership, and the purpose of the edge, so policies can describe not only who may act but how far their influence may travel. This allows nodes to treat near neighbors differently from distant observers without inventing ad-hoc filters.

Practical implications:

* **Degrees of separation**: applications can enforce first-degree rules for collaborators, looser policies for second-degree observers, and outright silence for unknown nodes.
* **Bounded broadcast and replication**: reads, writes, invitations, and announcements can specify maximum hop counts, preventing unsolicited proposals from traveling farther than intended.
* **Structural ignore**: identities outside the permitted radius have no path to the local device, so their messages never enter validation pipelines and consume zero trust budget.
* **Intentional expansion**: to grow reach, an identity must form explicit edges and be accepted by every hop, creating an audit trail of who granted influence and why.

These constraints prevent trust from spreading automatically, keep unsolicited reach narrow, and force influence to flow through intentional, inspectable relationships instead of global fan-out.

---

## 9. Sybil resistance through structure

Global Sybil prevention is not realistic for large, open networks. 2WAY focuses instead on making identity floods pointless by requiring every actor to earn their reach through visible, consented relationships.

Structural guardrails:

* **Anchoring required**: new keys have no influence until they form explicit edges with trusted anchors. Without that path, their proposals never leave the network buffer.
* **Application-scoped trust**: reputation lives in the shared graph but is interpreted per application, so a credential or score in one domain does not grant privileges anywhere else.
* **Explicit delegation**: edges that convey authority must be recorded by both parties, include bounded capabilities, and can be revoked like any other mutation.
* **Degree limits**: hop budgets prevent unsolicited fan-out. Nodes that never opted into a path toward an identity will never see its traffic.
* **Cost mirrors intent**: forming real relationships requires work (introductions, shared history, mutual acceptance), making it expensive for attackers to scale beyond nuisance traffic.

Attackers can still generate packets, but without anchors, recognized capabilities, and degree-limited paths, they cannot mutate state, borrow reputation, or force attention from unwilling nodes.

---

## 10. Denial-of-service containment

2WAY expects sustained abuse and is built to keep attackers on the defensive. Throughput may dip, but data integrity and ordering do not because every trust boundary can say “no” cheaply before expensive work starts.

The system keeps denial attempts unproductive by combining fast rejection (schema checks, permission gates, serialized writes, scoped sync windows) with adaptive cost shifting. When pressure rises, the node simply makes the requester spend more effort before each packet lands, so the attacker burns CPU while the defender stays mostly idle.

At a high level, untrusted traffic is handled in a shallow, easily restarted zone, while authenticated traffic moves deeper only after it clears admission. That separation means abusive bursts die at the boundary while established peers keep exchanging signed history.

Client puzzles stay dynamic: difficulty increases automatically for sources that misbehave and relaxes for peers that remain cooperative. Proofs expire quickly and cannot be replayed, so solving one puzzle never opens the door for someone else.

Because every device enforces these guardrails locally, damage stays contained. Compromised nodes may lose their own connectivity, but they cannot drag honest peers into coordination storms or force them to redo work simply by shouting louder.

---

## 11. Failure behavior

2WAY assumes things will go wrong: keys get stolen, devices crash mid-write, peers disagree, or malicious inputs flood a node. The system responds by failing closed instead of guessing what the operator intended.

When a rule is violated (schema mismatch, missing capability, conflicting ordering), the input is rejected before it touches durable state. No speculative writes stick around hoping to be fixed later. Each write still passes through the same serialized path, so local integrity holds even if the app above it is compromised.

Operation continues, just with reduced scope. Nodes quarantine the faulty identity, mark incomplete state as suspect, and keep serving peers whose histories remain intact. Isolation wins over availability: better to drop a misbehaving connection than let it corrupt the graph.

Recovery is deliberate and auditable. Administrators or applications must craft explicit corrective actions (revocations, replays, migrations, repairs) that pass exactly the same validation pipeline as any other write. There is no hidden “admin override” or silent reconciliation loop. If a fix cannot be encoded as a normal mutation, it does not happen, which keeps the audit trail honest and reproducible.

---

## 12. What the system guarantees

2WAY makes a small set of promises, all enforced structurally rather than by convention:

* **Identity-bound authorship**: every mutation is cryptographically tied to the device and identity that proposed it, so provenance is never ambiguous.
* **Append-only, tamper-evident history**: each node keeps its own ordered log with parent references and durable digests, enabling independent replay or audit.
* **Deterministic validation and ordering**: well-formed inputs produce identical outcomes on every node regardless of arrival timing or network behavior.
* **Structural application isolation**: applications observe the same feed but cannot touch each other's state without explicit delegation recorded in the graph.
* **Explicit authority delegation**: permissions originate only from recorded edges, not from environment variables, config files, or implied roles.
* **Fail-closed behavior**: missing context, conflicting data, or ambiguous authority yields rejection rather than guesswork, so attacks die at the boundary.

Because these guarantees live in structure, they are testable, auditable, and portable across implementations. If an implementation cannot demonstrate each property, it does not conform.

---

## 13. What the system enables but does not define

2WAY enforces structure but refuses to dictate meaning. It guarantees how identities relate, how permissions are enforced, and how history is recorded, yet it stays silent about why those relationships exist or what a domain should do with them. Interpretation belongs to the communities that use the substrate.

Because the data model is neutral, all of the following can emerge without being hard-coded:

* **Trust relationships** derived from shared edges without the platform declaring global trust.
* **Reputation signals** interpreted per application, allowing different scoring models for the same identity.
* **Social, economic, or organizational semantics** layered on neutral data structures.
* **Governance and moderation** tailored by applications, including sanction lists, appeals processes, or quorum rules.
* **Incentives and markets**, such as credits for resource sharing or bids for scarce namespaces.
* **Diverse user interfaces** that consume the same ordered state but present different experiences.

Structure is guaranteed; meaning is intentionally left open.

---

## 14. Application model for developers

Developers treat applications as deterministic state machines that react to the ordered graph feed and emit new proposals. They do not stand up servers that arbitrate every interaction; they write logic that interprets local state and responds to user input. Every surface (desktop, mobile, embedded, automation) executes the same rules because the substrate delivers the same ordered history everywhere.

Building on 2WAY means inheriting identity, permissions, ordering, and durability instead of reimplementing them. Applications focus on domain intent while the substrate handles authority edges, append-only logging, and replay. Teams ship features without provisioning databases, queuing systems, or bespoke sync jobs, yet retain deterministic audit trails that survive device swaps or offline use.

This model appeals to developers because it:

* **Collapses backend operations**: there is no control plane to babysit, only deterministic code that runs beside the substrate on each device.
* **Keeps users productive offline**: every node already owns the relevant slice of state, so workflows continue even when networks disappear.
* **Enables reproducible debugging**: developers can replay ordered logs to reproduce bugs or validate migrations without mocking remote services.
* **Lets multiple implementations coexist**: as long as they obey the schemas and invariants, different runtimes or UI stacks remain interoperable.

A typical workflow:

1. **Define schemas and invariants** for the objects the application cares about, including how they relate to other identities and capabilities.
2. **Subscribe to the ordered feed** that the substrate maintains locally, updating caches, UI state, or side effects using only accepted events.
3. **Let users interact with local data** (every node already stores the relevant slice) without waiting on a remote backend or reconciling divergent drafts.
4. **Propose mutations through substrate interfaces**; the platform enforces authority, ordering, and durability uniformly across peers, so applications never roll their own ACLs or sync logic.

Implications for developer experience:

* Applications never run central backends or maintain authoritative copies of shared state.
* Identity and key management remain inside the substrate; applications call provided APIs instead of handling secrets directly.
* Custom sync protocols, reconciliation loops, or ACL rebuilds are unnecessary; the substrate already enforces them structurally.
* Network input visible to applications has already passed validation, so application logic sees deterministic, trustworthy events.
* Testing becomes simpler because applications can replay ordered logs locally to reproduce user-visible state without mocking remote services.
* Feature delivery becomes incremental: schema updates, capability grants, and UI changes can ship independently because all peers enforce the same invariants.
* Cross-platform clients stay consistent by construction since they interpret the same ordered facts, not divergent replicas.

---

## 15. Application domains

2WAY is best suited for workflows where trust, history, and survivability matter more than raw throughput. Anywhere centralized backends struggle (because users need to keep operating offline, share authority across organizations, or prove provenance long after software changes), this structure shines.

Representative domains:

* **Web, mobile, desktop, and embedded apps** that must behave consistently on and offline without bespoke sync engines.
* **Messaging, collaboration, and shared workspaces** where every edit, mention, or invitation needs provenance and bounded reach.
* **Identity, credential, and access management** stacks that require distributed issuance, revocation, and auditability without a single CA.
* **Supply-chain and inter-vendor coordination** where mutually distrustful parties share state while retaining local authority.
* **Regulated or audit-heavy environments** such as finance, healthcare, or government that require append-only histories and explicit authority.
* **Offline-first, mesh, and edge networks** that must keep operating securely despite intermittent connectivity or hostile transports.
* **Critical infrastructure and defense systems** that cannot tolerate centralized control planes or silent compromise.

These use cases share a common need: structural guarantees about who can act, how data is ordered, and how history survives, regardless of which applications come and go.

---

## 16. Conformance

Conformance is binary. An implementation either satisfies every normative requirement in this repository or it does not. Passing tests or demonstrating interoperability is meaningless if core invariants have been weakened along the way.

To claim conformance, an implementation must demonstrate that:

* **All defined invariants hold** under every supported operating condition, including offline operation and hostile peers.
* **Forbidden behaviors remain structurally impossible**; relying on policy, logging, or operator vigilance is not an acceptable substitute for structural guards.
* **Validation, authorization, and ordering rules execute exactly as specified**, with no fast paths, heuristics, or “trusted modes” that bypass them.
* **No state mutation crosses boundaries out of band**; every write flows through the same serialized authority path regardless of origin.

Any deviation requires an Architecture Decision Record (ADR) that documents the reasoning, scope, and compensating controls. Without an ADR, the implementation is simply out of spec.

---

## 17. Scope boundary and status

This repository claims only what it states explicitly. Terms like “secure,” “trusted,” or “verified” carry meaning only when a section defines the exact conditions under which they apply. Examples illustrate possibilities, not mandates. Appendices, diagrams, or snippets are non-normative unless they are cited from a normative section.

The proof of concept remains a work in progress. Clarity, auditability, and structural correctness outrank performance, scale, or polish. Some trade-offs are intentionally unresolved until multiple implementations exercise the design. Treat this repository as the authoritative record of intent today, but not as a guarantee that future ADRs or revisions will keep every detail the same.
