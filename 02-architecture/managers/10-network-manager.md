



# 10. Network Manager

## 1. Purpose and scope

This document specifies the Network Manager. The Network Manager owns all peer to peer network communication for a 2WAY node. It defines transport abstraction, ordered network startup and shutdown, staged admission through a bastion, cryptographic binding at the network boundary, and coordination with the DoS Guard for abuse containment. It is the sole component through which network data may enter or leave the system, consistent with the responsibilities described in `01-protocol/00-protocol-overview.md` and the cryptographic boundary defined in `01-protocol/04-cryptography.md`.

This specification defines internal engines that together constitute the Network Manager. These engines are normative and required for correct implementation.

This document does not define protocol semantics, graph mutation logic, authorization decisions, synchronization ordering, or abuse policy.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

- Owning all inbound and outbound network listeners and connections.
- Abstracting supported network transports while preserving peer context per `01-protocol/08-network-transport-requirements.md`.
- Performing ordered network startup and shutdown sequencing.
- Managing onion service lifecycle where configured.
- Enforcing hard transport level limits on size, rate, and concurrency.
- Providing staged admission via a Bastion Engine aligned with the abuse resistance model coordinated through DoS Guard Manager.
- Coordinating admission decisions with the DoS Guard Manager.
- Managing post admission inbound and outbound communication paths.
- Performing cryptographic binding for network packages using the Key Manager exactly as mandated in `01-protocol/04-cryptography.md`.
- Verifying signatures and decrypting inbound packages addressed to the local node using the algorithms specified in `01-protocol/04-cryptography.md`.
- Signing and encrypting outbound packages as required by protocol rules defined in `01-protocol/04-cryptography.md` and `01-protocol/03-serialization-and-envelopes.md`.
- Ensuring only admitted and cryptographically verified packages are forwarded internally.
- Preserving transport metadata and admission context.
- Preserving envelope byte order and boundaries exactly across ingress and egress.
- Surfacing explicit best effort connection lifecycle and failure events to the State Manager, DoS Guard Manager, and Event Manager per `01-protocol/08-network-transport-requirements.md`.
- Treating transport provided peer references as advisory context only until cryptographic identity binding occurs.
- Exposing readiness and liveness state to the Health Manager.
- Emitting network level events, failures, and state transitions.

This specification does not cover the following:

- Definition of cryptographic primitives or algorithms.
- Key lifecycle management or storage.
- Puzzle definition, difficulty selection, or verification logic.
- Abuse classification or reputation systems.
- Schema validation, ACL evaluation, or graph semantics.
- Synchronization ordering, reconciliation, or replay handling.
- Application level APIs or user facing network interfaces.
- Peer discovery policy or routing strategy beyond transport abstraction.

## 3. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

- All network originated data is treated as untrusted until explicitly admitted and cryptographically verified.
- No inbound data reaches any Manager other than the Network Manager without passing Bastion admission.
- No inbound package reaches the State Manager without passing cryptographic verification and decryption where applicable.
- Rejected or unauthenticated network input cannot cause state mutation.
- Admission, verification, and forwarding decisions are deterministic for a given input and configuration.
- Transport metadata and admission context are preserved exactly in accordance with `01-protocol/08-network-transport-requirements.md`.
- Envelope payload bytes and protocol level metadata are immutable between transport ingress and State Manager handoff, except for cryptographic operations orchestrated with the Key Manager when producing outbound packages.
- Trust level increases only monotonically across defined boundaries.
- Transport provided peer references are never treated as authenticated identity without cryptographic verification, matching the trust model in `01-protocol/08-network-transport-requirements.md` and `01-protocol/04-cryptography.md`.
- All components treat transport connectivity as best effort: delivery, ordering, deduplication, and availability guarantees are never assumed.
- Only the Network Manager interacts directly with raw transport data per `01-protocol/08-network-transport-requirements.md`. Downstream consumers receive outputs solely through the verified package or telemetry paths described in this specification.
- Failure at any network boundary fails closed.
- These guarantees hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 4. Internal engine structure

The Network Manager is composed of four mandatory internal engines. These engines define strict phase boundaries and must not be collapsed, reordered, or bypassed.

### 4.1 Network Startup Engine

The Network Startup Engine governs ordered initialization and teardown of all network subsystems.

Responsibilities:

- Initializing transport subsystems.
- Binding to the Config Manager, Key Manager, DoS Guard Manager, Event Manager, and Health Manager.
- Starting onion services where configured.
- Registering inbound listeners prior to any outbound connection attempts.
- Initializing Bastion, Incoming, and Outgoing Engines in that order.
- Declaring network readiness only after successful initialization.
- Coordinating ordered shutdown on termination signals.

Constraints:

- The Network Startup Engine must not create or manage client puzzles.
- The Network Startup Engine must not access storage, graph, or state.
- Partial initialization must not result in network readiness.
- Startup failure must fail closed and prevent admission.

### 4.2 Bastion Engine

The Bastion Engine owns all unauthenticated and unadmitted network connections.

Responsibilities:

- Accepting initial inbound connections from external peers.
- Terminating onion services and direct transports at the Bastion boundary.
- Enforcing minimal framing, size, and rate gating prior to expensive processing.
- Maintaining provisional transport level peer context.
- Coordinating admission decisions with the DoS Guard Manager.
- Exchanging opaque challenge and response payloads as instructed.
- Holding unadmitted connections in a bounded and isolated state.
- Rejecting, throttling, or terminating connections based on DoS Guard directives.

Constraints:

- The Bastion Engine must not perform cryptographic verification.
- The Bastion Engine must not parse protocol semantics.
- The Bastion Engine must not forward data to protocol or application components.
- Challenge payloads are opaque and must not be interpreted.
- Transport level peer references exposed at the Bastion boundary are advisory and must not be treated as authenticated identity assertions.

### 4.3 Incoming Engine

The Incoming Engine owns all inbound communication after successful Bastion admission.

Responsibilities:

- Receiving inbound packages from admitted peers.
- Performing full transport framing validation.
- Enforcing post admission transport limits.
- Invoking the Key Manager to verify package signatures.
- Invoking the Key Manager to decrypt packages addressed to the local node.
- Associating verified signer identity with each package.
- Preserving the exact envelope boundaries and payload bytes delivered by the transport layer when forwarding to the State Manager.
- Forwarding only verified and decrypted packages to the State Manager.

Constraints:

- Data from unadmitted connections must not reach the Incoming Engine.
- Partially verified packages must not be forwarded.
- Authorization, schema, and graph evaluation are forbidden.
- Ordering, deduplication, retry, or delivery guarantees must not be inferred or introduced.

### 4.4 Outgoing Engine

The Outgoing Engine owns all outbound communication after successful Bastion admission.

Responsibilities:

- Establishing and maintaining outbound connections to admitted peers.
- Requesting outbound packages from the State Manager.
- Invoking the Key Manager to sign and encrypt outbound packages.
- Applying transport framing and transmission.
- Enforcing outbound transport limits.
- Preserving outbound envelope boundaries, byte content, and metadata as provided by the State Manager while applying cryptographic protection.
- Emitting explicit delivery failure, timeout, and disconnect events to the Event Manager, State Manager, and DoS Guard Manager without implicit retry.
- Reporting transmission failures and connection state changes.

Constraints:

- Outbound traffic to unadmitted peers is forbidden.
- Implicit retry or replay is forbidden unless specified elsewhere.
- Cryptographic or transport failure must fail closed.
- Ordering, deduplication, or delivery guarantees must not be promised beyond the transport specification.

### 4.5 Transport interface obligations

All engines interact with the transport abstraction defined by the protocol specification. The following requirements apply globally:

- Transport behavior is adversarial and best effort as described in `01-protocol/08-network-transport-requirements.md`. Drops, duplication, delay, and disconnects must be tolerated and surfaced without embellishment.
- Envelope payloads and boundaries must never be mutated or synthesized by the Network Manager, preserving the guarantees in `01-protocol/08-network-transport-requirements.md`.
- Peer references emitted by the transport remain advisory and must only be used for connection management, telemetry, and DoS Guard policy inputs until cryptographic identity binding is completed per `01-protocol/08-network-transport-requirements.md`.
- Delivery failure, timeout, and disconnect signals must be propagated to the Event Manager, State Manager, and DoS Guard Manager without implicit retry semantics per `01-protocol/08-network-transport-requirements.md`.
- No component outside the Network Manager, State Manager (through verified package delivery), and DoS Guard Manager (through telemetry feeds) may access transport derived data.

## 5. Admission and DoS Guard integration

### 5.1 Bastion to DoS Guard inputs

The Bastion Engine must provide:

- Connection identifier.
- Transport type and addressing metadata where available.
- Connection timing information.
- Byte and message counters.
- Local resource pressure indicators.
- Admission request type, inbound or outbound.
- Transport advisory peer references and observed routing metadata suitable for behavioral analysis per `01-protocol/08-network-transport-requirements.md`.

### 5.2 DoS Guard to Bastion outputs

The DoS Guard Manager returns one of:

- Allow admission.
- Deny admission.
- Require challenge.

Optional directives may include:

- Opaque challenge payload and validity window.
- Throttling parameters.
- Logging and severity classification.

Constraints:

- Admission requires explicit allow.
- Challenge content is opaque to the Network Manager.
- Puzzle ownership resides exclusively with the DoS Guard Manager.
- Telemetry or directives obtained during this exchange must not be repurposed as authenticated identity evidence.

## 6. Connection lifecycle and state transitions

Each network connection must exist in exactly one state:

- created
- bastion-held
- challenged
- admitted
- active-incoming
- active-outgoing
- closing
- closed

Allowed transitions:

- created to bastion-held
- bastion-held to challenged
- challenged to admitted
- admitted to active-incoming
- admitted to active-outgoing
- any state to closing
- closing to closed

Forbidden transitions:

- bastion-held directly to active-incoming or active-outgoing
- challenged directly to active-incoming or active-outgoing
- any state directly to State Manager
- closed to any other state

## 7. Inputs and outputs

### 7.1 Inputs

The Network Manager accepts:

- Raw inbound byte streams from supported transports.
- Outbound package requests from the State Manager.
- Configuration data from the Config Manager.
- Admission and challenge directives from the DoS Guard Manager.
- Startup and shutdown signals from the runtime environment.
- Readiness and liveness probes from the Health Manager.

All inbound network data is untrusted.

### 7.2 Outputs

The Network Manager produces:

- Verified inbound packages forwarded to the State Manager.
- Outbound network transmissions.
- Explicit rejection and challenge responses.
- Connection termination actions.
- Network events and failures emitted to the Event Manager.
- Readiness and liveness state updates to the Health Manager.

### 7.3 Transport semantics and consumers

- Transport services provide best effort delivery only, as explicitly stated in `01-protocol/08-network-transport-requirements.md`. Drops, delay, duplication, and disconnects must be surfaced as events without implying reliability, ordering, or deduplication guarantees.
- Peer references supplied by transport are advisory only per `01-protocol/08-network-transport-requirements.md`. Identity assertions must originate from cryptographic verification performed with the Key Manager.
- Only the Network Manager, State Manager (via verified package delivery), and DoS Guard Manager (via explicit telemetry) may consume transport outputs, matching the consumer list in `01-protocol/08-network-transport-requirements.md`. All other components are strictly prohibited from interacting with raw transport data.
- Delivery failure, timeout, and disconnect signals must be emitted promptly to both the Event Manager and State Manager so that higher layers can apply their own recovery or sync logic, consistent with `01-protocol/08-network-transport-requirements.md`.

## 8. Trust boundaries

The Network Manager defines multiple trust boundaries:

- External network boundary at Bastion Engine ingress.
- Admission boundary between Bastion and Incoming or Outgoing Engines.
- Cryptographic verification boundary prior to State Manager forwarding.

Trust escalation is explicit, monotonic, and irreversible.

## 9. Allowed and forbidden behaviors

### 9.1 Explicitly allowed behaviors

The Network Manager may:

- Maintain concurrent Bastion and admitted connections.
- Hold unauthenticated connections in bounded isolation.
- Enforce hard transport limits independently of DoS Guard policy.
- Terminate connections unilaterally on failure or shutdown.
- Emit detailed network and admission events.

### 9.2 Explicitly forbidden behaviors

The Network Manager must not:

- Forward data from unadmitted connections beyond the Bastion Engine.
- Accept inbound packages without cryptographic verification.
- Make puzzle policy or difficulty decisions.
- Modify package contents.
- Persist network input beyond transient buffering.
- Bypass defined engine transitions.
- Treat transport level peer identifiers as authenticated identity, which would violate `01-protocol/08-network-transport-requirements.md`.
- Synthesize or mutate envelope payloads or protocol metadata beyond cryptographic protection required for outbound packages.

## 10. Failure and rejection behavior

### 10.1 Invalid input

On malformed input:

- Reject immediately.
- Avoid allocation proportional to input size.
- Do not forward downstream.
- Emit rejection event where appropriate.

### 10.2 Admission failure

On denial or challenge timeout:

- Terminate the Bastion connection.
- Emit admission failure event.
- Apply throttling if instructed.

### 10.3 DoS Guard unavailability

If the DoS Guard Manager is unavailable:

- Fail closed for new admissions.
- Maintain existing admitted connections.
- Mark readiness as degraded.
- Emit critical failure event.

### 10.4 Onion service failure

On onion service startup or runtime failure:

- Do not declare readiness.
- Terminate affected ingress paths.
- Emit failure event.
- Require explicit recovery or restart.

### 10.5 Resource exhaustion

On resource pressure:

- Reject new Bastion connections first.
- Preserve admitted connections preferentially.
- Fail closed if limits are exceeded.

### 10.6 Internal failure

On internal failure:

- Halt new admissions.
- Preserve integrity of verified in flight packages.
- Require explicit recovery or restart.

## 11. Configuration and limits

The Network Manager enforces mandatory limits, including:

- Maximum concurrent Bastion connections.
- Maximum concurrent admitted connections.
- Maximum per connection message rate.
- Maximum package size.
- Maximum transient buffering per connection.

These limits are mandatory and cannot be disabled.

## 12. Security considerations

- The Network Manager is a primary external attack surface.
- All parsing must be bounded and fail fast.
- Bastion isolation must prevent amplification and exhaustion.
- Cryptographic binding must precede any stateful processing.
- Error signaling must not leak internal state or topology details.
