



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

## 3. Protocol layers and companion specifications

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
