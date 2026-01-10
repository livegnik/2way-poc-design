



# 2WAY PoC Design Repository

2WAY is a local-first, peer-to-peer, open source protocol and backend. It exists so application developers can stop rewriting identity, access control, synchronization, and trust for every product.

This repository is the normative design set. It explains how the system keeps security guarantees and application state correctness without leaning on per-app backends.

In 2WAY, application authors define schemas, optional domain logic, and user interfaces. The protocol and backend supply identity, storage, access control, cryptography, and peer-to-peer sync.

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

2WAY defines a decentralized application substrate that separates identity, permissions, ordering, and history from changeable application code. This repository is the proof-of-concept specification, and every invariant, guarantee, and constraint in the rest of the project traces back here.

Modern stacks lean on centralized backends to decide who users are, which actions they may take, how data is ordered, and whether history survives. Those backends turn into single points of control and failure. When operators change priorities, infrastructure disappears, or multiple deployments must cooperate, users inherit migrations and policy swings they never asked for.

2WAY moves authority to each node. Every device owns its cryptographic identity, enforces permissions locally, orders the changes it accepts, and stores its own history. Correctness comes from structure, not from a central coordinator or trusted transport.

Applications do not mutate storage directly. They describe schemas, propose graph mutations, and react to the ordered stream of accepted state. Each proposal must pass schema checks, authorization, deterministic ordering, and append-only commit on the device that receives it. Unsigned, ambiguous, or context-free input never survives the network buffer.

This repository does not ship production code. It records design intent, boundaries, guarantees, and failure behavior for a proof of concept that multiple implementations can target. Performance tuning, UI polish, and production bootstrapping stay out of scope. The following sections explain how the substrate works, why it exists, how it contains adversaries, and what a conformant build must honor.

---

## 1. 2WAY at a glance

2WAY replaces central backends with locally enforced structure. The platform guarantees:

- **Local authority and durability**: every device keeps an append-only log, holds its own keys, and decides independently what to accept. No remote operator is required.
- **Guarded inputs**: network data arrives untrusted. Schema checks, capability validation, and deterministic ordering run before commits, so malformed or replayed input dies at the boundary.
- **Bounded trust**: identities remain inert until the shared graph records them. Unknown apps or peers cannot borrow privilege or spread influence without explicit anchoring.
- **Structural containment**: graph ownership, permission edges, and ordering rules stop applications from crossing authority boundaries.
- **Deterministic rejection**: missing permission, unclear context, or invalid ancestry yields the same error on every device, which avoids silent divergence.
- **Progressive failure**: compromise or outage reduces capability instead of destroying state. Nodes isolate the fault, preserve trusted history, and continue serving peers that remain in good standing.

---

## 2. Repository guide

This repository is the source of record for the 2WAY proof of concept. It defines scope, invariants, architecture, data, security, flows, and acceptance criteria so independent implementations can be judged against the same rules. It does not provide runnable code, deployment advice, governance policy, or shortcuts that weaken structural guarantees. The guiding question is: if identity, permissions, ordering, and sync are enforced locally and structurally, what systems become possible that centralized backends struggle to deliver?

Lower-numbered directories hold higher authority: scope constrains protocol, protocol constrains architecture, and so on. When conflicts appear, record an Architecture Decision Record (ADR) to document the override.

| Folder | Authority focus | Typical questions |
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

Put each new artifact in the folder that matches its authority. Never let a lower folder contradict a higher one unless an ADR explains the exception.

---

## 3. What 2WAY is

2WAY is a local-first application substrate that replaces the traditional backend. Every participating device runs the same authority stack (identity, permissions, ordering, durability), so availability and policy never depend on a central service.

Each node keeps its own append-only log, validates every proposed change against local rules, and syncs only the data it trusts. Nodes can stay offline for long periods, then reconcile with peers without conceding control over history or policy.

All domain data lives in a structured graph that spans identities, relationships, capabilities, and application records. Ownership is explicit for each node and edge, so every mutation states which identity governs it. The substrate enforces graph rules, checks signatures, orders writes, and persists the result locally.

Applications run beside the substrate. They describe schemas, observe the ordered feed of accepted changes, and request new mutations through deterministic interfaces. They never own storage, manage keys, or bypass validation; they interpret and influence the shared graph only within the permissions they hold.

Because every device enforces the same rules, network input and peer behavior stay untrusted until proven valid. Unsigned, ambiguous, or out-of-order data is rejected before it touches durable state, so a compromised node cannot coerce another into rewriting history or leaking authority.

### Layered authority model

Authority flows downward from applications to storage.

```
Applications          Interpret ordered state, run UI, apply domain logic
    ↓
2WAY Substrate        Identity, permissions, ordering, graph state, sync, structural guards
    ↓
Storage & Transport   Local persistence and networking
```

| Layer | Responsibilities | Cannot bypass |
| --- | --- | --- |
| Applications | Interpret ordered state, run UI and domain logic, compose proposals | Substrate validation, ordering, authority rules |
| 2WAY Substrate | Own identity, permissions, ordering, synchronization, graph invariants | Storage guarantees or transport constraints |
| Storage & Transport | Persist append-only history and exchange messages with peers | Local authority of the substrate or per-device policy |

---

## 4. Why 2WAY exists

Modern systems falter because they concentrate authority. Root keys, ACLs, and data ownership sit next to business logic in a single backend, so the operator can rewrite history, change rules, or disappear. A breach or policy swing can revoke an entire product overnight, leaving customers with no reliable path to recover data or prove their rights.

Even cooperative backends integrate poorly. Teams either expose every service or hide everything behind brittle federation bridges. Each new integration expands the blast radius of compromise, and org changes break the hand-built trust agreements those bridges rely on. Data outlives software, yet migrations still require freeze-and-cutover projects because authority and storage are welded together.

2WAY exists to separate durable structure from transient software. Identities, relationships, ordering, and permissions live in a shared graph that every device enforces locally. Applications and operators can evolve or go offline without pulling authority with them. Compromise stays within the trust radius that granted access, and reconnecting peers replay signed history rather than trusting a central coordinator. Multiple implementations can cooperate without adopting each other's incentives or liabilities.

---

## 5. Core idea: a shared, local-first graph

2WAY revolves around a typed graph that every node keeps on its own hardware. There is no upstream database or replica set to join. Each device stores its portion of the graph, signs the history it authors, and shares only the changes it accepts.

The graph is the fact store for the entire system. It holds identities, devices, relationships, capabilities, application records, and the permissions that bind them. Every node or edge has a clear owner, so each mutation states which identity is responsible and which part of the structure it may influence.

History is append-only and rooted in per-device logs. Every change carries authorship, parent references, schema identifiers, and payload hashes. Peers can replay another device's log and decide for themselves whether that sequence satisfies their invariants; no opaque coordinator is needed.

Because the graph lives on every node, the system is local-first. Writes land on the originating device, then propagate as signed deltas when peers connect. Synchronization is incremental and scoped by trust: peers request only the ranges they want, verify ordering deterministically, and merge when every prerequisite holds. Long offline periods are normal; reconnection is another validation and merge pass.

Every proposal follows the same lifecycle:

1. An application proposes a change with a schema that states what must exist and how it may evolve.
2. Schema validation ensures references exist, types match, and the payload respects domain rules.
3. Authorization checks verify that the signer owns the relevant nodes or holds capabilities that allow the mutation.
4. Deterministic ordering picks where the proposal fits relative to accepted writes, preventing races.
5. The mutation commits to the local append-only log and, if desired, streams to peers that run the same pipeline.

If any step fails (missing reference, stale capability, conflicting order), the proposal never hits durable state. Rejection is deterministic, so correct nodes converge without negotiating or trusting the network.

---

## 6. Protocol object model

`01-protocol/02-object-model.md` defines the grammar of the shared graph. Every fact is one of five categories (Parent, Attribute, Edge, Rating, ACL) and every record carries metadata (`app_id`, `id`, `type_id`, `owner_identity`, `global_seq`, `sync_flags`). That metadata lets any peer replay history, verify authorship, and enforce ordering without a coordinator or custom storage tricks.

This small vocabulary can model any application schema:

* **Parents** anchor entities that deserve identity (users, devices, contracts, workflow stages, data feeds, moderation queues). Schemas define Parent types so developers can mint whatever anchors they need.
* **Attributes** attach typed payloads to Parents. One anchor can carry multiple Attributes (profile fields, encrypted blobs, configuration, even schema definitions) so optional features can coexist without side migrations.
* **Edges** describe relationships like membership, delegation, dependencies, revision links, supply-chain hops, or automation triggers. Edges can point to another Parent or to a specific Attribute.
* **Ratings** store evaluations such as votes, trust scores, endorsements, or moderation outcomes as first-class facts. They enrich objects without mutating them.
* **ACLs** are Parents plus constrained Attributes, so authorization structures live in the same graph, inherit the same ordering, and stay auditable.

These primitives let developers build any graph by instantiating Parents, attaching Attributes or Ratings, and wiring Edges. The model never dictates meaning; it guarantees that whatever schema a developer defines inherits identity, authorship, and deterministic ordering.

Graph Manager enforces three guardrails before Schema Manager or ACL Manager run:

- **Strict application scoping** keeps domains separate. `app_id` scopes every reference, so Attributes, Edges, Ratings, and ACL attachments can point only to objects in the same domain. Cross-app access requires explicit delegation objects.
- **Anchored ownership** makes every object answer to a Parent. Attributes bind to one Parent, Edges and Ratings originate from authoritative Parents, and ACLs are expressed entirely with Parent and Attribute records.
- **Explicit references only**. Every pointer is `<app_id, category, id>`. There are no implicit lookups, inferred scopes, or caller-local shortcuts, so unresolved references or duplicate selectors fail before storage changes.

Because structural validation runs first, malformed proposals (missing selectors, nonexistent anchors, attempts to mutate immutable metadata) fail early. Graph Manager rejects them, nothing commits, and Log Manager records the reason. Once a proposal passes this gate, schema validation, ACL evaluation, and ordering can rely on trusted structure.

---

## 7. Backend component model

If the object model defines what can be stored, `02-architecture/01-component-model.md` defines who can touch it. The backend is a long-lived process made of singleton managers (the protocol kernel) plus optional services layered on top. Each manager owns one domain, exposes a narrow API, and refuses to work outside that charter. Services orchestrate workflows but never bypass managers or mutate state on their own.

### Manager roster and responsibilities

Each manager is authoritative for its slice of behavior. Together they form the write path every mutation must follow:

- **Config Manager** loads static and runtime configuration and shares read-only access with other managers.
- **Storage Manager** is the sole interface to durable storage (SQLite in the PoC). All reads, writes, transactions, and durability guarantees pass through it.
- **Key Manager** owns node, user, and app key lifecycle: generation, storage (PEM), signing, decryption. No other component handles private keys.
- **Auth Manager** validates front-end credentials, establishes sessions, and resolves user or device identity.
- **Schema Manager** stores canonical schema definitions, resolves type IDs, and validates proposed mutations.
- **ACL Manager** evaluates permissions using `OperationContext` and graph data, then returns allow or deny decisions.
- **Graph Manager** serializes mutations, enforces object model invariants, assigns global sequence numbers, and commits accepted writes via Storage Manager.
- **State Manager** coordinates sync domains, reconciliation windows, and conflict handling so peers exchange ordered history safely.
- **Network Manager** manages transports, peer authentication, message exchange, encryption, and framing.
- **Event Manager** publishes internal events so services, apps, or tooling can react deterministically.
- **Log Manager** handles structured logging for audit, diagnostics, and incident response.
- **Health Manager** tracks liveness and health metrics for operations tooling.
- **DoS Guard Manager** enforces throttling, client puzzles, and abuse controls.
- **App Manager** registers applications, loads extension services, and binds them to `OperationContext` constraints.

These rules are structural. Graph mutations that skip Graph Manager, direct SQLite access without Storage Manager, or permission checks outside ACL Manager violate the specification.

### Services and OperationContext

System services and per-app extension services translate user intent into manager calls:

1. Accept API or automation input (always untrusted).
2. Build an `OperationContext` with caller identity, app scope, requested capability, and tracing data.
3. Call managers only through their public interfaces (Graph for writes, Schema for validation, ACL for authorization, Storage for permitted reads, Event for publication, Log for audit).

Services never talk to other services directly, never read private keys, and never persist data on their own. App extension services are sandboxed to their app domain; removing an app simply unregisters its services without touching the kernel.

### Trust boundaries and failure handling

Managers trust only validated inputs from peer managers. Services trust manager outputs but treat everything else (including other services) as untrusted. Network Manager and Auth Manager guard the boundary: they accept hostile traffic, authenticate it, and hand requests to services with minimal preprocessing. When a manager rejects a request (invalid structure, failed ACL, storage fault), no partial state remains. Graph Manager rolls back the transaction, Log Manager records the reason, and the caller receives a deterministic error.

Every write flows `Service → Graph Manager → Storage Manager`, and every validation step calls Schema, ACL, DoS Guard, and Key Managers explicitly. There are no parallel authority paths to forget. Changing services does not weaken guarantees; changing a manager requires an ADR because it rewires system invariants. This strict component model keeps implementations consistent even if runtime packaging differs.

---

## 8. Security model and threat framing

Legacy stacks often trust the network, a perimeter, or a central operator. 2WAY assumes none of those hold. Each node treats transport as hostile, assumes peers can lie or stay dark indefinitely, and refuses to trust an application until the graph records explicit capabilities. This posture survives compromised devices, rogue apps, and long offline periods without depending on a coordinating backend.

Threats handled by design:

- **Malicious or misconfigured peers** that inject malformed objects, replay stale history, tamper with ordering, or impersonate identities.
- **Sybil floods** that mint endless keys to borrow reputation, force validation work, or hide abuse behind throwaway identities.
- **Unauthorized graph mutation** that tries to cross ownership boundaries, escalate permissions, or bypass schema rules.
- **Replay and ordering attacks** that attempt to confuse deterministic state machines or resurrect revoked authority.
- **Denial attempts** using malformed payloads, unbounded fan-out, or resource-starving input.
- **Partial compromise of apps or nodes**, including stolen keys, tampered binaries, unvetted extensions, or insider abuse.

Protection flows from structure rather than from perimeter gear or best-effort logging:

- **Fixed validation order**. Schema checks, ACL evaluation, deterministic ordering, and append-only commit run in a fixed sequence on every device.
- **Per-node enforcement**. Each peer owns its keys, history, and rejection pipeline. Compromising one node yields isolation, not systemic privilege.
- **Deterministic rejection**. Missing context, ambiguous ownership, or conflicting history fails immediately before durable state changes, making attacks noisy and short-lived.

App developers inherit a security substrate that assumes attackers reach the boundary. If necessary edges or capabilities are missing, the action cannot be expressed. That provides Sybil resistance through anchoring, rate limiting via DoS Guard Manager, and confidence that offline devices stay safe until they replay history under the same rules.

---

## 9. Structural impossibility

2WAY encodes its rules so tightly that many unsafe actions have no execution path. If the graph lacks the required edges, ownership, or ancestry, the mutation cannot even be formed.

This structural approach covers:

* **Application isolation**: proposals cannot point at foreign state unless the graph already contains a delegation that allows it.
* **Access control enforcement**: capabilities exist as graph objects and must be present before any write is considered.
* **Graph mutation rules**: only the owning device can author changes for its portion of the graph because no other key can form the correct parent references.
* **State ordering guarantees**: ancestry links and deterministic ordering keep history append-only; retroactive edits have nowhere to land.

Even if an application is compromised or a key is stolen, it emits only proposals that fail validation. It cannot fabricate privilege, rewrite history, or create structural hooks that cross authority boundaries. Rejection happens automatically and deterministically.

---

## 10. Degrees of separation and influence limits

Authority in 2WAY is local, not global. Relationships capture direction, ownership, and purpose, so policies can define not only who may act but how far their influence travels. Nodes can treat close neighbors differently from distant observers without ad-hoc filters.

Practical effects:

* **Degrees of separation**: applications can enforce strict rules for collaborators, relaxed policies for second-degree observers, and silence for unknown nodes.
* **Bounded broadcast and replication**: reads, writes, invitations, and announcements can specify hop limits, keeping unsolicited proposals from traveling farther than intended.
* **Structural ignore**: identities outside the permitted radius never reach the local device, so their messages consume no validation resources.
* **Intentional expansion**: to gain reach, an identity forms explicit edges accepted by each hop, leaving an audit trail of who granted influence and why.

These constraints prevent trust from spreading automatically, keep unsolicited reach narrow, and force influence through intentional, inspectable relationships.

---

## 11. Sybil resistance through structure

Perfect Sybil prevention is unrealistic for open networks, so 2WAY makes identity floods unproductive. Every actor must earn reach through visible, consented relationships.

Structural guardrails:

* **Anchoring required**: new keys have no influence until they form edges with trusted anchors. Without that path, their proposals never leave the network buffer.
* **Application-scoped trust**: reputation lives in the shared graph but is interpreted per application, so standing in one domain grants nothing elsewhere.
* **Explicit delegation**: edges that convey authority must be recorded by both parties, include bounded capabilities, and stay revocable.
* **Degree limits**: hop budgets block unsolicited fan-out. Nodes that never opted into a path will never see its traffic.
* **Cost matches intent**: forming real relationships requires effort (introductions, shared history, mutual acceptance), making it expensive for attackers to scale.

Attackers can still generate packets, but without anchors, recognized capabilities, and degree-limited paths, they cannot mutate state, borrow reputation, or force attention.

---

## 12. Denial-of-service containment

2WAY assumes sustained abuse and keeps attackers on the defensive. Throughput may dip, but data integrity and ordering hold because every trust boundary can reject cheaply before expensive work begins.

The system combines fast rejection (schema checks, permission gates, serialized writes, scoped sync windows) with adaptive cost shifting. When pressure rises, nodes force requesters to spend more effort before each packet lands, so attackers burn CPU while defenders stay mostly idle.

Untrusted traffic lives in a shallow, restartable zone. Authenticated traffic moves deeper only after clearing admission. That separation lets abusive bursts die at the boundary while established peers keep exchanging signed history.

Client puzzles stay dynamic: difficulty ramps up for misbehaving sources and relaxes for cooperative peers. Proofs expire quickly and cannot be replayed, so solving one puzzle never opens the door for someone else.

Because every device enforces these guardrails locally, damage stays contained. A compromised node may lose its own connectivity, but it cannot drag honest peers into coordination storms or force them to redo work just by shouting louder.

---

## 13. Failure behavior

2WAY assumes things will go wrong. Keys get stolen, devices crash mid-write, peers disagree, or malicious inputs flood a node. The system fails closed instead of guessing what the operator intended.

When a rule is violated (schema mismatch, missing capability, conflicting ordering), the input is rejected before it touches durable state. No speculative writes remain. Each write still travels the same serialized path, so local integrity holds even when the app above it is compromised.

Operation continues with reduced scope. Nodes quarantine the faulty identity, mark incomplete state as suspect, and keep serving peers whose histories remain intact. Isolation beats availability: it is better to drop a misbehaving connection than to corrupt the graph.

Recovery is explicit and auditable. Administrators or applications craft corrective actions (revocations, replays, migrations, repairs) that pass the same validation pipeline as any other write. There is no hidden admin override or silent reconciliation loop. If a fix cannot be encoded as a normal mutation, it does not happen.

---

## 14. What the system guarantees

2WAY makes a small set of structural promises:

* **Identity-bound authorship**: every mutation is tied cryptographically to the device and identity that proposed it, so provenance is clear.
* **Append-only, tamper-evident history**: each node keeps an ordered log with parent references and durable digests, enabling independent replay and audit.
* **Deterministic validation and ordering**: well-formed inputs produce identical outcomes on every node regardless of arrival timing or network behavior.
* **Structural application isolation**: applications see the same feed but cannot touch each other's state without explicit delegation recorded in the graph.
* **Explicit authority delegation**: permissions originate only from recorded edges, not from config files or implied roles.
* **Fail-closed behavior**: missing context, conflicting data, or ambiguous authority leads to rejection, so attacks end at the boundary.

Because these guarantees live in structure, they are testable, auditable, and portable across implementations. If an implementation cannot demonstrate each property, it is out of spec.

---

## 15. What the system enables but does not define

2WAY enforces structure but does not dictate meaning. It guarantees how identities relate, how permissions are enforced, and how history is recorded, yet it stays silent about why relationships exist or how a domain should use them. Interpretation belongs to the communities that build on the substrate.

Because the data model is neutral, the following can emerge without being hard-coded:

* **Trust relationships** built from shared edges without declaring global trust.
* **Reputation signals** interpreted per application, supporting different scoring models for the same identity.
* **Social, economic, or organizational semantics** layered on neutral data structures.
* **Governance and moderation** tailored by applications, including sanction lists, appeals, or quorum rules.
* **Incentives and markets** such as credits for resource sharing or bids for scarce namespaces.
* **Diverse user interfaces** that present the same ordered state through different experiences.

Structure is guaranteed; meaning remains open.

---

## 16. Application model for developers

Developers treat applications as deterministic state machines that respond to the ordered graph feed and emit new proposals. They do not stand up servers to arbitrate every interaction. Instead, they write logic that interprets local state and reacts to user input. Every surface (desktop, mobile, embedded, automation) follows the same rules because the substrate delivers the same ordered history.

Building on 2WAY means inheriting identity, permissions, ordering, and durability instead of rebuilding them. Applications focus on domain intent while the substrate handles authority edges, append-only logging, and replay. Teams ship features without provisioning databases, queues, or bespoke sync jobs yet keep deterministic audit trails that survive device swaps or offline use.

This model appeals to developers because it:

* **Collapses backend operations**: there is no control plane to babysit, only deterministic code running beside the substrate on each device.
* **Keeps users productive offline**: every node already holds the relevant slice of state.
* **Enables reproducible debugging**: developers replay ordered logs to reproduce bugs or validate migrations without mocking remote services.
* **Allows multiple implementations to coexist**: as long as they honor schemas and invariants, different runtimes or UI stacks remain interoperable.

Typical workflow:

1. **Define schemas and invariants** for the objects the application cares about, plus their relationships and required capabilities.
2. **Subscribe to the ordered feed** the substrate maintains locally, updating caches, UI state, or side effects using only accepted events.
3. **Let users interact with local data** without waiting on a remote backend or reconciling divergent drafts.
4. **Propose mutations through substrate interfaces** so authority, ordering, and durability stay uniform across peers.

Developer experience implications:

* Applications never run central backends or keep authoritative copies of shared state.
* Identity and key management stay inside the substrate; applications use provided APIs instead of handling secrets.
* Custom sync, reconciliation, or ACL rebuilds are unnecessary.
* Application-visible network input has already passed validation, so logic sees deterministic events.
* Testing is simpler because logs can be replayed locally.
* Feature delivery becomes incremental: schema updates, capability grants, and UI changes can ship independently because peers enforce the same invariants.
* Cross-platform clients stay consistent because they interpret the same ordered facts.

---

## 17. Application domains

2WAY fits workloads where trust, verifiability, and survivability matter more than peak throughput. Offline collaboration, multi-party workflows, and audit-heavy systems benefit because authority stays local, history is replayable, and policy boundaries remain explicit even as applications change. Adopting 2WAY means promising users that collaboration endures without a master server, provenance stays inspectable, and failure modes stay bounded no matter who operates the UI.

Representative umbrella categories mirror earlier drafts: web, mobile, desktop, and embedded apps that need deterministic sync; messaging or shared workspaces that need provenance; distributed identity stacks; supply-chain coordination; regulated industries; offline-first meshes; and critical infrastructure that refuses silent overrides. The examples below show how the shared graph and manager pipeline make ambitious designs possible without recreating a backend per domain.

Teams in these spaces gain:

- **Predictable compliance** because append-only logs, explicit delegations, and deterministic validation map cleanly to regulatory controls.
- **Faster multi-party integrations** once schemas and capabilities align, since no bespoke backend trust deal is required.
- **User-facing empowerment** where auditing, recovery, and delegation can ship as first-class UX because the substrate already enforces them.

### 17.1 Messaging and chat

Messaging maps neatly to graph primitives. Conversations become `Parent` objects, participants are membership `Edge`s, individual messages are `Attribute` objects, and an `ACL` defines who may read or write. That layout is illustrative, not prescriptive; developers can model conversations, threads, or channels however their UX demands as long as the schema honors the object model.

Each outbound message is a proposed mutation submitted through State Manager. Graph Manager confirms that targets exist and references are well formed, Permission Manager evaluates the conversation ACL against the author identity verified by Identity Manager, and State Manager serializes and commits the write before Sync Manager offers it to peers. Because this pipeline runs locally and cannot be bypassed, malicious peers cannot inject unauthorized traffic or reorder history, offline writers keep working, and applications can focus on presentation, end-to-end encryption layered above the substrate, and retention policy instead of rebuilding the stack.

### 17.2 Social media and publishing

Social feeds or community tools can express their data as identities, follow or subscription relationships, posts, reactions, and moderation signals. Developers might encode follows as `Edge`s, posts or threads as `Parent`s, content bodies and timestamps as `Attribute`s, reactions or trust marks as `Rating`s, and visibility rules as `ACL`s. The protocol never mandates shape; it only requires that each fact obey the shared vocabulary.

Centralized networks enforce reach because they own the graph and policy. Many decentralized attempts drop backends but also drop enforceable structure, so spam and moderation stalemates dominate. 2WAY sits between these extremes. Distribution and visibility come from explicit data (`ACL`s, relationship `Edge`s, and Permission Manager evaluation) rather than from a hidden service. Developers can use degrees of separation to limit unsolicited reach. Moderation becomes data: attaching `Rating` or moderation `Attribute` objects records outcomes as ordered mutations that any app can interpret while still trusting authorship and validity.

### 17.3 Markets and exchange of goods and services

A marketplace can represent listings, offers, contracts, and reputation entirely within the graph: `Parent` objects for listings or contracts, `Attribute`s for terms and prices, `Edge`s for participant roles, `Rating`s for feedback, and `ACL`s to bound who may advance a contract state. Centralized markets simplify disputes by acting as arbiters, while fully peer-to-peer systems often lack a shared notion of contract progression.

2WAY enables a middle path by treating each contract as a state machine encoded in graph objects. Every transition is a mutation that Graph Manager validates, Permission Manager authorizes, and State Manager orders. History stays signed and replayable, so multiple market interfaces can coexist, compete on UX or fees, and still rely on the same canonical data. The substrate does not enforce payments or delivery; it ensures that only authorized transitions happen and that they land in an ordered, durable log shared through Sync Manager.

### 17.4 Marketplace-dependent applications

Many services rely on market-like coordination without being markets themselves. Ride-hailing, delivery, and local services involve offers, acceptances, and completions that benefit from enforceable identity and ordering even when central dispatch disappears.

#### Ride-hailing and drivers

Drivers, riders, availability, trip requests, offers, and completion events become explicit graph objects. Trips can be `Parent`s, location and schedule data can live in typed `Attribute`s, participant responsibilities are `Edge`s, and `ACL`s define who may accept or close a ride. Centralized dispatch works because a backend observes everything; decentralized broadcast systems drown in spam. On 2WAY, reach stays bounded: relationship `Edge`s, geographic attributes, or policy rules evaluated by Permission Manager determine who sees a trip. Accepting and closing a ride are ordered mutations, so both parties can verify the sequence, and offline work remains possible because nodes queue trusted mutations until Sync Manager shares them.

#### Food delivery and dispatch

Merchants and dispatch roles extend the same graph. Dispatch authority becomes a delegated capability encoded in `ACL`s and relationship objects rather than an implicit backend privilege. If a dispatcher or SaaS integration disappears, the system narrows gracefully. Couriers keep working against local state, and later reconciliation through Sync Manager restores global consistency without a panic cutover.

#### Goods and local services

Local services, repairs, rentals, or classifieds rely on long-lived identity and auditability. Centralized platforms often delete trust history when they shut down or pivot. In 2WAY, identity and contract history persist independent of a single interface, so neighborhood services survive platform churn while keeping verifiable audit trails.

### 17.5 Key revocation and recovery workflows

Keys, devices, and identity bindings are graph objects, so revocation is not a privileged administrative action. Changing which keys Identity Manager accepts is just another ordered mutation that travels through Graph, Permission, and State Managers. Recovery workflows can also live in data: `Edge`s and `ACL`s can require approvals from designated recovery identities before a new device key becomes valid. The substrate does not dictate policy, but once a policy is described, it enforces ordering, authorization, and auditability because every state change uses the same pipeline.

### 17.6 Verifying binaries and software supply chains

2WAY works as an identity and history layer for software distribution. Releases can be signed `Parent` objects with `Attribute`s storing hashes, metadata, or bills of materials, while publisher hierarchies are relationship `Edge`s. Trust in publishers is expressed explicitly in the graph, so installation becomes a local policy decision driven by verifiable state, not DNS or a hosted repository. If a signing key is compromised, a revocation mutation instructs peers to distrust it, and thanks to State Manager and Sync Manager preserving ordered, tamper-evident history, clients observe and enforce the change without waiting for a central takedown.

### 17.7 Device trust, enrollment, and compliance

Devices can be modeled as objects with attributes describing capabilities, compliance status, and desired posture. Policies are data enforced locally by Permission Manager rather than by a continuously available management server. Revocation becomes an ordered event, auditability comes from reading signed history, and organizations gain a model suited to environments where availability and inspection matter more than remote convenience.

### 17.8 Multi-party coordination and governance

Because 2WAY enforces ordered, authorized transitions, it supports workflows that need multiple approvals. Shared `Parent` objects represent the subject of governance, delegated capabilities live in `ACL`s, and each approval is an ordered mutation recorded by State Manager. The system never dictates governance rules; it provides primitives so communities can encode quorums, vetoes, or escalation paths as auditable workflows enforced by the substrate instead of by tradition.

### 17.9 Long-lived records and audit trails

Any workflow that values durable records benefits from identity-bound authorship, ordered history, and fail-closed enforcement. Records become graph objects with explicit ownership and immutable ancestry. Unlike centralized audit systems, correctness does not depend on trusting an operator, and unlike many peer-to-peer networks, ordering and authorization are enforced rather than heuristic. Even if an original application disappears, records remain verifiable to anyone who can replay history.

### 17.10 What ties these examples together

These examples are illustrative. They show that once identity, permissions, ordering, validation, and denial-of-service controls live below the application layer (in Identity, Graph, Permission, State, Sync, and DoS Guard Managers), whole classes of workloads become feasible without trusted backends. Centralized systems concentrate authority; many peer-to-peer systems lack structure. 2WAY works because every node enforces the same structure locally while letting developers decide how to model meaning on top.

---

## 18. Conformance

Conformance is binary. An implementation either satisfies every normative requirement in this repository or it does not. Passing tests or showing interoperability means nothing if core invariants were weakened.

To claim conformance, an implementation must prove that:

* **All defined invariants hold** under every supported operating condition, including offline operation and hostile peers.
* **Forbidden behaviors remain structurally impossible**; policy, logging, or operator vigilance are not substitutes for hard guards.
* **Validation, authorization, and ordering rules run exactly as specified**, with no fast paths, heuristics, or trusted modes.
* **No state mutation crosses boundaries out of band**; every write flows through the same serialized authority path regardless of origin.

Any deviation requires an ADR that documents the reasoning, scope, and compensating controls. Without an ADR, the implementation is out of spec.

---

## 19. Scope boundary and status

This repository claims only what it states explicitly. Words such as "secure," "trusted," or "verified" matter only when a section defines the exact conditions. Examples illustrate possibilities, not mandates. Appendices, diagrams, or snippets are non-normative unless a normative section cites them.

The proof of concept is a work in progress. Clarity, auditability, and structural correctness outrank performance, scale, or polish. Some trade-offs remain open until multiple implementations exercise the design. Treat this repository as the authoritative record of intent today, not a guarantee that future ADRs or revisions will keep every detail unchanged.

---
