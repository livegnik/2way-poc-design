
# 2WAY design repository

<br>

**Table of Contents**
- [1. 2WAY design repository in short](#1-2way-design-repository-in-short)
- [2. Why it exists](#2-why-it-exists)
- [3. Repository guide](#3-repository-guide)
- [4. What 2WAY is](#4-what-2way-is)
- [5. Graph, objects, and protocol model](#5-graph-objects-and-protocol-model)
- [6. Backend component model](#6-backend-component-model)
- [7. Security model](#7-security-model)
- [8. Incentives](#8-incentives)
- [9. Privacy](#9-privacy)
- [10. Application model and use cases](#10-application-model-and-use-cases)
- [11. Conformance](#11-conformance)
- [12. Scope boundary and current status](#12-scope-boundary-and-current-status)
- [13. How to use this README](#13-how-to-use-this-readme)
- [14. Acknowledgments](#14-acknowledgments)

<br>

## 1. 2WAY design repository in short

2WAY is a protocol and backend for software that stays correct without a central authority. It gives apps a local-first foundation for identity, permissions, ordering, storage, and sync, enforced by the system. Each device, user, and app keeps its own keys and history and enforces the same rules. Changes are accepted only if valid, authorized, and structurally sound.

State is a cryptographically verifiable graph, not mutable rows behind an API. Writes are checked against schema, ownership, and access before commit. Accepted changes form an append-only, ordered history with clear authorship. Sync trusts verification, not transport, timing, or peers.

This structure enables offline-first tools, partition-tolerant collaboration, and multi-party records without a trusted server. The protocol handles validation, permissions, reconciliation, and provenance so apps can focus on data model and UX.

This proof of concept defines the guarantees: a strict validation pipeline, graph-encoded permissions, replayable audit, and ordering assigned locally and replayable across nodes. Security assumes a hostile network, so every envelope is verified and rejected early if structure, schema, or authorization fail. Privacy is enforced by explicit read scopes, keeping data local by default and sharing only what a node is allowed to see. Incentives are neutral at the protocol layer, and conformance is binary.

This is not a sketch. It defines the object model, manager pipeline, and flows that bind identities and devices to keys, represent schema and ACLs, construct and replay sync packages, and apply DoS guardrails before correctness is threatened. This repository defines the protocol, architecture, and invariants that make those guarantees hold. It is a design repo, not an SDK and not a demo. The goal is a system that stays predictable under failure, adversarial input, and long time horizons.

Looking for a more comprehensive read-through? See [`README-long.md`](README-long.md).

---

## 2. Why it exists

Most systems tie identity, permissions, ordering, and storage to whoever runs the backend. That makes the operator part of the trust model. If the operator changes rules, gets compromised, shuts down, or makes a mistake, users lose authority over their own history. Federation rarely fixes this. It spreads the same problem across fragile bridges and special cases.

2WAY separates durable structure from transient infrastructure. Identity, ownership, permissions, and history live in a shared, cryptographically verifiable graph that every device, user, and app enforces locally. No server decides what is valid. No relay decides what is authoritative. Software can change, vendors can disappear, and the rules still hold.

Because all state changes are signed, ordered, and append-only, a device does not need to trust uptime or timing. It can go offline, fall behind, or disconnect. When it reconnects, it verifies and replays history until it converges again. Authority comes from keys and structure, not from who stayed online the longest.

The point is not decentralization for its own sake. The point is multi-party software that remains correct when operators fail, infrastructure degrades, or trust assumptions break.

---

## 3. Repository guide

This repo is the main design set for the proof of concept. It defines scope, rules, architecture, object models, security model, flows, and acceptance criteria, with PoC goals in [`07-poc`](07-poc). Lower-numbered folders carry higher authority. When conflicts appear, record an ADR in [`08-decisions`](08-decisions) so exceptions stay visible.

| Folder | Focus |
| --- | --- |
| [`00-scope`](00-scope) | Vocabulary, boundary, assumptions |
| [`01-protocol`](01-protocol) | Wire format, object model, rules |
| [`02-architecture`](02-architecture) | Managers and services that enforce the protocol |
| [`03-data`](03-data) | Persistence model and lifecycle |
| [`04-interfaces`](04-interfaces) | APIs and event surfaces |
| [`05-security`](05-security) | Threat framing and structural controls |
| [`06-flows`](06-flows) | Bootstrap, sync, recovery, governance flows |
| [`07-poc`](07-poc) | What the proof of concept must demonstrate |
| [`08-decisions`](08-decisions) | Architecture Decision Records |
| [`09-appendix`](09-appendix) / [`10-examples`](10-examples) | Reference material |

---

## 4. What 2WAY is

2WAY is a protocol and backend that replaces the traditional server as authority over application state. Every node runs the same core system for identity, permissions, ordering, storage, sync, and audit. Because those controls are enforced locally, devices can go offline, keep working, and later reconcile changes without handing authority to a central service.

Applications do not manage storage or trust directly. They define schemas, domain logic, and user interfaces, then operate against a constrained system interface. Apps submit proposed changes and the system validates them. Only changes that satisfy schema rules, ownership, and access control become part of shared state, so application logic stays expressive without bypassing correctness guarantees.

At the center is a shared graph: the canonical record of identities, devices, apps, relationships, capabilities, and application objects. Every object has explicit ownership. Every relationship is typed. Nothing is implicit. Each change declares which identity authored it and under which rules it is allowed to exist.

History is append-only and ordered. Once accepted, a change cannot be rewritten or physically removed; visibility suppression happens through Rating objects at read time rather than deletes. Each entry references its structure, payload, and ancestry so it can be independently verified. Peers exchange signed sequences, then replay and validate them locally. A node accepts only what satisfies its own rules, using the same logic it applies to local changes.

The result is a system where correctness does not depend on transport, uptime, or coordination. State converges because it is verifiable, not because a server says so.

---

## 5. Graph, objects, and protocol model

2WAY defines a protocol for how state is created, validated, ordered, and shared. That protocol is centered around a shared graph, not APIs, endpoints, or databases. The graph is the only source of truth, and every node builds, validates, and evolves it using the same rules. The [protocol overview](01-protocol/00-protocol-overview.md) provides the high-level structure.

All application state is represented as graph records with formal [object model](01-protocol/02-object-model.md) definitions. The model is small and explicit. Parents anchor identities, devices, apps, and domain objects. Attributes attach typed data to Parents. Edges express relationships, capabilities, and transitions. Ratings capture judgments such as endorsements or trust signals. Access control is not external logic. It is encoded into the same graph using constrained Parents and Attributes, keeping authorization visible, replayable, and verifiable like any other data, as described in the [access control model](01-protocol/06-access-control-model.md).

Apps are first-class participants in the protocol. Each app has its own namespace, schemas, and portion of the graph. Schemas are defined by apps and stored in the graph itself through the [Schema Manager](02-architecture/managers/05-schema-manager.md) and the shared [object model](01-protocol/02-object-model.md). They specify which object types exist, how they relate, and what values are valid. The protocol does not interpret application meaning. It enforces that meaning structurally and consistently, so every node evaluates the same rules when deciding whether a change is acceptable.

Every proposed change is wrapped in a protocol envelope that specifies the operation records and required identifiers, as defined in [Serialization and envelopes](01-protocol/03-serialization-and-envelopes.md). Sync packages add sender identity, domain metadata, and sequence fields for ordering and replay checks. When a node receives an envelope, it validates it locally. Structure is checked first, including object model invariants and app namespace boundaries. Schema rules are then applied to ensure the change fits the app's schema. Access control is evaluated next using graph-encoded permissions. Only if all checks succeed is the change assigned a global order and committed. This pipeline runs across the [Graph Manager](02-architecture/managers/07-graph-manager.md), [Schema Manager](02-architecture/managers/05-schema-manager.md), and [ACL Manager](02-architecture/managers/06-acl-manager.md).

History is append-only and ordered per [Sync and consistency](01-protocol/07-sync-and-consistency.md). Nodes exchange signed, ordered envelopes rather than mutable state. Each node replays those sequences independently and accepts only the parts that satisfy its local rules. Ordering comes from protocol-defined sequence assignment, not from message arrival or wall-clock time. This allows nodes to diverge temporarily, operate offline, and still converge without trusting transport or peers.

The result is a protocol where apps, schemas, identities, permissions, and records all live in the same verifiable structure. The graph is not an internal implementation detail. It is the protocol surface. Everything else, networking, storage engines, frontend frameworks, exists only to move envelopes in and out of that structure.

---

## 6. Backend component model

The backend makes the rules real. It is one integrated system that decides what is valid, what is allowed, what order changes land in, and what gets stored. If something fails validation, it never becomes part of state, no matter who sent it or how it arrived.

That is the key difference from architectures built around loose roles like clients, servers, and relays. In those systems, correctness depends on assumptions, relay behavior, server-side logic, or social norms. In 2WAY, authority lives in the protocol enforcement pipeline that every node runs locally. A node does not accept state because a peer says it is fine. It accepts state because it can verify it and it passes the same checks it applies to its own writes.

The backend is built from singleton managers with narrow jobs that form one path for reads and writes, as defined in the [Managers overview](02-architecture/managers/00-managers-overview.md). The [Config Manager](02-architecture/managers/01-config-manager.md) loads configuration and rejects unsafe settings. The [Auth Manager](02-architecture/managers/04-auth-manager.md) resolves local sessions into an `OperationContext` per the [protocol overview](01-protocol/00-protocol-overview.md). The [Key Manager](02-architecture/managers/03-key-manager.md) owns private keys and performs signing and encryption for trusted callers. The [App Manager](02-architecture/managers/08-app-manager.md) registers apps and app identities. The [Schema Manager](02-architecture/managers/05-schema-manager.md) checks that a change matches the app's declared structure. The [ACL Manager](02-architecture/managers/06-acl-manager.md) checks that the caller has the right to perform it, using the current `OperationContext`. The [Graph Manager](02-architecture/managers/07-graph-manager.md) is the only place where writes are accepted. It validates object model invariants, assigns a `global_seq`, and commits through the [Storage Manager](02-architecture/managers/02-storage-manager.md). The [State Manager](02-architecture/managers/09-state-manager.md) coordinates ordered sync and package construction from accepted history. The [Network Manager](02-architecture/managers/10-network-manager.md) admits peers, verifies and transports packages with the [DoS Guard Manager](02-architecture/managers/14-dos-guard-manager.md) and [Key Manager](02-architecture/managers/03-key-manager.md), and never changes protocol data. The [Event Manager](02-architecture/managers/11-event-manager.md) and [Log Manager](02-architecture/managers/12-log-manager.md) record what happened and why. The [Health Manager](02-architecture/managers/13-health-manager.md) and [DoS Guard Manager](02-architecture/managers/14-dos-guard-manager.md) keep the node stable and reject load before correctness can be threatened.

Services sit above the managers and provide higher-level behavior. They turn user intent into protocol-compliant operations, expose backend endpoints, and do app-specific aggregation or validation when needed. They do not get special authority. They cannot write around the managers, bypass schema or ACL checks, or touch keys, storage, or sockets directly. They must always call into the same enforcement path with a complete `OperationContext`.

There are two service classes. System services are always present and cover shared workflows that multiple apps rely on. App extension services are optional and scoped to one app. They exist for backend-heavy features like indexing or specialized queries, and removing them must not break the core or corrupt state.

The point of this design is that the backend behaves like a kernel. It enforces one coherent model of validity, permission, ordering, and persistence. Everything above it can change, but enforcement does not become optional.

---

## 7. Security model

2WAY assumes the network is adversarial and peers can be careless, compromised, or hostile. Security is enforced by protocol structure rather than operator policy. Each device, user, and app holds its own keys and history, and every node verifies incoming changes locally before accepting them per [Cryptography](01-protocol/04-cryptography.md) and [Keys and identity](01-protocol/05-keys-and-identity.md).

All writes, local or remote, use the same envelope path and validation order: structural checks first, then schema rules, then ACL authorization as defined in [Serialization and envelopes](01-protocol/03-serialization-and-envelopes.md) and the [access control model](01-protocol/06-access-control-model.md). Ordering is assigned locally and is repeatable, so replayed or reordered input cannot change outcomes per [Sync and consistency](01-protocol/07-sync-and-consistency.md).

Sybil resistance comes from bounded reach, not global reputation. Identities are key-bound, app namespaces are isolated, and permissions are explicit in the graph, so unknown identities cannot gain broad access without explicit edges or ACL grants per [Identifiers and namespaces](01-protocol/01-identifiers-and-namespaces.md) and the [access control model](01-protocol/06-access-control-model.md). This limits the blast radius of fake identities and impersonation attempts.

Denial-of-service protection is part of the protocol pipeline, not a bolt-on. The DoS Guard Manager gates admission at the network boundary and can require client puzzles before any payload flows inward, following [DoS guard and client puzzles](01-protocol/11-dos-guard-and-client-puzzles.md) and [Network transport requirements](01-protocol/08-network-transport-requirements.md). Puzzle difficulty adjusts dynamically to load and abuse signals, and the system fails closed on policy or puzzle failures. Earlier stages reject malformed input without expensive work, and failures are classified consistently by the [protocol overview](01-protocol/00-protocol-overview.md) and [Errors and failure modes](01-protocol/09-errors-and-failure-modes.md).

Recovery is intentionally simple. Accepted changes are signed, ordered, and append-only, so a node can rebuild by replaying history and reapplying the same rules. Unverifiable history is rejected rather than patched or trusted per [Sync and consistency](01-protocol/07-sync-and-consistency.md).

The protocol does not define social or political choices. Governance models, moderation rules, incentives, and policy meaning live in application schemas and data. The protocol enforces correctness, authorship, and ordering, not policy content.

---

## 8. Incentives

2WAY is neutral on economic incentives at the protocol level. The protocol includes Ratings as a first-class object category, and ACL rules can gate actions using app-defined rating or trust thresholds, but those values live in application data and are scoped to the app domain. There is no global reputation score, token, reward scheme, or fee market enforced by the protocol itself. That is intentional.

The core incentive is correctness. Nodes participate because enforcing the protocol locally protects their own state. A node that validates strictly, rejects invalid input, and orders changes correctly ends up with a coherent, auditable history it can rely on. A node that cuts corners gains nothing durable and risks corrupting its own state. This creates a baseline incentive to follow the rules without payments or coordination.

For users, good behavior is the easiest way to keep their own graph usable and their relationships intact. Most value in 2WAY flows through explicit edges and permissions, so bad behavior breaks access, severs collaboration, and makes a user's own history less trusted by the people and apps they want to work with. Good behavior preserves continuity: your device keeps syncing, your records remain accepted, and your peers keep you in their allowed scopes. The balance comes from local enforcement and mutual dependence. You cannot force others to accept bad input, and they cannot be forced to keep sharing with you if you violate rules, so honest participation is the stable path.

Because every device, user, and app keeps its own keys and history, there is no central operator that can extract rent by default. Running a node does not grant control over others, and there is no privileged position to monetize purely by being in the middle. This removes many perverse incentives in centralized systems, where operators are rewarded for lock-in, opacity, or silent rule changes.

Abuse resistance is handled structurally rather than economically. Sybil behavior is limited by relationship depth, ACLs, and schema constraints, not by proof-of-work or staking. Flooding the network is discouraged by DoS guards, early rejection, and local resource limits. These mechanisms do not reward good behavior with payouts, but they make bad behavior ineffective and costly in local resources.

Incentives that matter to users and developers live above the protocol, inside applications. Apps can define their own economic models, governance rules, trust signals, or reputation systems as graph data. Markets can encode listings, contracts, escrow, and settlement logic. Communities can encode moderation, membership, and voting. Enterprises can encode approvals, compliance flows, and audit requirements. None of these meanings are hard-coded into 2WAY, but all of them benefit from the same guarantees around identity, ordering, authorship, and replayability.

This separation is intentional. It prevents the protocol from baking in assumptions about value, scarcity, or motivation that may not hold across domains or over time. It also avoids coupling long-term infrastructure correctness to short-term incentive fashions. If an incentive model is flawed, it can be changed at the application level without forking the protocol or rewriting history.

For operators and integrators, the incentive is leverage. By building on 2WAY, they avoid re-implementing identity, permissions, sync, and audit for every system. They gain durability and user trust without having to promise perpetual uptime or benevolent control. For users, the incentive is autonomy. Their data, history, and authority persist even if an app, vendor, or service disappears.

In short, 2WAY does not try to motivate participation with rewards. It motivates participation by making correct behavior the simplest path, abusive behavior ineffective, and long-term control stay with the people and applications that use the system.

---

## 9. Privacy

2WAY treats privacy as a structural property, not as a feature layered on later. The system is designed so nodes only see what they are allowed to see, and only share what they explicitly choose to share. There is no global view of the network, no mandatory data aggregation point, and no requirement to disclose more information than an application's rules demand.

Each node keeps its own full state locally. Data is not pulled into a central service by default, and there is no background process that mirrors complete histories elsewhere. When nodes exchange data, they do so through scoped synchronization. Only the parts of the graph that fall within an allowed domain and pass access checks are included. Objects outside those scopes never leave the device, even if they exist in the same local graph.

Visibility is enforced by the same mechanisms that enforce correctness. Access control rules live in the graph and are evaluated for every read and every sync decision. If an identity does not have permission to read an object, that object is omitted entirely rather than redacted after the fact. This prevents accidental disclosure and makes privacy failures easier to reason about, because absence is explicit rather than inferred.

Identity is decentralized and composable. Users, devices, and apps each have their own keys, and relationships between them are explicit. This allows people to operate across multiple apps or contexts without collapsing everything into a single global profile. Pseudonymous identities can exist alongside real-world ones, and applications can choose how, or whether, to link them. The protocol does not require universal discoverability.

Network privacy is separate from data privacy. Transport can run over Tor or other privacy-preserving networks, but the protocol does not assume the transport layer is trusted or private. Messages are signed so authorship can be verified, and they can be encrypted so contents are not visible to intermediaries. Even if transport metadata leaks, the graph structure limits what meaningful information can be inferred.

Because history is append-only and verifiable, privacy does not depend on secrecy alone. Unauthorized parties cannot rewrite or silently alter records to remove traces or fabricate consent. At the same time, applications can encode expiration, revocation, or visibility rules directly into their schemas to limit how long data remains relevant or accessible. The protocol enforces those rules consistently across nodes.

The result is a system where privacy emerges from local control, explicit sharing, and enforced boundaries. Users do not have to trust a service to handle their data carefully. They can verify what is shared, with whom, and under which rules, because those rules are part of the state itself.

---

## 10. Application model and use cases

In 2WAY, an application is not a backend service that owns data. It is a way of working with shared state the system already knows how to protect. That model assumes the protocol-level incentives and privacy boundaries already described: apps inherit correctness-first participation and scoped visibility, rather than reinventing them. From a user's perspective, an app feels local and responsive. You can create, edit, and inspect records on your own device, even when you are offline. When the network is available again, your changes are checked, ordered, and merged with everyone else's in a predictable way. Nothing disappears because a server is down, and nothing silently changes because a service updated its logic.

From a developer's perspective, an app defines what the data means and how people interact with it. You describe the kinds of records the app uses, how they relate, and who is allowed to do what. The system takes care of identity, permissions, history, synchronization, and audit. Instead of writing custom backend logic to keep things consistent, you propose changes through the protocol and let the system decide whether they are valid. If they are accepted on one node, they will be accepted the same way everywhere.

Apps model their domain data with the same graph primitives: Parents, Attributes, Edges, and Ratings. That makes relationship queries first-class. Degrees-of-separation queries become bounded graph traversals across explicit edges (contacts-of-contacts, delegated access, trust paths), filtered by schema and ACL so results only include readable nodes. App extension services can build indexes or materialized views for large datasets, but they still evaluate the same rules and cannot manufacture authority.

This makes apps easier to reason about and test. State changes form an ordered history that can be replayed to reconstruct the app at any point in time. Bugs are easier to track because there is a clear record of what happened and why. Multiple frontends or implementations can work with the same app data as long as they follow the same schemas and rules, which means user interfaces can evolve or be replaced without breaking the underlying state.

Because the state already lives locally, queries are fast and dependable. You are not waiting on a central server or a fragile API to answer basic questions. The relevant data flows to your device, and you can read it directly even when the network is slow or missing. This separation is powerful in a decentralized app substrate. It keeps control of data and context on the user side, and it lets people switch apps, change providers, or run their own tools without losing access to their history or their ability to make sense of it.

Moderation and spam control are expressed as state rather than hidden server logic. Blocks, mutes, allowlists, reputation signals, and community votes can live as ratings or edges in the graph. Apps can enforce inbox filters, rate limits, or visibility rules based on those signals, while the DoS Guard protects the protocol surface from abusive traffic. Different communities can tune policies without forking the protocol.

In practice, this model fits domains where history, collaboration, and durability matter. Messaging and chat become collections of explicit conversations, participants, and messages that remain inspectable and trustworthy even when people are offline. Social and publishing tools treat posts, reactions, moderation actions, and discovery paths as part of a shared record rather than hidden server decisions. Marketplaces and service platforms can model listings, offers, agreements, escrow, fulfillment, and reputation as state that all parties can verify and audit. Operational workflows like logistics, access control, or governance can be expressed as sequences of approved changes that remain auditable long after the original software is gone.

Across all of these cases, the common thread is that apps do not have to reinvent trust. Identity, permissions, ordering, and resilience are part of the system below them. That lets developers focus on what their app is for, and lets users keep control over their data and its history, regardless of which app or vendor they are using at the moment.

## 11. Conformance

2WAY only works if the rules are followed exactly. An implementation either conforms or it does not. Validation, permissions, ordering, and storage must behave the same way in all conditions, including offline use and hostile input. Forbidden behavior must be impossible by design, not merely detected after the fact or left to operator judgment.

All state changes must pass through the same enforcement path. There are no shortcuts, no trusted fast paths, and no exceptions for convenience. If an implementation diverges from the documented behavior, that divergence must be written down as an Architecture Decision Record with clear scope and compensating measures. Without that, the implementation is out of spec, even if it appears to work.

---

## 12. Scope boundary and current status

This repository only promises what it states explicitly. Examples are illustrative, not requirements. The proof of concept prioritizes correctness, clarity, and inspectability over polish or performance. Details may evolve over time, but changes are intentional and documented.

Treat this repository as the authoritative description of how the system is meant to behave today. Build against the guarantees it defines, not against assumptions or implied features.

---

## 13. How to use this README

This README gives you the mental model. It explains what 2WAY is, why it exists, how the graph and backend work, and what guarantees the system enforces. It does not replace the detailed documents.

Once the overview is clear, move into the numbered folders. The protocol folder defines rules and invariants. The architecture folder explains how those rules are enforced in practice. Any deviation should be recorded as an ADR so the system remains coherent over time.

The key idea to keep in mind is that every node enforces the same structure locally. Collaboration works because correctness is shared, not because authority is centralized.

---

## 14. Acknowledgments

Credit to Martti Malmi (Sirius) for his work on Iris, formerly Identifi, an MIT-licensed project available at [https://github.com/irislib/iris-client](https://github.com/irislib/iris-client). When the project was still Identifi and implemented as a fork of the Bitcoin daemon in C++, encountering it helped shape early ideas about private, user-controlled data layers that go beyond simple broadcast messaging with the help of a simple object model.

Our projects took different paths over the years, but that early work influenced this line of thinking and deserves explicit acknowledgment.

---
