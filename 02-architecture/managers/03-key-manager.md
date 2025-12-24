



# 03. Key Manager

## 1. Purpose and scope

This document specifies the Key Manager component in the 2WAY backend. It defines local private key generation, storage, loading, and the narrowly scoped signing, encryption, and decryption operations the protocol allows this component to perform with those keys.

This file covers only local key material and key backed operations. It does not define protocol cryptography, envelope formats, identity semantics, ACL policy, sync rules, or network transport behavior, except where required to define inputs, outputs, trust boundaries, and rejection conditions.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Generating secp256k1 keypairs for node, identity, and app identities.
* Persisting private keys to the backend key directory using PEM encoding.
* Loading and validating key files at startup and on demand.
* Deriving public keys from private keys for publication into the graph by the Graph Manager.
* Performing signing operations for explicitly requested identity scopes.
* Performing ECIES encryption for outbound payloads when a caller supplies a recipient public key.
* Performing ECIES decryption for ciphertexts addressed to locally held private keys.
* Enforcing that private keys are never returned, serialized into graph objects, written into logs, or emitted into network payloads.
* Serving as the only component that may touch private keys for signing or decryption operations.
* Ensuring the node key exists and is usable before any component that requires node signing or node decryption can operate.

This specification does not cover the following:

* Signature verification of remote envelopes or remote objects.
* Policy decisions determining when outbound payloads must be encrypted or decrypted.
* Definition of identity Parents, Attributes, or schema rules in app_0.
* Determination of authorship, ownership, or permission semantics.
* ACL evaluation, authorization policy, or OperationContext construction.
* Sync package construction, application, conflict resolution, or revocation precedence.
* Frontend key storage, client side signing, or key export UX.
* Key escrow, key synchronization between nodes, or remote key recovery.

## 3. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* All keypairs managed by this component use secp256k1.
* All private keys are stored only in the backend key directory as PEM encoded EC private keys.
* Private keys are never written to the graph, never emitted over the network, and never returned to any caller.
* Public keys are always derived from private keys and are the only key material permitted to be persisted into the graph.
* Signing, encryption, and decryption operations either succeed using protocol-mandated algorithms and validated locally held keys or fail with explicit errors.
* Silent fallback, scope inference, or alternate key selection is forbidden.
* All inputs to cryptographic operations are treated as untrusted bytes and are validated for size and type before use.
* The Key Manager signs only for explicitly specified identity scopes that are locally held and loadable.
* The Key Manager never determines authorship. It only performs cryptographic operations for a caller provided author identity.
* Only the Key Manager may access private keys for signing or decryption. Other components must call into it rather than read private key material.
* A derived public key is bound to exactly one identity scope and must never be submitted for or reassigned to another identity Parent once persisted.
* Startup must not complete successfully unless the node key is present, valid, and usable.

These guarantees hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 4. Identity scopes and key classes

Identity scopes are internal addressing constructs used by the Key Manager to select locally held private keys. They are not protocol level concepts and do not appear in the graph or on the wire.

Each scope corresponds to a protocol identity represented as a Parent in app_0.

### 4.1 Node scope

* Exactly one node keypair exists per backend instance.
* The node scope corresponds to the node identity Parent in app_0.
* The node keypair is used for:
  * Signing outbound sync packages when required by protocol flows.
  * ECIES decryption of inbound payloads addressed to the node identity.
* The node keypair must exist before the Network Manager or State Manager can perform any operation requiring node signing or decryption.

### 4.2 Identity scopes

* One or more identity keypairs may exist locally for a given identity Parent.
* Identity keypairs are used for identity scoped signing when required by higher level flows.
* Multiple keypairs for the same identity are permitted over time.
* The Key Manager does not select which identity key is active. Key selection is determined by the caller based on authoritative graph state.

### 4.3 App scopes

* App identity keypairs exist for app identities that require backend signing or decryption.
* App scopes distinguish app level cryptographic actions from user or node actions.
* App identities are treated as first class protocol identities and follow the same binding rules as other identities.

## 5. Persistent key storage

### 5.1 Storage root and directory layout

The Key Manager stores key files under a single configured directory root within the backend filesystem.

The following paths are used:

* `backend/keys/nodes/node_key.pem`
* `backend/keys/identities/<identity_id>/<key_id>.pem`
* `backend/keys/apps/<app_id>/<key_id>.pem`

The key directory is treated as sensitive data and must not be served, indexed, or exposed via any HTTP, WebSocket, or app extension surface.

### 5.2 Encoding and representation

* Each key file is a PEM encoded EC private key for secp256k1.
* Public keys are derived from private keys when needed.
* No separate public key files are required or permitted.

### 5.3 File creation and update rules

* Key generation must be atomic from the perspective of other components.
* A generated key must be durably persisted before success is returned to the caller.
* Existing key files must not be overwritten except as part of an explicit rotation flow.
* Multiple key files may exist for the same identity scope.
* If the node key is duplicated or ambiguous, startup must fail.

### 5.4 Local only property

* Private key material must not leave the backend key directory except into process memory for cryptographic operations.
* The Key Manager must not accept private key material from the graph, from network input, or from frontend input.

## 6. Public key binding to graph identities

### 6.1 Binding requirement

For each locally held identity scope used for signing, a corresponding public key must exist in the graph.

Binding is implemented as follows:

* The Key Manager derives the public key from a private key.
* The Graph Manager persists the public key as a `pubkey` Attribute on the corresponding identity Parent in app_0.
* A derived public key can only be offered for the identity scope that produced it, and it becomes immutable once accepted into the graph.

The Key Manager must not write directly to the graph or database.

### 6.2 Identity existence requirement

The Key Manager must not sign or provide public key material for an identity scope unless the corresponding identity Parent already exists in the graph, except when explicitly invoked as part of an identity creation or identity reconstruction flow.

### 6.3 Authority split

* The Key Manager is authoritative for private keys and derived public keys.
* The Graph Manager is authoritative for persisting public keys and binding them to identity Parents.

## 7. Interfaces and interactions

This section defines formal inputs and outputs. Callers are internal backend managers and system services only.

### 7.1 Inputs

The Key Manager accepts the following inputs:

* Configuration inputs:
  * Key directory root path.
  * Policy for generating missing keys per scope.
* Key lifecycle requests:
  * Ensure node key exists.
  * Create a new keypair for a specified identity or app scope.
  * Load a specific key by scope and key identifier.
* Cryptographic operation requests:
  * Sign a byte sequence for a specified identity scope and key identifier.
  * Encrypt a byte sequence for a specified recipient identity or public key.
  * Decrypt an ECIES ciphertext for a specified identity scope and key identifier.

All requests must originate from trusted backend components.

### 7.2 Outputs

The Key Manager provides the following outputs:

* Derived public key bytes for graph binding.
* Signature bytes for caller provided data.
* Ciphertext bytes from ECIES encryption using caller supplied recipient public keys.
* Plaintext bytes from ECIES decryption.

Private key material or representations enabling reconstruction are never returned.

### 7.3 Scope specification

Each operation must specify exactly one identity scope and one key identifier. Requests that do not do so must be rejected.

### 7.4 Authorization boundary

The Key Manager enforces a minimal authorization boundary:

* Only internal backend components may call it.
* Scope must be explicit and never inferred.
* Operations must be rejected if the requested scope or key is not locally present.
* No other component may access private keys or bypass the Key Manager for signing, encryption, or decryption.

Higher level authorization and ACL evaluation occur elsewhere.

## 8. Allowed and forbidden behaviors

### 8.1 Explicitly allowed behaviors

* Generate secp256k1 keypairs for explicitly requested scopes.
* Persist keys before reporting success.
* Load and cache private keys in memory for the lifetime of the process.
* Derive public keys for graph binding via the Graph Manager.
* Encrypt payload bytes via ECIES when the protocol flow requires confidentiality for a recipient public key.
* Enforce size limits and validation on cryptographic inputs.

### 8.2 Explicitly forbidden behaviors

* Exporting private keys in any form.
* Returning raw key objects or serialized private key material.
* Accepting private keys from the graph, remote peers, frontend requests, or app extensions.
* Writing to the graph, database, or sync state directly.
* Verifying signatures or inferring authorship.
* Selecting an identity or key on behalf of the caller.
* Continuing operation after detecting an invalid node key.
* Using any algorithm other than secp256k1 for signing or ECIES over secp256k1 for asymmetric encryption.

## 9. Failure handling

### 9.1 Startup failures

Startup must fail if any of the following occur:

* The node key is missing and generation is not permitted.
* The node key file is unreadable or malformed.
* The node key is not secp256k1.
* The node key cannot be used for required signing or decryption operations.

Startup failure is fatal for the backend process.

### 9.2 Runtime rejections

Operations must be rejected with explicit errors if:

* The requested scope or key does not exist locally.
* The requested key is unreadable or malformed.
* The operation input is invalid, empty where not permitted, or exceeds size limits.
* ECIES decryption fails.
* Encryption or signing requests specify unsupported algorithms or omit the recipient public key required for ECIES encryption.
* The request does not specify exactly one scope and key identifier.

Alternate scopes, silent retries, or fallback behavior are forbidden.

### 9.3 Key and graph mismatch

If a request targets an identity scope that is not bound in the graph, it must be rejected unless the request is explicitly part of an identity creation or reconstruction flow.

The Key Manager must not attempt to repair graph state.

### 9.4 Rotation and revocation interactions

Key rotation and revocation semantics are defined at the protocol and flow layers.

The Key Manager provides support behavior only:

* Creating and persisting new keypairs when invoked by an authorized rotation flow.
* Retaining older keys on disk without selecting active keys.
* Refusing to use keys marked as revoked when the caller supplies authoritative revocation status.

The Key Manager does not determine revocation precedence.

## 10. Operational constraints

* The backend key directory is the single source of truth for private keys.
* Loss of a private key prevents future signing and decryption for that scope but does not corrupt existing graph state.
* The Key Manager must not introduce background tasks beyond startup loading and request time operations.
