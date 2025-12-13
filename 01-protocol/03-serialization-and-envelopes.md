



# 03 Serialization and envelopes

## 1. Purpose and scope

This document defines the canonical serialization rules and envelope structure used by the 2WAY protocol to represent operations, objects, and sync payloads. It specifies how data is encoded for persistence and transmission, how authorship and integrity are bound to serialized data, and which invariants must hold for serialized material to be considered valid.

This document does not define object semantics, schema rules, access control, sync policy, or cryptographic algorithms in detail. Those are specified in other protocol documents and are referenced here only where required to define correctness boundaries.

## 2. Responsibilities

This specification is responsible for defining:

* The envelope as the atomic unit of transport and validation.
* Canonical serialization rules for envelopes and enclosed payloads.
* The binding between serialized content, identity, and cryptographic signatures.
* Required and forbidden fields and structures.
* Failure handling for malformed or invalid serialized input.

This specification is not responsible for:

* Interpreting object meaning or schema validity.
* Granting or denying permissions.
* Managing storage layout or database schema.
* Network transport selection or session management.

## 3. Terminology

For the purposes of this document:

* Envelope refers to a signed, serialized container that carries one or more graph mutations or protocol control objects.
* Payload refers to the content inside an envelope that is subject to signature verification.
* Author refers to the identity that signs the envelope.
* Identity refers to a Parent object with one or more associated public keys, as defined in the identity and key specification.
* Sequence refers to global or domain sequence numbers assigned by the receiving node.

## 4. Envelope role and guarantees

### 4.1 Guarantees

A valid envelope provides the following guarantees:

* Authorship. The envelope is cryptographically bound to exactly one author identity.
* Integrity. Any modification to the payload invalidates the signature.
* Atomicity. All enclosed payload elements are accepted or rejected as a unit.
* Replay detectability. The envelope can be identified as duplicate or out of order relative to prior envelopes from the same author.

### 4.2 Non-guarantees

The envelope does not guarantee:

* Authorization to perform the enclosed operations.
* Semantic correctness of enclosed objects.
* Ordering relative to envelopes from other authors.
* Confidentiality unless combined with an encrypted transport.

## 5. Canonical serialization

### 5.1 Format requirements

All envelopes and payloads are serialized using a deterministic, canonical encoding with the following properties:

* Field ordering is fixed and deterministic.
* No optional field may be omitted if its value is semantically required.
* No field may appear more than once.
* Numeric values are represented in a single canonical form.
* String values are encoded as UTF-8.
* Binary values are encoded as explicit byte sequences, not implicit encodings.

The specific encoding format is defined in the protocol overview and applies uniformly across all protocol components.

### 5.2 Canonicalization invariant

Before signing or verification:

* The payload MUST be serialized into its canonical byte representation.
* The signature MUST be computed over exactly those bytes.
* Verification MUST reject any envelope whose canonicalized payload differs from the signed bytes.

Any deviation from canonical form renders the envelope invalid.

## 6. Envelope structure

### 6.1 Required fields

Every envelope MUST contain the following fields:

* `author_id`. A reference to the Parent identity claiming authorship.
* `author_key`. An identifier for the specific public key used to sign.
* `payload`. The serialized payload content.
* `signature`. A cryptographic signature over the canonical payload.
* `envelope_type`. A discriminator defining how the payload is interpreted.
* `envelope_version`. A protocol version identifier.

### 6.2 Optional fields

An envelope MAY contain additional fields only if explicitly defined by the envelope type. Undeclared or unknown fields are forbidden.

### 6.3 Forbidden structures

The following are explicitly forbidden:

* Nested envelopes.
* Multiple signatures within a single envelope.
* Ambiguous or polymorphic payload encodings.
* Payload fields that depend on out-of-band context for interpretation.

## 7. Payload rules

### 7.1 Payload composition

A payload consists of one or more protocol-defined objects. These may include:

* Graph mutations.
* Control objects related to sync, revocation, or schema propagation.

All objects inside a payload are interpreted in the context of the envelope author.

### 7.2 Atomic acceptance

If any object within the payload fails validation at any stage, the entire envelope is rejected. Partial acceptance is forbidden.

## 8. Identity and signature binding

### 8.1 Signature requirements

* The signature MUST be verifiable using the public key referenced by `author_key`.
* The referenced key MUST belong to the identity referenced by `author_id`.
* The key MUST not be revoked at the time of validation.

### 8.2 Identity resolution

Identity resolution is performed by the receiving node using its local graph state. The envelope does not carry identity definitions inline.

If identity resolution fails, the envelope is rejected.

## 9. Interaction with validation pipeline

### 9.1 Inputs and outputs

Inputs:

* Serialized envelope bytes.
* Local graph state.
* Local key and revocation state.

Outputs:

* Either a fully parsed, verified envelope passed to higher layers.
* Or a terminal rejection with no side effects.

### 9.2 Trust boundaries

The envelope is the sole trust boundary between external input and internal processing. No assumptions are made about the source, transport, or intent of the sender.

## 10. Sequence handling

### 10.1 External sequence declarations

Envelopes received from peers MAY declare expected sequence ranges as part of their payload, depending on envelope type.

Declared sequences are advisory and subject to independent verification.

### 10.2 Local sequence assignment

Global and domain sequence numbers are assigned by the receiving node after acceptance. Envelopes do not carry authoritative sequence numbers for local state.

## 11. Failure and rejection behavior

### 11.1 Immediate rejection conditions

An envelope MUST be rejected immediately if any of the following are true:

* Serialization is not canonical.
* Required fields are missing or duplicated.
* Signature verification fails.
* Author identity or key cannot be resolved.
* Envelope version is unsupported.
* Forbidden fields or structures are present.

### 11.2 Rejection effects

On rejection:

* No payload objects are processed.
* No state is mutated.
* The envelope is not forwarded, stored, or partially recorded, except for optional rate limiting or abuse tracking as defined elsewhere.

### 11.3 Error visibility

Error details MAY be logged locally. Error information returned to peers, if any, is implementation-defined and must not leak internal state.

## 12. Explicitly allowed behaviors

This specification explicitly allows:

* Stateless validation of envelopes.
* Offline verification of stored envelopes.
* Deferred semantic validation after signature verification.
* Envelope types with distinct payload semantics, provided they adhere to this structure.

## 13. Explicitly forbidden behaviors

This specification explicitly forbids:

* Inferring identity from transport or session context.
* Accepting unsigned or partially signed payloads.
* Modifying payload content prior to verification.
* Accepting envelopes that rely on implicit defaults or contextual interpretation.

## 14. Security invariants

The following invariants MUST hold at all times:

* No graph mutation enters the system without a valid envelope.
* No envelope is accepted without a verifiable author.
* No accepted envelope can be altered without detection.
* Envelope validity is independent of transport security.

Failure to uphold any invariant constitutes a protocol violation.

## 15. References

This document depends on and is consistent with:

* Identity and keys specification.
* Cryptography specification.
* Graph object model.
* Sync and consistency specification.
* Security model overview.

No other dependencies exist.
