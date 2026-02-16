



# 08 Network transport requirements

## 1. Purpose and scope

This document defines the normative requirements for the network transport layer of the 2WAY protocol. It specifies the responsibilities, invariants, guarantees, allowed behaviors, forbidden behaviors, and failure handling of the transport abstraction. It does not define concrete network implementations, routing mechanisms, [cryptographic formats](../../../01-protocol/04-cryptography.md), or [sync logic](../../../01-protocol/07-sync-and-consistency.md) beyond transport level constraints. All higher level protocol semantics are defined elsewhere.

This specification references:

- [03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)
- [04-cryptography.md](../../../01-protocol/04-cryptography.md)
- [05-keys-and-identity.md](../../../01-protocol/05-keys-and-identity.md)
- [06-access-control-model.md](../../../01-protocol/06-access-control-model.md)
- [07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
- [09-dos-guard-and-client-puzzles.md](../../../01-protocol/09-dos-guard-and-client-puzzles.md)
- [10-network-manager.md](../../../02-architecture/managers/10-network-manager.md)
- [14-dos-guard-manager.md](../../../02-architecture/managers/14-dos-guard-manager.md)

## 2. Position in the system

The transport layer is not a trust boundary and must be treated as adversarial by all consuming components.

## 3. Responsibilities and boundaries

All correctness and security guarantees are enforced above this layer, including those in [03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md) and [07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md).

This specification does not cover the following:

- Authenticating peer identity (see [05-keys-and-identity.md](../../../01-protocol/05-keys-and-identity.md)).
- Authorizing operations (see [06-access-control-model.md](../../../01-protocol/06-access-control-model.md)).
- [Verifying cryptographic signatures](../../../01-protocol/04-cryptography.md) or selecting public keys.
- [Encrypting](../../../01-protocol/04-cryptography.md) or decrypting payloads.
- Enforcing replay protection, ordering, or deduplication (see [07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)).
- Inspecting or interpreting [envelope contents](../../../01-protocol/03-serialization-and-envelopes.md).
- Applying [schema](../../../02-architecture/managers/05-schema-manager.md), [ACL](../../../01-protocol/06-access-control-model.md), or sync-domain policy.
- Persisting envelopes beyond transient buffering required for delivery.
- Performing sync reconciliation or state repair.
