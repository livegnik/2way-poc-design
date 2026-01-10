# 2WAY PoC Design Repository

2WAY is a local-first, peer-to-peer, open-source application protocol and backend designed to eliminate repeated reimplementation of identity, access control, synchronization, and trust in application development.

This repository contains the normative design documentation, defining how security and application state correctness are enforced by the system rather than reimplemented by each app.

In 2WAY, applications are defined by schemas, optional domain logic, and user interfaces. Identity, data storage, access control, cryptography, and peer-to-peer synchronization are provided by the protocol and backend.

---

## Table of Contents

* [Introduction](#introduction)
* [1. 2WAY at a glance](#1-2way-at-a-glance)
* [2. Repository guide](#2-repository-guide)
* [3. What 2WAY is](#3-what-2way-is)
* [4. Why 2WAY exists](#4-why-2way-exists)
* [5. Core idea: a shared, local-first graph](#5-core-idea-a-shared-local-first-graph)
* [6. Protocol object model](#6-protocol-object-model)
* [7. Backend component model](#7-backend-component-model)
* [8. Security model and threat framing](#8-security-model-and-threat-framing)
* [9. Structural impossibility](#9-structural-impossibility)
* [10. Degrees of separation and influence limits](#10-degrees-of-separation-and-influence-limits)
* [11. Sybil resistance through structure](#11-sybil-resistance-through-structure)
* [12. Denial-of-service containment](#12-denial-of-service-containment)
* [13. Failure behavior](#13-failure-behavior)
* [14. What the system guarantees](#14-what-the-system-guarantees)
* [15. What the system enables but does not define](#15-what-the-system-enables-but-does-not-define)
* [16. Application model for developers](#16-application-model-for-developers)
* [17. Application domains](#17-application-domains)
  * [17.1 Messaging and chat](#171-messaging-and-chat)
  * [17.2 Social media and publishing](#172-social-media-and-publishing)
  * [17.3 Markets and exchange of goods and services](#173-markets-and-exchange-of-goods-and-services)
  * [17.4 Marketplace-dependent applications](#174-marketplace-dependent-applications)
  * [17.5 Key revocation and recovery workflows](#175-key-revocation-and-recovery-workflows)
  * [17.6 Verifying binaries and software supply chains](#176-verifying-binaries-and-software-supply-chains)
  * [17.7 Device trust, enrollment, and compliance](#177-device-trust-enrollment-and-compliance)
  * [17.8 Multi-party coordination and governance](#178-multi-party-coordination-and-governance)
  * [17.9 Long-lived records and audit trails](#179-long-lived-records-and-audit-trails)
  * [17.10 What ties these examples together](#1710-what-ties-these-examples-together)
* [18. Conformance](#18-conformance)
* [19. Scope boundary and status](#19-scope-boundary-and-status)

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

## 6. Protocol object model

`01-protocol/02-object-model.md` defines the canonical grammar of the shared graph. Every persisted fact is one of five categories (Parent, Attribute, Edge, Rating, or ACL) and every record carries immutable metadata (`app_id`, `id`, `type_id`, `owner_identity`, `global_seq`, `sync_flags`). That metadata lets any peer replay history, verify authorship, and enforce ordering without consulting a coordinator or inventing new storage classes.

This minimal vocabulary is expressive enough to encode any application schema:

* **Parents** anchor entities that deserve identity: users, devices, contracts, workflow stages, data feeds, moderation queues. Schemas define Parent types, so developers can mint whatever anchors their domain requires without touching protocol code.
* **Attributes** attach typed payloads to Parents. A single anchor can carry multiple Attributes (profile fields, encrypted blobs, configuration knobs, even versioned schema definitions) letting optional features coexist without migrations outside the domain.
* **Edges** articulate relationships: membership, delegation, dependencies, references between revisions, supply-chain hops, automation triggers. Edges can point to another Parent or to a specific Attribute, which keeps both coarse and fine-grained links uniform.
* **Ratings** capture evaluations (votes, trust scores, endorsements, moderation outcomes) as first-class facts. They enrich any object without mutating it, so applications can apply their own semantics while the platform preserves provenance.
* **ACLs** are just Parents plus constrained Attributes, meaning authorization structures live in the same graph, inherit the same ordering, and are auditable with the same tools.

With these pieces, developers can compose trees, meshes, or any hybrid graph simply by instantiating Parents, attaching Attributes/Ratings, and wiring Edges. The object model never dictates meaning; it guarantees that whatever schema a developer defines will inherit identity, authorship, and deterministic ordering.

That freedom relies on three non-negotiable guardrails enforced by Graph Manager before Schema Manager or ACL Manager do their work:

- **Strict application scoping** keeps domains from bleeding into one another. `app_id` scopes every reference, so Attributes, Edges, Ratings, and ACL attachments can point only to objects inside the same domain. Cross-app access must be encoded through explicit delegation objects, not implied references.
- **Anchored ownership** makes every object answer to a Parent. Attributes bind typed data to a single Parent, Edges and Ratings originate from authoritative Parents, and ACLs are encoded entirely using Parent/Attribute records. There is no way to smuggle in foreign ownership metadata.
- **Explicit references only**: every pointer is the triple `<app_id, category, id>`. No implicit inheritance, inferred scope, or caller-local lookups are permitted, so unresolved references, duplicate selectors, or rebinding attempts fail deterministically before touching storage.

Because structural validation happens first, malformed proposals (missing required selectors, referencing nonexistent anchors, attempting to mutate immutable metadata) die in the shallow end: Graph Manager rejects them, nothing commits, and Log Manager records deterministic reasons. When a proposal passes this gate, downstream schema validation, ACL evaluation, and ordering can operate on trusted structure. The result is a small set of primitives that can encode any application data model while still guaranteeing provenance, referential integrity, and cross-app isolation.

---

## 7. Backend component model

If the object model defines what can be stored, `02-architecture/01-component-model.md` defines who is allowed to touch it. The backend is a single long-lived process composed of singleton managers (the protocol kernel) and optional services layered on top. Every manager owns one domain, exposes narrow APIs, and refuses to perform work outside that charter. Services orchestrate workflows but never bypass managers or mutate state directly.

### Manager roster and responsibilities

Each manager is authoritative for its slice of behavior. Together they form the write path that every mutation must traverse:

- **Config Manager** loads static/runtime configuration and exposes read-only access to other managers.
- **Storage Manager** is the sole interface to the durable store (SQLite in the PoC). All reads/writes, transactions, and durability guarantees flow through it.
- **Key Manager** owns node, user, and app key lifecycle: generation, storage (PEM), signing, decryption. No other component ever handles private keys.
- **Auth Manager** validates front-end credentials, establishes sessions, and resolves user/device identity.
- **Schema Manager** stores canonical schema definitions, resolves type IDs, and performs schema validation on proposed mutations.
- **ACL Manager** evaluates permissions using OperationContext plus graph data and issues allow/deny decisions.
- **Graph Manager** serializes all graph mutations, enforces the object model invariants, assigns global sequence numbers, and commits accepted writes via Storage Manager.
- **State Manager** coordinates sync domains, reconciliation windows, and conflict handling so peers exchange ordered history safely.
- **Network Manager** manages transports, peer authentication, message exchange, encryption, and framing.
- **Event Manager** publishes internal events so services, apps, or tooling can react to state changes deterministically.
- **Log Manager** owns structured logging for audit, diagnostics, and incident response.
- **Health Manager** tracks liveness/health metrics and exposes them for ops tooling.
- **DoS Guard Manager** enforces throttling, puzzles, and abuse controls at the boundary.
- **App Manager** registers applications, loads extension services, and binds them to OperationContext constraints.

These invariants are structural: Graph mutations that bypass Graph Manager, direct SQLite access without Storage Manager, or permission checks outside ACL Manager are specification violations, not implementation bugs.

### Services and OperationContext

System services and per-app extension services translate user intent into manager calls. They:

1. Accept API or automation input (always untrusted).
2. Build an `OperationContext` containing caller identity, app scope, requested capability, and tracing data.
3. Invoke managers strictly through their public interfaces (Graph for writes, Schema for validation, ACL for authorization, Storage for permitted reads, Event for publication, Log for audit).

Services never talk to other services directly, never read private keys, and never persist data on their own. App extension services are sandboxed to their app domain; removing an app simply unregisters its services without touching the kernel.

### Trust boundaries and failure handling

Managers trust only validated inputs from peer managers. Services trust manager outputs but treat everything else (including other services) as untrusted. Network Manager and Auth Manager are the boundary guardians: they accept hostile traffic, authenticate it, and only then hand requests to services with minimal pre-processing. When a manager rejects a request (invalid structure, failed ACL, storage fault), no partial state remains; Graph Manager rolls back the transaction, Log Manager records the reason, and the caller receives a deterministic error.

Because every write flows `Service → Graph Manager → Storage Manager`, and every validation step calls into Schema, ACL, DoS Guard, and Key Managers explicitly, there are no parallel authority paths to forget. Changing the set of services does not weaken guarantees; changing a manager requires an Architecture Decision Record because it rewires system invariants. This strict component model is what lets multiple implementations enforce the same rules even if their runtime packaging differs.

---

## 8. Security model and threat framing

Legacy stacks typically trust the network, a perimeter, or a central operator. 2WAY assumes none of that holds. Every node treats the transport as hostile, assumes peers can lie or go dark indefinitely, and refuses to trust an application until the graph records explicit capabilities. The result is a security posture that survives compromised devices, rogue apps, and long stretches of offline operation without depending on a coordinating backend.

Threats considered routine:

- **Malicious or misconfigured peers** injecting malformed objects, replaying stale history, tampering with ordering, or impersonating identities.
- **Sybil floods** that mint endless keys to borrow reputation, force expensive validation, or hide abuse behind throwaway identities.
- **Unauthorized graph mutation** that attempts to cross ownership boundaries, escalate permissions, or bypass schema-defined invariants.
- **Replay and ordering attacks** that try to confuse deterministic state machines or resurrect revoked authority.
- **Denial attempts** via malformed payloads, unbounded fan-out, and resource-starving validation paths.
- **Partial compromise of apps or nodes**, including stolen keys, tampered binaries, unvetted extensions, and insider abuse.

What makes the model durable is that protection flows from structure, not perimeter gear or best-effort logging:

- **Fixed validation order**: schema checks, ACL evaluation, deterministic ordering, and append-only commit run in a strict sequence on every device. Nothing skips ahead, even for “trusted” code.
- **Per-node enforcement**: every peer owns its keys, history, and rejection pipeline. Compromise of one node yields isolation, not systemic privilege.
- **Deterministic rejection**: missing context, ambiguous ownership, or conflicting history immediately fails the request before any durable state changes, making attacks noisy and short-lived.

For app developers, this means you inherit a security substrate that does not rely on keeping attackers out. Instead, it contains them with structural guarantees: if the graph lacks the necessary edges or capabilities, the action simply cannot be expressed. That gives you Sybil resistance through anchoring, rate- and resource-limiting at the DoS Guard Manager, and the confidence that offline devices stay safe until they can reconnect and replay history under the same rules.

---

## 9. Structural impossibility

2WAY does not rely on policy or best effort to block dangerous behavior. It encodes the rules of the system so tightly that many attacks have no valid execution path. If the graph lacks the required edges, ownership, or ancestry, the mutation cannot even be expressed, let alone committed.

This structural approach covers:

* **Application isolation**: proposals cannot point at foreign state unless the graph already records a delegation that allows it.
* **Access control enforcement**: capabilities are first-class graph objects that must exist before any write is considered; without them the proposal is malformed.
* **Graph mutation rules**: only the owning device can author changes for its portion of the graph because no other key can form the required parent references.
* **State ordering guarantees**: ancestry links and deterministic ordering ensure history remains append-only; retroactive edits simply have nowhere to land.

As a result, even a compromised application or stolen key can only emit proposals that fail validation. It cannot fabricate privilege, rewrite history, or manufacture the structural hooks it would need to cross authority boundaries. Rejection is automatic and deterministic, not a matter of luck or operator vigilance.

---

## 10. Degrees of separation and influence limits

Authority in 2WAY is not global. Relationships in the graph include direction, ownership, and the purpose of the edge, so policies can describe not only who may act but how far their influence may travel. This allows nodes to treat near neighbors differently from distant observers without inventing ad-hoc filters.

Practical implications:

* **Degrees of separation**: applications can enforce first-degree rules for collaborators, looser policies for second-degree observers, and outright silence for unknown nodes.
* **Bounded broadcast and replication**: reads, writes, invitations, and announcements can specify maximum hop counts, preventing unsolicited proposals from traveling farther than intended.
* **Structural ignore**: identities outside the permitted radius have no path to the local device, so their messages never enter validation pipelines and consume zero trust budget.
* **Intentional expansion**: to grow reach, an identity must form explicit edges and be accepted by every hop, creating an audit trail of who granted influence and why.

These constraints prevent trust from spreading automatically, keep unsolicited reach narrow, and force influence to flow through intentional, inspectable relationships instead of global fan-out.

---

## 11. Sybil resistance through structure

Global Sybil prevention is not realistic for large, open networks. 2WAY focuses instead on making identity floods pointless by requiring every actor to earn their reach through visible, consented relationships.

Structural guardrails:

* **Anchoring required**: new keys have no influence until they form explicit edges with trusted anchors. Without that path, their proposals never leave the network buffer.
* **Application-scoped trust**: reputation lives in the shared graph but is interpreted per application, so a credential or score in one domain does not grant privileges anywhere else.
* **Explicit delegation**: edges that convey authority must be recorded by both parties, include bounded capabilities, and can be revoked like any other mutation.
* **Degree limits**: hop budgets prevent unsolicited fan-out. Nodes that never opted into a path toward an identity will never see its traffic.
* **Cost mirrors intent**: forming real relationships requires work (introductions, shared history, mutual acceptance), making it expensive for attackers to scale beyond nuisance traffic.

Attackers can still generate packets, but without anchors, recognized capabilities, and degree-limited paths, they cannot mutate state, borrow reputation, or force attention from unwilling nodes.

---

## 12. Denial-of-service containment

2WAY expects sustained abuse and is built to keep attackers on the defensive. Throughput may dip, but data integrity and ordering do not because every trust boundary can say “no” cheaply before expensive work starts.

The system keeps denial attempts unproductive by combining fast rejection (schema checks, permission gates, serialized writes, scoped sync windows) with adaptive cost shifting. When pressure rises, the node simply makes the requester spend more effort before each packet lands, so the attacker burns CPU while the defender stays mostly idle.

At a high level, untrusted traffic is handled in a shallow, easily restarted zone, while authenticated traffic moves deeper only after it clears admission. That separation means abusive bursts die at the boundary while established peers keep exchanging signed history.

Client puzzles stay dynamic: difficulty increases automatically for sources that misbehave and relaxes for peers that remain cooperative. Proofs expire quickly and cannot be replayed, so solving one puzzle never opens the door for someone else.

Because every device enforces these guardrails locally, damage stays contained. Compromised nodes may lose their own connectivity, but they cannot drag honest peers into coordination storms or force them to redo work simply by shouting louder.

---

## 13. Failure behavior

2WAY assumes things will go wrong: keys get stolen, devices crash mid-write, peers disagree, or malicious inputs flood a node. The system responds by failing closed instead of guessing what the operator intended.

When a rule is violated (schema mismatch, missing capability, conflicting ordering), the input is rejected before it touches durable state. No speculative writes stick around hoping to be fixed later. Each write still passes through the same serialized path, so local integrity holds even if the app above it is compromised.

Operation continues, just with reduced scope. Nodes quarantine the faulty identity, mark incomplete state as suspect, and keep serving peers whose histories remain intact. Isolation wins over availability: better to drop a misbehaving connection than let it corrupt the graph.

Recovery is deliberate and auditable. Administrators or applications must craft explicit corrective actions (revocations, replays, migrations, repairs) that pass exactly the same validation pipeline as any other write. There is no hidden “admin override” or silent reconciliation loop. If a fix cannot be encoded as a normal mutation, it does not happen, which keeps the audit trail honest and reproducible.

---

## 14. What the system guarantees

2WAY makes a small set of promises, all enforced structurally rather than by convention:

* **Identity-bound authorship**: every mutation is cryptographically tied to the device and identity that proposed it, so provenance is never ambiguous.
* **Append-only, tamper-evident history**: each node keeps its own ordered log with parent references and durable digests, enabling independent replay or audit.
* **Deterministic validation and ordering**: well-formed inputs produce identical outcomes on every node regardless of arrival timing or network behavior.
* **Structural application isolation**: applications observe the same feed but cannot touch each other's state without explicit delegation recorded in the graph.
* **Explicit authority delegation**: permissions originate only from recorded edges, not from environment variables, config files, or implied roles.
* **Fail-closed behavior**: missing context, conflicting data, or ambiguous authority yields rejection rather than guesswork, so attacks die at the boundary.

Because these guarantees live in structure, they are testable, auditable, and portable across implementations. If an implementation cannot demonstrate each property, it does not conform.

---

## 15. What the system enables but does not define

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

## 16. Application model for developers

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

## 17. Application domains

2WAY shines wherever trust, verifiability, and survivability matter more than pushing raw throughput. Everywhere centralized backends wobble (offline collaboration, multi-party workflows, postmortem accountability), this substrate keeps authority local, history replayable, and policy boundaries explicit even as applications evolve. Adopting 2WAY means applications promise users that collaboration endures without a master server, provenance is inspectable without middlemen, and failure modes remain bounded no matter who operates the UI above the substrate.

Representative umbrella categories still mirror those in earlier drafts: web, mobile, desktop, and embedded apps craving deterministic sync; messaging or shared workspaces that need provenance on every edit; distributed identity stacks; supply-chain coordination; regulated industries; offline-first meshes; and critical infrastructure that refuses silent overrides. The sections below dive deeper into concrete examples drawn from those categories to illustrate how the shared graph and manager pipeline make ambitious designs practical without recreating backends for every domain.

Developers operating in these spaces still gain:

- **Predictable compliance** because append-only logs, explicit delegations, and deterministic validation map neatly onto regulatory controls.
- **Faster multi-party integrations** once schemas and capabilities align, since no bespoke backend trust agreement is required.
- **User-facing empowerment** where auditing, recovery, and delegation can ship as first-class UX given the substrate already enforces them.

### 17.1 Messaging and chat

A messaging or chat workload maps cleanly to graph primitives. Conversations become `Parent` objects, participants are modeled via membership `Edge`s, individual messages land as `Attribute` objects with payloads and metadata, and a dedicated `ACL` object defines who may read or write. That layout is illustrative, not prescriptive; developers remain free to remodel conversations, threads, or channels however their UX demands, so long as their schema honors the object model and mutation rules.

What turns that flexibility into a viable backend replacement is the enforced pipeline. Every outbound message is just another proposed mutation submitted through the State Manager. Graph Manager confirms that targets exist and references are well-formed, Permission Manager evaluates the conversation ACL against the author identity verified by Identity Manager, and only then does the State Manager serialize the write, commit it durably, and surface it to peers through Sync Manager. Because this gauntlet runs locally on every node and cannot be bypassed, a malicious peer cannot inject unauthorized traffic or reorder history, offline writers can keep authoring while disconnected, and applications concentrate on presentation details such as rendering, end-to-end encryption above the substrate, and retention policy instead of reinventing identity checks, access control, ordered persistence, or failure handling.

### 17.2 Social media and publishing

Social feeds, publishing tools, or community spaces can express their data as a graph of identities, follow or subscription relationships, posts, reactions, and moderation signals. Developers might pick `Edge`s to encode follows, `Parent`s for posts or threads, `Attribute`s for content bodies and timestamps, `Rating`s for reactions or trust annotations, and `ACL`s to define visibility. This is only one schema among many; the protocol never mandates shape, only that every fact obeys the shared object vocabulary.

Centralized networks enforce reach because they own the graph and the policy. Many decentralized attempts jettison the backend but also discard enforceable structure, so spam and moderation stalemates dominate. 2WAY sits between those extremes: distribution and visibility are driven by explicit data such as `ACL`s, relationship `Edge`s, and Permission Manager evaluation rather than by an opaque service. Developers can incorporate degrees of separation into authorization logic, limiting unsolicited reach without heuristics. Moderation also becomes data: attaching `Rating` or moderation `Attribute` objects to content or identities records outcomes as ordered mutations that any application can interpret differently while still trusting authorship and validity. Structure, not central authority, keeps the network usable.

### 17.3 Markets and exchange of goods and services

A marketplace can represent listings, offers, contracts, and reputation entirely within the graph: `Parent` objects for listings or contracts, `Attribute`s for terms and prices, `Edge`s for participant roles, `Rating`s for feedback, and `ACL`s to bound who may advance a contract’s state. Centralized markets simplify disputes by acting as the arbiter, while fully peer-to-peer systems often lack a shared notion of contract progression, making coordination brittle.

2WAY enables a middle ground by treating each contract as a state machine encoded directly in graph objects. Every transition is a mutation that Graph Manager validates, Permission Manager authorizes, and State Manager orders. History stays signed and replayable, so multiple market interfaces can coexist, compete on user experience or fees, and yet rely on the same canonical contract data. The substrate does not enforce payments or physical delivery; it enforces that only authorized transitions happen and that they land in an ordered, durable log synchronized through Sync Manager.

### 17.4 Marketplace-dependent applications

Many real-world services depend on market-like coordination without being markets themselves. Ride-hailing, delivery, and local services all involve offers, acceptances, and completions that benefit from enforceable identity and ordering even when central dispatch disappears.

#### Ride-hailing and drivers

Drivers, riders, availability signals, trip requests, offers, and completion events all become explicit graph objects. Trips can be `Parent`s, location and schedule data can live in typed `Attribute`s, participant responsibilities are `Edge`s, and `ACL`s define who may accept or finalize a ride. Centralized dispatch works because a backend observes everything; decentralized broadcast systems tend to drown in spam. On 2WAY, reach is structurally bounded: relationship `Edge`s, geographic attributes, or policy rules evaluated by Permission Manager determine who learns about a trip. Accepting and closing a ride are ordered mutations, so both parties can verify the sequence independently, and offline operation remains viable because nodes queue trusted mutations until Sync Manager can share them.

#### Food delivery and dispatch

Adding merchants and dispatch roles simply extends the graph. Dispatch authority becomes a delegated capability encoded in `ACL`s and relationship objects rather than an implicit backend privilege. If a dispatcher or SaaS integration disappears, the system narrows gracefully, letting couriers keep working against local state while later reconciliation through Sync Manager restores global consistency without a panic cutover.

#### Goods and local services

Local services, repairs, rentals, or classifieds hinge on long-lived identity and auditability. Centralized platforms often delete trust history when they shut down or pivot. In 2WAY, identity and contract history persist independently of any single interface, so neighborhood services can survive platform churn while retaining verifiable audit trails.

### 17.5 Key revocation and recovery workflows

Keys, devices, and identity bindings are all first-class graph objects, meaning revocation is not a privileged administrative override. Changing which keys Identity Manager will accept is just another ordered mutation that runs through Graph Manager, Permission Manager, and State Manager. Recovery workflows can likewise be modeled in data: `Edge`s and `ACL`s can require approvals from designated recovery identities before a new device key becomes valid. The substrate refuses to dictate policy, but once a policy is described, it enforces ordering, authorization, and auditability consistently because every state change flows through the same pipeline.

### 17.6 Verifying binaries and software supply chains

2WAY also works as an identity and history layer for software distribution. Releases can be signed `Parent` objects with `Attribute`s that store hashes, metadata, or bill-of-materials entries, while publisher hierarchies are just relationship `Edge`s. Trust in publishers is expressed explicitly in the graph, so installation becomes a local policy decision driven by verifiable state, not by DNS or a hosted repository. If a signing key is compromised, a revocation mutation instructs peers to distrust it, and thanks to the State Manager and Sync Manager preserving ordered, tamper-evident history, clients observe and enforce the change without waiting for a central takedown service.

### 17.7 Device trust, enrollment, and compliance

Devices can be modeled as their own objects with attributes describing capabilities, compliance status, and desired posture. Policies themselves are data, enforced locally by Permission Manager rather than by a continuously available management server. Revocation becomes an ordered event, auditability comes from reading signed history, and organizations gain a model suited to environments where availability and inspection matter more than remote convenience.

### 17.8 Multi-party coordination and governance

Because 2WAY enforces ordered, authorized transitions, it naturally supports workflows that demand multiple approvals. Shared `Parent` objects can represent the subject of governance, delegated capabilities live in `ACL`s, and each approval is an ordered mutation that the State Manager records. The system never dictates governance rules; it provides primitives that let communities encode quorums, vetoes, or escalation paths as auditable workflows enforced by the substrate rather than by tradition.

### 17.9 Long-lived records and audit trails

Any workflow that values durable records benefits from identity-bound authorship, ordered history, and fail-closed enforcement. Records become graph objects with explicit ownership and immutable ancestry. Unlike centralized audit systems, correctness does not depend on trusting an operator, and unlike many peer-to-peer networks, ordering and authorization are enforced rather than heuristic. Even if an original application disappears, records remain verifiable to anyone who can replay the history.

### 17.10 What ties these examples together

These examples are intentionally hypothetical. They demonstrate that once identity, permissions, ordering, validation, and denial-of-service controls are enforced below the application layer (by the Identity Manager, Graph Manager, Permission Manager, State Manager, Sync Manager, and DoS Guard Manager), entire classes of workloads become feasible without trusted backends. Centralized systems concentrate authority; many peer-to-peer systems lack enforceable structure. 2WAY works because every node enforces the same structure locally and consistently, leaving application developers free to decide how to model meaning on top while the substrate guarantees authorship, ordering, and survivability.

---

## 18. Conformance

Conformance is binary. An implementation either satisfies every normative requirement in this repository or it does not. Passing tests or demonstrating interoperability is meaningless if core invariants have been weakened along the way.

To claim conformance, an implementation must demonstrate that:

* **All defined invariants hold** under every supported operating condition, including offline operation and hostile peers.
* **Forbidden behaviors remain structurally impossible**; relying on policy, logging, or operator vigilance is not an acceptable substitute for structural guards.
* **Validation, authorization, and ordering rules execute exactly as specified**, with no fast paths, heuristics, or “trusted modes” that bypass them.
* **No state mutation crosses boundaries out of band**; every write flows through the same serialized authority path regardless of origin.

Any deviation requires an Architecture Decision Record (ADR) that documents the reasoning, scope, and compensating controls. Without an ADR, the implementation is simply out of spec.

---

## 19. Scope boundary and status

This repository claims only what it states explicitly. Terms like “secure,” “trusted,” or “verified” carry meaning only when a section defines the exact conditions under which they apply. Examples illustrate possibilities, not mandates. Appendices, diagrams, or snippets are non-normative unless they are cited from a normative section.

The proof of concept remains a work in progress. Clarity, auditability, and structural correctness outrank performance, scale, or polish. Some trade-offs are intentionally unresolved until multiple implementations exercise the design. Treat this repository as the authoritative record of intent today, but not as a guarantee that future ADRs or revisions will keep every detail the same.

---
