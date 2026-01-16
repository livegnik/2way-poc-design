



# 2WAY design repository in short

2WAY is a protocol and backend for building software that stays correct without a central authority. It gives apps a shared, local-first foundation for identity, permissions, ordering, storage, and sync, enforced at the system level instead of reimplemented in every app. Each device, user, and app holds its own keys and history, and enforces the same rules locally. No change is accepted unless it is valid, authorized, and structurally sound.

The core idea is simple. Treat state as a cryptographically verifiable graph, not as mutable rows behind an API. Every write is checked against schema, ownership, and access rules before it is committed. Every accepted change becomes part of an append-only history with clear authorship and ordering. Sync does not trust transport, timing, or peers. It only trusts what can be verified.

This makes a class of apps practical that usually fall apart under real-world conditions. Apps that work offline by default. Apps that survive node loss, network partitions, and server shutdowns. Apps where collaboration does not depend on one operator behaving correctly forever. The protocol handles the hard parts, validation, permissions, reconciliation, and provenance, so applications can focus on their data model and user experience.

This repository defines the protocol, architecture, and invariants that make those guarantees hold. It is a design repo, not an SDK and not a demo. The goal is to specify a system that remains predictable under failure, adversarial input, and long time horizons.

Looking for a more comprehensive read-through? See [README-long.md](README-long.md).

---

## Why it exists

Most systems tie identity, permissions, ordering, and storage to whoever runs the backend. That makes the operator part of the trust model, whether you intend it or not. If the operator changes rules, gets compromised, shuts down, or simply makes a mistake, users lose authority over their own history. Federation usually does not fix this. It just spreads the same problem across fragile bridges and special cases.

2WAY exists to separate durable structure from transient infrastructure. Identity, ownership, permissions, and history live in a shared, cryptographically verifiable graph that every device, user, and app enforces locally. No server decides what is valid. No relay decides what is authoritative. Software can change, vendors can disappear, and the rules still hold.

Because all state changes are signed, ordered, and append-only, a device does not need to trust uptime or timing. It can go offline, fall behind, or disconnect entirely. When it reconnects, it verifies and replays history until it converges again. Authority comes from keys and structure, not from who stayed online the longest.

The point is not decentralization for its own sake. The point is to make multi-party software that remains correct even when operators fail, infrastructure degrades, or trust assumptions break.

---

## Repository guide

This repo is the main design set for the proof of concept. It defines scope, rules, architecture, object models, security framing, flows, and acceptance criteria. Lower-numbered folders carry higher authority. When conflicts appear, record an ADR in `08-decisions` so exceptions stay visible.

| Folder | Focus |
| --- | --- |
| `00-scope` | Vocabulary, boundary, assumptions |
| `01-protocol` | Wire format, object model, rules |
| `02-architecture` | Managers and services that enforce the protocol |
| `03-data` | Persistence model and lifecycle |
| `04-interfaces` | APIs and event surfaces |
| `05-security` | Threat framing and structural controls |
| `06-flows` | Bootstrap, sync, recovery, governance flows |
| `07-poc` | What the proof of concept must demonstrate |
| `08-decisions` | Architecture Decision Records |
| `09-appendix` / `10-examples` | Reference material |

---

## What 2WAY is

2WAY is a protocol and backend that replaces the traditional server as the authority over application state. Every node runs the same core system for identity, permissions, ordering, storage, sync, and audit. Because those controls are enforced locally, devices can go offline, continue operating, and later reconcile changes without handing authority to a central service.

Applications do not manage storage or trust directly. They define schemas, domain logic, and user interfaces, then operate against a constrained system interface. Apps submit proposed changes. The system validates them. Only changes that satisfy schema rules, ownership, and access control become part of shared state. This keeps application logic expressive without allowing it to bypass correctness guarantees.

At the center is a shared graph that represents identities, devices, apps, relationships, capabilities, and application records. Every object has explicit ownership. Every relationship is typed. Nothing is implicit. Each change declares which identity authored it and under which rules it is allowed to exist.

History is append-only and ordered. Once accepted, a change cannot be rewritten or silently removed. Each entry references its structure, its payload, and its ancestry in a way that can be independently verified. Peers exchange history as signed sequences, then replay and validate it locally. A node accepts only what satisfies its own rules, using the same logic it applies to local changes.

The result is a system where correctness does not depend on transport, uptime, or coordination. State converges because it is verifiable, not because a server says so.

---

## Graph, objects, and protocol model

2WAY defines a protocol for how state is created, validated, ordered, and shared. That protocol is centered around a shared graph, not around APIs, endpoints, or databases. The graph is the only source of truth, and every node builds, validates, and evolves it using the same rules. The high-level structure of the protocol is introduced in `01-protocol/00-protocol-overview.md`.

All application state is represented as graph records, defined formally in `01-protocol/02-object-model.md`. The model is intentionally small and explicit. Parents anchor identities, devices, apps, and domain objects. Attributes attach typed data to those Parents. Edges express relationships, capabilities, and transitions. Ratings capture judgments such as endorsements or trust signals. Access control is not external logic. It is encoded into the same graph using constrained Parents and Attributes, with its semantics defined in `01-protocol/06-access-control-model.md`, so authorization state is visible, replayable, and verifiable like any other data.

Apps are first-class participants in the protocol. Each app has its own namespace, its own schemas, and its own portion of the graph. Schemas are defined by apps and stored in the graph itself, as described in `02-architecture/managers/05-schema-manager.md` and `01-protocol/02-object-model.md`. They specify which object types exist, how they relate, and what values are valid. The protocol does not interpret application meaning. It enforces that meaning structurally and consistently, so every node evaluates the same rules when deciding whether a change is acceptable.

Every proposed change is wrapped in a protocol envelope, defined in `01-protocol/03-serialization-and-envelopes.md`. Graph message envelopes carry the operation records and required identifiers. Sync packages add sender identity, domain metadata, and sequence fields for ordering and replay checks. When a node receives an envelope, it validates it locally. Structure is checked first, including object model invariants and app namespace boundaries. Schema rules are then applied to ensure the change fits the app's schema. Access control is evaluated next using graph-encoded permissions. Only if all checks succeed is the change assigned a global order and committed. This pipeline is defined across `02-architecture/managers/07-graph-manager.md`, `02-architecture/managers/05-schema-manager.md`, and `02-architecture/managers/06-acl-manager.md`.

History is append-only and ordered, as defined in `01-protocol/07-sync-and-consistency.md`. Nodes exchange signed, ordered envelopes rather than mutable state. Each node replays those sequences independently and accepts only the parts that satisfy its local rules. Ordering comes from protocol-defined sequence assignment, not from message arrival or wall-clock time. This is what allows nodes to diverge temporarily, operate offline, and still converge without trusting transport or peers.

The result is a protocol where apps, schemas, identities, permissions, and records all live in the same verifiable structure. The graph is not an internal implementation detail. It *is* the protocol surface. Everything else, networking, storage engines, frontend frameworks, exists only to move envelopes in and out of that structure.

---

## Backend component model

The backend is the part of 2WAY that makes the rules real. It is not a set of cooperating components that try to behave by convention. It is one integrated system that decides what is valid, what is allowed, what order changes land in, and what gets stored. If something fails validation, it does not become part of state, regardless of who sent it or how it arrived.

That is the key difference from architectures built around loose roles like clients, servers, and relays. In those systems, correctness often depends on shared assumptions, relay behavior, server-side business logic, or social norms. In 2WAY, authority lives in the protocol enforcement pipeline that every node runs locally. A node does not accept state because a peer says it is fine. It accepts state because it can verify it and it passes the same checks it would apply to its own writes.

The backend is built from singleton managers with narrow jobs that fit together into one path for reads and writes (see `02-architecture/managers/00-managers-overview.md`). Config Manager loads configuration and rejects unsafe settings (`02-architecture/managers/01-config-manager.md`). Auth Manager resolves local sessions into an `OperationContext` (`02-architecture/managers/04-auth-manager.md`, `01-protocol/00-protocol-overview.md`). Key Manager owns private keys and performs signing and encryption for trusted callers (`02-architecture/managers/03-key-manager.md`). App Manager registers apps and app identities (`02-architecture/managers/08-app-manager.md`). Schema Manager checks that a change matches the app's declared structure (`02-architecture/managers/05-schema-manager.md`). ACL Manager checks that the caller has the right to perform it, using the current `OperationContext` (`02-architecture/managers/06-acl-manager.md`). Graph Manager is the only place where writes are accepted. It validates object model invariants, assigns a `global_seq`, and commits through Storage Manager (`02-architecture/managers/07-graph-manager.md`, `02-architecture/managers/02-storage-manager.md`). State Manager coordinates ordered sync and package construction from accepted history (`02-architecture/managers/09-state-manager.md`). Network Manager admits peers, verifies and transports packages with DoS Guard and Key Manager, and never changes protocol data (`02-architecture/managers/10-network-manager.md`, `02-architecture/managers/14-dos-guard-manager.md`). Event and Log Managers record what happened and why (`02-architecture/managers/11-event-manager.md`, `02-architecture/managers/12-log-manager.md`). Health and DoS Guard Managers keep the node stable and reject load before correctness can be threatened (`02-architecture/managers/13-health-manager.md`, `02-architecture/managers/14-dos-guard-manager.md`).

Services sit above the managers and provide higher-level behavior. They turn user intent into protocol-compliant operations, expose backend endpoints, and do app-specific aggregation or validation when needed. They do not get special authority. They cannot write around the managers, they cannot bypass schema or ACL checks, and they cannot touch keys, storage, or sockets directly. They must always call into the same enforcement path with a complete `OperationContext`.

There are two service classes. System services are always present and cover shared workflows that multiple apps rely on. App extension services are optional and scoped to one app. They exist for backend-heavy features like indexing or specialized queries, and removing them must not break the core or corrupt state.

The point of this design is that the backend behaves like a kernel. It enforces one coherent model of validity, permission, ordering, and persistence. Everything above it can change, but the enforcement does not become optional.

---

## Security framing

2WAY assumes untrusted networks and potentially hostile peers, so the controls are structural rather than policy text. Each device keeps its own keys, log, and durable state, which blocks a compromised operator from revoking global authority. Inputs are checked in order through schema, capability validation, and repeatable ordering before storage commits, and permission edges plus relationship depth limit unsolicited reach and fake-identity influence. DoS protection comes from Auth, Network, and DoS Guard Managers that throttle abusive traffic and fail closed when resources tighten, while Log and Event Managers capture reasons and signals so applications can respond without guesswork. Recovery stays simple because a node can rebuild by replaying signed history, with no special bootstrap modes or hidden overrides.

The system guarantees that malformed writes never land, unauthorized operations fail identically everywhere, and history remains hard to fake. What the protocol enables but does not define: governance, policy meanings, incentive design, lives entirely in application schemas and data.

---

## Application model

Applications behave like state machines you can replay. They define schemas, rules, and desired capabilities, subscribe to the ordered feed the system maintains locally, let users work against local state even offline, and propose changes through system interfaces so authority, ordering, and durability stay uniform. Developers inherit identity, permissions, sync, and audit, which keeps the focus on domain logic and UX. Testing becomes replaying ordered logs, and multiple implementations can coexist as long as they honor schemas and rules.

---

## Example domains

2WAY fits best when clear history, collaboration, or resilience matter more than centralized throughput. In messaging and chat, conversations, participants, messages, and ACLs become explicit graph objects, which keeps offline authorship and moderation trustworthy; social media and publishing use the same mapping for follows, posts, reactions, and moderation signals while keeping reach bounded. Markets and services model listings, offers, contracts, and reputation as graph-based state machines, and ride-hailing or logistics can keep trips, assignments, and settlements as ordered changes that stay auditable even when dispatch services change. Key revocation and recovery work cleanly because keys and approvals are data, not an admin side channel, and software supply chains treat releases, attestations, and trust hierarchies as checkable graph structures that clients validate locally. Governance and compliance keep approvals, vetoes, and escalations in the graph for replayable audit trails, and long-lived records like archives, ledgers, and attestations remain checkable even after the original UI is gone.

These examples share one theme: identity, permissions, ordering, and DoS controls sit below the application, so developers can offer powerful features without handing control to a central backend.

---

## Conformance

Conformance is binary. An implementation must honor every rule under all supported conditions, including offline operation and adversarial peers, and it must make forbidden behaviors structurally impossible rather than rely on logging or operator vigilance. Validation, authorization, and ordering have to run exactly as specified with no trust shortcuts, and every mutation must flow through the single ordered pipeline. Any deviation demands a recorded ADR with scope and compensating controls; without that, the implementation is out of spec even if it seems convenient.

---

## Scope boundary and status

This repository promises only what it states explicitly, and the examples illustrate possibilities rather than requirements. The proof of concept favors clarity and correctness over polish, and future ADRs may refine details. Treat the repo as the official statement of intent today and build against the guarantees it documents.

---

## Using this README

Start here when you need the essentials: what 2WAY is, why it exists, how the object model and managers work, and which guarantees implementations must uphold. Dive into the numbered folders for full detail, record exceptions as ADRs, and remember that every device enforces the same structure so collaboration can survive without surrendering authority.

---

## Acknowledgments

Credit to Martti Malmi (Sirius) for his work on Iris (formerly Identifi), an MIT-licensed project: https://github.com/irislib/iris-client. When it was still Identifi and a fork of the Bitcoin daemon in C++, seeing it sparked my early realization about what a private data layer could enable beyond simple broadcast messaging. Our projects evolved in different directions over the years, but his early work helped shape this thinking and deserves explicit credit.

---
