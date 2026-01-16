



# 2WAY design repository in short

Looking for a more comprehensive read-through? See [README-long.md](README-long.md).

2WAY is a local-first, peer-to-peer protocol and backend that gives decentralized applications device-level identity, permissions, ordering, sync, and audit guarantees so people can collaborate without trusting a central operator. Every device keeps its keys, write-once log, permission graph, and slice of shared state, and nodes validate each proposed change before it hits storage so malformed, replayed, or unauthorized input gets rejected at the boundary. The goal is to make resilient, multi-party software practical without trading away control.

---

## Why it exists

Centralized backends tie identity, policy, ordering, and storage to a single operator. If that operator changes plans, disappears, or gets compromised, users lose both history and authority. Federation often just moves trust to brittle bridges. 2WAY keeps durable structure separate from changing software: identities, relationships, and permissions live in a shared graph that each device enforces. Applications and vendors can evolve or even vanish without taking authority with them, and a device that reconnects later simply replays signed history until it catches up.

---

## Acknowledgments

Credit to Martti Malmi (Sirius) for his work on Iris (formerly Identifi), an MIT-licensed project: https://github.com/irislib/iris-client. When it was still Identifi and a fork of the Bitcoin daemon in C++, seeing it sparked my early realization about what a private data layer could enable beyond simple broadcast messaging. Our projects evolved in different directions over the years, but his early work helped shape this thinking and deserves explicit credit.

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

2WAY is a platform that replaces the conventional backend. Each node runs the same core controls for identity, permissions, ordering, storage, sync, and audit, so devices can go offline, keep working, and reconcile without giving up control. Applications define schemas and logic, interpret the ordered feed of accepted changes, and request new changes through strict interfaces rather than touching storage or keys directly.

The shared graph is the source of truth for identities, devices, relationships, capabilities, and application records. Ownership is explicit for every node and edge, so each change declares which identity governs it. History is write-once with checkable ancestry, payload hashes, and schema references, and peers replay one another's logs independently, accepting only the parts that satisfy local rules.

---

## Object and protocol model

`01-protocol/02-object-model.md` defines five core record types. A Parent anchors entities such as people, devices, contracts, or workflows, while an Attribute attaches typed payloads like profiles, configs, or encrypted blobs to a Parent; an Edge expresses relationships or workflow transitions, a Rating captures evaluations such as votes or endorsements, and an ACL is encoded as constrained Parent plus Attribute records so authorization state stays auditable.

Every record carries shared metadata (`app_id`, category, ids, owner, `global_seq`, sync flags). References are explicit triples `<app_id, category, id>`, so there are no implied lookups. Graph Manager enforces structural guards before anything else: strict app scoping, anchored ownership, and explicit references. Once a change passes this gate, Schema Manager checks types and rules, ACL Manager verifies capability, and Graph Manager commits the ordered change through Storage Manager. Rejection is consistent on every node, so divergence never hides behind network quirks.

---

## Backend component model

The backend is a collection of singleton managers that make the protocol enforceable, and it includes Config, Auth, Key, Schema, ACL, Graph, Storage, App, State, Network, Event, Log, Health, and DoS Guard Managers. Config Manager loads and checks configuration for safe runtime use, Auth Manager handles device and peer identity with local keys and logs, Key Manager owns signing and key storage, Schema and ACL Managers apply schemas and permissions using each `OperationContext`, Graph Manager orders writes, assigns `global_seq`, and hands committed data to Storage Manager, App Manager registers applications and scopes extensions, State Manager streams accepted history to peers, Network Manager handles exchange and encrypted transport, Event Manager emits consistent signals for accepted outcomes, Log Manager records structured reasons for accept or reject paths, Health Manager reports readiness and liveness, and DoS Guard Manager sheds load before corruption.

Services are long-lived workers that sit above the managers and compose their interfaces. They translate high-level intent into ordered manager calls, add domain-specific validation, aggregate reads, and expose backend endpoints. Services never define protocol rules and never bypass the managers; every write still flows through Graph Manager with Schema and ACL checks, and every read is still governed by the same rules.

There are two service classes. System services are always present, run under the system app (`app_0`), and cover shared workflows like provisioning or sync helpers. App extension services are optional, bound to a single app, and must be removable without breaking the core. Both kinds of services are treated as untrusted by managers, must include a complete `OperationContext` on every call, and cannot touch storage, keys, or network sockets directly.

Managers form one pipeline for reads and writes. Unsigned or ambiguous input never bypasses it, and there are no trusted fast paths. Optional services (applications, automation, UIs) sit above the managers and must obey the same interfaces.

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
