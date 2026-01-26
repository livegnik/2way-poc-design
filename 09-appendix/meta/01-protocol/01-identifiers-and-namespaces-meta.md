



# 01 Identifiers and Namespaces

## 1. Purpose and scope

This document defines the identifier classes and namespace rules used by the 2WAY protocol as specified by the PoC design. It establishes how identities, applications, objects, domains, and schemas are named, scoped, and referenced at the protocol level. It specifies invariants, guarantees, allowed behaviors, forbidden behaviors, and failure handling required for correctness and security.

This specification references:

* [02-object-model.md](02-object-model.md)
* [04-cryptography.md](04-cryptography.md)
* [05-keys-and-identity.md](05-keys-and-identity.md)
* [06-access-control-model.md](06-access-control-model.md)
* [07-sync-and-consistency.md](07-sync-and-consistency.md)
* [08-network-transport-requirements.md](08-network-transport-requirements.md)
* [10-errors-and-failure-modes.md](10-errors-and-failure-modes.md)

This document is authoritative only for identifier semantics and namespace isolation. It does not define [cryptographic primitives](04-cryptography.md), [schema content](02-object-model.md), [ACL logic](06-access-control-model.md), [sync mechanics](07-sync-and-consistency.md), [storage layout](../03-data/01-sqlite-layout.md), or [network transport](08-network-transport-requirements.md), except where identifier structure directly constrains those systems. All such behavior is defined elsewhere and referenced implicitly.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining all identifier classes used by the protocol.
* Defining namespace boundaries and isolation rules.
* Defining identifier uniqueness, immutability, and lifetime guarantees.
* Defining how identifiers are interpreted across trust boundaries.
* Defining rejection behavior for invalid, ambiguous, or unauthorized identifier usage.

This specification does not cover the following:

* [Key generation](04-cryptography.md), signing algorithms, or encryption algorithms.
* [Graph object schemas](02-object-model.md) or attribute semantics.
* [Access control](06-access-control-model.md) evaluation rules.
* [Sync ordering](07-sync-and-consistency.md), conflict resolution, or replication mechanics.
* [Physical storage](../03-data/01-sqlite-layout.md), indexing, or persistence strategies.
* [Network addressing](08-network-transport-requirements.md) or peer discovery identifiers.

## 3. Guarantees summary

This specification guarantees:

* Stable identity anchoring.
* Deterministic object ownership.
* Strict namespace isolation.
* Predictable failure behavior.
* Absence of identifier-based privilege escalation.

No guarantees beyond those explicitly stated are implied.
