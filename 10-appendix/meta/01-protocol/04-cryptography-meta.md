



# 04 Cryptography

## 1. Purpose and scope

This file specifies the cryptographic algorithms and protocol level rules for signing, verification, encryption, and decryption of 2WAY node to node messages and [graph envelopes](../../../01-protocol/03-serialization-and-envelopes.md). It defines what must be signed, what may be encrypted, what inputs are required, what outputs are produced, and what must be rejected on failure.

This specification references:

- [03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)
- [05-keys-and-identity.md](../../../01-protocol/05-keys-and-identity.md)
- [06-access-control-model.md](../../../01-protocol/06-access-control-model.md)
- [07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
- [08-network-transport-requirements.md](../../../01-protocol/08-network-transport-requirements.md)
- [09-dos-guard-and-client-puzzles.md](../../../01-protocol/09-dos-guard-and-client-puzzles.md)

Key lifecycle, key storage layout, identity creation, key rotation, revocation, alarm keys, delegated keys, and any identity binding semantics beyond providing a public key to verification are specified in [05-keys-and-identity.md](../../../01-protocol/05-keys-and-identity.md), [02-architecture/managers/03-key-manager.md](../../../02-architecture/managers/03-key-manager.md), and the [data layout documents](../../../03-data/01-sqlite-layout.md), and are out of scope here.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

- The required signing algorithm for protocol messages and envelopes.
- The required asymmetric encryption algorithm for confidential payloads.
- Canonical JSON serialization rules and signature encoding for signed payloads.
- What fields are cryptographically protected, and what fields must remain visible for routing and validation.
- Verification and decryption failure behavior at protocol boundaries.
- Cryptographic trust boundaries between [Network Manager](../../../02-architecture/managers/10-network-manager.md), [State Manager](../../../02-architecture/managers/09-state-manager.md), [Key Manager](../../../02-architecture/managers/03-key-manager.md), and [Graph Manager](../../../02-architecture/managers/07-graph-manager.md).

This specification does not cover the following:

- How keys are generated, stored, rotated, revoked, or delegated (see [05-keys-and-identity.md](../../../01-protocol/05-keys-and-identity.md)).
- How identities are represented in the graph (see [05-keys-and-identity.md](../../../01-protocol/05-keys-and-identity.md)).
- [ACL rules](../../../01-protocol/06-access-control-model.md), [schema rules](../../../02-architecture/managers/05-schema-manager.md), or write permissions.
- The full envelope schema beyond fields required to apply cryptographic rules (see [03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)).

## 3. Graph envelopes transmitted over remote sync

The full envelope and operation structure is defined in [03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md) and in the PoC build guide. This file defines only the cryptographic rules that apply to those structures.

## 4. Signed portion

The cryptographic algorithms and key distribution rules are defined in [04-cryptography.md](../../../01-protocol/04-cryptography.md) and [05-keys-and-identity.md](../../../01-protocol/05-keys-and-identity.md). This section defines only the binding between the signature and the serialized package fields.

## 5. Relationship to OperationContext

This document does not define OperationContext fields beyond those required to interpret the sync package metadata.

## 6. Sequence validation for sync packages

The specific sync_state rules are defined by [07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md). This section defines only the required envelope fields and their basic ordering constraints.

## 7. Guarantees

The cryptographic layer provides no guarantee of:

- [Authorization](../../../01-protocol/06-access-control-model.md) correctness.
- [Schema](../../../02-architecture/managers/05-schema-manager.md) correctness.
- Delivery, ordering, liveness, or availability.

## 8. Cryptographic success with higher layer rejection

The handling of peer scoring, rate limiting, and sync state consequences of repeated failures is defined in [09-dos-guard-and-client-puzzles.md](../../../01-protocol/09-dos-guard-and-client-puzzles.md) and [07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md), not in this file.
