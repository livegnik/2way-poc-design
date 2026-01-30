



# 11 Versioning and compatibility

Defines protocol version identifiers and compatibility rules for 2WAY peers. Specifies compatibility validation boundaries and rejection behavior. Defines allowed/forbidden cross-version interactions and guarantees.

For the meta specifications, see [11-versioning-and-compatibility meta](../09-appendix/meta/01-protocol/11-versioning-and-compatibility-meta.md).

## 1. Protocol version identifier

### 1.1 Representation

The protocol version is represented as a tuple of three integers:

- Major version.
- Minor version.
- Patch version.

The tuple is compared lexicographically.

### 1.2 Interpretation

The semantic meaning of each component is as follows:

- Major version denotes protocol incompatibility.
- Minor version denotes backward compatible protocol extensions.
- Patch version denotes clarifications or corrections that do not affect protocol semantics.

Patch version differences must not affect compatibility decisions or runtime behavior.

## 2. Compatibility rules

### 2.1 Compatibility definition

Two peers are protocol compatible if and only if all of the following conditions hold:

- The major version is identical.
- The local peer minor version is greater than or equal to the remote peer minor version.
- The remote peer does not require protocol behavior not defined at or below the local peer minor version.

Compatibility is asymmetric. A peer implementing a higher minor version may accept peers implementing lower minor versions of the same major version. The reverse is forbidden.

### 2.2 Compatibility guarantees

When compatibility conditions are satisfied, the following guarantees apply:

- All protocol invariants remain enforceable.
- [Envelope validation](03-serialization-and-envelopes.md), [ACL enforcement](06-access-control-model.md), and [sync ordering](07-sync-and-consistency.md) are deterministic.
- Security properties defined by the protocol are not weakened.
- Unsupported features are not implicitly enabled.

No guarantees are made regarding availability of features introduced after the negotiated minor version.

## 3. Version declaration and validation

### 3.1 Declaration requirement

A peer must declare its protocol version during any interaction that establishes protocol state or trust, including:

- Initial peer handshake.
- Sync session establishment.

Version declarations are treated as untrusted input.

### 3.2 Validation boundary

Protocol version compatibility must be evaluated before any of the following occur:

- [Graph mutation](../02-architecture/managers/07-graph-manager.md).
- State allocation.
- [Sync processing](07-sync-and-consistency.md).
- Resource reservation.

If compatibility cannot be established, the interaction must not proceed.

## 4. Allowed and forbidden behaviors

### 4.1 Explicitly allowed behaviors

The following behaviors are allowed:

- Accepting peers with the same major version and lower or equal minor version.
- Restricting protocol behavior to the feature set defined by the negotiated minor version.
- Maintaining concurrent connections to peers running different minor versions of the same major version.

### 4.2 Explicitly forbidden behaviors

The following behaviors are forbidden:

- Accepting any interaction from a peer with a different major version.
- Processing [envelopes](03-serialization-and-envelopes.md) that depend on protocol behavior not defined by the local version.
- Guessing, inferring, or emulating behavior outside the negotiated protocol version.
- Weakening [validation](10-errors-and-failure-modes.md), [ACL enforcement](06-access-control-model.md), or [sync guarantees](07-sync-and-consistency.md) due to version mismatch.

Forbidden behavior must result in rejection.

## 5. Interaction with other components

### 5.1 Inputs

This specification consumes the following inputs:

- Declared protocol version from a remote peer.
- Locally configured protocol version.

### 5.2 Outputs

This specification produces the following outputs:

- A compatibility decision, compatible or incompatible.
- An effective protocol version, defined as the remote peer minor version when compatible.

### 5.3 Trust boundary

This specification operates at the boundary between local protocol logic and remote peers (see [08-network-transport-requirements.md](08-network-transport-requirements.md)). No assumptions are made about correctness, honesty, or completeness of remote declarations.

## 6. Failure and rejection behavior

### 6.1 Incompatible versions

If protocol versions are incompatible, the system must:

- Reject the interaction deterministically (see [10-errors-and-failure-modes.md](10-errors-and-failure-modes.md)).
- Perform no graph mutation (see [02-architecture/managers/07-graph-manager.md](../02-architecture/managers/07-graph-manager.md)).
- Perform no [sync](07-sync-and-consistency.md) processing.
- Release or avoid allocating protocol resources.

### 6.2 Invalid version declarations

If a version declaration is missing, malformed, or semantically invalid, it must be treated as incompatible and rejected.

### 6.3 Late detection

If incompatibility is detected after partial interaction, the system must:

- Abort the interaction immediately.
- Discard all uncommitted data (see [02-architecture/managers/02-storage-manager.md](../02-architecture/managers/02-storage-manager.md)).
- Preserve all local invariants.

No retry or downgrade behavior is defined at the protocol level.

## 7. Invariants and guarantees

### 7.1 Invariants

The following invariants must always hold:

- Protocol compatibility is evaluated before trust or state exchange (see [08-network-transport-requirements.md](08-network-transport-requirements.md)).
- Version mismatch cannot weaken security or validation guarantees.
- Protocol behavior is deterministic within a negotiated version.

### 7.2 Guarantees

The protocol provides the following guarantees:

- Safe coexistence of peers across compatible minor versions.
- Explicit and deterministic rejection of incompatible peers.
- Absence of silent degradation or implicit fallback behavior.

No additional guarantees are implied.
