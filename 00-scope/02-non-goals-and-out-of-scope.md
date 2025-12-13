



# 02 Non-goals and out-of-scope

## 1. Purpose and scope

This document defines what the 2WAY system explicitly does not attempt to provide, guarantee, or solve. Its purpose is to establish hard boundaries around responsibility, trust, functionality, and assumptions, in order to prevent scope creep, incorrect threat assumptions, and invalid architectural dependencies.

This document is normative. Any behavior, property, or guarantee not explicitly included in the system design or explicitly excluded here must be assumed to be unsupported.

## 2. Non-goals

### 2.1 Global identity verification

The system does not attempt to prove real-world identity, legal identity, or uniqueness of human actors.

- There is no notion of government identity, biometric identity, or external KYC.
- There is no global registry of identities.
- There is no guarantee that one human corresponds to one identity.

Identity in 2WAY is cryptographic and structural only, as defined elsewhere.

### 2.2 Global Sybil prevention

The system does not attempt to eliminate Sybil identities at the protocol level.

- There is no proof-of-work, proof-of-stake, or proof-of-personhood.
- There is no global reputation score.
- There is no network-wide trust anchor.

Sybil resistance is achieved only through graph structure, local trust decisions, and app-defined rules. No stronger guarantee is claimed.

### 2.3 Consensus or global agreement

The system does not provide global consensus.

- There is no single canonical global state.
- There is no total ordering of operations across all nodes.
- There is no guarantee that all nodes converge to identical graphs.

Each node is authoritative over its own graph and enforces its own validation rules.

### 2.4 High availability guarantees

The system does not guarantee uptime, latency bounds, or availability.

- Nodes may be offline indefinitely.
- Sync is opportunistic and peer-dependent.
- Message delivery is best-effort within allowed domains.

Availability is a property of deployment, not of the protocol.

### 2.5 Real-time guarantees

The system does not guarantee real-time delivery or ordering.

- There are no deadlines, timeouts, or real-time constraints.
- Ordering guarantees apply only where explicitly defined, such as global_seq within a node.
- Wall-clock time is not a trust input.

### 2.6 Economic or incentive mechanisms

The system does not define economic incentives.

- There are no tokens, fees, rewards, or penalties.
- There is no built-in marketplace or pricing mechanism.
- There is no economic deterrent to misuse.

Any economic layer must be implemented entirely at the app level.

### 2.7 Content moderation or policy enforcement

The system does not enforce global content policies.

- There is no censorship logic.
- There is no moderation authority.
- There is no definition of acceptable content.

Moderation, filtering, and policy enforcement are app responsibilities.

### 2.8 User experience guarantees

The system does not guarantee usability, discoverability, or safety for end users.

- There are no UX constraints at the protocol level.
- There is no protection against social engineering.
- There is no prevention of user error.

Frontend behavior is explicitly out of scope.

## 3. Out-of-scope behaviors

### 3.1 Implicit trust

The system forbids implicit trust.

- No operation is trusted based on network origin.
- No operation is trusted based on connection state.
- No operation is trusted based on historical behavior alone.

Any component relying on implicit trust violates the design.

### 3.2 Silent failure handling

The system forbids silent acceptance of invalid input.

- Invalid envelopes must be rejected.
- Unauthorized operations must not be applied partially.
- Malformed data must not be coerced into valid state.

Failure must be explicit at the validation boundary.

### 3.3 Automatic conflict resolution across nodes

The system forbids automatic global conflict resolution.

- Conflicts are resolved locally or at the app level.
- There is no forced merge strategy.
- There is no authoritative peer.

### 3.4 Cross-app interpretation

The system forbids cross-app semantic interpretation.

- Objects from one app must not be reinterpreted by another app.
- Ratings, trust edges, and schemas are app-scoped.
- System services do not reinterpret app-defined meaning.

### 3.5 Backend extensibility without constraint

The system forbids unrestricted backend modification.

- Apps must not bypass managers.
- Apps must not perform raw storage writes.
- Apps must not override validation, ACLs, or sync rules.

Backend isolation is mandatory.

## 4. Explicit exclusions

The following are explicitly excluded from the design and must not be assumed:

- Distributed consensus algorithms.
- Byzantine fault tolerance.
- Global clocks or time synchronization.
- Centralized identity providers.
- Automatic data recovery without trusted history.
- Guaranteed message delivery.
- Global search or indexing.
- Data mining or analytics across nodes.
- Network anonymity guarantees beyond transport properties.

## 5. Interactions with other components

This document has no direct inputs or outputs.

It defines constraints that apply to all components equally.

Other components must not assume behaviors or guarantees excluded here. Any such assumption constitutes a design error.

## 6. Behavior on violation

If an implementation introduces behavior that contradicts this document:

- The behavior is non-compliant.
- Security assumptions elsewhere become invalid.
- The implementation must be considered unsafe until corrected.

There is no graceful degradation for violations of scope boundaries.
