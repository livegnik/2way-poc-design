



# 04. Cryptography

## 1. Purpose and scope

This document defines the cryptographic primitives, guarantees, and constraints used by the 2WAY protocol at the protocol layer. It specifies how cryptography is applied to protocol messages, objects, and transport envelopes, independent of identity semantics, key lifecycle management, or access control policy. Key ownership, identity binding, rotation, revocation, and delegation are defined elsewhere and are not covered here.

This document is normative.

## 2. Responsibilities

The cryptographic layer defined here is responsible for:

- Providing authenticity of protocol messages and graph mutations.
- Providing integrity of envelopes and transported data.
- Providing confidentiality where explicitly required.
- Enabling replay detection and ordered verification in conjunction with sequence metadata.
- Operating independently of transport security guarantees.

The cryptographic layer is not responsible for:

- Identity creation or management.
- Authorization or permission evaluation.
- Trust decisions beyond signature verification.
- Key rotation, revocation, or recovery semantics.

## 3. Cryptographic primitives

### 3.1 Asymmetric signing

- All signatures use secp256k1 elliptic curve cryptography.
- Signatures are deterministic.
- Each signed artifact has exactly one author.
- The signing algorithm provides message authenticity and integrity.

The protocol does not permit alternative signing curves or algorithms.

### 3.2 Asymmetric encryption

- Confidential payloads use ECIES over secp256k1.
- Encryption is optional and context dependent.
- Encryption applies only to explicitly defined payload sections.

The protocol does not define symmetric-only encryption modes at the protocol level.

### 3.3 Hashing

- Cryptographic hashes are used only for integrity verification and signature binding.
- Hash algorithms must be collision resistant and deterministic.
- Hashes are never treated as identifiers or authorities on their own.

## 4. Signed artifacts

### 4.1 Envelope signatures

Every protocol envelope that crosses a trust boundary must be signed.

A signature covers:

- The complete serialized envelope payload.
- All declared metadata fields relevant to validation.
- Sequence identifiers included in the envelope.

Unsigned envelopes are invalid and must be rejected without further processing.

### 4.2 Object signatures

Graph objects are not individually signed outside of their enclosing envelope.

Integrity and authorship are derived from:

- The envelope signature.
- The declared author identity.
- The immutable ownership rules enforced elsewhere.

The protocol forbids partially signed envelopes or mixed-author envelopes.

## 5. Encryption rules

### 5.1 Encryption scope

Encryption may be applied to:

- Envelope payloads.
- Subsections of payloads explicitly marked as confidential.

Encryption must not obscure fields required for routing, validation, or replay protection.

### 5.2 Encryption requirements

When encryption is used:

- The recipient must be explicitly identifiable.
- The encryption key must correspond to the recipient’s public key.
- Decryption failure must result in envelope rejection.

The protocol forbids opportunistic or unauthenticated encryption.

## 6. Replay protection and ordering

### 6.1 Sequence binding

Signatures bind to:

- Global sequence identifiers.
- Domain-specific sequence identifiers when present.

A valid signature does not override sequence validation rules.

### 6.2 Replay rejection

An envelope must be rejected if:

- Its sequence identifiers are stale or duplicated.
- Its sequence range conflicts with known sync state.
- Its signature is valid but bound to an invalid sequence context.

Cryptographic validity alone is insufficient for acceptance.

## 7. Trust boundaries and interactions

### 7.1 Inputs

The cryptographic layer accepts:

- Serialized envelopes.
- Declared author public keys.
- Optional recipient public keys for encrypted payloads.

### 7.2 Outputs

The cryptographic layer produces:

- Signature verification results.
- Decryption results or failures.
- Deterministic acceptance or rejection signals.

### 7.3 Trust assumptions

- No trust is placed in the transport layer.
- No trust is placed in peer ordering or delivery guarantees.
- All trust derives from cryptographic verification and local state.

## 8. Invariants and guarantees

The following invariants always hold:

- A valid envelope has exactly one verifiable author.
- Any modification to a signed envelope invalidates its signature.
- Encrypted payloads cannot be interpreted without successful decryption.
- Cryptographic verification is deterministic.

The following guarantees are provided:

- Authenticity of authorship.
- Integrity of transmitted data.
- Confidentiality when encryption is applied correctly.

The protocol makes no guarantee of availability, liveness, or delivery.

## 9. Explicitly allowed behavior

The protocol explicitly allows:

- Operating over untrusted or hostile networks.
- Partial encryption of payloads.
- Offline verification of signatures.
- Independent verification by each node.

## 10. Explicitly forbidden behavior

The protocol explicitly forbids:

- Accepting unsigned envelopes.
- Accepting envelopes signed with unknown or mismatched keys.
- Modifying signed data in transit or at rest.
- Inferring authorship from transport or connection context.
- Using cryptographic primitives not defined in this document.

## 11. Failure and rejection behavior

On cryptographic failure:

- The envelope must be rejected immediately.
- No further validation or processing is permitted.
- No partial state changes may occur.

Failures include:

- Invalid signatures.
- Decryption errors.
- Malformed cryptographic fields.
- Algorithm mismatches.

Failures are non-recoverable at the envelope level. Recovery, retry, or remediation is handled by higher protocol layers.

## 12. Non-goals

This specification does not define:

- Key storage formats.
- Key lifecycle events.
- Identity semantics.
- Authorization logic.
- Transport anonymity guarantees.

Those concerns are explicitly delegated to other documents in the repository.
