



# 2WAY design repository (extended README)

2WAY is a local-first, peer-to-peer, open source protocol and backend. It provides decentralized applications with device-level identity, permissions, sync, and audit guarantees so collaboration can span disconnected devices, untrusted networks, and independent operators without delegating authority to a central service.

Every participant keeps their cryptographic keys, append-only log, permission graph, and copy of shared state. The protocol synchronizes these structures deterministically, so each device accepts or rejects mutations the same way, even after long partitions. Because every write carries verifiable ancestry and capability proofs, invalid or replayed input is discarded before it reaches durable storage and the blast radius of a compromise stays bound to the affected identity.

These guarantees make it practical to offer features such as shared history that survives data-center failures, per-tenant policy without forked deployments, provenance-aware media and messaging, verifiable supply-chain attestations, and governance workflows where no operator can rewrite decisions. The same structure applies to everyday use cases: transportation networks where drivers and riders keep their own receipts, marketplaces where buyers and sellers prove inventory without handing control to a platform, private messaging that still validates authorship, or social feeds that carry embedded provenance so false posts cannot spread without exposure. Applications define their schemas and domain logic on top of the substrate while the protocol enforces ordering, storage, and influence limits.

This repository is the normative design set for the proof of concept. It records the guarantees, boundaries, and threat model that every implementation must follow so separate builds can interoperate safely. Use it to evaluate how these invariants enable durable messaging, marketplaces, compliance tooling, or any other multi-party system that needs trust without surrendering control.

In 2WAY, application authors define schemas, optional domain logic, and user interfaces. The protocol and backend supply identity, storage, access control, cryptography, and peer-to-peer sync so developers can focus on the experiences they present to users.

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
* [8. One pipeline for reads and writes](#8-one-pipeline-for-reads-and-writes)
* [9. Security model and threat framing](#9-security-model-and-threat-framing)
* [10. Structural impossibility](#10-structural-impossibility)
* [11. Degrees of separation and influence limits](#11-degrees-of-separation-and-influence-limits)
* [12. Sybil resistance through structure](#12-sybil-resistance-through-structure)
* [13. Denial-of-service containment](#13-denial-of-service-containment)
* [14. Failure behavior](#14-failure-behavior)
* [15. What the system guarantees](#15-what-the-system-guarantees)
* [16. What the system enables but does not define](#16-what-the-system-enables-but-does-not-define)
* [17. Application model for developers](#17-application-model-for-developers)
* [18. Application domains](#18-application-domains)
  * [18.1 Messaging and chat](#181-messaging-and-chat)
  * [18.2 Social media and publishing](#182-social-media-and-publishing)
  * [18.3 Markets and exchange of goods and services](#183-markets-and-exchange-of-goods-and-services)
  * [18.4 Marketplace-dependent applications](#184-marketplace-dependent-applications)
  * [18.5 Key revocation and recovery workflows](#185-key-revocation-and-recovery-workflows)
  * [18.6 Verifying binaries and software supply chains](#186-verifying-binaries-and-software-supply-chains)
  * [18.7 Device trust, enrollment, and compliance](#187-device-trust-enrollment-and-compliance)
  * [18.8 Multi-party coordination and governance](#188-multi-party-coordination-and-governance)
  * [18.9 Long-lived records and audit trails](#189-long-lived-records-and-audit-trails)
  * [18.10 What ties these examples together](#1810-what-ties-these-examples-together)
* [19. Conformance](#19-conformance)
* [20. Scope boundary and status](#20-scope-boundary-and-status)
* [21. Acknowledgments](#21-acknowledgments)
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

This repository is the source of record for the 2WAY proof of concept. Normative specifications live under `specs/` and define scope, invariants, architecture, data, security, flows, and acceptance criteria so independent implementations can be judged against the same rules. `docs-build/` is a non-normative build pack (requirements ledger, build plan, traceability) that must stay aligned with the specs. In conflicts, the specs win and any exception must be recorded as an ADR in `specs/09-decisions`.

Lower-numbered spec directories hold higher authority: scope constrains protocol, protocol constrains architecture, and so on.

| Folder | Authority focus | Typical questions |
| --- | --- | --- |
| `specs/00-scope` | System boundary and vocabulary | What is in or out of scope? Which assumptions are mandatory? |
| `specs/01-protocol` | Wire format and invariants | How are identities, objects, and signatures encoded? |
| `specs/02-architecture` | Runtime composition | Which managers exist and how do they interact? |
| `specs/03-data` | Persistence model | How is state stored, versioned, and migrated locally? |
| `specs/04-interfaces` | APIs and event surfaces | How do components and applications integrate? |
| `specs/05-security` | Threat framing and controls | Which adversaries are assumed and how are they contained? |
| `specs/06-flows` | End-to-end operations | How do bootstrap, sync, and recovery behave? |
| `specs/07-poc` | Execution scope | What must the proof of concept build, demo, and test? |
| `specs/08-testing` | Testing and conformance | What test categories and conformance rules apply? |
| `specs/09-decisions` | Recorded trade-offs | Which ADRs modify previous rules and why? |
| `specs/10-appendix` / `specs/11-examples` | Reference material | What supporting context or illustrations exist? |
| `docs-build` | Build planning (non-normative) | How are requirements traced and implemented? |

Meta specifications and diagrams live under `specs/10-appendix/meta` and `specs/10-appendix/diagrams`. Glossary, reference config, and open questions live in `specs/10-appendix`.

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
+---------------------------------------------------+
|                  Applications                     |
|  - Interpret ordered state                        |
|  - Run UI and domain logic                        |
|  - Compose proposals                              |
|  Cannot bypass -> substrate validation, ordering, |
|  authority rules                                  |
+---------------------------------------------------+
                      |
                      v
+---------------------------------------------------+
|                2WAY Substrate                     |
|  - Identity, permissions, ordering                |
|  - Graph state, sync, structural guards           |
|  Cannot bypass -> storage guarantees or           |
|  transport constraints                            |
+---------------------------------------------------+
                      |
                      v
+---------------------------------------------------+
|            Storage and Transport                  |
|  - Local persistence and networking               |
|  - Append-only history, peer exchange             |
|  Cannot bypass -> local substrate authority or    |
|  per-device policy                                |
+---------------------------------------------------+
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

Every proposal follows the lifecycle described in `specs/01-protocol/00-protocol-overview.md` and enforced by the managers named in `specs/02-architecture/01-component-model.md`:

1. A service obtains an immutable `OperationContext` (Auth Manager for local requests; State Manager for remote sync).
2. Graph Manager performs structural validation first, rejecting malformed envelopes before any other work occurs.
3. Schema Manager validates references, types, and domain rules according to the active schema set.
4. ACL Manager evaluates permissions using the supplied `OperationContext` and graph state; authorization must succeed before any write proceeds.
5. Graph Manager serializes the write, assigns a monotonic `global_seq`, commits through Storage Manager, and emits post-commit events and logs. State Manager records the new sequence for sync.

If any step fails (missing reference, stale capability, conflicting order), the proposal never hits durable state. Rejection is deterministic, so correct nodes converge without negotiating or trusting the network.

---

## 6. Protocol object model

`specs/01-protocol/02-object-model.md` defines the grammar of the shared graph. Facts fall into five canonical categories: Parent, Attribute, Edge, Rating, and ACL (ACL structures are encoded as constrained Parent plus Attribute records). Parent, Attribute, Edge, and Rating records carry the shared metadata set (`app_id`, `id`, `type_id`, `owner_identity`, `global_seq`, `sync_flags`) so any peer can replay history, verify authorship, and enforce ordering without a coordinator or custom storage tricks.

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

If the object model defines what can be stored, `specs/02-architecture/01-component-model.md` defines who can touch it. The backend is a long-lived process made of singleton managers (the protocol kernel) plus optional services layered on top. Each manager owns one domain, exposes a narrow API, and refuses to work outside that charter. Services orchestrate workflows but never bypass managers or mutate state on their own.

### Manager roster and responsibilities

Each manager is authoritative for its slice of behavior. Together they form the write path every mutation must follow:

- **Config Manager** loads `.env` plus SQLite settings, validates them, and publishes immutable snapshots; no other component reads configuration directly.
- **Storage Manager** is the sole interface to durable storage (SQLite in the PoC). All reads, writes, transactions, migrations, and sequencing go through it.
- **Key Manager** owns node, identity, and app key lifecycle, signing, and decryption; private keys never leave this manager.
- **Auth Manager** validates frontend authentication, establishes sessions, and constructs local `OperationContext`.
- **Schema Manager** stores schema definitions, resolves type IDs, and validates proposed mutations.
- **ACL Manager** evaluates permissions using `OperationContext` and graph data and returns allow or deny decisions.
- **Graph Manager** validates envelopes, serializes mutations, coordinates reads, assigns `global_seq`, and commits accepted writes via Storage Manager.
- **App Manager** registers apps, assigns app identities, and wires app services.
- **State Manager** coordinates sync domains, ordering checks, and remote `OperationContext` construction.
- **Network Manager** owns transport surfaces, admission, signature verification, and encryption/decryption, then hands verified packages to State Manager.
- **Event Manager** publishes internal events for services and tooling after commit.
- **Log Manager** emits structured audit and diagnostic logs.
- **Health Manager** tracks liveness and readiness across managers.
- **DoS Guard Manager** issues admission decisions, throttling, and client puzzles.

These rules are structural. Graph mutations that skip Graph Manager, direct SQLite access without Storage Manager, or permission checks outside ACL Manager violate the specification.

### Services and OperationContext

System services and per-app services translate user intent into manager calls:

1. Accept API or automation input (always untrusted).
2. Build an immutable `OperationContext` with caller identity, app scope, requested capability, and tracing data (Auth Manager for local requests; State Manager for remote sync; automation contexts follow the same rules).
3. Call managers only through their public interfaces (Graph for writes/reads, Schema for validation, ACL for authorization, Storage for permitted reads or derived caches, Event for publication, Log for audit).

Services never talk to other services directly without an explicit interface contract, never read private keys, and never persist authoritative data on their own. App services are sandboxed to their app domain; removing an app simply unregisters its services without touching the kernel.

PoC system services are defined in `specs/02-architecture/services-and-apps/02-system-services.md` (Setup Service, Identity Service, Sync Service, Admin Service). They are always present, app services are optional, and both are untrusted relative to manager invariants.

### Trust boundaries and failure handling

Managers trust only validated inputs from peer managers. Services trust manager outputs but treat everything else as untrusted. Local entrypoints rely on Auth Manager to bind identity into `OperationContext`. Remote entrypoints rely on DoS Guard and Network Manager admission followed by State Manager construction of a remote `OperationContext`. When a manager rejects a request (invalid structure, failed ACL, storage fault), no partial state remains. Storage Manager rolls back the transaction, Log Manager records the reason, and the caller receives a deterministic error. Canonical error shapes and transport mappings are defined in [04-error-model.md](specs/04-interfaces/04-error-model.md).

Every write flows `Service -> Graph Manager -> Storage Manager`, with Schema and ACL checks in order. DoS Guard and Network Manager verification apply at the network boundary, not inside local write processing. There are no parallel authority paths to forget. Changing services does not weaken guarantees; changing a manager requires an ADR because it rewires system invariants. This strict component model keeps implementations consistent even if runtime packaging differs.

---

## 8. One pipeline for reads and writes

Writes and reads originate from different places (local services, remote peers, API calls), and the protocol treats that context explicitly. Local authorship starts with frontend credentials, while remote sync begins with signed packages that reference peer ids and sequence ranges. Even so, once input reaches the kernel, every path uses the same managers in the same order so the guarantees remain identical. The flows below summarize the normative behavior described in `specs/01-protocol/00-protocol-overview.md` and the manager responsibilities in `specs/02-architecture/01-component-model.md`.

### Local authorship

1. **Authenticate and scope**: A frontend request hits Auth Manager, which verifies the user or device and produces an immutable `OperationContext` that states who is acting and for which app.
2. **Describe the change**: Services bundle the desired Parents, Attributes, Edges, Ratings, or ACL updates into a graph message envelope. Every write uses that envelope format.
3. **Check readiness**: Health Manager readiness gates admission of new work. Interface-specific limits may reject requests before expensive validation.
4. **Validate structure**: Graph Manager checks the envelope for missing selectors, wrong ancestry, or cross-app references and drops anything that fails.
5. **Validate schemas**: Schema Manager confirms the data belongs to the right app, uses the right types, and meets schema rules.
6. **Authorize**: ACL Manager decides whether the actor described in the `OperationContext` is allowed to make the change.
7. **Commit**: Graph Manager assigns the next `global_seq`, Storage Manager writes the change atomically, Event Manager emits post-commit events, and Log Manager records the outcome.
8. **Prep for sync**: State Manager notes the new sequence so other peers can fetch it later.

### Remote synchronization

1. **Admit the session**: Network Manager accepts the package only after Bastion admission and DoS Guard Manager directives (`allow`, `deny`, `require_challenge`).
2. **Verify and bind**: Network Manager verifies the sync package signature, decrypts when required, and binds the sender identity to the package.
3. **Check ordering**: State Manager validates `sync_domain`, `from_seq`, and `to_seq` against sync state, then constructs a remote `OperationContext`.
4. **Run the same pipeline**: Each graph message envelope runs through the same Graph, Schema, and ACL checks as a local write. Remote never means trusted.
5. **Store or reject**: Accepted envelopes get fresh `global_seq` numbers, Storage Manager commits them, and State Manager advances the peer cursor only after acceptance. Rejection leaves the cursor unchanged.

### Read path (local or remote callers)

1. **Identify the caller**: Reads start with Auth Manager so the system knows who is asking and which app they belong to. Remote peers receive data through sync packages, not ad-hoc read calls.
2. **Apply limits**: Health Manager readiness gates heavy reads and Graph Manager enforces bounded read budgets. Services may apply additional interface-level rate limits.
3. **Ask Graph Manager**: Services call Graph Manager read helpers. Graph Manager validates the request, consults ACL Manager for read authorization, and uses schema metadata to enforce boundaries.
4. **Let Storage Manager do the read**: Storage Manager executes the bounded query and returns immutable rows. Optional visibility filters (for example, rating-based suppression) happen after the read and never mutate state.
5. **Return with context**: Results include ordering markers such as `global_seq` or `snapshot_seq` so clients can align reads with history.

### Expressive and bounded queries

Graph reads are explicit and bounded. Clients submit a `GraphReadRequest` (see `specs/04-interfaces/03-internal-apis-between-components.md`) that declares the target kind, type keys, filters, limits, and optional snapshot bounds. Filters are schema-aware and constrained (attribute checks, rating thresholds, group membership, edge existence), and bounded traversals are limited by depth and node caps. In the PoC, degree filters are explicitly limited to the contact graph (`app.contacts`) and to degrees 0-3, so reach remains predictable and enforceable.

Because filters are part of the request, Graph Manager can validate them, ACL Manager can authorize them, and Storage Manager can execute them without ad hoc code paths. That yields deterministic results across nodes and makes it safe to build higher-level queries such as:

- "Contacts within two degrees who rated this parent above 4.0."
- "Records tagged with a schema-defined attribute and created within a time range."
- "Objects authored by members of a specific system group."

These examples are illustrative; the substrate enforces only the structural rules and authorization bounds the schema declares.

### Uniform guarantees

Reads and writes inherit the same posture: the caller must prove identity, ACL Manager must approve scope, Storage Manager is the only database surface, and responses always reflect accepted, replayable history. Any service or transport that attempts to skip a manager or mutate state directly is out of spec and must be rejected.

## 9. Security model and threat framing

2WAY assumes attackers reach every boundary, so the protocol, managers, and data model enforce the defense instead of checklists. Nodes never trust transport metadata, gossip, or local apps until the graph proves a key and capability exist.

### 9.1 Baseline posture

- No safe perimeter: every packet is untrusted. DoS Guard and Network Manager admit remote traffic before State Manager sees it, and Auth Manager gates local entrypoints.
- Identity equals recorded Parents plus keys. `OperationContext` always references that record; IPs, TLS info, or UI accounts do not matter.
- Managers fail closed. If Config, Schema, ACL, Graph, Storage, State, or DoS Guard is degraded, the node denies work and logs why.
- Offline nodes rejoin by replaying history under the same validation order, so downtime never skips checks.

### 9.2 Assets and boundaries

Graph data (Parents, Attributes, Edges, ACLs, Ratings) is append-only and written only by Graph + Storage after Schema and ACL approval. Keys and identities stay inside Key Manager; all private-key operations are centralized there. Network boundaries belong to DoS Guard and Network Manager; puzzles, signatures, and ordering checks block tampering or replay before State Manager sees the payload. Config snapshots are node-local and immutable, and no component reads `.env` or settings directly outside Config Manager. Log, Event, and Health managers form the observability plane, and selective sync plus ACL filtering determine what can leave the node.

### 9.3 Threats and claims

2WAY defends against remote attackers, Sybil floods, compromised peers, malicious app services, careless operators, hardware theft, hostile transports, and censorship attempts by keeping compromises local. Validation always runs structural -> schema -> ACL -> storage, and rejected envelopes never touch disk. Degree-of-separation limits and domain scoping prevent trust borrowing, DoS Guard sheds abusive traffic, and signed sync packages plus `global_seq` ordering block replay, reordering, or message forgery. Keys can be rotated or revoked by recording graph objects or ratings, and those revocations apply prospectively without rewriting history. Nodes can operate offline or without a central coordinator, so outages cannot force trust leaps. Every decision is recorded so investigations can replay what happened.

### 9.4 Privacy and selective sync

Privacy is enforced structurally. Sync domains are explicit and app-scoped, State Manager exports only eligible objects, and ACL visibility rules are enforced before any data leaves the node. Metadata is minimized to the fields required for validation and sync, and local-only fields never leave the device. See `specs/05-security/09-privacy-selective-sync-and-domain-scoping.md`.

### 9.5 Limits and operator duties

The platform does not protect against rooted hosts, broken hypervisors, or side-channel attacks. Metadata stays visible to the parties that participate in that slice of the graph, and end-to-end encryption of payloads is an application choice. Unsafe defaults (auto-accepting everyone, blanket delegates) can reintroduce risk, so schema and ACL changes deserve the same review as code. Regulatory tasks (retention, deletion, jurisdictional routing) remain with app owners.

### 9.6 Failure and recovery behavior

Missing configuration, schema mismatches, storage corruption, lost keys, or unavailable DoS Guard all trigger denial plus telemetry. Recovery means replaying trusted history while the same validation rules run; revocations and key rotation are ordinary graph mutations, and offline peers catch up through the append-only log. Backup and restore behaviors are defined in `specs/03-data/08-backup-restore-and-portability.md`. Keep Log/Event sinks healthy so these transitions remain visible.

---

## 10. Structural impossibility

2WAY encodes its rules so tightly that many unsafe actions have no valid execution path. If the graph lacks the required Parents, schema types, or ACL objects, the mutation is rejected before it can reach storage.

This structural approach covers:

* **Application isolation**: proposals cannot point at foreign state unless the graph already contains explicit delegation objects that allow it.
* **Access control enforcement**: capabilities and ACLs exist as graph objects and must be present before any write is authorized.
* **Ownership immutability**: `owner_identity` and `type_id` cannot be rewritten, so authority does not drift over time.
* **State ordering guarantees**: envelopes are applied atomically and ordered deterministically; retroactive edits have nowhere to land.

Compromise is contained to the authority recorded in the graph. A stolen key can act only within its recorded scope; it cannot bypass schema, ACL, or app boundaries or rewrite accepted history. Rejection is deterministic and leaves no partial state.

---

## 11. Degrees of separation and influence limits

Authority in 2WAY is local, not global. Every key only sees what its graph has accepted and replayed. Anything beyond that view requires explicit edges that describe direction, ownership, and purpose so policies can decide who may act and how far their influence can travel. Degree-of-separation limits are schema-declared, graph-derived constraints evaluated by ACL Manager, not UI heuristics.

Practical effects:

* **Zeroth-degree anchoring**: own data is visible by default, everything else requires explicit edges or ACLs.
* **Explicit expansion**: gaining reach means creating edges that every hop signs off on, leaving audit trails that can be revoked.
* **Bounded visibility**: schemas can require degree limits, membership edges, or trust thresholds before reads or writes are allowed.
* **Deterministic enforcement**: Graph Manager and ACL Manager enforce the same limits on every node; remote peers cannot widen reach by transport tricks.
* **PoC constraints**: degree filters exposed via `GraphReadRequest` are limited to the contact graph (`app.contacts`) and to degrees 0-3, keeping reach predictable.

These guardrails keep trust from spreading on its own, limit unsolicited reach, and make relationships inspectable. Degree enforcement also feeds Sybil resistance (see Section 12) by forcing explicit, revocable paths rather than opportunistic broadcast.

This approach is not the PGP Web of Trust. PGP attestations mostly claim that someone saw another key, and each client invents its own policy afterward. 2WAY edges bundle permissions and revocation behavior, so they carry governed capability rather than social proof. When a node withdraws an edge, reach shrinks immediately according to recorded limits.

---

## 12. Sybil resistance through structure

Perfect Sybil prevention is unrealistic for open networks, so 2WAY makes identity floods unproductive. Every actor must earn reach through visible, consented relationships.

Structural guardrails:

* **Anchoring required**: new keys have no influence until they form edges with trusted anchors. Without that path, their proposals are rejected or never authorized.
* **Application-scoped trust**: reputation lives in the shared graph but is interpreted per application, so standing in one domain grants nothing elsewhere.
* **Explicit delegation**: edges that convey authority must be recorded by both parties, include bounded capabilities, and stay revocable.
* **Degree limits**: schema-declared degree constraints block unsolicited fan-out. Nodes that never opted into a path will never see its traffic.
* **Cost matches intent**: forming real relationships requires effort (introductions, shared history, mutual acceptance), making it expensive for attackers to scale.

Attackers can still generate packets, but without anchors, recognized capabilities, and degree-limited paths, they cannot mutate state, borrow reputation, or force attention.

---

## 13. Denial-of-service containment

2WAY assumes abusive traffic and fails closed. Every write proposal travels the same `Service -> Graph Manager -> Storage Manager` path, and each hop rejects malformed input cheaply:

- **Interface layer**: endpoints validate inputs early and construct `OperationContext` through Auth Manager.
- **Graph Manager**: structural validation rejects malformed envelopes before schema or ACL work.
- **Schema Manager**: rejects invalid types or schema violations.
- **ACL Manager**: rejects unauthorized actions.
- **State Manager**: enforces sync windows and ordering for remote input.
- **Storage Manager**: commits last, after every other manager consents.

Remote traffic is gated at the network boundary. Network Manager's Bastion Engine holds unadmitted sessions and consults DoS Guard Manager for `allow`, `deny`, or `require_challenge`. Only after admission does Network Manager verify signatures, decrypt when required, and forward packages to State Manager. DoS Guard uses `dos.*` policy plus Health Manager signals; missing telemetry or degraded readiness raises difficulty or denies admission. DoS Guard unavailability results in deny to preserve fail-closed behavior.

Client puzzles are opaque to Network Manager and verified only by DoS Guard. Challenges include a `challenge_id`, expiration, context binding, and difficulty parameters. Failed or expired puzzles escalate difficulty or trigger denial. These controls keep abusive bursts at the edge and prevent resource exhaustion from reaching Graph or Storage.

---

## 14. Failure behavior

2WAY assumes things will go wrong. Keys get stolen, devices crash mid-write, peers disagree, or malicious inputs flood a node. The system fails closed instead of guessing what the operator intended.

Failure handling happens at multiple layers:

- **Protocol gatekeeping**: Graph Manager enforces object-model invariants before Schema Manager or ACL Manager see the request. Invalid envelopes are dropped, a rejection reason is logged, and nothing touches Storage Manager.
- **Authority pipeline**: Schema Manager, ACL Manager, and Graph Manager run deterministically with the supplied `OperationContext`. Any disagreement returns a hard error that every peer will hit when replaying the same input.
- **Transport boundary**: DoS Guard and Network Manager refuse traffic they cannot admit or verify. Sync state does not advance on rejection.

When a rule is violated (schema mismatch, missing capability, conflicting ordering), the input is rejected before it touches durable state. No speculative writes remain. Each write still travels the same serialized path, so local integrity holds even when the app above it is compromised.

Recovery is explicit and auditable. Administrators or applications craft corrective actions (revocations, replays, migrations, repairs) that pass the same validation pipeline as any other write. There is no hidden admin override or silent reconciliation loop. If a fix cannot be encoded as a normal mutation, it does not happen.

Different failure classes map to targeted containment strategies:

- **Node or manager crash**: Storage Manager's persisted state is authoritative. Managers restart, rebuild in-memory state, and Health Manager keeps admission closed until readiness returns.
- **Divergent histories**: State Manager enforces ordering and requests missing ranges. Nodes replay signed history rather than speculate about intent.
- **Key compromise or revocation**: Revocation is recorded as graph objects or ratings. ACL Manager enforces the change immediately because authorization derives from recorded edges, not cached sessions.
- **Storage corruption**: Invariant checks fail closed and the node stops processing until the operator restores from a trusted backup (see `specs/03-data/08-backup-restore-and-portability.md`).
- **Unbounded input or spam**: DoS Guard denies admission, Network Manager drops sessions, and ACL Manager rejects unauthorized operations long before disk writes.

Accepted mutations and rejection reasons remain visible through Log Manager and Event Manager, so auditors can replay what happened and operators can trace which rule failed. Nodes never guess or silently heal; they either prove a fact in the graph or refuse the action.

---

## 15. What the system guarantees

2WAY promises a grounded set of default behaviors. They stay small, testable, and tied to concrete managers so every implementation can be audited and every operator knows what the system delivers before any custom logic is added.

* **Every change names its author**: Each mutation records `owner_identity` bound to a graph identity. Sync packages are signed by node keys and verified before acceptance.
* **History is append-only and replayable**: Storage Manager persists ordered graph records with `global_seq`. Nodes replay accepted history to recover or audit; there is no rewrite or delete path.
* **Validation and ordering always match**: Schema Manager, ACL Manager, and Graph Manager run in the same order on every device. Give them the same inputs and they either all accept or all reject, regardless of latency, topology, or who connects first.
* **Schema and reference integrity never bend**: Graph Manager checks object-model rules first, then Schema Manager confirms that references exist, types match, and invariants hold. Malformed envelopes die before they touch storage.
* **Applications stay in their lane**: Every app reads the same feed but can only touch graph segments it owns or that someone delegated through recorded edges. Crossing boundaries requires those edges.
* **Delegation is provable and reversible**: Capabilities live entirely in the graph. ACL Manager honors only recorded edges, and revocation is another mutation with an audit trail.
* **Failures shut the door instead of corrupting data**: Missing context, stale parents, conflicting permissions, or health issues stop the write before it reaches storage. Failure shrinks the blast radius and leaves trusted history intact.
* **Sync and recovery use the same rules**: The facts that make a write acceptable are the same facts peers check when syncing. There are no special bootstrapping modes or one-time migration grants.
* **Local custody of identity and data is mandatory**: Every device stores its own keys, logs, and durable state. No central operator can pull privilege out from under a peer.
* **Decisions stay observable**: Log Manager records structured reasons for accept and reject paths, and Event Manager emits post-commit signals. Auditors can read why something failed and operators can alert on it.
* **Network admission stays bounded**: DoS Guard and Network Manager enforce admission, puzzles, and rate limits at the transport boundary, while Auth Manager gates local sessions. If health drops, the node stops admitting work rather than risking corruption.
* **Portability across implementations is enforced**: Because every guarantee is structural, the same ordered history will pass validation on any conformant build. Mixing runtimes, UI stacks, or storage backends does not weaken guarantees as long as each manager honors its contract.


If a build cannot prove each promise under its supported conditions, it is out of spec no matter how fast, convenient, or popular it may be.

---

## 16. What the system enables but does not define

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

## 17. Application model for developers

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

## 18. Application domains

2WAY fits workloads where trust, verifiability, and survivability matter more than peak throughput. Offline collaboration, multi-party workflows, and audit-heavy systems benefit because authority stays local, history is replayable, and policy boundaries remain explicit even as applications change. Adopting 2WAY means promising users that collaboration endures without a master server, provenance stays inspectable, and failure modes stay bounded no matter who operates the UI.

Representative umbrella categories include web, mobile, desktop, and embedded apps that need deterministic sync; messaging or shared workspaces that need provenance; distributed identity stacks; supply-chain coordination; regulated industries; offline-first meshes; and critical infrastructure that refuses silent overrides. The examples below show how the shared graph and manager pipeline make ambitious designs possible without recreating a backend per domain.

Teams in these spaces gain:

- **Predictable compliance** because append-only logs, explicit delegations, and deterministic validation map cleanly to regulatory controls.
- **Faster multi-party integrations** once schemas and capabilities align, since no bespoke backend trust deal is required.
- **User-facing empowerment** where auditing, recovery, and delegation can ship as first-class UX because the substrate already enforces them.

### 18.1 Messaging and chat

Messaging maps neatly to graph primitives. Conversations become `Parent` objects, participants are membership `Edge`s, individual messages are `Attribute` objects, and an `ACL` defines who may read or write. That layout is illustrative, not prescriptive; developers can model conversations, threads, or channels however their UX demands as long as the schema honors the object model.

Each outbound message is a proposed mutation handled by Graph Manager. Graph Manager confirms that targets exist, references are well formed, and ordering constraints hold. ACL Manager evaluates the conversation ACL using the author identity in the `OperationContext`, and once the write commits, State Manager coordinates replication while Network Manager offers it to peers. Because this pipeline runs locally and cannot be bypassed, malicious peers cannot inject unauthorized traffic or reorder history, offline writers keep working, and applications can focus on presentation, end-to-end encryption layered above the substrate, and retention policy instead of rebuilding the stack.

### 18.2 Social media and publishing

Social feeds or community tools can express their data as identities, follow or subscription relationships, posts, reactions, and moderation signals. Developers might encode follows as `Edge`s, posts or threads as `Parent`s, content bodies and timestamps as `Attribute`s, reactions or trust marks as `Rating`s, and visibility rules as `ACL`s. The protocol never mandates shape; it only requires that each fact obey the shared vocabulary.

Centralized networks enforce reach because they own the graph and policy. Many decentralized attempts drop backends but also drop enforceable structure, so spam and moderation stalemates dominate. 2WAY sits between these extremes. Distribution and visibility come from explicit data (`ACL`s, relationship `Edge`s, and ACL Manager evaluation) rather than from a hidden service. Developers can use degrees of separation to limit unsolicited reach. Moderation becomes data: attaching `Rating` or moderation `Attribute` objects records outcomes as ordered mutations that any app can interpret while still trusting authorship and validity.

### 18.3 Markets and exchange of goods and services

A marketplace can represent listings, offers, contracts, and reputation entirely within the graph: `Parent` objects for listings or contracts, `Attribute`s for terms and prices, `Edge`s for participant roles, `Rating`s for feedback, and `ACL`s to bound who may advance a contract state. Centralized markets simplify disputes by acting as arbiters, while fully peer-to-peer systems often lack a shared notion of contract progression.

2WAY enables a middle path by treating each contract as a state machine encoded in graph objects. Every transition is a mutation that Graph Manager validates and orders after ACL Manager authorizes it. History stays signed and replayable, so multiple market interfaces can coexist, compete on UX or fees, and still rely on the same canonical data. The substrate does not enforce payments or delivery; it ensures that only authorized transitions happen and that they land in an ordered, durable log that State Manager and Network Manager relay to peers.

### 18.4 Marketplace-dependent applications

Many services rely on market-like coordination without being markets themselves. Ride-hailing, delivery, and local services involve offers, acceptances, and completions that benefit from enforceable identity and ordering even when central dispatch disappears.

#### Ride-hailing and drivers

Drivers, riders, availability, trip requests, offers, and completion events become explicit graph objects. Trips can be `Parent`s, location and schedule data can live in typed `Attribute`s, participant responsibilities are `Edge`s, and `ACL`s define who may accept or close a ride. Centralized dispatch works because a backend observes everything; decentralized broadcast systems drown in spam. On 2WAY, reach stays bounded: relationship `Edge`s, geographic attributes, or policy rules evaluated by ACL Manager determine who sees a trip. Accepting and closing a ride are ordered mutations, so both parties can verify the sequence, and offline work remains possible because nodes queue trusted mutations until State Manager distributes them through Network Manager.

#### Food delivery and dispatch

Merchants and dispatch roles extend the same graph. Dispatch authority becomes a delegated capability encoded in `ACL`s and relationship objects rather than an implicit backend privilege. If a dispatcher or SaaS integration disappears, the system narrows gracefully. Couriers keep working against local state, and later reconciliation orchestrated by State Manager restores global consistency without a panic cutover.

#### Goods and local services

Local services, repairs, rentals, or classifieds rely on long-lived identity and auditability. Centralized platforms often delete trust history when they shut down or pivot. In 2WAY, identity and contract history persist independent of a single interface, so neighborhood services survive platform churn while keeping verifiable audit trails.

### 18.5 Key revocation and recovery workflows

Keys, devices, and identity bindings are graph objects, so revocation is not a privileged administrative action. Changing which keys Key Manager trusts is just another ordered mutation that travels through Graph, ACL, and State Managers. Recovery workflows can also live in data: `Edge`s and `ACL`s can require approvals from designated recovery identities before a new device key becomes valid. The substrate does not dictate policy, but once a policy is described, it enforces ordering, authorization, and auditability because every state change uses the same pipeline.

### 18.6 Verifying binaries and software supply chains

2WAY works as an identity and history layer for software distribution. Releases can be signed `Parent` objects with `Attribute`s storing hashes, metadata, or bills of materials, while publisher hierarchies are relationship `Edge`s. Trust in publishers is expressed explicitly in the graph, so installation becomes a local policy decision driven by verifiable state, not DNS or a hosted repository. If a signing key is compromised, a revocation mutation instructs peers to distrust it, and thanks to Graph Manager and State Manager preserving ordered, tamper-evident history, clients observe and enforce the change without waiting for a central takedown.

### 18.7 Device trust, enrollment, and compliance

Devices can be modeled as objects with attributes describing capabilities, compliance status, and desired posture. Policies are data enforced locally by ACL Manager rather than by a continuously available management server. Revocation becomes an ordered event, auditability comes from reading signed history, and organizations gain a model suited to environments where availability and inspection matter more than remote convenience.

### 18.8 Multi-party coordination and governance

Because 2WAY enforces ordered, authorized transitions, it supports workflows that need multiple approvals. Shared `Parent` objects represent the subject of governance, delegated capabilities live in `ACL`s, and each approval is an ordered mutation recorded by State Manager. The system never dictates governance rules; it provides primitives so communities can encode quorums, vetoes, or escalation paths as auditable workflows enforced by the substrate instead of by tradition.

### 18.9 Long-lived records and audit trails

Any workflow that values durable records benefits from identity-bound authorship, ordered history, and fail-closed enforcement. Records become graph objects with explicit ownership and immutable ancestry. Unlike centralized audit systems, correctness does not depend on trusting an operator, and unlike many peer-to-peer networks, ordering and authorization are enforced rather than heuristic. Even if an original application disappears, records remain verifiable to anyone who can replay history.

### 18.10 What ties these examples together

These examples are illustrative. They show that once identity, permissions, ordering, validation, and denial-of-service controls live below the application layer (in Auth, Graph, ACL, State, Network, and DoS Guard Managers), whole classes of workloads become feasible without trusted backends. Centralized systems concentrate authority; many peer-to-peer systems lack structure. 2WAY works because every node enforces the same structure locally while letting developers decide how to model meaning on top.

---

## 19. Conformance

Conformance is binary. An implementation either satisfies every normative requirement in this repository or it does not. Passing tests or showing interoperability means nothing if core invariants were weakened.

To claim conformance, an implementation must prove that:

* **All defined invariants hold** under every supported operating condition, including offline operation and hostile peers.
* **Forbidden behaviors remain structurally impossible**; policy, logging, or operator vigilance are not substitutes for hard guards.
* **Validation, authorization, and ordering rules run exactly as specified**, with no fast paths, heuristics, or trusted modes.
* **No state mutation crosses boundaries out of band**; every write flows through the same serialized authority path regardless of origin.

Any deviation requires an ADR that documents the reasoning, scope, and compensating controls. Without an ADR, the implementation is out of spec.

---

## 20. Scope boundary and status

This repository claims only what it states explicitly. Words such as "secure," "trusted," or "verified" matter only when a section defines the exact conditions. Examples illustrate possibilities, not mandates. Appendices, diagrams, or snippets are non-normative unless a normative section cites them.

The proof of concept is a work in progress. Clarity, auditability, and structural correctness outrank performance, scale, or polish. Some trade-offs remain open until multiple implementations exercise the design. Treat this repository as the authoritative record of intent today, not a guarantee that future ADRs or revisions will keep every detail unchanged.

---

## 21. Acknowledgments

Credit to [Martti Malmi, a.k.a., Sirius](https://github.com/mmalmi) for his work on [Iris](https://github.com/irislib/iris-client), formerly [Identifi](https://github.com/livegnik/identifi), an MIT-licensed project. When the project was still Identifi and implemented as a fork of the Bitcoin daemon in C++ (originally created by Satoshi Nakamoto and worth a hat-tip here), first seeing it helped shape early ideas about private, user-controlled data layers that go beyond simple broadcast messaging through a minimal object model. Our projects took different paths over the years. That early work still influenced this line of thinking and deserves explicit acknowledgment.

Credit to [Nick Szabo](https://x.com/NickSzabo4) for his long-running work on decentralized systems. He also explored social contracts in a way that kept these ideas active for me. His public writing sustained this problem space well before 2WAY existed. His essay [Trusted Third Parties Are Security Holes](https://nakamotoinstitute.org/library/trusted-third-parties/) remains a standout reference for its framing of trust boundaries. It is a personal favorite.

Credit to [Phil Zimmermann](https://philzimmermann.com/) for creating PGP and the Web of Trust model. The way PGP makes trust explicit and composable across social graphs shaped how I think about trust edges, endorsements, and traversal in 2WAY's graph. That lineage helped turn the graph from a storage structure into a verifiable relationship map for endorsements and delegation.

Credit to [Robert Hettinga, a.k.a., RAH](https://x.com/hettinga) for his essay [The Geodesic Market](https://nakamotoinstitute.org/library/the-geodesic-market/). It sharpened my understanding of how geodesic networks shift power. It also reframed how I think about coordination. It highlighted resilience as a property of network shape. That framing clarified why topology and path structure matter when you design systems meant to hold up without a central authority.

Credit to [Ian Grigg](https://x.com/iang_fc) for his work on [Financial Cryptography in 7 Layers](https://iang.org/papers/fc7.html). His essay on [The Ricardian Contract](https://iang.org/papers/ricardian_contract.html) clarified how contractual intent can live alongside cryptographic enforcement. His broader body of writing shaped how I think about layered trust. It also sharpened how I draw the boundary between protocol and policy. Those ideas influenced how this design separates enforceable structure from application meaning.

Credit to [Carsten Keutmann](https://x.com/keutmann/) for his work on the [Digital Trust Protocol](https://github.com/DigitalTrustProtocol). He also shared a practical insight that certain flows get faster and simpler when you treat RAM as scarce. He pairs that with the observation that disk is cheap. That framing helped me see where to favor durable append-first structures instead of memory-heavy shortcuts.

Credit to [Adam Back](https://x.com/adam3us) for his work on proof of work with Hashcash. It grounded how I think about resource-based abuse resistance. It also highlighted the trade-offs in making spam expensive at the protocol edge. It made DoS costs feel like a first-class design input.

Credit to [Ari Juels](https://www.arijuels.com/) for his paper [New Client Puzzle Outsourcing Techniques for DoS Resistance](https://www.arijuels.com/wp-content/uploads/2013/09/WJHF04.pdf). It clarified how to structure puzzles so relays can resist abuse without outsourcing trust. That line of thinking connects directly to the DoS Guard Manager's puzzle flow in this design.
