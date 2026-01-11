



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
┌──────────────────────────────────────────┐
│              Applications                │
│  • Interpret ordered state               │
│  • Run UI and domain logic               │
│  • Compose proposals                     │
│  Cannot bypass → substrate validation,   │
│  ordering, authority rules               │
└──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│            2WAY Substrate                │
│  • Identity, permissions, ordering       │
│  • Graph state, sync, structural guards  │
│  Cannot bypass → storage guarantees or   │
│  transport constraints                   │
└──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│        Storage and Transport             │
│  • Local persistence and networking      │
│  • Append-only history, peer exchange    │
│  Cannot bypass → local substrate         │
│  authority or per-device policy          │
└──────────────────────────────────────────┘
```

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

Every proposal follows the lifecycle described in `01-protocol/00-protocol-overview.md` and enforced by the managers named in `02-architecture/01-component-model.md`:

1. An application or service constructs an `OperationContext` and graph message envelope that states the desired mutation.
2. Graph Manager performs structural validation first, rejecting malformed envelopes before any other work occurs.
3. Schema Manager validates references, types, and domain rules according to the active schema set.
4. ACL Manager evaluates permissions using the supplied `OperationContext` and graph state; authorization must succeed before any write proceeds.
5. Graph Manager assigns a monotonic `global_seq`, commits the mutation through Storage Manager, and State Manager later syncs the accepted history to peers in order.

If any step fails (missing reference, stale capability, conflicting order), the proposal never hits durable state. Rejection is deterministic, so correct nodes converge without negotiating or trusting the network.

---

## 6. Protocol object model

`01-protocol/02-object-model.md` defines the grammar of the shared graph. Facts fall into five canonical categories: Parent, Attribute, Edge, Rating, and ACL (ACL structures are encoded as constrained Parent plus Attribute records). Parent, Attribute, Edge, and Rating records carry the shared metadata set (`app_id`, record id, `type_id`, `owner_identity`, `global_seq`, `sync_flags`) so any peer can replay history, verify authorship, and enforce ordering without a coordinator or custom storage tricks.

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

Authority in 2WAY is local, not global. Every private key, whether it belongs to a person, device, service, or automation, only sees the network from its zeroth degree: the graph it already trusts and the history it has replayed. Anything beyond that view requires explicit edges that describe direction, ownership, and purpose so policies can decide who may act and how far their influence can travel. Because each node enforces the same hop rules, degree filtering comes from the substrate, not from a UI toggle. Until a new identity forms edges with trusted anchors, its proposals never leave the network buffer.

Practical effects:

* **Zeroth-degree anchoring**: proposals are judged against the local view first. Subscribing to a broad topic does nothing until a first-degree link authorizes fetching and replay.
* **Gradient trust**: first-degree collaborators get fast reads and writes, second-degree observers may see delayed or read-only data, and unknown nodes stay invisible. Schema, ACL, and sync policies all honor that gradient.
* **Bounded broadcast and replication**: operations can declare a hop budget such as "friends of friends." Once that budget expires the mutation stops propagating, so spam bursts and storage growth stay tied to explicit consent.
* **Structural ignore**: identities beyond the chosen radius never reach ACL Manager or State Manager. Degree filters shed that work before it hits CPU or disk, which doubles as DoS protection.
* **Intentional expansion**: gaining reach means creating edges that every hop signs off on. Each hop records why it vouched for the next, so audits can trace influence and operators can retract it by pruning specific links.
* **UI determinism**: applications that render feeds, alerts, marketplaces, or governance queues know that every record already passed the user's degree filters. The zeroth-degree view defines what "global" means for that key.
* **Security layering**: degree filters form concentric rings. Unknown keys can send packets, but they cannot trigger schema validation, ACL evaluation, or disk writes until a trusted hop lets them through. Widening reach always leaves a recorded edge.
* **Sybil drag**: cloned identities must earn approval at every hop. Hop budgets and per-hop policy make that expensive, and removing any one link collapses the entire route.

These guardrails keep trust from spreading on its own, limit unsolicited reach, and make every relationship inspectable. Degrees of separation are an architectural tool that spans storage, sync, ACLs, and user experience instead of a loose moderation guideline.

The same mechanics feed directly into Sybil resistance (see Section 11). Degree enforcement keeps anonymous floods away from ACL evaluation, shows exactly who vouched for each identity, and lets defenders cut off whole branches by revoking a single edge. Sybils cannot borrow trust because every hop is intentional, reviewable, and revocable.

This approach is not the PGP Web of Trust. PGP attestations mostly claim that someone saw another key, and each client invents its own policy afterward. 2WAY edges bundle permissions, hop limits, and revocation behavior, so they carry governed capability rather than social proof. When a node withdraws an edge, reach shrinks immediately according to the recorded degree limits, not according to convention.

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

Because 2WAY is local-first, most defenses fire before the network sees anything. Every write proposal travels the same Service → Graph → Storage path, and each hop rejects malformed or abusive input cheaply:
- **Interface layer**: Services expose narrow, typed endpoints, publish cost hints, and throttle callers before domain work begins.
- **Auth and Key Managers**: Key verification and OperationContext construction confirm signatures and enrollment before any proposal is considered.
- **Schema Manager**: Structural validation kills malformed payloads without touching application logic.
- **ACL Manager**: Capability checks run before mutations, so unauthorized traffic never triggers heavy computation.
- **Graph Manager**: Deterministic ordering and ancestry checks discard duplicates and conflicting writes early.
- **State Manager**: Sync windows limit how much history a peer can demand, stopping replay floods.
- **Storage Manager**: Append-only commits happen last, after every other manager consents, so disk I/O cannot be weaponized.
Because each manager fails closed, an attacker must bypass multiple deterministic gates just to reach durable state.

Those local defenses keep most abuse from ever touching the network layer, but 2WAY still assumes attackers keep trying from across the wire. To contain them, the Network Manager's Bastion Engine receives each inbound or outbound handshake and immediately consults the DoS Guard Manager for an `allow`, `deny`, or `require_challenge` directive. Bastion and the DoS Guard Manager operate as a single admission loop: transport traffic stays in the holding area while the DoS Guard Manager evaluates telemetry and policy, and Bastion does not move the session forward without that decision. Only after the handshake clears this joint gate does Network Manager's Incoming and Outgoing Engine pair move envelopes between peers. Nothing expensive (schema checks, ACL evaluation, ordering, or storage) runs until that cheap admission filter succeeds.

The DoS Guard Manager applies multiple defenses before puzzles ever appear:
- **Admission gating**: Each connection gets one decision (`allow`, `deny`, or `require_challenge`) and anything but `allow` keeps the session outside the trusted surfaces. The Bastion Engine never proceeds without that verdict.
- **Rate and burst limits**: Global caps, per identity budgets, and anonymous source heuristics throttle message rates, concurrent sessions, and outstanding challenges. Limits are configured through the `dos.*` namespace and enforced deterministically.
- **Telemetry driven posture**: Network Manager streams byte counts, message rates, transport type, and resource pressure. The DoS Guard Manager biases toward denial when telemetry is missing or shows spikes, so abusive floods die at the edge rather than reaching Graph or Storage.
- **Health-aware throttling**: When Health Manager marks the node `not_ready`, the DoS Guard Manager automatically raises the admission bar or shuts off new handshakes, preventing compromised subsystems from being overwhelmed.
- **Fail-closed defaults**: Loss of configuration, Key Manager seeds, or internal capacity translates into denial of new sessions while existing admitted links drain safely.

Only after those fast checks succeed does the DoS Guard Manager fall back to puzzles. Borrowing the "New Client Puzzle Outsourcing Techniques for DoS Resistance" approach from Ari Juels et al., it shifts work to the requester whenever telemetry, policy, or Health Manager signals still show strain. Every puzzle includes a unique `challenge_id`, opaque payload, context binding, expiration, and algorithm selector. Network Manager only relays the bytes. The DoS Guard Manager records success and failure per peer, per anonymous source, and across the node, so abusive senders see difficulty rise steadily and only see relief after they behave. Proofs expire fast, cannot be replayed on other connections, and take far more effort to solve than to verify, which keeps defenders cool while attackers burn CPU.

The telemetry and policy loop keeps puzzles adaptive instead of static throttles:
- **Telemetry-driven escalation**: Transport byte counts, message rates, and resource pressure feed the DoS Guard Manager's admission logic. Crossing configured `dos.*` limits raises puzzle cost or triggers a deny, and missing telemetry defaults to `require_challenge`.
- **Health-aware gating**: When Health Manager reports `not_ready`, the DoS Guard Manager raises difficulty or stops admitting traffic so the node never accepts work it cannot finish safely.
- **Config-bound ceilings**: Config Manager sets minimum and maximum difficulty, limits on outstanding puzzles, and decay periods, so puzzle outsourcing stays bounded and predictable across builds.

Because untrusted traffic never leaves the shallow bastion zone until puzzles (if any) and crypto checks pass, abusive bursts die at the edge. Each node enforces these DoS Guard Manager rules on its own device and fails closed if the manager is unavailable, so a compromised or overloaded peer might lose connectivity, but it cannot drag honest nodes into storms or force them to redo work just by shouting louder.

---

## 13. Failure behavior

2WAY assumes things will go wrong. Keys get stolen, devices crash mid-write, peers disagree, or malicious inputs flood a node. The system fails closed instead of guessing what the operator intended.

Failure handling happens at multiple layers:

- **Protocol gatekeeping**: Graph Manager enforces object-model invariants before Schema Manager or ACL Manager see the request. Invalid envelopes are dropped, a rejection reason is logged, and nothing touches Storage Manager.
- **Authority pipeline**: Schema Manager, ACL Manager, and Graph Manager run deterministically with the supplied `OperationContext`. Any disagreement (missing schema, revoked capability, forked ancestry) returns a hard error that every peer will hit when replaying the same input.
- **Transport boundary**: Network and DoS Guard Managers refuse traffic they cannot attribute, rate-limit, or puzzle-gate. Connections fail fast rather than letting junk flow toward storage.

When a rule is violated (schema mismatch, missing capability, conflicting ordering), the input is rejected before it touches durable state. No speculative writes remain. Each write still travels the same serialized path, so local integrity holds even when the app above it is compromised.

Operation continues with reduced scope. Nodes quarantine the faulty identity, mark incomplete state as suspect, and keep serving peers whose histories remain intact. Isolation beats availability: it is better to drop a misbehaving connection than to corrupt the graph. Health Manager and DoS Guard Manager cooperate to block new work if liveness or telemetry sinks, so overload becomes back-pressure, not inconsistent state.

Recovery is explicit and auditable. Administrators or applications craft corrective actions (revocations, replays, migrations, repairs) that pass the same validation pipeline as any other write. There is no hidden admin override or silent reconciliation loop. If a fix cannot be encoded as a normal mutation, it does not happen.

Different failure classes map to targeted containment strategies:

- **Node or manager crash**: Storage Manager's append-only log lets the node replay accepted history after restart. Managers initialize independently, and any manager that cannot load reports `not_ready`, which keeps Network Manager from admitting fresh work until the fault clears.
- **Divergent histories**: Graph Manager refuses to advance `global_seq` if ancestry is missing. State Manager requests the missing range, replays it deterministically, and only then resumes sync. Peers never speculate about intent; they insist on ordered, signed history.
- **Key compromise or revocation**: Key Manager replaces trust roots only via explicit graph mutations (revocations, recovery flows). Once a revocation lands, ACL Manager removes the capability immediately because authorization decisions derive from recorded edges, not cached sessions.
- **Storage corruption**: Checksums and parent pointers make tampering or disk errors obvious. A corrupted log segment fails validation and the node stops processing until the operator restores from a trusted snapshot. Partial data never leaks upward because Graph Manager refuses to commit on inconsistent storage.
- **Unbounded input or spam**: Network Manager, DoS Guard Manager, and ACL Manager can independently cut a peer off. The system prefers deliberate disconnects over degraded correctness, so abusive sessions see puzzles escalate to denial long before they can saturate CPU.

Because every mitigation is itself part of the ordered, signed record, auditors can see what failed, what was rejected, what was quarantined, and how it was repaired. Nodes never guess or silently heal; they either prove a fact in the graph or refuse the action.

---

## 14. What the system guarantees

2WAY makes a small set of structural promises. They are narrow on purpose so anyone can audit whether they hold and so multiple implementations can ship without reinterpretation.

* **Identity-bound authorship**: Every mutation carries the public key and device lineage that produced it. Key Manager owns signing keys, Graph Manager refuses unsigned data, and replaying history shows exactly who authored each fact. No component may edit an event after the signature lands.
* **Append-only, tamper-evident history**: Storage Manager writes ordered logs with parent references and durable digests. Peers can replay another node's history, verify each hash chain, and detect any attempt to delete, reorder, or silently rewrite data. Recovery never relies on a hidden database or trusted operator.
* **Deterministic validation and ordering**: Schema Manager, ACL Manager, and Graph Manager run in a fixed order on every node. Given the same inputs, they either all accept or all reject. Timing, network jitter, or topology changes cannot change the outcome, so peers converge without coordination tricks.
* **Structural application isolation**: Applications subscribe to the same ordered feed, but they can influence only the graph segments they own or that were explicitly delegated to them. Cross-app writes require recorded delegation edges; there are no backdoors or config overrides that let UI code trespass.
* **Explicit authority delegation**: Capabilities originate inside the graph. Permissions cannot be implied by hostname, environment, or out-of-band agreements. ACL Manager evaluates only recorded edges, so every privilege jump is visible, auditable, and revocable.
* **Fail-closed, progressive failure**: Missing context, conflicting data, or ambiguous authority leads to rejection before storage changes. Health and DoS Guard Managers cut load when the system falters, so failure reduces scope instead of corrupting history. Recovery actions use the same mutation pipeline, leaving an audit trail.

Because these guarantees live in structure, they are testable, auditable, and portable across implementations. If an implementation cannot demonstrate each property under its supported conditions, it is out of spec regardless of performance or UX polish.

---


## 15. What the system enables but does not define

2WAY locks down structure but leaves meaning up to the people who use it. It makes sure identities, permissions, and history stay consistent, yet it never dictates why a relationship exists or what an application should do with the facts. Communities, not the protocol, decide how those facts matter.

Because the object model, validation rules, and sync process are neutral, different groups can read the same data and reach their own conclusions. A social app, a supply-chain network, or a city archive all plug into the same guardrails. Years later someone else can replay that history, build a new tool, and learn something the original authors did not plan for.

### What this unlocks

- **Trust networks that fit the community**: Groups can model endorsements, blocks, referrals, or sponsorships without relying on one global authority. Each community chooses how far trust travels.
- **Multiple reputation views**: Marketplaces, moderators, and auditors can each score the same identities in their own way while sharing the same facts underneath.
- **Governance as data**: Votes, approvals, vetoes, and appeals become ordered events. Anyone can audit the process or move it into a new tool without losing history.
- **Programmable incentives**: Credits, rates, access quotas, or staking rules live in the graph. Changing an economy means changing data, not migrating accounts.
- **Flexible privacy**: Apps choose what to reveal. Payloads can stay encrypted, expose only summaries, or sync inside private domains while still benefiting from shared ordering and authorship.
- **Many ways to interact**: Command-line tools, automation, mobile apps, and archival readers all watch the same feed but present it differently. A log captured offline in a field tool can be reviewed later in a dashboard with no conversion.
- **Easy collaboration between apps**: Separate products can agree on schemas or delegation rules and immediately work together because identity and access are already enforced below them. Customers keep their history and hand out scope as needed.
- **Records that survive vendors**: Cultural archives, civic ledgers, research notes, or legal proofs stay verifiable even if the original app disappears. New layers like translation, annotation, or compliance can sit on top without rewriting the past.

### What people can expect

- **Developers** describe schemas, constraints, and UX. They inherit identity, ordering, conflict handling, and durability, so they focus on their domain instead of rebuilding plumbing. Different clients can implement the same spec and still work together.
- **Operators and institutions** get reliable coordination. They can prove where data came from, trace influence, or revoke authority without calling every participant, and they can run offline without losing integrity.
- **End users** keep their data, context, and delegations even if a vendor shuts down. They can swap interfaces, automate tasks locally, and rebuild trust links after an outage because no single backend controls their history.

Structure is guaranteed; meaning stays open. When the specification holds, software authors describe intent, communities encode their norms in data, and users move across tools without having to trust any one operator by default.

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

Representative umbrella categories include web, mobile, desktop, and embedded apps that need deterministic sync; messaging or shared workspaces that need provenance; distributed identity stacks; supply-chain coordination; regulated industries; offline-first meshes; and critical infrastructure that refuses silent overrides. The examples below show how the shared graph and manager pipeline make ambitious designs possible without recreating a backend per domain.

Teams in these spaces gain:

- **Predictable compliance** because append-only logs, explicit delegations, and deterministic validation map cleanly to regulatory controls.
- **Faster multi-party integrations** once schemas and capabilities align, since no bespoke backend trust deal is required.
- **User-facing empowerment** where auditing, recovery, and delegation can ship as first-class UX because the substrate already enforces them.

### 17.1 Messaging and chat

Messaging maps neatly to graph primitives. Conversations become `Parent` objects, participants are membership `Edge`s, individual messages are `Attribute` objects, and an `ACL` defines who may read or write. That layout is illustrative, not prescriptive; developers can model conversations, threads, or channels however their UX demands as long as the schema honors the object model.

Each outbound message is a proposed mutation handled by Graph Manager. Graph Manager confirms that targets exist, references are well formed, and ordering constraints hold. ACL Manager evaluates the conversation ACL using the author identity that Auth Manager resolved, and once the write commits locally, State Manager coordinates replication while Network Manager offers it to peers. Because this pipeline runs locally and cannot be bypassed, malicious peers cannot inject unauthorized traffic or reorder history, offline writers keep working, and applications can focus on presentation, end-to-end encryption layered above the substrate, and retention policy instead of rebuilding the stack.

### 17.2 Social media and publishing

Social feeds or community tools can express their data as identities, follow or subscription relationships, posts, reactions, and moderation signals. Developers might encode follows as `Edge`s, posts or threads as `Parent`s, content bodies and timestamps as `Attribute`s, reactions or trust marks as `Rating`s, and visibility rules as `ACL`s. The protocol never mandates shape; it only requires that each fact obey the shared vocabulary.

Centralized networks enforce reach because they own the graph and policy. Many decentralized attempts drop backends but also drop enforceable structure, so spam and moderation stalemates dominate. 2WAY sits between these extremes. Distribution and visibility come from explicit data (`ACL`s, relationship `Edge`s, and ACL Manager evaluation) rather than from a hidden service. Developers can use degrees of separation to limit unsolicited reach. Moderation becomes data: attaching `Rating` or moderation `Attribute` objects records outcomes as ordered mutations that any app can interpret while still trusting authorship and validity.

### 17.3 Markets and exchange of goods and services

A marketplace can represent listings, offers, contracts, and reputation entirely within the graph: `Parent` objects for listings or contracts, `Attribute`s for terms and prices, `Edge`s for participant roles, `Rating`s for feedback, and `ACL`s to bound who may advance a contract state. Centralized markets simplify disputes by acting as arbiters, while fully peer-to-peer systems often lack a shared notion of contract progression.

2WAY enables a middle path by treating each contract as a state machine encoded in graph objects. Every transition is a mutation that Graph Manager validates and orders after ACL Manager authorizes it. History stays signed and replayable, so multiple market interfaces can coexist, compete on UX or fees, and still rely on the same canonical data. The substrate does not enforce payments or delivery; it ensures that only authorized transitions happen and that they land in an ordered, durable log that State Manager and Network Manager relay to peers.

### 17.4 Marketplace-dependent applications

Many services rely on market-like coordination without being markets themselves. Ride-hailing, delivery, and local services involve offers, acceptances, and completions that benefit from enforceable identity and ordering even when central dispatch disappears.

#### Ride-hailing and drivers

Drivers, riders, availability, trip requests, offers, and completion events become explicit graph objects. Trips can be `Parent`s, location and schedule data can live in typed `Attribute`s, participant responsibilities are `Edge`s, and `ACL`s define who may accept or close a ride. Centralized dispatch works because a backend observes everything; decentralized broadcast systems drown in spam. On 2WAY, reach stays bounded: relationship `Edge`s, geographic attributes, or policy rules evaluated by ACL Manager determine who sees a trip. Accepting and closing a ride are ordered mutations, so both parties can verify the sequence, and offline work remains possible because nodes queue trusted mutations until State Manager distributes them through Network Manager.

#### Food delivery and dispatch

Merchants and dispatch roles extend the same graph. Dispatch authority becomes a delegated capability encoded in `ACL`s and relationship objects rather than an implicit backend privilege. If a dispatcher or SaaS integration disappears, the system narrows gracefully. Couriers keep working against local state, and later reconciliation orchestrated by State Manager restores global consistency without a panic cutover.

#### Goods and local services

Local services, repairs, rentals, or classifieds rely on long-lived identity and auditability. Centralized platforms often delete trust history when they shut down or pivot. In 2WAY, identity and contract history persist independent of a single interface, so neighborhood services survive platform churn while keeping verifiable audit trails.

### 17.5 Key revocation and recovery workflows

Keys, devices, and identity bindings are graph objects, so revocation is not a privileged administrative action. Changing which keys Key Manager trusts is just another ordered mutation that travels through Graph, ACL, and State Managers. Recovery workflows can also live in data: `Edge`s and `ACL`s can require approvals from designated recovery identities before a new device key becomes valid. The substrate does not dictate policy, but once a policy is described, it enforces ordering, authorization, and auditability because every state change uses the same pipeline.

### 17.6 Verifying binaries and software supply chains

2WAY works as an identity and history layer for software distribution. Releases can be signed `Parent` objects with `Attribute`s storing hashes, metadata, or bills of materials, while publisher hierarchies are relationship `Edge`s. Trust in publishers is expressed explicitly in the graph, so installation becomes a local policy decision driven by verifiable state, not DNS or a hosted repository. If a signing key is compromised, a revocation mutation instructs peers to distrust it, and thanks to Graph Manager and State Manager preserving ordered, tamper-evident history, clients observe and enforce the change without waiting for a central takedown.

### 17.7 Device trust, enrollment, and compliance

Devices can be modeled as objects with attributes describing capabilities, compliance status, and desired posture. Policies are data enforced locally by ACL Manager rather than by a continuously available management server. Revocation becomes an ordered event, auditability comes from reading signed history, and organizations gain a model suited to environments where availability and inspection matter more than remote convenience.

### 17.8 Multi-party coordination and governance

Because 2WAY enforces ordered, authorized transitions, it supports workflows that need multiple approvals. Shared `Parent` objects represent the subject of governance, delegated capabilities live in `ACL`s, and each approval is an ordered mutation recorded by State Manager. The system never dictates governance rules; it provides primitives so communities can encode quorums, vetoes, or escalation paths as auditable workflows enforced by the substrate instead of by tradition.

### 17.9 Long-lived records and audit trails

Any workflow that values durable records benefits from identity-bound authorship, ordered history, and fail-closed enforcement. Records become graph objects with explicit ownership and immutable ancestry. Unlike centralized audit systems, correctness does not depend on trusting an operator, and unlike many peer-to-peer networks, ordering and authorization are enforced rather than heuristic. Even if an original application disappears, records remain verifiable to anyone who can replay history.

### 17.10 What ties these examples together

These examples are illustrative. They show that once identity, permissions, ordering, validation, and denial-of-service controls live below the application layer (in Auth, Graph, ACL, State, Network, and DoS Guard Managers), whole classes of workloads become feasible without trusted backends. Centralized systems concentrate authority; many peer-to-peer systems lack structure. 2WAY works because every node enforces the same structure locally while letting developers decide how to model meaning on top.

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
