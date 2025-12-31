



# 03 Key Manager

## 1. Purpose and scope

This document defines the Key Manager component in the 2WAY backend. It specifies the authoritative handling of all local private key material and the narrowly scoped cryptographic operations permitted to be performed using those keys.

Key Manager is responsible for key generation, durable storage, loading, and controlled use of private keys for signing and asymmetric encryption or decryption. It is a security critical manager with strict boundaries. It does not interpret protocol semantics, graph meaning, ACL rules, or sync logic. It performs cryptographic operations only when explicitly instructed by authorized backend components.

This specification defines structure, responsibilities, invariants, lifecycle behavior, failure handling, and interaction contracts required to implement the Key Manager correctly.

This specification consumes the protocol contracts defined in:
* `01-protocol/04-cryptography.md`
* `01-protocol/05-keys-and-identity.md`
* `01-protocol/06-access-control-model.md`
* `01-protocol/07-sync-and-consistency.md`
* `01-protocol/09-errors-and-failure-modes.md`

Those files remain normative for all behaviors described here.

## 2. Responsibilities and boundaries

This specification is responsible for the following

* Generating secp256k1 keypairs for node, identity, and app scopes exactly as mandated by `01-protocol/04-cryptography.md`.
* Persisting private keys to disk using a deterministic and validated on disk format so private material never leaves the local authority boundaries defined in `01-protocol/04-cryptography.md`.
* Loading and validating private key material at startup and on demand.
* Deriving public keys from locally held private keys before those keys are published into the graph per `01-protocol/05-keys-and-identity.md`.
* Performing signing operations defined in `01-protocol/04-cryptography.md` for explicitly specified scopes and key identifiers.
* Performing ECIES encryption for outbound payloads when a recipient public key is provided, as required by `01-protocol/04-cryptography.md`.
* Performing ECIES decryption for inbound payloads addressed to locally held private keys, as required by `01-protocol/04-cryptography.md`.
* Enforcing that private keys are never returned, serialized, logged, or emitted, preserving the fail-closed posture in `01-protocol/04-cryptography.md`.
* Acting as the sole component permitted to access private key material.
* Ensuring the node key exists, is valid, and is usable before dependent managers may operate, matching the Node key requirements in `01-protocol/05-keys-and-identity.md`.
* Refusing all cryptographic operations when invariants are violated, surfacing failures that map to `01-protocol/09-errors-and-failure-modes.md`.

This specification does not cover the following

* Signature verification of remote envelopes or objects, which belong to the verification flows defined in `01-protocol/04-cryptography.md`.
* Protocol level decisions about when signing or encryption is required, which are enforced by network and sync logic in `01-protocol/07-sync-and-consistency.md`.
* Graph object creation, persistence, or schema enforcement.
* ACL evaluation or permission semantics.
* Identity ownership, authorship, or trust interpretation.
* Sync package construction or application.
* Frontend key storage or client side signing.
* Key escrow, key export, or key sharing between nodes.
* Network transport or peer communication.

## 3. Invariants and guarantees

Across all components and contexts defined in this file, the following invariants and guarantees hold:

* All keypairs use secp256k1 exclusively and all asymmetric encryption uses ECIES over secp256k1, as mandated by `01-protocol/04-cryptography.md`.
* All private keys exist only on disk and in process memory.
* Private keys are never written to the graph, database, logs, or network.
* Public keys are always derived from private keys.
* Every cryptographic operation uses an explicitly specified scope and key identifier.
* No implicit scope selection or fallback is permitted.
* Invalid, missing, or malformed keys cause explicit failure.
* The node key must exist and be valid before startup completes, satisfying the node identity guarantees in `01-protocol/05-keys-and-identity.md`.
* The Key Manager never determines authorship or authority and defers to identity semantics defined in `01-protocol/05-keys-and-identity.md`.
* Only the Key Manager may perform signing or decryption using private keys, keeping the private-key boundary enforced by `01-protocol/04-cryptography.md`.

These guarantees hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 4. Internal structure

The Key Manager is internally structured into explicit engines. These engines are required for correctness and clarity.

### 4.1 Key Storage Engine

The Key Storage Engine owns:

* Filesystem layout and directory management.
* Atomic creation of key files.
* Loading and parsing of key files.
* Validation of key format and curve type.
* Ensuring uniqueness and non ambiguity of node keys.

It performs no cryptographic operations beyond parsing and validation.

### 4.2 Key Generation Engine

The Key Generation Engine owns:

* Generation of secp256k1 keypairs.
* Assignment of key identifiers.
* Coordination with the Storage Engine to persist keys durably.
* Ensuring generated keys are usable before returning success.

It does not bind keys to graph identities directly.

### 4.3 Crypto Operation Engine

The Crypto Operation Engine owns:

* Signing byte sequences with a specified private key exactly as defined in `01-protocol/04-cryptography.md`.
* ECIES encryption using a supplied recipient public key in compliance with `01-protocol/04-cryptography.md`.
* ECIES decryption using a specified private key in compliance with `01-protocol/04-cryptography.md`.
* Input validation for cryptographic operations.
* Enforcing algorithm and size constraints.

It never selects keys implicitly.

### 4.4 Key Cache Engine

The Key Cache Engine owns:

* In memory caching of parsed private keys.
* Cache invalidation on key rotation or failure.
* Ensuring cached keys match on disk representations.

Caching is an optimization only and must not change semantics.

## 5. Identity scopes and key classes

Identity scopes are internal addressing constructs used by the Key Manager. They correspond to protocol identities represented as Parents in app_0, as described in `01-protocol/05-keys-and-identity.md`, but do not appear on the wire.

### 5.1 Node scope

* Exactly one node keypair exists per backend instance.
* The node scope corresponds to the node identity Parent defined in `01-protocol/05-keys-and-identity.md`.
* The node key is used for:
  * Signing outbound sync related payloads when required.
  * Decrypting inbound payloads addressed to the node.
* Startup must fail if the node key is missing or unusable.

### 5.2 Identity scopes

* One or more identity keypairs may exist locally for a given identity.
* Identity keys may represent users or system identities.
* Multiple keys over time are permitted to support rotation.
* The Key Manager does not choose which identity key is active.

### 5.3 App scopes

* App keypairs exist for app identities that require backend cryptographic operations.
* App scopes are distinct from user and node scopes.
* App identities are first class identities and follow the same binding rules.

## 6. Persistent key storage

### 6.1 Storage root and layout

All key material is stored under a single backend directory.

Paths are:

* `backend/keys/nodes/node_key.pem`
* `backend/keys/identities/<identity_id>/<key_id>.pem`
* `backend/keys/apps/<app_id>/<key_id>.pem`

This directory must never be exposed via any API or static file server.

### 6.2 Encoding and format

* Keys are stored in a validated deterministic format that encodes the curve and key material exactly as required by `01-protocol/04-cryptography.md`.
* The format must encode curve type, public key, and private key.
* Public keys are always derivable from private keys.
* Separate public key files are forbidden.

### 6.3 Creation and update rules

* Key creation must be atomic.
* Existing key files must never be overwritten implicitly.
* Node key duplication or ambiguity causes startup failure.
* Old keys remain on disk after rotation.

### 6.4 Local only constraint

* Private keys must not be accepted from external input.
* Private keys must not be reconstructed from graph state.

## 7. Public key binding to graph identities

### 7.1 Binding contract

* Public keys are derived by the Key Manager.
* Graph Manager persists them as public key Attributes as defined in `01-protocol/05-keys-and-identity.md`.
* A public key binds permanently to one identity Parent.

The Key Manager never writes to the graph directly.

### 7.2 Identity existence requirement

* Signing or public key exposure is forbidden unless the identity Parent exists, matching the binding rules in `01-protocol/05-keys-and-identity.md`.
* Exception is allowed only during identity creation flows explicitly orchestrated by higher layers.

### 7.3 Authority split

* Key Manager owns private keys and derivation.
* Graph Manager owns persistence and binding.

## 8. Interfaces and interactions

### 8.1 Inputs

* Configuration:
  * Key directory path.
  * Policy for missing key generation.
* Lifecycle requests:
  * Ensure node key exists.
  * Generate new keypair for a scope.
  * Load key by scope and identifier.
* Cryptographic requests:
  * Sign bytes.
  * Encrypt bytes with recipient public key.
  * Decrypt ciphertext.

All callers are trusted backend components.

### 8.2 Outputs

* Public key bytes.
* Signature bytes.
* Ciphertext bytes.
* Plaintext bytes.

Private key material is never returned.

### 8.3 Scope specification

Every request must specify:

* Exactly one scope.
* Exactly one key identifier.

Requests that do not are rejected.

### 8.4 Authorization boundary

* Only backend managers and services may call the Key Manager.
* Scope and key identifiers are never inferred.
* Missing or invalid keys cause rejection.

## 9. Startup and shutdown behavior

### 9.1 Startup

Startup proceeds as follows:

1. Resolve key directory path.
2. Load and validate node key.
3. Validate node key uniqueness.
4. Prepare in memory caches.
5. Expose readiness to dependent managers.

Failure aborts backend startup.

### 9.2 Shutdown

* No special shutdown actions are required.
* In memory caches are discarded with process exit.

## 10. Allowed and forbidden behaviors

### 10.1 Allowed behaviors

* Generating keys for explicit scopes.
* Loading keys into memory.
* Performing signing and ECIES operations.
* Deriving public keys for graph binding.
* Enforcing strict validation.

### 10.2 Forbidden behaviors

* Exporting private keys.
* Accepting private keys from external sources.
* Writing to the graph or database.
* Verifying signatures.
* Selecting keys implicitly.
* Continuing after node key failure.
* Using non secp256k1 algorithms.

## 11. Failure handling

### 11.1 Startup failures

Startup must fail if:

* Node key is missing and cannot be generated.
* Node key is malformed or wrong curve.
* Node key cannot sign or decrypt.

### 11.2 Runtime failures

Operations must fail if:

* Scope or key does not exist.
* Key is malformed.
* Inputs are invalid or oversized.
* Decryption fails.
* Algorithm constraints are violated.

Silent fallback is forbidden.

### 11.3 Graph and key mismatch

If graph state indicates revocation or mismatch, the Key Manager refuses use of the key when instructed by higher layers. It does not repair graph state.

### 11.4 Rotation and revocation support

The Key Manager supports rotation by:

* Creating new keys on request.
* Retaining old keys.
* Refusing revoked keys when provided authoritative status.

It does not decide revocation precedence.

## 12. Operational constraints

* Key directory is the sole private key authority.
* Loss of keys prevents future operations but does not corrupt history.
* No background tasks beyond load and request handling.
