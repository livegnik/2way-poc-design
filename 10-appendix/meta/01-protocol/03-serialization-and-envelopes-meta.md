



# 03 Serialization and envelopes

## 1. Purpose and scope

This document defines the normative envelope structures and serialization rules used by 2WAY for local graph mutations and for node to node sync packages. It specifies field names, required and optional fields, how operations are represented, what is signed, and what must be rejected.

This specification references:

* [01-identifiers-and-namespaces.md](../../../01-protocol/01-identifiers-and-namespaces.md)
* [02-object-model.md](../../../01-protocol/02-object-model.md)
* [04-cryptography.md](../../../01-protocol/04-cryptography.md)
* [05-keys-and-identity.md](../../../01-protocol/05-keys-and-identity.md)
* [06-access-control-model.md](../../../01-protocol/06-access-control-model.md)
* [07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
* [08-network-transport-requirements.md](../../../01-protocol/08-network-transport-requirements.md)

This document does not define [object semantics](../../../01-protocol/02-object-model.md), [schema content](../../../02-architecture/managers/05-schema-manager.md), [ACL logic](../../../01-protocol/06-access-control-model.md), [sync selection rules](../../../01-protocol/07-sync-and-consistency.md), or [storage layout](../../../03-data/01-sqlite-layout.md). Those are defined elsewhere.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Envelope types and their required fields.
* Temporary minimal-commit subset constraints used during early durable-write bring-up.
* Operation identifiers and operation record shapes for [Parent](../../../01-protocol/02-object-model.md), [Attribute](../../../01-protocol/02-object-model.md), [Edge](../../../01-protocol/02-object-model.md), [Rating](../../../01-protocol/02-object-model.md).
* Serialization constraints for interoperability, including field naming conventions.
* The signed portion of envelopes that carry signatures.
* Structural validation and rejection conditions for malformed envelopes.

This specification does not cover the following:

* Mapping `type_key` to `type_id`, or validating [schema semantics](../../../02-architecture/managers/05-schema-manager.md).
* Evaluating [authorization](../../../01-protocol/06-access-control-model.md) and ACL rules.
* Assigning `global_seq` for local writes, or managing [sync state](../../../01-protocol/07-sync-and-consistency.md).
* Defining transport framing, auth tokens, or peer discovery (see [08-network-transport-requirements.md](../../../01-protocol/08-network-transport-requirements.md)).

## 3. Guarantees

This file does not define [authorization](../../../01-protocol/06-access-control-model.md), [schema validity](../../../02-architecture/managers/05-schema-manager.md), or application semantics, and therefore does not guarantee them.

## 4. Operation identifiers

Pruning requires complexity outside the scope of this protocol version.

## 5. Signed portion

The cryptographic algorithms and key distribution rules are defined in [04-cryptography.md](../../../01-protocol/04-cryptography.md) and [05-keys-and-identity.md](../../../01-protocol/05-keys-and-identity.md). This section defines only the binding between the signature and the serialized package fields.

## 6. Relationship to OperationContext

This document does not define OperationContext fields beyond those required to interpret the sync package metadata.

## 7. Sequence validation for sync packages

The specific sync_state rules are defined by [07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md). This section defines only the required envelope fields and their basic ordering constraints.
