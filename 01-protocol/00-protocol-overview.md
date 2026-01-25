



# 00 Protocol overview

## 1. Purpose and scope

This document defines the role and posture of the 2WAY protocol within the PoC design repository. It is a graph-native, envelope-based mutation and replication protocol intended for distrustful peers. It explains protocol boundaries, mandatory invariants, and how the protocol's subsystems compose, without redefining details owned by other protocol files.

This overview references:

* [01-protocol/**](./)
* [01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)
* [02-object-model.md](02-object-model.md)
* [03-serialization-and-envelopes.md](03-serialization-and-envelopes.md)
* [04-cryptography.md](04-cryptography.md)
* [05-keys-and-identity.md](05-keys-and-identity.md)
* [06-access-control-model.md](06-access-control-model.md)
* [07-sync-and-consistency.md](07-sync-and-consistency.md)
* [08-network-transport-requirements.md](08-network-transport-requirements.md)
* [09-dos-guard-and-client-puzzles.md](09-dos-guard-and-client-puzzles.md)
* [10-errors-and-failure-modes.md](10-errors-and-failure-modes.md)
* [11-versioning-and-compatibility.md](11-versioning-and-compatibility.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* The protocol's externally observable responsibilities, identity binding, envelope submission, validation ordering, and sync sequencing posture.
* Mandatory invariants that all implementations must preserve across local writes and remote synchronization.
* The lifecycle of an operation from authoring through persistence, including where rejection must occur.

This specification does not cover the following:

* [Database schema details](../03-data/01-sqlite-layout.md), table layouts, index choices, or persistence optimizations.
* [Concrete transport encodings](08-network-transport-requirements.md), routing, peer discovery, or deployment topology.
* UI behavior, app workflows, or domain-specific application semantics beyond protocol constraints.

## 3. Protocol posture and guiding principles

* All graph mutations use [graph message envelopes](03-serialization-and-envelopes.md), including local writes, so local and remote paths share the same validation and persistence pipeline.
* [Graph Manager](../02-architecture/managers/07-graph-manager.md) is the only write path. [Storage Manager](../02-architecture/managers/02-storage-manager.md) is the only raw database path. No component may bypass these boundaries.
* The network is untrusted. Trust is established only via [cryptographic verification](04-cryptography.md) and local policy enforcement.
* Authorization is deterministic and local. It is enforced before persistence and before advancing [sync state](07-sync-and-consistency.md).
* Synchronization is incremental and sequence-anchored. A receiver must reject replayed, out-of-order, malformed, or policy-violating packages without side effects (see [07-sync-and-consistency.md](07-sync-and-consistency.md)).
* App namespaces are isolated. Each app defines its own types, ratings, and domain semantics, and those semantics cannot spill into other apps without explicit interpretation by a consuming app.

## 4. Protocol layers and companion specifications

The protocol is intentionally partitioned so each layer owns a narrow set of invariants. Detailed behavior lives in companion specifications within [01-protocol/**](./):

* [01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md) defines identifier classes, namespace isolation, and rejection rules for ambiguous identifiers.
* [02-object-model.md](02-object-model.md) defines Parent, Attribute, Edge, Rating, and ACL structures plus immutable metadata constraints.
* [03-serialization-and-envelopes.md](03-serialization-and-envelopes.md) defines graph message envelope structure, operation identifiers, signed portions, and structural validation rules.
* [04-cryptography.md](04-cryptography.md) defines secp256k1 signing, ECIES encryption usage, verification rules, and key handling boundaries.
* [05-keys-and-identity.md](05-keys-and-identity.md) defines identity representation in `app_0`, key binding, authorship proof, and key lifecycle primitives.
* [06-access-control-model.md](06-access-control-model.md) defines ownership semantics, ACL evaluation inputs, and authorization ordering.
* [07-sync-and-consistency.md](07-sync-and-consistency.md) defines sync domains, sequence tracking, package construction, package application, and monotonicity requirements.
* [08-network-transport-requirements.md](08-network-transport-requirements.md) defines the adversarial transport abstraction and mandatory signaling and delivery properties.
* [10-errors-and-failure-modes.md](10-errors-and-failure-modes.md) defines canonical error classes, precedence rules, and mandatory rejection behavior.
* [11-versioning-and-compatibility.md](11-versioning-and-compatibility.md) defines version tuples and compatibility checks.
* [09-dos-guard-and-client-puzzles.md](09-dos-guard-and-client-puzzles.md) defines admission control policy, client puzzle lifecycle, and DoS Guard Manager responsibilities.

## 5. Operation lifecycle

### 5.1 Authoring and local submission

* A local frontend request authenticates via a frontend session token.
* [Auth Manager](../02-architecture/managers/04-auth-manager.md) resolves the session token to an `identity_id`.
* The HTTP layer constructs an [OperationContext](../02-architecture/services-and-apps/05-operation-context.md) containing, at minimum, requester identity, `app_id`, a remote or local flag, and a trace id.
* The caller submits a [graph message envelope](03-serialization-and-envelopes.md) for all writes, even locally.
* Local automation jobs or internal services construct an [OperationContext](../02-architecture/services-and-apps/05-operation-context.md) with `is_remote=false` before submitting envelopes, following the same authorization and ordering rules as interactive requests.

### 5.2 Envelope construction and structural validation

* An [envelope](03-serialization-and-envelopes.md) contains one or more operations with supervised operation identifiers, using lowercase snake_case naming conventions.
* Structural validation runs before [schema validation](../02-architecture/managers/05-schema-manager.md) and before [ACL evaluation](06-access-control-model.md).
* Structural validation must reject malformed envelopes without allocating expensive resources or taking write locks.

### 5.3 Schema validation and authorization

* [Schema Manager](../02-architecture/managers/05-schema-manager.md) validates that referenced types belong to the declared app namespace, that values match their declared representation, and that relations respect allowed edge constraints.
* [ACL Manager](../02-architecture/managers/06-acl-manager.md) evaluates permissions using [OperationContext](../02-architecture/services-and-apps/05-operation-context.md), schema defaults, object-level overrides, and ownership semantics.
* If the envelope declares an author identity, the implementation must enforce that the author identity used for enforcement is explicit and consistent with the authenticated context, and must not be inferred from transport metadata.

### 5.4 Sequencing and persistence

* [Graph Manager](../02-architecture/managers/07-graph-manager.md) assigns a monotonic `global_seq` during successful application.
* Envelope application is transactional. Either the entire envelope is applied or none of it is.
* Persistence occurs only through [Storage Manager](../02-architecture/managers/02-storage-manager.md) after successful structural validation, schema validation, and authorization.

### 5.5 Remote synchronization

* [State Manager](../02-architecture/managers/09-state-manager.md) is the only producer of outbound sync packages and the only consumer of inbound sync packages.
* Remote sync uses the same [graph message envelope](03-serialization-and-envelopes.md) format as local writes, wrapped with sync metadata, including sender identity, sync domain name, and a declared sequence range such as `from_seq` and `to_seq`.
* [DoS Guard Manager](../02-architecture/managers/14-dos-guard-manager.md) enforces admission control and client puzzles before [Network Manager](../02-architecture/managers/10-network-manager.md) processes inbound connections, per [09-dos-guard-and-client-puzzles.md](09-dos-guard-and-client-puzzles.md).
* [Network Manager](../02-architecture/managers/10-network-manager.md) handles transport and cryptography, including signature creation and verification, and ECIES encryption where confidentiality is required (see [04-cryptography.md](04-cryptography.md)).
* The receiver enforces per-peer, per-domain ordering rules and must reject packages that are replayed, out of order, malformed, or inconsistent with known sync state.

## 6. Guarantees and invariants

* Every accepted envelope is validated structurally, validated against [schema rules](../02-architecture/managers/05-schema-manager.md), authorized via [ACL evaluation](06-access-control-model.md), and applied transactionally.
* [Graph Manager](../02-architecture/managers/07-graph-manager.md) is the only write path for Parents, Attributes, Edges, Ratings, and ACL-related mutations.
* All accepted writes receive a monotonic `global_seq`.
* [Sync ordering](07-sync-and-consistency.md) is monotonic per peer and per domain. Sync state advances only after successful envelope application.
* [Cryptographic verification](04-cryptography.md) precedes semantic processing for remote input. Unsigned or invalidly signed packages are rejected.
* Private keys are not serialized into the graph and are not emitted inside sync packages.

## 7. Allowed and forbidden behaviors

### 7.1 Allowed

* Local writes via HTTP using [graph message envelopes](03-serialization-and-envelopes.md), with authorization based on [OperationContext](../02-architecture/services-and-apps/05-operation-context.md).
* Remote sync via [State Manager](../02-architecture/managers/09-state-manager.md) using signed and optionally encrypted packages carrying graph envelopes and domain sequence metadata (see [04-cryptography.md](04-cryptography.md)).
* Multiple keys per identity and multi-device operation, provided authorization and key binding rules are enforced per the [identity specification](05-keys-and-identity.md).
* Silent rejection of invalid remote input while continuing to process other peers.

### 7.2 Forbidden

* Any mutation path that bypasses [graph message envelopes](03-serialization-and-envelopes.md) or bypasses [Graph Manager](../02-architecture/managers/07-graph-manager.md).
* Any direct database write outside [Storage Manager](../02-architecture/managers/02-storage-manager.md).
* Any authorization decision based on transport metadata or remote assertions not validated against local identity and [ACL state](06-access-control-model.md).
* Partial application of an envelope, or advancing sync state after a rejection.
* Accepting remote packages without [cryptographic verification](04-cryptography.md), or attempting to "guess" missing metadata to recover from failures.

## 8. Failure posture

* Rejection is atomic. A rejected envelope or package produces no state changes and does not advance sync state.
* Failures are classified by the earliest stage that detects them, including structural, cryptographic, schema, authorization, [sync ordering](07-sync-and-consistency.md), and resource constraints.
* Precedence is strict. Structural failures preempt schema and [ACL checks](06-access-control-model.md). Cryptographic failures preempt semantic processing. [Revocation decisions](05-keys-and-identity.md) override freshness decisions and must be applied before processing additional envelopes where applicable.
* Debugging and inspection surfaces are read-only and must remain behind administrative authorization.

## 9. Compatibility and evolution

* Protocol versions use `(major, minor, patch)` tuples.
* Major mismatches are fatal. Version negotiation occurs before trust or state exchange.
* No implicit downgrade, feature guessing, or fallback mode is permitted.
* Naming conventions for envelopes, domains, and events are normative and must remain consistent to preserve compatibility across nodes and tools.
