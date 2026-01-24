



# 04 Cryptography

## 1. Purpose and scope

This file specifies the cryptographic algorithms and protocol level rules for signing, verification, encryption, and decryption of 2WAY node to node messages and [graph envelopes](03-serialization-and-envelopes.md). It defines what must be signed, what may be encrypted, what inputs are required, what outputs are produced, and what must be rejected on failure.

This specification references:

- [03-serialization-and-envelopes.md](03-serialization-and-envelopes.md)
- [05-keys-and-identity.md](05-keys-and-identity.md)
- [06-access-control-model.md](06-access-control-model.md)
- [07-sync-and-consistency.md](07-sync-and-consistency.md)
- [08-network-transport-requirements.md](08-network-transport-requirements.md)
- [09-dos-guard-and-client-puzzles.md](09-dos-guard-and-client-puzzles.md)

Key lifecycle, key storage layout, identity creation, key rotation, revocation, alarm keys, delegated keys, and any identity binding semantics beyond providing a public key to verification are specified in [05-keys-and-identity.md](05-keys-and-identity.md), [02-architecture/managers/03-key-manager.md](../02-architecture/managers/03-key-manager.md), and the [data layout documents](../03-data/01-sqlite-layout.md), and are out of scope here.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

- The required signing algorithm for protocol messages and envelopes.
- The required asymmetric encryption algorithm for confidential payloads.
- What fields are cryptographically protected, and what fields must remain visible for routing and validation.
- Verification and decryption failure behavior at protocol boundaries.
- Cryptographic trust boundaries between [Network Manager](../02-architecture/managers/10-network-manager.md), [State Manager](../02-architecture/managers/09-state-manager.md), [Key Manager](../02-architecture/managers/03-key-manager.md), and [Graph Manager](../02-architecture/managers/07-graph-manager.md).

This specification does not cover the following:

- How keys are generated, stored, rotated, revoked, or delegated (see [05-keys-and-identity.md](05-keys-and-identity.md)).
- How identities are represented in the graph (see [05-keys-and-identity.md](05-keys-and-identity.md)).
- [ACL rules](06-access-control-model.md), [schema rules](../02-architecture/managers/05-schema-manager.md), or write permissions.
- The full envelope schema beyond fields required to apply cryptographic rules (see [03-serialization-and-envelopes.md](03-serialization-and-envelopes.md)).

## 3. Cryptographic algorithms

## 3.1 Signing

- All signatures use secp256k1.
- Signatures are applied to protocol message bytes as defined by the message serialization used for transport.
- Verification uses the corresponding public key supplied by local state as defined in [05-keys-and-identity.md](05-keys-and-identity.md).

## 3.2 Asymmetric encryption

- Confidentiality uses ECIES over secp256k1.
- Encryption and decryption operate on message bytes, or on explicitly designated payload portions.
- Encryption is applied only when the protocol step requires confidentiality.

## 3.3 Algorithm constraints

- Nodes must not negotiate alternative signing or encryption algorithms within the PoC protocol scope.
- Nodes must not accept messages that claim an unsupported algorithm.

## 4. Cryptographically protected structures

## 4.1 Node to node packages

Node to node packages are cryptographically protected at the package level.

A node to node package that crosses the node trust boundary defined by [08-network-transport-requirements.md](08-network-transport-requirements.md) must include:

- A signature over the package content.
- Sender identification sufficient for the receiver to select the correct public key from local state.

If confidentiality is required for the package payload, the payload must be encrypted using ECIES as specified in 3.2.

## 4.2 Graph envelopes transmitted over remote sync

Remote sync uses the same [graph envelope](03-serialization-and-envelopes.md) abstraction used for local writes, with additional metadata required for [sync](07-sync-and-consistency.md).

For cryptographic purposes, a remote sync envelope must include the following metadata fields, because they participate in validation and replay protection:

- sender identity
- domain name
- from_seq
- to_seq
- signature

The full envelope and operation structure is defined in [03-serialization-and-envelopes.md](03-serialization-and-envelopes.md) and in the PoC build guide. This file defines only the cryptographic rules that apply to those structures.

## 4.3 Signature coverage

A signature must cover all bytes whose modification could change meaning, [authorization context](06-access-control-model.md), or replay semantics.

At minimum, the signature must cover:

- The operations contained in the package or envelope.
- The sync metadata fields listed in 4.2 when present.

A receiver must treat any message as invalid if signature verification succeeds but the receiver cannot associate the verified signature with the exact metadata and operations the receiver is about to apply.

## 5. Visibility requirements for cryptographic processing

Fields required for routing, [sync validation](07-sync-and-consistency.md), and signature verification must remain visible to the receiver prior to decryption.

The protocol forbids encrypting the entire message in a way that prevents the receiver from:

- Selecting the correct public key for signature verification from local state.
- Reading domain name and sequence range values needed to validate ordering and replay constraints.

If partial encryption is used, the encrypted portion must be limited to payload bytes that are not required for the checks above.

## 6. Component interactions and trust boundaries

## 6.1 Key Manager

Inputs:

- Requests to sign bytes.
- Requests to decrypt ECIES ciphertext.
- Requests to encrypt bytes for a specified recipient public key.

Outputs:

- Signatures over provided bytes.
- Plaintext bytes after successful decryption.
- Ciphertext bytes after successful encryption.

Trust boundary:

- [Key Manager](../02-architecture/managers/03-key-manager.md) is the only component that may access private keys for signing and decryption.
- Callers must treat [Key Manager](../02-architecture/managers/03-key-manager.md) outputs as cryptographic results only. Authorization semantics are out of scope for Key Manager.

## 6.2 Network Manager

Inputs:

- Raw inbound remote packages from [transport](08-network-transport-requirements.md).
- Outbound packages produced by [State Manager](../02-architecture/managers/09-state-manager.md).

Outputs:

- Verified package bytes and extracted metadata for consumption by State Manager.
- Rejection of invalid packages.
- Encrypted and signed outbound packages for transport.

Trust boundary:

- [Network Manager](../02-architecture/managers/10-network-manager.md) terminates the network trust boundary and applies cryptographic verification and decryption required for remote packages.
- Network Manager must not interpret graph semantics, [schema semantics](../02-architecture/managers/05-schema-manager.md), or [ACL semantics](06-access-control-model.md).

## 6.3 State Manager

Inputs:

- Verified and, where required, decrypted packages from [Network Manager](../02-architecture/managers/10-network-manager.md).

Outputs:

- Envelopes submitted to [Graph Manager](../02-architecture/managers/07-graph-manager.md) for validation and application.
- Outbound sync packages provided to [Network Manager](../02-architecture/managers/10-network-manager.md) for signing and optional encryption.

Trust boundary:

- [State Manager](../02-architecture/managers/09-state-manager.md) must rely on cryptographic verification performed at the Network Manager boundary.
- State Manager must additionally enforce [sync ordering constraints](07-sync-and-consistency.md) using sequence metadata. Cryptographic validity does not override ordering rules.

## 6.4 Graph Manager

Inputs:

- Envelopes and operations accompanied by signer identity information as provided by [Network Manager](../02-architecture/managers/10-network-manager.md) and [State Manager](../02-architecture/managers/09-state-manager.md).

Outputs:

- Acceptance or rejection of operations based on validation, [schema](../02-architecture/managers/05-schema-manager.md), and [ACL processing](06-access-control-model.md).
- No direct cryptographic outputs.

Trust boundary:

- [Graph Manager](../02-architecture/managers/07-graph-manager.md) is cryptography agnostic. It must not perform signing, verification, encryption, or decryption.
- Graph Manager must not accept any remote sourced envelope that is not delivered through the [Network Manager](../02-architecture/managers/10-network-manager.md) and [State Manager](../02-architecture/managers/09-state-manager.md) path.

## 7. Invariants and guarantees

## 7.1 Invariants

- Every remote package that crosses the node trust boundary is either rejected or verified using secp256k1.
- If ECIES encryption is used for a payload, the payload is either decrypted successfully and processed, or rejected without partial application.
- Cryptographic verification and decryption occur before any envelope is eligible for graph application (see [03-serialization-and-envelopes.md](03-serialization-and-envelopes.md)).

## 7.2 Guarantees

When verification succeeds and the message is accepted by higher layers:

- Message integrity is guaranteed with respect to the signed bytes.
- Message authenticity is guaranteed with respect to the public key selected by the receiver from local state as defined in [05-keys-and-identity.md](05-keys-and-identity.md).
- Confidentiality is provided for encrypted payload bytes, assuming correct recipient key selection and correct ECIES usage.

The cryptographic layer provides no guarantee of:

- [Authorization](06-access-control-model.md) correctness.
- [Schema](../02-architecture/managers/05-schema-manager.md) correctness.
- Delivery, ordering, liveness, or availability.

## 8. Allowed behavior

The specification explicitly allows:

- Operating without relying on [transport](08-network-transport-requirements.md) security properties.
- Signing and verifying node to node packages and graph envelopes at the [Network Manager](../02-architecture/managers/10-network-manager.md) boundary.
- Encrypting payload bytes when confidentiality is required by the protocol step.
- Rejecting messages solely on cryptographic failure, without additional processing.

## 9. Forbidden behavior

The specification explicitly forbids:

- Accepting any remote package or envelope that lacks a verifiable signature.
- Accepting any message using an algorithm other than secp256k1 for signatures and ECIES for encryption.
- Allowing components other than [Key Manager](../02-architecture/managers/03-key-manager.md) to access private keys for signing or decryption.
- Allowing [Graph Manager](../02-architecture/managers/07-graph-manager.md) or app extensions to bypass [Network Manager](../02-architecture/managers/10-network-manager.md) and [State Manager](../02-architecture/managers/09-state-manager.md) to introduce remote envelopes.
- Encrypting required routing or [sync validation](07-sync-and-consistency.md) metadata such that the receiver cannot validate signature, domain name, or sequence range prior to decryption.

## 10. Failure and rejection behavior

## 10.1 Verification failure

If signature verification fails, the receiver must:

- Reject the package or envelope.
- Perform no further processing of the contained operations.
- Perform no state changes, including [sync state updates](07-sync-and-consistency.md).

## 10.2 Decryption failure

If decryption is required for a payload and decryption fails, the receiver must:

- Reject the package or envelope.
- Perform no further processing of the contained operations.
- Perform no state changes, including [sync state updates](07-sync-and-consistency.md).

## 10.3 Unsupported algorithm or malformed cryptographic fields

If a message claims an unsupported algorithm, or its cryptographic fields are malformed, the receiver must:

- Reject the package or envelope.
- Treat the failure as non recoverable for that message.
- Avoid attempting partial interpretation of operations.

## 10.4 Cryptographic success with higher layer rejection

If cryptographic checks succeed but higher layers reject the envelope due to [ordering](07-sync-and-consistency.md), [schema](../02-architecture/managers/05-schema-manager.md), or [ACL rules](06-access-control-model.md), the message must be treated as rejected. Cryptographic validity must not override ordering constraints, schema constraints, or ACL constraints.

The handling of peer scoring, rate limiting, and sync state consequences of repeated failures is defined in [09-dos-guard-and-client-puzzles.md](09-dos-guard-and-client-puzzles.md) and [07-sync-and-consistency.md](07-sync-and-consistency.md), not in this file.
