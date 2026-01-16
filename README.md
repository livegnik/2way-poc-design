



# 2WAY design repository in short

2WAY is a protocol and backend for building software that stays correct without a central authority. It gives apps a shared, local-first foundation for identity, permissions, ordering, storage, and sync, enforced at the system level instead of reimplemented in every app. Each device, user, and app holds its own keys and history, and enforces the same rules locally. No change is accepted unless it is valid, authorized, and structurally sound.

The core idea is simple. Treat state as a cryptographically verifiable graph, not as mutable rows behind an API. Every write is checked against schema, ownership, and access rules before it is committed. Every accepted change becomes part of an append-only history with clear authorship and ordering. Sync does not trust transport, timing, or peers. It only trusts what can be verified.

This makes a class of apps practical that usually fall apart under real-world conditions. Apps that work offline by default. Apps that survive node loss, network partitions, and server shutdowns. Apps where collaboration does not depend on one operator behaving correctly forever. The protocol handles the hard parts, validation, permissions, reconciliation, and provenance, so applications can focus on their data model and user experience.

This repository defines the protocol, architecture, and invariants that make those guarantees hold. It is a design repo, not an SDK and not a demo. The goal is to specify a system that remains predictable under failure, adversarial input, and long time horizons.

Looking for a more comprehensive read-through? See [`README-long.md`](README-long.md).

---

## Why it exists

Most systems tie identity, permissions, ordering, and storage to whoever runs the backend. That makes the operator part of the trust model, whether you intend it or not. If the operator changes rules, gets compromised, shuts down, or simply makes a mistake, users lose authority over their own history. Federation usually does not fix this. It just spreads the same problem across fragile bridges and special cases.

2WAY exists to separate durable structure from transient infrastructure. Identity, ownership, permissions, and history live in a shared, cryptographically verifiable graph that every device, user, and app enforces locally. No server decides what is valid. No relay decides what is authoritative. Software can change, vendors can disappear, and the rules still hold.

Because all state changes are signed, ordered, and append-only, a device does not need to trust uptime or timing. It can go offline, fall behind, or disconnect entirely. When it reconnects, it verifies and replays history until it converges again. Authority comes from keys and structure, not from who stayed online the longest.

The point is not decentralization for its own sake. The point is to make multi-party software that remains correct even when operators fail, infrastructure degrades, or trust assumptions break.

---

## Repository guide

This repo is the main design set for the proof of concept. It defines scope, rules, architecture, object models, security framing, flows, and acceptance criteria. Lower-numbered folders carry higher authority. When conflicts appear, record an ADR in [`08-decisions`](08-decisions) so exceptions stay visible.

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

## What 2WAY is

2WAY is a protocol and backend that replaces the traditional server as the authority over application state. Every node runs the same core system for identity, permissions, ordering, storage, sync, and audit. Because those controls are enforced locally, devices can go offline, continue operating, and later reconcile changes without handing authority to a central service.

Applications do not manage storage or trust directly. They define schemas, domain logic, and user interfaces, then operate against a constrained system interface. Apps submit proposed changes. The system validates them. Only changes that satisfy schema rules, ownership, and access control become part of shared state. This keeps application logic expressive without allowing it to bypass correctness guarantees.

At the center is a shared graph that represents identities, devices, apps, relationships, capabilities, and application records. Every object has explicit ownership. Every relationship is typed. Nothing is implicit. Each change declares which identity authored it and under which rules it is allowed to exist.

History is append-only and ordered. Once accepted, a change cannot be rewritten or silently removed. Each entry references its structure, its payload, and its ancestry in a way that can be independently verified. Peers exchange history as signed sequences, then replay and validate it locally. A node accepts only what satisfies its own rules, using the same logic it applies to local changes.

The result is a system where correctness does not depend on transport, uptime, or coordination. State converges because it is verifiable, not because a server says so.

---

## Graph, objects, and protocol model

2WAY defines a protocol for how state is created, validated, ordered, and shared. That protocol is centered around a shared graph, not around APIs, endpoints, or databases. The graph is the only source of truth, and every node builds, validates, and evolves it using the same rules. The high-level structure of the protocol is introduced in [[1](#ref-1)].

All application state is represented as graph records, defined formally in [[3](#ref-3)]. The model is intentionally small and explicit. Parents anchor identities, devices, apps, and domain objects. Attributes attach typed data to those Parents. Edges express relationships, capabilities, and transitions. Ratings capture judgments such as endorsements or trust signals. Access control is not external logic. It is encoded into the same graph using constrained Parents and Attributes, with its semantics defined in [[7](#ref-7)], so authorization state is visible, replayable, and verifiable like any other data.

Apps are first-class participants in the protocol. Each app has its own namespace, its own schemas, and its own portion of the graph. Schemas are defined by apps and stored in the graph itself, as described in [[17](#ref-17)] and [[3](#ref-3)]. They specify which object types exist, how they relate, and what values are valid. The protocol does not interpret application meaning. It enforces that meaning structurally and consistently, so every node evaluates the same rules when deciding whether a change is acceptable.

Every proposed change is wrapped in a protocol envelope, defined in [[4](#ref-4)]. Graph message envelopes carry the operation records and required identifiers. Sync packages add sender identity, domain metadata, and sequence fields for ordering and replay checks. When a node receives an envelope, it validates it locally. Structure is checked first, including object model invariants and app namespace boundaries. Schema rules are then applied to ensure the change fits the app's schema. Access control is evaluated next using graph-encoded permissions. Only if all checks succeed is the change assigned a global order and committed. This pipeline is defined across [[19](#ref-19)] [[17](#ref-17)] and [[18](#ref-18)].

History is append-only and ordered, as defined in [[8](#ref-8)]. Nodes exchange signed, ordered envelopes rather than mutable state. Each node replays those sequences independently and accepts only the parts that satisfy its local rules. Ordering comes from protocol-defined sequence assignment, not from message arrival or wall-clock time. This is what allows nodes to diverge temporarily, operate offline, and still converge without trusting transport or peers.

The result is a protocol where apps, schemas, identities, permissions, and records all live in the same verifiable structure. The graph is not an internal implementation detail. It *is* the protocol surface. Everything else, networking, storage engines, frontend frameworks, exists only to move envelopes in and out of that structure.

---

## Backend component model

The backend is the part of 2WAY that makes the rules real. It is not a set of cooperating components that try to behave by convention. It is one integrated system that decides what is valid, what is allowed, what order changes land in, and what gets stored. If something fails validation, it does not become part of state, regardless of who sent it or how it arrived.

That is the key difference from architectures built around loose roles like clients, servers, and relays. In those systems, correctness often depends on shared assumptions, relay behavior, server-side business logic, or social norms. In 2WAY, authority lives in the protocol enforcement pipeline that every node runs locally. A node does not accept state because a peer says it is fine. It accepts state because it can verify it and it passes the same checks it would apply to its own writes.

The backend is built from singleton managers with narrow jobs that fit together into one path for reads and writes (see [[12](#ref-12)]). Config Manager loads configuration and rejects unsafe settings [[13](#ref-13)]. Auth Manager resolves local sessions into an `OperationContext` [[16](#ref-16)] [[1](#ref-1)]. Key Manager owns private keys and performs signing and encryption for trusted callers [[15](#ref-15)]. App Manager registers apps and app identities [[20](#ref-20)]. Schema Manager checks that a change matches the app's declared structure [[17](#ref-17)]. ACL Manager checks that the caller has the right to perform it, using the current `OperationContext` [[18](#ref-18)]. Graph Manager is the only place where writes are accepted. It validates object model invariants, assigns a `global_seq`, and commits through Storage Manager [[19](#ref-19)] [[14](#ref-14)]. State Manager coordinates ordered sync and package construction from accepted history [[21](#ref-21)]. Network Manager admits peers, verifies and transports packages with DoS Guard and Key Manager, and never changes protocol data [[22](#ref-22)] [[26](#ref-26)]. Event and Log Managers record what happened and why [[23](#ref-23)] [[24](#ref-24)]. Health and DoS Guard Managers keep the node stable and reject load before correctness can be threatened [[25](#ref-25)] [[26](#ref-26)].

Services sit above the managers and provide higher-level behavior. They turn user intent into protocol-compliant operations, expose backend endpoints, and do app-specific aggregation or validation when needed. They do not get special authority. They cannot write around the managers, they cannot bypass schema or ACL checks, and they cannot touch keys, storage, or sockets directly. They must always call into the same enforcement path with a complete `OperationContext`.

There are two service classes. System services are always present and cover shared workflows that multiple apps rely on. App extension services are optional and scoped to one app. They exist for backend-heavy features like indexing or specialized queries, and removing them must not break the core or corrupt state.

The point of this design is that the backend behaves like a kernel. It enforces one coherent model of validity, permission, ordering, and persistence. Everything above it can change, but the enforcement does not become optional.

---

## Security framing

2WAY assumes the network is adversarial and peers can be careless, compromised, or hostile. Security is enforced by protocol structure rather than operator policy. Each device, user, and app holds its own keys and history, and every node verifies incoming changes locally before accepting them [[5](#ref-5)] [[6](#ref-6)].

All writes, local or remote, use the same envelope path and validation order: structural checks first, then schema rules, then ACL authorization [[4](#ref-4)] [[7](#ref-7)]. Ordering is assigned locally and is repeatable, so replayed or reordered input cannot change outcomes [[8](#ref-8)].

Sybil resistance comes from bounded reach, not global reputation. Identities are key-bound, app namespaces are isolated, and permissions are explicit in the graph, so unknown identities cannot gain broad access without explicit edges or ACL grants [[2](#ref-2)] [[7](#ref-7)]. This limits the blast radius of fake identities and impersonation attempts.

Denial-of-service protection is part of the protocol pipeline, not a bolt-on. The DoS Guard Manager gates admission at the network boundary and can require client puzzles before any payload flows inward [[11](#ref-11)] [[9](#ref-9)]. Puzzle difficulty adjusts dynamically to load and abuse signals, and the system fails closed on policy or puzzle failures. Earlier stages reject malformed input without expensive work, and failures are classified consistently [[1](#ref-1)] [[10](#ref-10)].

Recovery is intentionally boring. Accepted changes are signed, ordered, and append-only, so a node can rebuild by replaying history and reapplying the same rules. Unverifiable history is rejected rather than patched or trusted [[8](#ref-8)].

The protocol does not define social or political choices. Governance models, moderation rules, incentives, and policy meaning live in application schemas and data. The protocol enforces correctness, authorship, and ordering, not policy content.

---

## Application model and use cases

In 2WAY, an application is not a backend service that owns data. It is a way of working with shared state that the system already knows how to protect. From a user's perspective, an app feels local and responsive. You can create, edit, and inspect records on your own device, even when you are offline. When the network is available again, your changes are checked, ordered, and merged with everyone else's in a predictable way. Nothing disappears because a server is down, and nothing silently changes because a service updated its logic.

From a developer's perspective, an app defines what the data means and how people interact with it. You describe the kinds of records the app uses, how they relate, and who is allowed to do what. The system takes care of identity, permissions, history, synchronization, and audit. Instead of writing custom backend logic to keep things consistent, you propose changes through the protocol and let the system decide whether they are valid. If they are accepted on one node, they will be accepted the same way everywhere.

This makes apps easier to reason about and easier to test. State changes form an ordered history that can be replayed to reconstruct the app at any point in time. Bugs are easier to track because there is a clear record of what happened and why. Multiple frontends or implementations can work with the same app data as long as they follow the same schemas and rules, which means user interfaces can evolve or be replaced without breaking the underlying state.

In practice, this model fits domains where history, collaboration, and durability matter. Messaging and chat become collections of explicit conversations, participants, and messages that remain inspectable and trustworthy even when people are offline. Social and publishing tools treat posts, reactions, and moderation actions as part of a shared record rather than hidden server decisions. Marketplaces and service platforms can model offers, agreements, and reputation as state that all parties can verify. Operational workflows like logistics, access control, or governance can be expressed as sequences of approved changes that remain auditable long after the original software is gone.

Across all of these cases, the common thread is that apps do not have to reinvent trust. Identity, permissions, ordering, and resilience are part of the system below them. That lets developers focus on what their app is for, and lets users keep control over their data and its history, regardless of which app or vendor they are using at the moment.

## Conformance

2WAY only works if the rules are followed exactly. An implementation either conforms or it does not. Validation, permissions, ordering, and storage must behave the same way in all conditions, including offline use and hostile input. Forbidden behavior must be impossible by design, not merely detected after the fact or left to operator judgment.

All state changes must pass through the same enforcement path. There are no shortcuts, no trusted fast paths, and no exceptions for convenience. If an implementation diverges from the documented behavior, that divergence must be written down as an Architecture Decision Record with clear scope and compensating measures. Without that, the implementation is out of spec, even if it appears to work.

---

## Scope boundary and current status

This repository only promises what it states explicitly. Examples are illustrative, not requirements. The proof of concept prioritizes correctness, clarity, and inspectability over polish or performance. Details may evolve over time, but changes are intentional and documented.

Treat this repository as the authoritative description of how the system is meant to behave today. Build against the guarantees it defines, not against assumptions or implied features.

---

## How to use this README

This README is meant to give you the mental model. It explains what 2WAY is, why it exists, how the graph and backend work, and what guarantees the system enforces. It does not replace the detailed documents.

Once the overview is clear, move into the numbered folders. The protocol folder defines rules and invariants. The architecture folder explains how those rules are enforced in practice. Any deviation should be recorded as an ADR so the system remains coherent over time.

The key idea to keep in mind is that every node enforces the same structure locally. Collaboration works because correctness is shared, not because authority is centralized.

---

## Acknowledgments

Credit to Martti Malmi (Sirius) for his work on Iris, formerly Identifi, an MIT-licensed project available at [https://github.com/irislib/iris-client](https://github.com/irislib/iris-client). When the project was still Identifi and implemented as a fork of the Bitcoin daemon in C++, encountering it helped shape early ideas about private, user-controlled data layers that go beyond simple broadcast messaging with the help of a simple object model.

Our projects took different paths over the years, but that early work influenced this line of thinking and deserves explicit acknowledgment.

---

## References

<a id="ref-1"></a>[1] Protocol overview - [01-protocol/00-protocol-overview.md](01-protocol/00-protocol-overview.md)
<a id="ref-2"></a>[2] Identifiers and namespaces - [01-protocol/01-identifiers-and-namespaces.md](01-protocol/01-identifiers-and-namespaces.md)
<a id="ref-3"></a>[3] Object model - [01-protocol/02-object-model.md](01-protocol/02-object-model.md)
<a id="ref-4"></a>[4] Serialization and envelopes - [01-protocol/03-serialization-and-envelopes.md](01-protocol/03-serialization-and-envelopes.md)
<a id="ref-5"></a>[5] Cryptography - [01-protocol/04-cryptography.md](01-protocol/04-cryptography.md)
<a id="ref-6"></a>[6] Keys and identity - [01-protocol/05-keys-and-identity.md](01-protocol/05-keys-and-identity.md)
<a id="ref-7"></a>[7] Access control model - [01-protocol/06-access-control-model.md](01-protocol/06-access-control-model.md)
<a id="ref-8"></a>[8] Sync and consistency - [01-protocol/07-sync-and-consistency.md](01-protocol/07-sync-and-consistency.md)
<a id="ref-9"></a>[9] Network transport requirements - [01-protocol/08-network-transport-requirements.md](01-protocol/08-network-transport-requirements.md)
<a id="ref-10"></a>[10] Errors and failure modes - [01-protocol/09-errors-and-failure-modes.md](01-protocol/09-errors-and-failure-modes.md)
<a id="ref-11"></a>[11] DoS guard and client puzzles - [01-protocol/11-dos-guard-and-client-puzzles.md](01-protocol/11-dos-guard-and-client-puzzles.md)
<a id="ref-12"></a>[12] Managers overview - [02-architecture/managers/00-managers-overview.md](02-architecture/managers/00-managers-overview.md)
<a id="ref-13"></a>[13] Config Manager - [02-architecture/managers/01-config-manager.md](02-architecture/managers/01-config-manager.md)
<a id="ref-14"></a>[14] Storage Manager - [02-architecture/managers/02-storage-manager.md](02-architecture/managers/02-storage-manager.md)
<a id="ref-15"></a>[15] Key Manager - [02-architecture/managers/03-key-manager.md](02-architecture/managers/03-key-manager.md)
<a id="ref-16"></a>[16] Auth Manager - [02-architecture/managers/04-auth-manager.md](02-architecture/managers/04-auth-manager.md)
<a id="ref-17"></a>[17] Schema Manager - [02-architecture/managers/05-schema-manager.md](02-architecture/managers/05-schema-manager.md)
<a id="ref-18"></a>[18] ACL Manager - [02-architecture/managers/06-acl-manager.md](02-architecture/managers/06-acl-manager.md)
<a id="ref-19"></a>[19] Graph Manager - [02-architecture/managers/07-graph-manager.md](02-architecture/managers/07-graph-manager.md)
<a id="ref-20"></a>[20] App Manager - [02-architecture/managers/08-app-manager.md](02-architecture/managers/08-app-manager.md)
<a id="ref-21"></a>[21] State Manager - [02-architecture/managers/09-state-manager.md](02-architecture/managers/09-state-manager.md)
<a id="ref-22"></a>[22] Network Manager - [02-architecture/managers/10-network-manager.md](02-architecture/managers/10-network-manager.md)
<a id="ref-23"></a>[23] Event Manager - [02-architecture/managers/11-event-manager.md](02-architecture/managers/11-event-manager.md)
<a id="ref-24"></a>[24] Log Manager - [02-architecture/managers/12-log-manager.md](02-architecture/managers/12-log-manager.md)
<a id="ref-25"></a>[25] Health Manager - [02-architecture/managers/13-health-manager.md](02-architecture/managers/13-health-manager.md)
<a id="ref-26"></a>[26] DoS Guard Manager - [02-architecture/managers/14-dos-guard-manager.md](02-architecture/managers/14-dos-guard-manager.md)
