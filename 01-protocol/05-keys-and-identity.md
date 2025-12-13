



# 05. Keys and Identity

## 1. Purpose and scope

This document defines how identities and cryptographic keys are represented, bound, and interpreted at the protocol level in 2WAY. It specifies identity structure, key ownership, key relationships, and the invariants that govern authorship and authority. It does not define storage, rotation workflows, revocation mechanics, transport encryption, or access control evaluation, which are specified elsewhere.

This document is normative for all protocol-compliant implementations.

## 2. Responsibilities

This specification defines:

- The protocol-level definition of an identity.
- The binding between identities and cryptographic keys.
- The representation of identities and keys in the graph.
- The rules governing authorship, ownership, and authority.
- The validity requirements for signatures and identity references in protocol envelopes.

This specification does not define:

- Key storage mechanisms.
- Key generation procedures.
- Cryptographic algorithms beyond required properties.
- UI or user-facing identity management.
- Application-specific interpretation of identity beyond protocol guarantees.

## 3. Core concepts

### 3.1 Identity

An identity is a first-class protocol entity that represents an actor capable of authorship. Actors include users, devices, backend nodes, services, and delegated agents.

An identity is represented as a Parent object in app_0.

An identity exists if and only if:

- A corresponding Parent object exists.
- At least one valid public key is bound to that Parent.

There is no anonymous identity at the protocol level.

### 3.2 Cryptographic keys

Each identity is anchored by one or more asymmetric cryptographic keypairs.

Keys have the following properties:

- Each keypair consists of exactly one private key and one public key.
- The public key is represented as an Attribute attached to the identity Parent.
- The private key never appears in the graph or protocol messages.

The protocol requires that keys support:

- Deterministic signature verification.
- Non-malleable signatures.
- Unique binding between message and signer.

The specific cryptographic algorithms are defined in the cryptography specification.

### 3.3 Key binding

A public key is bound to an identity by attaching it as an Attribute to the identity Parent.

Key binding is immutable once accepted. A bound key cannot be reassigned to another identity.

Multiple keys may be bound to the same identity Parent, subject to schema and ACL rules.

## 4. Invariants and guarantees

### 4.1 Identity invariants

The following invariants are mandatory:

- Every operation has exactly one author identity.
- Every author identity resolves to exactly one Parent.
- Every Parent that represents an identity has at least one bound public key.
- Identity Parents are immutable once created.
- Ownership of an identity Parent cannot be transferred.

### 4.2 Authorship guarantees

The protocol guarantees:

- Every accepted operation can be attributed to a cryptographically verifiable identity.
- Authorship is stable across time and sync.
- No operation can be accepted without a valid signature from a key bound to the claimed identity.

### 4.3 Ownership guarantees

The protocol guarantees:

- Objects created by an identity are permanently owned by that identity unless explicitly defined otherwise by schema.
- Ownership cannot be overwritten by remote peers.
- Ownership is verified independently of transport or trust assumptions.

## 5. Allowed behaviors

The following behaviors are explicitly allowed:

- An identity may have multiple bound public keys.
- A single device may hold multiple identities.
- Multiple devices may be bound to the same identity through separate keys.
- An identity may delegate limited authority through additional keys, subject to schema and ACL constraints.
- Nodes may reject identities that violate schema, ACL, or trust constraints.

## 6. Forbidden behaviors

The following behaviors are explicitly forbidden:

- Accepting an operation without verifying its signature.
- Accepting an operation signed by a key not bound to the claimed identity.
- Reassigning a public key to a different identity Parent.
- Mutating an identity Parent after creation.
- Inferring identity from transport context, network address, or session state.
- Treating unsigned data as authoritative input.

## 7. Interaction with other components

### 7.1 Inputs

This specification consumes:

- Signed protocol envelopes that declare an author identity.
- Public keys stored as Attributes in the graph.
- Schema definitions that classify identity Parents and key Attributes.

### 7.2 Outputs

This specification produces:

- A binary decision on whether an operation’s claimed identity is valid.
- A resolved identity reference for downstream components.

### 7.3 Trust boundaries

Identity validation occurs before:

- Schema-level semantic validation.
- Access control evaluation.
- Persistent storage writes.

No downstream component may bypass identity verification.

## 8. Failure and rejection behavior

An operation must be rejected if any of the following conditions hold:

- The author identity does not exist.
- The author identity has no bound public keys.
- The signature does not verify against any bound public key.
- The envelope claims an identity inconsistent with the signing key.
- The identity Parent violates schema invariants.

Rejection is final for the operation. Rejected operations must not:

- Be written to persistent storage.
- Affect sync state.
- Trigger side effects or events.

## 9. Security properties

This specification enforces:

- Strong authorship attribution.
- Non-repudiation at the protocol level.
- Structural resistance to impersonation.
- Independence from network or transport trust.

No confidentiality, availability, or authorization guarantees are provided by this specification alone. These are defined in other components.

## 10. Compliance requirements

An implementation is protocol-compliant with respect to keys and identity if and only if:

- All invariants defined in this document are enforced.
- All forbidden behaviors are structurally impossible.
- All rejection conditions are correctly applied.
- Identity verification precedes all state mutation paths.
