



# 05 Keys and Identity

Defines protocol identity and key representations for 2WAY. Specifies key binding, authorship assertion, and signature verification rules. Defines identity invariants, allowed/forbidden behaviors, and rejection conditions.

For the meta specifications, see [05-keys-and-identity meta](../10-appendix/meta/01-protocol/05-keys-and-identity-meta.md).

## 1. Identity model

### 1.1 Identity representation

An identity is a first-class protocol entity that represents an actor capable of authorship.

An identity is represented as a [Parent](02-object-model.md) object in [app_0](01-identifiers-and-namespaces.md).

An identity exists if and only if:

- The Parent object exists in the graph.
- The Parent has at least one bound public key [Attribute](02-object-model.md) that is valid under [schema rules](../02-architecture/managers/05-schema-manager.md).

Identities are not inferred, implicit, or contextual. All identities are explicit [graph objects](02-object-model.md).

### 1.2 Identity scope

Identities may represent:

- Users.
- Nodes.
- Backend services.
- Delegated or automated actors.

The protocol does not distinguish these categories at the identity layer. Distinctions, if any, are imposed by [schema](../02-architecture/managers/05-schema-manager.md), [ACL](06-access-control-model.md), or application logic.

### 1.3 Identity versus device (PoC auth posture)

For PoC authentication, identity and device are separate concepts:

- **Identity** is a long-lived backend principal anchored to a public key.
- **Device** is an optional, separate concept used for device enrollment and revocation.

Device identifiers and device binding are defined in [01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md) and service flows, but the PoC frontend auth flow MUST NOT conflate device identity with the backend identity used for authentication.
Frontend auth registration MUST NOT create, bind, or revoke device identities; device metadata is informational only.

## 2. Key model

### 2.1 Key type

Keys are asymmetric cryptographic keypairs.

Protocol requirements for keys:

- The public key is represented as an [Attribute](02-object-model.md) attached to an identity Parent.
- The private key is never represented in the graph or transmitted.
- Each keypair uniquely identifies a signing authority.

### 2.2 Key binding

A public key is bound to an identity by being attached as an [Attribute](02-object-model.md) to the identity Parent.

Key binding rules:

- A bound public key belongs to exactly one identity.
- A bound public key cannot be reassigned to another identity.
- Key binding is immutable once accepted into the graph.

Multiple public keys may be bound to the same identity Parent, subject to [schema](../02-architecture/managers/05-schema-manager.md) and [ACL](06-access-control-model.md) constraints.

## 3. Authorship and signatures

### 3.1 Authorship assertion

Every [operation envelope](03-serialization-and-envelopes.md) declares exactly one author identity.

Authorship is asserted by:

- Including the identity reference in the envelope.
- Signing the envelope with a private key corresponding to a public key bound to that identity, as defined in [04-cryptography.md](04-cryptography.md).

The backend never infers authorship from [transport](08-network-transport-requirements.md), session state, or network metadata.

### 3.2 Signature verification

An operation is considered authentic if and only if:

- The claimed author identity exists.
- The identity has at least one bound public key.
- The envelope signature verifies against one of the bound public keys.

Signature verification is mandatory and precedes all other validation steps, including [schema validation](../02-architecture/managers/05-schema-manager.md) and [ACL evaluation](06-access-control-model.md).

## 4. Invariants and guarantees

### 4.1 Mandatory invariants

The following invariants are enforced by the protocol:

- Every accepted operation has exactly one author identity.
- Every author identity resolves to exactly one identity Parent.
- Every identity Parent has at least one bound public key.
- Identity Parents are immutable after creation.
- Public keys cannot change identity ownership.

### 4.2 Guarantees

The protocol guarantees:

- Stable and permanent authorship attribution.
- Cryptographic verifiability of all accepted operations.
- Structural prevention of identity impersonation.
- Independence of identity verification from network trust.

## 5. Allowed behaviors

The following behaviors are explicitly allowed:

- Binding multiple public keys to a single identity.
- Using different keys for the same identity across devices.
- Using identities for users, nodes, services, or delegated actors.
- Rejecting identities that violate [schema](../02-architecture/managers/05-schema-manager.md) or validation rules.

## 6. Forbidden behaviors

The following behaviors are explicitly forbidden:

- Accepting an operation without a valid signature.
- Accepting an operation signed by a key not bound to the claimed identity.
- Rebinding a public key to a different identity.
- Mutating an identity Parent after creation.
- Inferring identity from IP address, session, or [transport](08-network-transport-requirements.md) channel.
- Treating unsigned or partially signed data as authoritative.

## 7. Interaction with other components

### 7.1 Inputs

This specification consumes:

- [Operation envelopes](03-serialization-and-envelopes.md) with declared author identities.
- Public key [Attributes](02-object-model.md) stored on identity Parents.
- [Schema definitions](../02-architecture/managers/05-schema-manager.md) that classify identity Parents and key Attributes.

### 7.2 Outputs

This specification produces:

- A verified or rejected identity assertion.
- A resolved author identity for downstream components.

### 7.3 Trust boundaries

Identity and signature verification occurs before:

- [Schema semantic validation](../02-architecture/managers/05-schema-manager.md).
- [ACL evaluation](06-access-control-model.md).
- Any persistent [graph mutation](../02-architecture/managers/07-graph-manager.md).

No component may bypass identity verification.

## 8. Failure and rejection behavior

An operation must be rejected if any of the following conditions occur:

- The author identity does not exist.
- The author identity has no bound public keys.
- The envelope signature fails verification.
- The signature does not correspond to the claimed identity.
- The identity Parent violates schema invariants.

Rejected operations:

- Must not be written to [storage](../03-data/01-sqlite-layout.md).
- Must not advance [sequence state](07-sync-and-consistency.md).
- Must not produce side effects or events.

Rejection is final for the envelope.

## 9. Compliance requirements

An implementation is compliant with this specification if and only if:

- All invariants defined in this document are enforced.
- All forbidden behaviors are structurally impossible.
- Identity verification precedes all state mutation paths.
- Rejection conditions are applied deterministically and consistently.
