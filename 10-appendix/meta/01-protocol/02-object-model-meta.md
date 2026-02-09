



# 02 Object model

## 1. Purpose and scope

This document defines the normative graph object model used by 2WAY. It specifies the canonical object categories, required fields, structural constraints, and invariants that must hold for any object to be accepted into the graph.

This specification references:

* [01-identifiers-and-namespaces.md](../../../01-protocol/01-identifiers-and-namespaces.md)
* [03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)
* [04-cryptography.md](../../../01-protocol/04-cryptography.md)
* [05-keys-and-identity.md](../../../01-protocol/05-keys-and-identity.md)
* [06-access-control-model.md](../../../01-protocol/06-access-control-model.md)
* [07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)

This document does not define [serialization formats](../../../01-protocol/03-serialization-and-envelopes.md), [envelope structures](../../../01-protocol/03-serialization-and-envelopes.md), [schema semantics](../../../02-architecture/managers/05-schema-manager.md), [ACL evaluation logic](../../../01-protocol/06-access-control-model.md), [persistence layout](../../../03-data/01-sqlite-layout.md), or [synchronization behavior](../../../01-protocol/07-sync-and-consistency.md). Those concerns are defined in other protocol and architecture documents and are referenced here only where required to establish correctness boundaries.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* The canonical graph object categories.
* Required fields and reference structure for each object category.
* Object level invariants that are enforced independently of schema or ACL logic.
* Cross object and cross category structural constraints.
* Explicit rejection conditions for structurally invalid objects.

This specification does not cover the following:

* [Schema meaning](../../../02-architecture/managers/05-schema-manager.md), type validation, or value interpretation.
* [Authorization rules](../../../01-protocol/06-access-control-model.md) or ACL evaluation.
* [Envelope formats](../../../01-protocol/03-serialization-and-envelopes.md) or wire serialization.
* [Persistence schemas](../../../03-data/01-sqlite-layout.md), indexes, or query behavior.
* [Sync ordering](../../../01-protocol/07-sync-and-consistency.md), conflict resolution, or domain selection.

### 3. Guarantees

This document does not guarantee [schema validity](../../../02-architecture/managers/05-schema-manager.md), [authorization correctness](../../../01-protocol/06-access-control-model.md), or semantic consistency beyond structural constraints.

### 4. Required metadata fields

The presence and immutability of these fields are defined here. Their assignment and interpretation are defined elsewhere, including [01-identifiers-and-namespaces.md](../../../01-protocol/01-identifiers-and-namespaces.md) and [07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md).

### 5. Inputs

Authentication, [signature verification](../../../01-protocol/04-cryptography.md), [schema validation](../../../02-architecture/managers/05-schema-manager.md), and [ACL evaluation](../../../01-protocol/06-access-control-model.md) are assumed to occur outside this specification.
