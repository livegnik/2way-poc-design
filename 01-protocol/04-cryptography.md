



# 04 Cryptography

Defines cryptographic algorithms and rules for signing, verification, encryption, and decryption of 2WAY messages and envelopes. Specifies signature coverage, visibility constraints, and validation ordering for cryptographic processing. Defines component responsibilities for cryptographic operations and failure handling.

For the meta specifications, see [04-cryptography meta](../10-appendix/meta/01-protocol/04-cryptography-meta.md).

## 1. Cryptographic algorithms

## 1.1 Signing

- All signatures use secp256k1.
- Signatures are applied to protocol message bytes as defined by the message serialization used for transport.
- Verification uses the corresponding public key supplied by local state as defined in [05-keys-and-identity.md](05-keys-and-identity.md).

### 1.1.1 Signature encoding

When signatures are represented in JSON or other text formats:

- The signature value MUST be base64 encoding of the raw 64-byte `(r || s)` secp256k1 signature.
- The encoding MUST be standard base64 with padding.
- Consumers MUST reject signatures that do not decode to exactly 64 bytes.

### 1.1.2 Canonical serialization for signing

All signed JSON payloads use a canonical JSON serialization so the sender and verifier reproduce identical bytes.

Canonicalization requirements:

- UTF-8 encoding.
- JSON canonicalization follows RFC 8785 (JSON Canonicalization Scheme, JCS).
- Object member order is lexicographic by Unicode code point as required by JCS.
- Numbers are serialized per JCS numeric rules (no superfluous zeros, no `+`, no exponent when not required).
- No additional whitespace outside the canonical JSON produced by JCS.

When a specification defines a "signed portion" of a JSON payload, the bytes to sign are the UTF-8 JCS serialization of that signed portion object, excluding any `signature` field unless explicitly stated otherwise.

## 1.2 Asymmetric encryption

- Confidentiality uses ECIES over secp256k1.
- Encryption and decryption operate on message bytes, or on explicitly designated payload portions.
- Encryption is applied only when the protocol step requires confidentiality.

## 1.3 Algorithm constraints

- Nodes must not negotiate alternative signing or encryption algorithms within the PoC protocol scope.
- Nodes must not accept messages that claim an unsupported algorithm.

## 2. Cryptographically protected structures

## 2.1 Node to node packages

Node to node packages are cryptographically protected at the package level.

A node to node package that crosses the node trust boundary defined by [08-network-transport-requirements.md](08-network-transport-requirements.md) must include:

- A signature over the package content.
- Sender identification sufficient for the receiver to select the correct public key from local state.

If confidentiality is required for the package payload, the payload must be encrypted using ECIES as specified in 3.2.

## 2.2 Graph envelopes transmitted over remote sync

Remote sync uses the same [graph envelope](03-serialization-and-envelopes.md) abstraction used for local writes, with additional metadata required for [sync](07-sync-and-consistency.md).

For cryptographic purposes, a remote sync envelope must include the following metadata fields, because they participate in validation and replay protection:

- sender identity
- domain name
- from_seq
- to_seq
- signature

## 2.3 Signature coverage

A signature must cover all bytes whose modification could change meaning, [authorization context](06-access-control-model.md), or replay semantics.

At minimum, the signature must cover:

- The operations contained in the package or envelope.
- The sync metadata fields listed in 4.2 when present.

A receiver must treat any message as invalid if signature verification succeeds but the receiver cannot associate the verified signature with the exact metadata and operations the receiver is about to apply.

## 3. Visibility requirements for cryptographic processing

Fields required for routing, [sync validation](07-sync-and-consistency.md), and signature verification must remain visible to the receiver prior to decryption.

The protocol forbids encrypting the entire message in a way that prevents the receiver from:

- Selecting the correct public key for signature verification from local state.
- Reading domain name and sequence range values needed to validate ordering and replay constraints.

If partial encryption is used, the encrypted portion must be limited to payload bytes that are not required for the checks above.

## 4. Component interactions and trust boundaries

## 4.1 Key Manager

Inputs:

- Requests to sign bytes.
- Requests to decrypt ECIES ciphertext.

Outputs:

- Signatures over provided bytes.
- Plaintext bytes after successful decryption.

Trust boundary:

- [Key Manager](../02-architecture/managers/03-key-manager.md) is the only backend component that may access backend private keys for signing and decryption.
- This backend-only restriction does not apply to frontend clients, which sign locally using their own private keys per the auth registration flow and envelope rules.
- Signature verification and public-key encryption may be performed by authorized managers or services using identity data from the graph and an appropriate [OperationContext](../02-architecture/services-and-apps/05-operation-context.md).
- Callers must treat [Key Manager](../02-architecture/managers/03-key-manager.md) outputs as cryptographic results only. Authorization semantics are out of scope for Key Manager.

## 4.2 Network Manager

Inputs:

- Raw inbound remote packages from [transport](08-network-transport-requirements.md).
- Outbound packages produced by [State Manager](../02-architecture/managers/09-state-manager.md).

Outputs:

- Verified package bytes and extracted metadata for consumption by State Manager.
- Rejection of invalid packages.
- Signed outbound packages for transport and encrypted payloads using recipient public keys when required.

Trust boundary:

- [Network Manager](../02-architecture/managers/10-network-manager.md) terminates the network trust boundary and applies cryptographic verification and decryption required for remote packages.
- Network Manager must not interpret graph semantics, [schema semantics](../02-architecture/managers/05-schema-manager.md), or [ACL semantics](06-access-control-model.md).

## 4.3 State Manager

Inputs:

- Verified and, where required, decrypted packages from [Network Manager](../02-architecture/managers/10-network-manager.md).

Outputs:

- Envelopes submitted to [Graph Manager](../02-architecture/managers/07-graph-manager.md) for validation and application.
- Outbound sync packages provided to [Network Manager](../02-architecture/managers/10-network-manager.md) for signing and optional encryption using recipient public keys.

Trust boundary:

- [State Manager](../02-architecture/managers/09-state-manager.md) must rely on cryptographic verification performed at the Network Manager boundary.
- State Manager must additionally enforce [sync ordering constraints](07-sync-and-consistency.md) using sequence metadata. Cryptographic validity does not override ordering rules.

## 4.4 Graph Manager

Inputs:

- Envelopes and operations accompanied by signer identity information as provided by [Network Manager](../02-architecture/managers/10-network-manager.md) and [State Manager](../02-architecture/managers/09-state-manager.md).

Outputs:

- Acceptance or rejection of operations based on validation, [schema](../02-architecture/managers/05-schema-manager.md), and [ACL processing](06-access-control-model.md).
- No direct cryptographic outputs.

Trust boundary:

- [Graph Manager](../02-architecture/managers/07-graph-manager.md) is cryptography agnostic. It must not perform signing, verification, encryption, or decryption.
- Graph Manager must not accept any remote sourced envelope that is not delivered through the [Network Manager](../02-architecture/managers/10-network-manager.md) and [State Manager](../02-architecture/managers/09-state-manager.md) path.

## 5. Invariants and guarantees

## 5.1 Invariants

- Every remote package that crosses the node trust boundary is either rejected or verified using secp256k1.
- If ECIES encryption is used for a payload, the payload is either decrypted successfully and processed, or rejected without partial application.
- Cryptographic verification and decryption occur before any envelope is eligible for graph application (see [03-serialization-and-envelopes.md](03-serialization-and-envelopes.md)).

## 5.2 Guarantees

When verification succeeds and the message is accepted by higher layers:

- Message integrity is guaranteed with respect to the signed bytes.
- Message authenticity is guaranteed with respect to the public key selected by the receiver from local state as defined in [05-keys-and-identity.md](05-keys-and-identity.md).
- Confidentiality is provided for encrypted payload bytes, assuming correct recipient key selection and correct ECIES usage.

## 6. Allowed behavior

The specification explicitly allows:

- Operating without relying on [transport](08-network-transport-requirements.md) security properties.
- Signing and verifying node to node packages and graph envelopes at the [Network Manager](../02-architecture/managers/10-network-manager.md) boundary.
- Encrypting payload bytes when confidentiality is required by the protocol step.
- Rejecting messages solely on cryptographic failure, without additional processing.

## 7. Forbidden behavior

The specification explicitly forbids:

- Accepting any remote package or envelope that lacks a verifiable signature.
- Accepting any message using an algorithm other than secp256k1 for signatures and ECIES for encryption.
- Allowing components other than [Key Manager](../02-architecture/managers/03-key-manager.md) to access private keys for signing or decryption.
- Allowing [Graph Manager](../02-architecture/managers/07-graph-manager.md) or app extensions to bypass [Network Manager](../02-architecture/managers/10-network-manager.md) and [State Manager](../02-architecture/managers/09-state-manager.md) to introduce remote envelopes.
- Encrypting required routing or [sync validation](07-sync-and-consistency.md) metadata such that the receiver cannot validate signature, domain name, or sequence range prior to decryption.

## 8. Failure and rejection behavior

## 8.1 Verification failure

If signature verification fails, the receiver must:

- Reject the package or envelope.
- Perform no further processing of the contained operations.
- Perform no state changes, including [sync state updates](07-sync-and-consistency.md).

## 8.2 Decryption failure

If decryption is required for a payload and decryption fails, the receiver must:

- Reject the package or envelope.
- Perform no further processing of the contained operations.
- Perform no state changes, including [sync state updates](07-sync-and-consistency.md).

## 8.3 Unsupported algorithm or malformed cryptographic fields

If a message claims an unsupported algorithm, or its cryptographic fields are malformed, the receiver must:

- Reject the package or envelope.
- Treat the failure as non recoverable for that message.
- Avoid attempting partial interpretation of operations.

## 8.4 Cryptographic success with higher layer rejection

If cryptographic checks succeed but higher layers reject the envelope due to [ordering](07-sync-and-consistency.md), [schema](../02-architecture/managers/05-schema-manager.md), or [ACL rules](06-access-control-model.md), the message must be treated as rejected. Cryptographic validity must not override ordering constraints, schema constraints, or ACL constraints.
