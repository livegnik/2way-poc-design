



# 05 Keys and Identity

## 1. Purpose and scope

This document defines the protocol-level model for identities and cryptographic keys in 2WAY. It specifies how identities are represented in the graph, how public keys are bound to identities, how authorship is asserted and verified, and which invariants and failure conditions apply. It is limited to protocol semantics. Storage, rotation procedures, revocation mechanics, transport encryption, ACL evaluation, and device or app policy are defined in other documents and are only referenced where required for correctness.

This specification references:

- [01-identifiers-and-namespaces.md](../../../01-protocol/01-identifiers-and-namespaces.md)
- [02-object-model.md](../../../01-protocol/02-object-model.md)
- [03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)
- [04-cryptography.md](../../../01-protocol/04-cryptography.md)
- [04-error-model.md](../../../04-interfaces/04-error-model.md)
- [06-access-control-model.md](../../../01-protocol/06-access-control-model.md)
- [07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
- [08-network-transport-requirements.md](../../../01-protocol/08-network-transport-requirements.md)
- [10-errors-and-failure-modes.md](../../../01-protocol/10-errors-and-failure-modes.md)
- [13-auth-session.md](../../../04-interfaces/13-auth-session.md)

This document is normative for all 2WAY-compliant implementations.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

- The definition of an identity at the protocol level.
- The binding between identities and public keys.
- The rules for authorship and ownership attribution.
- The requirements for identity references and signatures in envelopes.
- Mandatory invariants and rejection conditions related to identity and keys.

This specification does not cover the following:

- Key generation or entropy requirements.
- Private key storage or protection (see [02-architecture/managers/03-key-manager.md](../../../02-architecture/managers/03-key-manager.md)).
- Key rotation, revocation, or recovery workflows (see [02-architecture/managers/03-key-manager.md](../../../02-architecture/managers/03-key-manager.md)).
- Transport-level confidentiality (see [04-cryptography.md](../../../01-protocol/04-cryptography.md)).
- [Authorization rules](../../../01-protocol/06-access-control-model.md) or permission evaluation.
- [Application-specific identity semantics](../../../01-protocol/02-object-model.md).

## 3. Key model

### 3.1 Key type

The specific algorithms and encodings are defined in [04-cryptography.md](../../../01-protocol/04-cryptography.md).
