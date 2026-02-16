



# 03 Key Manager

## 1. Purpose and scope

The Key Manager is the authoritative component responsible for the scope described below. This document defines the Key Manager component in the 2WAY backend. It specifies the authoritative handling of all local private key material and the narrowly scoped cryptographic operations permitted to be performed using those keys.

Key Manager is responsible for key generation, durable storage, loading, and controlled use of private keys for signing and decryption. It is a security critical manager with strict boundaries. It does not interpret protocol semantics, graph meaning, ACL rules, or sync logic. It performs cryptographic operations only when explicitly instructed by authorized backend components. This specification defines structure, responsibilities, invariants, lifecycle behavior, failure handling, and interaction contracts required to implement the Key Manager correctly.

This specification consumes the protocol contracts defined in:

* [01-protocol/04-cryptography.md](../../../../01-protocol/04-cryptography.md)
* [01-protocol/05-keys-and-identity.md](../../../../01-protocol/05-keys-and-identity.md)
* [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/10-errors-and-failure-modes.md](../../../../01-protocol/10-errors-and-failure-modes.md)

Those files remain normative for all behaviors described here.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Generating secp256k1 keypairs for node, identity, and app scopes exactly as mandated by [01-protocol/04-cryptography.md](../../../../01-protocol/04-cryptography.md).
* Persisting private keys to disk using a deterministic and validated on disk format so private material never leaves the local authority boundaries defined in [01-protocol/04-cryptography.md](../../../../01-protocol/04-cryptography.md).
* Loading and validating private key material at startup and on demand.
* Deriving public keys from locally held private keys before those keys are published into the graph per [01-protocol/05-keys-and-identity.md](../../../../01-protocol/05-keys-and-identity.md).
* Performing signing operations defined in [01-protocol/04-cryptography.md](../../../../01-protocol/04-cryptography.md) for explicitly specified scopes and key identifiers.
* Performing private-key decryption for inbound payloads as required by [01-protocol/04-cryptography.md](../../../../01-protocol/04-cryptography.md).
* Performing ECIES decryption for inbound payloads addressed to locally held private keys, as required by [01-protocol/04-cryptography.md](../../../../01-protocol/04-cryptography.md).
* Enforcing that private keys are never returned, serialized, logged, or emitted, preserving the fail-closed posture in [01-protocol/04-cryptography.md](../../../../01-protocol/04-cryptography.md).
* Acting as the sole component permitted to access private key material.
* Declaring the first external route bindings that prove Key Manager hardened behavior (`/auth/identity/register`, `/system/sync/packages`).
* Ensuring the node key exists, is valid, and is usable before dependent managers may operate, matching the Node key requirements in [01-protocol/05-keys-and-identity.md](../../../../01-protocol/05-keys-and-identity.md).
* Refusing all cryptographic operations when invariants are violated, surfacing failures that map to [01-protocol/10-errors-and-failure-modes.md](../../../../01-protocol/10-errors-and-failure-modes.md).
* Declaring the `key.*` configuration surface and its key directory binding.

This specification does not cover the following:

* Signature verification of remote envelopes or objects, which belong to the verification flows defined in [01-protocol/04-cryptography.md](../../../../01-protocol/04-cryptography.md).
* Protocol level decisions about when signing or encryption is required, which are enforced by network and sync logic in [01-protocol/07-sync-and-consistency.md](../../../../01-protocol/07-sync-and-consistency.md).
* Graph object creation, persistence, or schema enforcement.
* ACL evaluation or permission semantics.
* Identity ownership, authorship, or trust interpretation.
* Sync package construction or application.
* Frontend key storage or client side signing.
* Key escrow, key export, or key sharing between nodes.
* Network transport or peer communication.
