



# 03 Key Manager

Defines key generation, storage, and cryptographic operations for backend private keys. Specifies key scopes, storage layout, and interfaces for signing and decryption. Defines lifecycle, failure handling, and operational constraints for key management.

For the meta specifications, see [03-key-manager meta](../../10-appendix/meta/02-architecture/managers/03-key-manager-meta.md).

## 1. Invariants and guarantees

Across all components and contexts defined in this file, the following invariants and guarantees hold:

* All keypairs use secp256k1 exclusively and all asymmetric encryption uses ECIES over secp256k1, as mandated by [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md).
* All private keys exist only on disk and in process memory.
* Private keys are never written to the graph, database, logs, or network.
* Public keys are always derived from private keys.
* Every cryptographic operation uses an explicitly specified scope and key identifier.
* No implicit scope selection or fallback is permitted.
* Invalid, missing, or malformed keys cause explicit failure.
* The node key must exist and be valid before startup completes, satisfying the node identity guarantees in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* The [Key Manager](03-key-manager.md) never determines authorship or authority and defers to identity semantics defined in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Only the [Key Manager](03-key-manager.md) may perform signing or decryption using private keys, keeping the private-key boundary enforced by [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md).
* Signature verification and public-key encryption may be performed by other managers or services when authorized by the relevant [OperationContext](../services-and-apps/05-operation-context.md) and identity data in the graph; they must not require access to private keys.

These guarantees hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 2. Internal structure

The [Key Manager](03-key-manager.md) is internally structured into explicit engines. These engines are required for correctness and clarity.

### 2.1 Key Storage Engine

The Key Storage Engine owns:

* Filesystem layout and directory management.
* Atomic creation of key files.
* Loading and parsing of key files.
* Validation of key format and curve type.
* Ensuring uniqueness and non ambiguity of node keys.

It performs no cryptographic operations beyond parsing and validation.

### 2.2 Key Generation Engine

The Key Generation Engine owns:

* Generation of secp256k1 keypairs.
* Assignment of key identifiers.
* Coordination with the Storage Engine to persist keys durably.
* Ensuring generated keys are usable before returning success.

It does not bind keys to graph identities directly.

### 2.3 Crypto Operation Engine

The Crypto Operation Engine owns:

* Signing byte sequences with a specified private key exactly as defined in [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md).
* ECIES decryption using a specified private key in compliance with [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md).
* Input validation for cryptographic operations.
* Enforcing algorithm and size constraints.

It never selects keys implicitly.

### 2.4 Key Cache Engine

The Key Cache Engine owns:

* In memory caching of parsed private keys.
* Cache invalidation on key rotation or failure.
* Ensuring cached keys match on disk representations.

Caching is an optimization only and must not change semantics.

## 3. Identity scopes and key classes

Identity scopes are internal addressing constructs used by the [Key Manager](03-key-manager.md). They correspond to protocol identities represented as Parents in app_0, as described in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md), but do not appear on the wire.

### 3.1 Node scope

* Exactly one node keypair exists per backend instance.
* The node scope corresponds to the node identity Parent defined in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* The node key is used for:
  * Signing outbound sync related payloads when required.
  * Decrypting inbound payloads addressed to the node.
* Startup must fail if the node key is missing or unusable.

### 3.2 Identity scopes

* One or more identity keypairs may exist locally for a given identity.
* Identity keys may represent users or system identities.
* Multiple keys over time are permitted to support rotation.
* The [Key Manager](03-key-manager.md) does not choose which identity key is active.

### 3.3 App scopes

* App keypairs exist for app identities that require backend cryptographic operations.
* App scopes are distinct from user and node scopes.
* App identities are first class identities and follow the same binding rules.

## 4. Persistent key storage

### 4.1 Storage root and layout

All key material is stored under a single backend directory.

Paths are:

* `backend/keys/nodes/node_key.pem`
* `backend/keys/identities/<identity_id>/<key_id>.pem`
* `backend/keys/apps/<app_id>/<key_id>.pem`

This directory must never be exposed via any API or static file server.

### 4.2 Encoding and format

* Keys are stored in a validated deterministic format that encodes the curve and key material exactly as required by [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md).
* The format must encode curve type, public key, and private key.
* Public keys are always derivable from private keys.
* Separate public key files are forbidden.

### 4.3 Creation and update rules

* Key creation must be atomic.
* Existing key files must never be overwritten implicitly.
* Node key duplication or ambiguity causes startup failure.
* Old keys remain on disk after rotation.

### 4.4 Local only constraint

* Private keys must not be accepted from external input.
* Private keys must not be reconstructed from graph state.

## 5. Public key binding to graph identities

### 5.1 Binding contract

* Public keys are derived by the [Key Manager](03-key-manager.md).
* [Graph Manager](07-graph-manager.md) persists them as public key Attributes as defined in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* A public key binds permanently to one identity Parent.

The [Key Manager](03-key-manager.md) never writes to the graph directly.

### 5.2 Identity existence requirement

* Signing or public key exposure is forbidden unless the identity Parent exists, matching the binding rules in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Exception is allowed only during identity creation flows explicitly orchestrated by higher layers.

### 5.3 Authority split

* [Key Manager](03-key-manager.md) owns private keys and derivation.
* [Graph Manager](07-graph-manager.md) owns persistence and binding.

## 6. Interfaces and interactions

### 6.1 Inputs

* Configuration:
  * Key directory path from [Config Manager](01-config-manager.md).
  * Policy for missing key generation.
* Lifecycle requests:
  * Ensure node key exists.
  * Generate new keypair for a scope.
  * Load key by scope and identifier.
* Cryptographic requests:
  * Sign bytes.
  * Decrypt ciphertext.

All callers are trusted backend components.

### 6.2 Outputs

* Public key bytes.
* Signature bytes.
* Plaintext bytes.

Private key material is never returned.

### 6.3 Scope specification

Every request must specify:

* Exactly one scope.
* Exactly one key identifier.

Requests that do not are rejected.

### 6.4 Authorization boundary

* Only backend managers and services defined in [02-architecture/services-and-apps/**](../services-and-apps/) may call the [Key Manager](03-key-manager.md).
* Scope and key identifiers are never inferred.
* Missing or invalid keys cause rejection.

## 7. Startup and shutdown behavior

### 7.1 Startup

Startup proceeds as follows:

1. Resolve key directory path.
2. Load and validate node key.
3. Validate node key uniqueness.
4. Prepare in memory caches.
5. Expose readiness to dependent managers.

Failure aborts backend startup.

### 7.2 Shutdown

* No special shutdown actions are required.
* In memory caches are discarded with process exit.

## 8. Allowed and forbidden behaviors

### 8.1 Allowed behaviors

* Generating keys for explicit scopes.
* Loading keys into memory.
* Performing signing and decryption operations.
* Deriving public keys for graph binding.
* Enforcing strict validation.

### 8.2 Forbidden behaviors

* Exporting private keys.
* Accepting private keys from external sources.
* Writing to the graph or database.
* Verifying signatures.
* Performing public-key-only encryption that does not require private-key access.
* Selecting keys implicitly.
* Continuing after node key failure.
* Using non secp256k1 algorithms.

## 9. Failure handling

### 9.1 Startup failures

Startup must fail if:

* Node key is missing and cannot be generated.
* Node key is malformed or wrong curve.
* Node key cannot sign or decrypt.

### 9.2 Runtime failures

Operations must fail if:

* Scope or key does not exist.
* Key is malformed.
* Inputs are invalid or oversized.
* Decryption fails.
* Algorithm constraints are violated.

Silent fallback is forbidden.

### 9.3 Graph and key mismatch

If graph state indicates revocation or mismatch, the [Key Manager](03-key-manager.md) refuses use of the key when instructed by higher layers such as [Graph Manager](07-graph-manager.md) and [State Manager](09-state-manager.md). It does not repair graph state.

### 9.4 Rotation and revocation support

The [Key Manager](03-key-manager.md) supports rotation by:

* Creating new keys on request.
* Retaining old keys.
* Refusing revoked keys when provided authoritative status.

It does not decide revocation precedence.

## 10. Operational constraints

* Key directory is the sole private key authority.
* Loss of keys prevents future operations but does not corrupt history.
* No background tasks beyond load and request handling.

## 11. Configuration surface, `key.*`

[Key Manager](03-key-manager.md) owns the `key.*` namespace in [Config Manager](01-config-manager.md).

| Key | Type | Reloadable | Default | Description |
| --- | --- | --- | --- | --- |
| `key.dir` | Path | No | `backend/keys` | Key material directory path (mirrors `KEYS_DIR` from `.env`). |
