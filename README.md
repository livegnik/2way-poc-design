# 2WAY in short

Looking for a more comprehensive read-through? See [README-long.md](README-long.md).

2WAY is a local-first, peer-to-peer protocol and backend. It gives decentralized applications device-level identity, permissions, ordering, sync, and audit guarantees so people can collaborate without trusting a central operator. Every device keeps its keys, append-only log, permission graph, and slice of shared state. Nodes validate every proposed change before it hits storage, so malformed, replayed, or unauthorized input dies at the boundary. The goal is to make resilient, multi-party software practical without trading away control.

---

## Why it exists

Centralized backends weld identity, policy, ordering, and storage to a single operator. The moment that operator changes plans, disappears, or gets compromised, users lose both history and authority. Federation often just shifts trust to brittle bridges. 2WAY separates durable structure from transient software: identities, relationships, and permissions live in a shared graph that each device enforces. Applications and vendors can evolve or even vanish without dragging authority along, and a device that reconnects later simply replays signed history until it catches up.

---

## Repository guide

This repo is the normative design set for the proof of concept. It defines scope, invariants, architecture, object models, security framing, flows, and acceptance criteria. Lower-numbered folders carry higher authority. When conflicts appear, record an ADR in `08-decisions` so exceptions stay visible.

| Folder | Focus |
| --- | --- |
| `00-scope` | Vocabulary, boundary, assumptions |
| `01-protocol` | Wire format, object model, invariants |
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

2WAY is an application substrate that replaces the conventional backend. Each node runs the same authority stack: identity, permissions, ordering, storage, sync, and audit. Nodes can go offline, keep working, then reconcile without surrendering custody. Applications describe schemas and logic, interpret the ordered feed of accepted changes, and request new mutations through deterministic interfaces. They never bypass validation, own storage, or manage cryptographic keys directly.

The shared graph is the fact store for identities, devices, relationships, capabilities, and application records. Ownership is explicit for every node and edge, so each mutation declares which identity governs it. History is append-only with verifiable ancestry, payload hashes, and schema references. Peers replay one another’s logs independently and accept only the parts that satisfy local invariants.

---

## Object and protocol model

`01-protocol/02-object-model.md` defines five canonical record types:

- **Parent**: anchors entities such as people, devices, contracts, or workflows.
- **Attribute**: attaches typed payloads (profiles, configs, encrypted blobs) to a Parent.
- **Edge**: expresses relationships, delegations, dependencies, or workflow transitions.
- **Rating**: captures evaluations like votes, moderation decisions, or endorsements.
- **ACL**: encoded as constrained Parent + Attribute records so authorization state is auditable.

Every record carries shared metadata (`app_id`, category, ids, owner, `global_seq`, sync flags). References are explicit triples `<app_id, category, id>`, so there are no implied lookups. Graph Manager enforces structural guards before anything else: strict app scoping, anchored ownership, and explicit references. Once a proposal survives this gate, Schema Manager checks types and invariants, ACL Manager verifies capability, and Graph Manager commits the ordered mutation through Storage Manager. Rejection is deterministic on every node, so divergence never hides behind network quirks.

---

## Backend component model

The backend is a collection of singleton managers that make the protocol enforceable:

- **Auth Manager** resolves device and peer identity using local keys and append-only logs.
- **Graph Manager** validates structure, orders writes, and assigns `global_seq`.
- **Schema Manager** enforces schemas and domain logic supplied by applications.
- **ACL Manager** evaluates permissions using the current graph and `OperationContext`.
- **Storage Manager** persists commits, histories, and cryptographic material.
- **State Manager** streams accepted history to peers and reconciles inbound logs.
- **Network Manager** handles peer exchange, pacing, and encrypted transport.
- **DoS Guard Manager** watches load and sheds work before corruption.
- **Event and Log Managers** record deterministic reasons for accept or reject paths.

Managers form one pipeline for reads and writes. Unsigned or ambiguous input never bypasses it, and there are no trusted fast paths. Optional services (applications, automation, UIs) sit above the managers and must obey the same interfaces.

---

## Security framing

2WAY assumes untrusted networks and potentially hostile peers. Security controls are structural, not policy text:

- **Local custody**: every device holds its keys, log, and durable state. A compromised operator cannot revoke global authority.
- **Guarded inputs**: schema checks, capability validation, and deterministic ordering run before storage commits.
- **Degrees of separation**: permission edges and relationship depth limit unsolicited reach and Sybil influence.
- **DoS containment**: Auth, Network, and DoS Guard Managers throttle unauthenticated or abusive traffic and fail closed when resources tighten.
- **Auditability**: Log Manager captures structured reasons for acceptance or rejection, and Event Manager emits deterministic signals so applications can react without heuristics.
- **Replay and recovery**: rebuilding a node means replaying signed history; there are no special bootstrap modes or hidden overrides.

The system guarantees that malformed writes never land, unauthorized operations fail identically everywhere, and history remains tamper-evident. What the protocol enables but does not define—governance, policy meanings, incentive design—lives entirely in application schemas and data.

---

## Application model

Applications act as deterministic state machines:

1. Define schemas, invariants, and desired capabilities.
2. Subscribe to the ordered feed the substrate maintains locally.
3. Let users work against local state, even offline.
4. Propose mutations through substrate interfaces so authority, ordering, and durability stay uniform.

Developers inherit identity, permissions, sync, and audit, so they focus on domain logic and UX. Testing becomes replaying ordered logs. Multiple implementations can coexist as long as they honor schemas and invariants.

---

## Example domains

2WAY shines when provenance, collaboration, or survivability matter more than centralized throughput. Patterns include:

- **Messaging and chat**: conversations, participants, messages, and ACLs become explicit graph objects, so offline authorship and moderation stay trustworthy.
- **Social media and publishing**: follows, posts, reactions, and moderation signals map to Parents, Attributes, Edges, and Ratings while keeping reach bounded.
- **Markets and services**: listings, offers, contracts, and reputation are state machines encoded in the graph, so multiple marketplaces can share data without a central arbiter.
- **Ride-hailing, delivery, logistics**: trips, assignments, and settlements flow as ordered mutations that stay auditable even when dispatch services change.
- **Key revocation and recovery**: keys and approvals are data, so revocation is a standard mutation, not an administrative side channel.
- **Software supply chains**: releases, attestations, and trust hierarchies become verifiable graph structures that clients validate locally.
- **Governance and compliance**: approvals, vetoes, and escalations live in the graph, creating tamper-evident audit trails that anyone can replay.
- **Long-lived records**: archives, ledgers, and attestations remain verifiable independent of the original UI.

These examples share one theme: identity, permissions, ordering, and denial-of-service controls sit below the application, so developers can offer powerful features without handing control to a central backend.

---

## Conformance

Conformance is binary. An implementation must:

- Honor every invariant under all supported conditions, including offline operation and adversarial peers.
- Keep forbidden behaviors structurally impossible; logging or operator vigilance is not a substitute.
- Run validation, authorization, and ordering exactly as specified, with no trust shortcuts.
- Flow every mutation through the single serialized pipeline.

Any deviation demands a recorded ADR with scope and compensating controls. Without that, the implementation is out of spec even if it seems convenient.

---

## Scope boundary and status

This repository promises only what it states explicitly. Examples illustrate possibilities, not requirements. The proof of concept favors clarity and correctness over polish, and future ADRs may refine details. Treat the repo as the authoritative statement of intent today and build against the guarantees it documents.

---

## Using this README-short

Start here when you need the essentials: what 2WAY is, why it exists, how the object model and managers work, and which guarantees implementations must uphold. Dive into the numbered folders for full detail, record exceptions as ADRs, and remember that every device enforces the same structure so collaboration can survive without surrendering authority.
