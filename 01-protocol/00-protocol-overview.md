# 00 Protocol overview

## 1. Purpose and scope

This document introduces the 2WAY protocol, a graph-native, envelope-based replication system for distrustful peers. It explains how the protocol layers interact, the boundaries they enforce, and the guarantees they collectively provide. The goal is to help implementers understand the intent of the detailed specifications in this folder before consulting each specialty document.

## 2. Responsibilities

This specification is responsible for the following:

- The high-level responsibilities of the protocol, including how identities author data, how that data is serialized, transported, validated, and synchronized.
- The invariants that must hold across all protocol layers so that downstream documents can focus on their own scopes without redefining the whole system.
- How failures propagate and which components own recovery or rejection decisions.

This specification does not cover the following:

- Concrete storage formats, database schemas, deployment topologies, or network routing strategies.
- User interfaces, operational tooling, peer discovery, or policy decisions beyond the protocol boundary.
- Transport-specific encodings, API payloads, or implementation-specific optimizations.

## 3. Protocol posture and guiding principles

- Identities are explicit graph objects anchored in `app_0` and bound to keys; nothing is inferred from transport metadata (`01-identifiers-and-namespaces.md`, `05-keys-and-identity.md`).
- All persistent data is represented using the canonical object model and accessed through supervised operations (`02-object-model.md`, `03-serialization-and-envelopes.md`).
- The network and peers are untrusted; only cryptographic verification and local policy create trust (`04-cryptography.md`, `08-network-transport-requirements.md`).
- Envelopes are the atomic unit of mutation and sync; they are accepted or rejected as a whole (`03-serialization-and-envelopes.md`, `07-sync-and-consistency.md`).
- Authorization, schema rules, and sync ordering are enforced deterministically and locally before state changes occur (`06-access-control-model.md`, `07-sync-and-consistency.md`, `09-errors-and-failure-modes.md`).
- Version negotiation is explicit and conservative; major mismatches are fatal (`10-versioning-and-compatibility.md`).

## 4. Protocol layers and companion specifications

The protocol stack is partitioned so that each layer owns a narrow set of invariants. The detailed behavior of each layer is defined by the documents in this folder:

- `01-identifiers-and-namespaces.md` defines identifier classes, namespace isolation, and rejection rules for ambiguous or unauthorized identifiers.
- `02-object-model.md` defines the canonical Parent, Attribute, Edge, Rating, and ACL record structures plus immutable metadata constraints.
- `03-serialization-and-envelopes.md` defines the envelope format, supervised operation identifiers, signed portions, and structural validation rules.
- `04-cryptography.md` defines signing, optional encryption, and the trust boundaries between Key Manager, Network Manager, and State Manager.
- `05-keys-and-identity.md` defines how identities are represented, how keys bind to identities, and how authorship is proven.
- `06-access-control-model.md` defines the authorization order, ownership semantics, and ACL evaluation rules.
- `07-sync-and-consistency.md` defines the synchronization model, ordering constraints, and the unit of replication.
- `08-network-transport-requirements.md` defines the minimal, adversarial network transport abstraction and its invariants.
- `09-errors-and-failure-modes.md` defines canonical error classes, precedence rules, and failure handling guarantees.
- `10-versioning-and-compatibility.md` defines protocol version tuples, compatibility checks, and mandatory rejection behavior for mismatches.

## 5. Operation lifecycle

### 5.1 Authoring and local submission

An identity resolves to a Parent with bound keys (05). The author chooses the application namespace and object types defined by the schema (01, 02) and prepares operations that respect ownership and ACL policies (06). All local writes, even internal services, must submit operations through graph message envelopes using the serialization rules in `03-serialization-and-envelopes.md`.

### 5.2 Envelope construction and validation

Operations are grouped into an envelope whose structure, field names, and allowable operations are defined in `03-serialization-and-envelopes.md`. Structural validation runs before any schema or ACL checks, preventing malformed data from crossing the Graph Manager boundary. The envelope establishes a single author context and target sync domain, which become inputs to downstream authorization and sequencing logic.

### 5.3 Secure transport preparation

For remote sync, State Manager wraps the graph envelope inside a sync package, adds sequence metadata, and requests Key Manager to sign (04). Network Manager is responsible for attaching the signature, optional ECIES payload encryption, and providing the opaque bytes to the transport abstraction (04, 08). Transport maintains byte integrity and signaling but does not perform validation or ordering (`08-network-transport-requirements.md`).

### 5.4 Reception, validation, and persistence

The receiving node reverses the process: Network Manager verifies signatures and decrypts payloads (04), State Manager enforces sync ordering per domain and peer (07), and Graph Manager executes structural validation, schema validation, ACL evaluation, and object model checks (02, 03, 06). Only when every stage succeeds is the envelope persisted and the sync state advanced (07). Any failure triggers the canonical rejection behavior defined in `09-errors-and-failure-modes.md`.

### 5.5 Sync propagation and replay protection

Sync state is maintained per peer and domain and advances only after successful envelope application (`07-sync-and-consistency.md`). Peers exchange envelopes monotonically based on local global sequence numbers, and replays or gaps are rejected. Failure to meet version compatibility or sequence expectations aborts the interaction without side effects (07, 10).

## 6. Guarantees and invariants

- Every accepted envelope has exactly one verified author identity and signature bound to the declared metadata (05).
- All graph mutations use the canonical object categories and immutable metadata defined by the object model (02).
- Authorization is deterministic, local, and enforced before persistence or sync state advancement (06).
- Sync ordering is strictly monotonic per peer and domain; no partial acceptance or skipped ranges occur (07).
- Transport-level anomalies cannot cause semantic changes because envelopes are signed end-to-end and validated locally (04, 08).
- Version compatibility decisions are made before resource allocation, preventing downgrade attacks or undefined behavior (10).

## 7. Allowed and forbidden behaviors

### 7.1 Allowed

- Independent creation of identifiers and objects within declared namespaces, provided they satisfy structural, schema, and ACL rules (01, 02, 06).
- Concurrent connections to multiple peers and domains, as long as each session honors ordering and sync boundaries (07, 08).
- Use of multiple keys per identity and selective domain participation, as long as signatures and domain declarations remain consistent (05, 07).
- Silent rejection of invalid remote input while continuing to process other peers (07, 09).

### 7.2 Forbidden

- Bypassing envelopes to mutate graph state, or mutating data outside the canonical object model (02, 03).
- Accepting unsigned or cryptographically invalid packages, or guessing at metadata to recover from failures (04, 08, 09).
- Allowing schema, ACL, or authorization checks to depend on network metadata or remote assertions (06, 08).
- Reassigning identifiers, weakening namespace isolation, or retroactively mutating ownership (01, 02, 05).
- Performing partial application of an envelope or advancing sync state after a rejection (07, 09).

## 8. Failure posture

Failures are classified by the earliest stage that detects them (structural, cryptographic, schema, authorization, sync, or resource) as defined in `09-errors-and-failure-modes.md`. Rejection at any stage is atomic: no state changes, no sequence advancement, and no retries implied. Structural errors take precedence, cryptographic errors supersede schema and authorization, and revocation decisions override freshness. Rejections may be silent to peers, while local callers receive symbolic error codes.

## 9. Compatibility and evolution

Protocol versions are expressed as `(major, minor, patch)` tuples (`10-versioning-and-compatibility.md`). Nodes must negotiate versions before trust or state exchange; mismatched major versions or unsupported minor features force deterministic rejection. When peers share a major version and the receiver's minor version is equal or higher, the interaction proceeds using the remote minor version as the effective feature ceiling. No implicit downgrade, feature guessing, or fallback mode is permitted, ensuring that the guarantees in the preceding sections remain valid over time.
