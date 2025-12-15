



# 10. Versioning and compatibility

## 1. Purpose and scope

This document defines protocol versioning and compatibility rules for 2WAY. It specifies how protocol versions are represented, how peers determine compatibility, and how version mismatches are handled. This file applies strictly to the protocol layer. It does not define application versioning, schema evolution, storage migrations, API versioning, or deployment concerns.

## 2. Responsibilities

This specification is responsible for the following:

- Defining the protocol version identifier and its interpretation.
- Defining compatibility requirements between peers.
- Defining allowed and forbidden interactions across protocol versions.
- Defining mandatory failure behavior when versions are incompatible.
- Preserving protocol safety, determinism, and security guarantees across versions.

This specification does not cover the following:

- Schema compatibility or schema migration rules.
- Application or service feature negotiation.
- Backend or frontend API versioning.
- Database layout evolution.
- Transport negotiation or transport versioning.
- Upgrade orchestration or rollout strategy.

## 3. Protocol version identifier

### 3.1 Representation

The protocol version is represented as a tuple of three integers:

- Major version.
- Minor version.
- Patch version.

The tuple is compared lexicographically.

### 3.2 Interpretation

The semantic meaning of each component is as follows:

- Major version denotes protocol incompatibility.
- Minor version denotes backward compatible protocol extensions.
- Patch version denotes clarifications or corrections that do not affect protocol semantics.

Patch version differences must not affect compatibility decisions or runtime behavior.

## 4. Compatibility rules

### 4.1 Compatibility definition

Two peers are protocol compatible if and only if all of the following conditions hold:

- The major version is identical.
- The local peer minor version is greater than or equal to the remote peer minor version.
- The remote peer does not require protocol behavior not defined at or below the local peer minor version.

Compatibility is asymmetric. A peer implementing a higher minor version may accept peers implementing lower minor versions of the same major version. The reverse is forbidden.

### 4.2 Compatibility guarantees

When compatibility conditions are satisfied, the following guarantees apply:

- All protocol invariants remain enforceable.
- Envelope validation, ACL enforcement, and sync ordering are deterministic.
- Security properties defined by the protocol are not weakened.
- Unsupported features are not implicitly enabled.

No guarantees are made regarding availability of features introduced after the negotiated minor version.

## 5. Version declaration and validation

### 5.1 Declaration requirement

A peer must declare its protocol version during any interaction that establishes protocol state or trust, including:

- Initial peer handshake.
- Sync session establishment.

Version declarations are treated as untrusted input.

### 5.2 Validation boundary

Protocol version compatibility must be evaluated before any of the following occur:

- Graph mutation.
- State allocation.
- Sync processing.
- Resource reservation.

If compatibility cannot be established, the interaction must not proceed.

## 6. Allowed and forbidden behaviors

### 6.1 Explicitly allowed behaviors

The following behaviors are allowed:

- Accepting peers with the same major version and lower or equal minor version.
- Restricting protocol behavior to the feature set defined by the negotiated minor version.
- Maintaining concurrent connections to peers running different minor versions of the same major version.

### 6.2 Explicitly forbidden behaviors

The following behaviors are forbidden:

- Accepting any interaction from a peer with a different major version.
- Processing envelopes that depend on protocol behavior not defined by the local version.
- Guessing, inferring, or emulating behavior outside the negotiated protocol version.
- Weakening validation, ACL enforcement, or sync guarantees due to version mismatch.

Forbidden behavior must result in rejection.

## 7. Interaction with other components

### 7.1 Inputs

This specification consumes the following inputs:

- Declared protocol version from a remote peer.
- Locally configured protocol version.

### 7.2 Outputs

This specification produces the following outputs:

- A compatibility decision, compatible or incompatible.
- An effective protocol version, defined as the remote peer minor version when compatible.

### 7.3 Trust boundary

This specification operates at the boundary between local protocol logic and remote peers. No assumptions are made about correctness, honesty, or completeness of remote declarations.

## 8. Failure and rejection behavior

### 8.1 Incompatible versions

If protocol versions are incompatible, the system must:

- Reject the interaction deterministically.
- Perform no graph mutation.
- Perform no sync processing.
- Release or avoid allocating protocol resources.

### 8.2 Invalid version declarations

If a version declaration is missing, malformed, or semantically invalid, it must be treated as incompatible and rejected.

### 8.3 Late detection

If incompatibility is detected after partial interaction, the system must:

- Abort the interaction immediately.
- Discard all uncommitted data.
- Preserve all local invariants.

No retry or downgrade behavior is defined at the protocol level.

## 9. Invariants and guarantees

### 9.1 Invariants

The following invariants must always hold:

- Protocol compatibility is evaluated before trust or state exchange.
- Version mismatch cannot weaken security or validation guarantees.
- Protocol behavior is deterministic within a negotiated version.

### 9.2 Guarantees

The protocol provides the following guarantees:

- Safe coexistence of peers across compatible minor versions.
- Explicit and deterministic rejection of incompatible peers.
- Absence of silent degradation or implicit fallback behavior.

No additional guarantees are implied.
