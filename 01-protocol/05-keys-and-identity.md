



# 05. Keys and Identity

## 1. Purpose and scope

This document defines the protocol-level model for identities and cryptographic keys in 2WAY. It specifies how identities are represented in the graph, how public keys are bound to identities, how authorship is asserted and verified, and which invariants and failure conditions apply. It is limited to protocol semantics. Storage, rotation procedures, revocation mechanics, transport encryption, ACL evaluation, and device or app policy are defined in other documents and are only referenced where required for correctness.

This document is normative for all 2WAY-compliant implementations.

## 2. Responsibilities

This specification is responsible for the following:

- The definition of an identity at the protocol level.
- The binding between identities and public keys.
- The rules for authorship and ownership attribution.
- The requirements for identity references and signatures in envelopes.
- Mandatory invariants and rejection conditions related to identity and keys.

This specification does not cover the following:

- Key generation or entropy requirements.
- Private key storage or protection.
- Key rotation, revocation, or recovery workflows.
- Transport-level confidentiality.
- Authorization rules or permission evaluation.
- Application-specific identity semantics.

## 3. Identity model

### 3.1 Identity representation

An identity is a first-class protocol entity that represents an actor capable of authorship.

An identity is represented as a Parent object in app_0.

An identity exists if and only if:

- The Parent object exists in the graph.
- The Parent has at least one bound public key Attribute that is valid under schema rules.

Identities are not inferred, implicit, or contextual. All identities are explicit graph objects.

### 3.2 Identity scope

Identities may represent:

- Users.
- Nodes.
- Devices.
- Backend services.
- Delegated or automated actors.

The protocol does not distinguish these categories at the identity layer. Distinctions, if any, are imposed by schema, ACL, or application logic.

## 4. Key model

### 4.1 Key type

Keys are asymmetric cryptographic keypairs.

Protocol requirements for keys:

- The public key is represented as an Attribute attached to an identity Parent.
- The private key is never represented in the graph or transmitted.
- Each keypair uniquely identifies a signing authority.

The specific algorithms and encodings are defined in the cryptography specification referenced by the PoC build guide.

### 4.2 Key binding

A public key is bound to an identity by being attached as an Attribute to the identity Parent.

Key binding rules:

- A bound public key belongs to exactly one identity.
- A bound public key cannot be reassigned to another identity.
- Key binding is immutable once accepted into the graph.

Multiple public keys may be bound to the same identity Parent, subject to schema and ACL constraints.

## 5. Authorship and signatures

### 5.1 Authorship assertion

Every operation envelope declares exactly one author identity.

Authorship is asserted by:

- Including the identity reference in the envelope.
- Signing the envelope with a private key corresponding to a public key bound to that identity.

The backend never infers authorship from transport, session state, or network metadata.

### 5.2 Signature verification

An operation is considered authentic if and only if:

- The claimed author identity exists.
- The identity has at least one bound public key.
- The envelope signature verifies against one of the bound public keys.

Signature verification is mandatory and precedes all other validation steps.

## 6. Invariants and guarantees

### 6.1 Mandatory invariants

The following invariants are enforced by the protocol:

- Every accepted operation has exactly one author identity.
- Every author identity resolves to exactly one identity Parent.
- Every identity Parent has at least one bound public key.
- Identity Parents are immutable after creation.
- Public keys cannot change identity ownership.

### 6.2 Guarantees

The protocol guarantees:

- Stable and permanent authorship attribution.
- Cryptographic verifiability of all accepted operations.
- Structural prevention of identity impersonation.
- Independence of identity verification from network trust.

## 7. Allowed behaviors

The following behaviors are explicitly allowed:

- Binding multiple public keys to a single identity.
- Using different keys for the same identity across devices.
- Using identities for users, nodes, services, or delegated actors.
- Rejecting identities that violate schema or validation rules.

## 8. Forbidden behaviors

The following behaviors are explicitly forbidden:

- Accepting an operation without a valid signature.
- Accepting an operation signed by a key not bound to the claimed identity.
- Rebinding a public key to a different identity.
- Mutating an identity Parent after creation.
- Inferring identity from IP address, session, or transport channel.
- Treating unsigned or partially signed data as authoritative.

## 9. Interaction with other components

### 9.1 Inputs

This specification consumes:

- Operation envelopes with declared author identities.
- Public key Attributes stored on identity Parents.
- Schema definitions that classify identity Parents and key Attributes.

### 9.2 Outputs

This specification produces:

- A verified or rejected identity assertion.
- A resolved author identity for downstream components.

### 9.3 Trust boundaries

Identity and signature verification occurs before:

- Schema semantic validation.
- ACL evaluation.
- Any persistent graph mutation.

No component may bypass identity verification.

## 10. Failure and rejection behavior

An operation must be rejected if any of the following conditions occur:

- The author identity does not exist.
- The author identity has no bound public keys.
- The envelope signature fails verification.
- The signature does not correspond to the claimed identity.
- The identity Parent violates schema invariants.

Rejected operations:

- Must not be written to storage.
- Must not advance sequence state.
- Must not produce side effects or events.

Rejection is final for the envelope.

## 11. Compliance requirements

An implementation is compliant with this specification if and only if:

- All invariants defined in this document are enforced.
- All forbidden behaviors are structurally impossible.
- Identity verification precedes all state mutation paths.
- Rejection conditions are applied deterministically and consistently.
