



# 10. Network Manager

## 1. Purpose and scope

This document specifies the Network Manager.

The Network Manager owns all peer to peer network I/O for a 2WAY node. It is the only component allowed to touch raw transport data. It defines transport abstraction, ordered startup and shutdown of network surfaces, staged admission through a bastion boundary, cryptographic binding at the network edge, and integration with DoS Guard for abuse containment.  

This specification defines internal engines that together constitute the Network Manager. These engines and their boundaries are normative and required for correct implementation.

This specification consumes the protocol contracts defined in `01-protocol/08-network-transport-requirements.md`, `01-protocol/03-serialization-and-envelopes.md`, `01-protocol/04-cryptography.md`, `01-protocol/05-keys-and-identity.md`, and `01-protocol/11-dos-guard-and-client-puzzles.md`. Those files remain normative for all behaviors described here.

This document does not define synchronization policy, graph semantics, authorization decisions, or DoS policy logic.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Owning all inbound and outbound listeners, sessions, and connection state machines for supported transports, consolidating the consumer boundary defined in `01-protocol/08-network-transport-requirements.md`.
* Abstracting transport implementations while preserving peer context and transport metadata, exactly as required by `01-protocol/08-network-transport-requirements.md`.
* Providing ordered startup and shutdown sequencing for all network surfaces, including onion service lifecycle where configured, so that surfaces mandated by `01-protocol/08-network-transport-requirements.md` are either ready or explicitly failed closed.
* Enforcing hard transport-level limits for size, rate, concurrency, and buffering independently of any DoS policy, satisfying the resource-failure constraints defined in `01-protocol/08-network-transport-requirements.md` and `01-protocol/09-errors-and-failure-modes.md`.
* Providing staged admission via a Bastion Engine that isolates unauthenticated peers and coordinates with DoS Guard for allow, deny, and challenge flows per `01-protocol/11-dos-guard-and-client-puzzles.md`.
* Executing challenge transport as an opaque exchange, without interpreting puzzle content, difficulty, or verification logic, which are owned by DoS Guard and defined in `01-protocol/11-dos-guard-and-client-puzzles.md`.
* Binding transport sessions to cryptographic identity only through Key Manager verification, never through transport-provided identifiers, preserving the identity model in `01-protocol/05-keys-and-identity.md`.
* Verifying signatures and decrypting inbound envelopes addressed to the local node, and attaching verified signer identity to the delivered package, exactly as mandated by `01-protocol/04-cryptography.md` and `01-protocol/05-keys-and-identity.md`.
* Signing and encrypting outbound envelopes as required by protocol rules and configuration, via the Key Manager, following the algorithms defined in `01-protocol/04-cryptography.md`.
* Delivering only admitted and cryptographically verified inbound packages to the State Manager, preserving the envelope semantics of `01-protocol/03-serialization-and-envelopes.md` and the sync ordering rules of `01-protocol/07-sync-and-consistency.md`.
* Transmitting outbound packages received from the State Manager, without adding retry semantics or persistence, thus honoring the best-effort semantics of `01-protocol/08-network-transport-requirements.md`.
* Emitting explicit connection lifecycle events, admission outcomes, transport failures, and health signals to the Event Manager and Health Manager, and emitting admission telemetry to DoS Guard as required by `01-protocol/08-network-transport-requirements.md` and `01-protocol/11-dos-guard-and-client-puzzles.md`.
* Supporting multiple transport surfaces when configured, including the legacy dual-surface model where a bastion surface is separated from an admitted data surface, without changing the trust boundary rules mandated in `01-protocol/08-network-transport-requirements.md`.

This specification does not cover the following:

* Definition of cryptographic primitives, algorithms, key formats, key rotation, or key storage.
* Definition of envelope schemas, sync semantics, replay rules, reconciliation logic, or ordering guarantees.
* ACL evaluation, schema validation, graph mutation logic, conflict handling, or any state write behavior.
* DoS policy decisions, puzzle creation, puzzle verification, difficulty selection, reputation scoring, or abuse classification.
* Peer discovery policy, routing policy, multi-hop relay policy, or any topology strategy beyond the transport boundary.
* Any user-facing APIs, UI behavior, or admin workflows.

## 3. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* All transport-derived input is untrusted until it passes bastion admission and cryptographic verification, consistent with `01-protocol/08-network-transport-requirements.md`.
* No inbound data reaches any manager other than the Network Manager without passing Bastion admission.
* No inbound package reaches the State Manager unless admission succeeded and signature verification succeeded, and decryption succeeded when required.
* Transport-provided peer references are advisory only. They are never treated as authenticated identity evidence. 
* Envelope bytes retain the exact structure defined in `01-protocol/03-serialization-and-envelopes.md`; the Network Manager never rewrites them while verifying or forwarding packages.
* All cryptographic operations use the algorithms defined in `01-protocol/04-cryptography.md`, and signer identity binding follows `01-protocol/05-keys-and-identity.md`.
* Admission, deny, and challenge behaviors follow `01-protocol/11-dos-guard-and-client-puzzles.md`, including opacity of puzzles and the requirement to fail closed on DoS Guard unavailability.
* Trust escalation is explicit, monotonic, and irreversible across the boundaries defined in this file.
* Envelope bytes and envelope boundaries are preserved end-to-end between transport ingress and State Manager delivery, except for cryptographic unwrap required to obtain the plaintext envelope for local delivery.
* The Network Manager never performs schema validation, ACL evaluation, graph mutation, sync ordering, or reconciliation.
* The Network Manager never introduces delivery, ordering, deduplication, or retry guarantees beyond what the transport provides, as mandated by `01-protocol/08-network-transport-requirements.md`.
* Failures at any trust boundary fail closed. When a required check cannot be performed, the input is rejected and not forwarded, matching the failure posture defined in `01-protocol/09-errors-and-failure-modes.md`.
* These guarantees hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise. 

## 4. Internal engine structure

The Network Manager is composed of four mandatory internal engines. These engines define strict phase boundaries and must not be collapsed, reordered, or bypassed. 

### 4.1 Network Startup Engine

The Network Startup Engine governs ordered initialization, readiness gating, and teardown of all network subsystems.

Responsibilities:

* Loading network configuration and limits from Config Manager.
* Binding to Key Manager, DoS Guard Manager, State Manager, Event Manager, and Health Manager.
* Initializing transport adapters and registering transport error hooks.
* Validating that each adapter satisfies the send, receive, and telemetry expectations defined in `01-protocol/08-network-transport-requirements.md` before it is exposed downstream.
* Creating and starting inbound transport surfaces in a defined order:

  * Bastion ingress surface.
  * Optional admitted data surface, if configured as a distinct surface.
* Publishing readiness only after all required surfaces are live, the Bastion Engine is able to accept connections, and DoS Guard dependencies defined in `01-protocol/11-dos-guard-and-client-puzzles.md` are reachable or explicitly configured out.
* Starting the Bastion, Incoming, and Outgoing Engines in that order.
* Starting the Network Manager runtime loop responsibilities that belong to this manager:

  * connection reaping and timeout enforcement
  * keepalive scheduling if the transport requires it
  * handshake maintenance that is strictly transport-level and does not alter protocol semantics
* Coordinating ordered shutdown and surfacing shutdown progress to Health Manager.

Constraints:

* The Startup Engine must not create, solve, interpret, or verify client puzzles.
* The Startup Engine must not access Storage Manager or Graph Manager.
* The Startup Engine must not trigger graph mutations to publish endpoint changes. It may only emit events and hand off endpoint facts to the appropriate manager.
* Partial initialization must not result in readiness. Startup failure must fail closed and prevent new admissions.

### 4.2 Bastion Engine

The Bastion Engine owns all unauthenticated and unadmitted connections.

Responsibilities:

* Accepting initial inbound sessions from external peers on the bastion ingress surface.
* Enforcing minimal framing and strict pre-admission limits to avoid expensive processing on hostile input, preserving the transport constraints defined in `01-protocol/08-network-transport-requirements.md`.
* Maintaining provisional transport context for telemetry and throttling, without treating it as identity.
* Emitting admission telemetry to DoS Guard and consuming DoS Guard directives defined in `01-protocol/11-dos-guard-and-client-puzzles.md`.
* Executing the admission state machine for both inbound and outbound session attempts, exactly as defined in `01-protocol/11-dos-guard-and-client-puzzles.md`:

  * allow admission
  * deny admission
  * require challenge, then re-evaluate on response
* Exchanging opaque challenge and response payloads as instructed by DoS Guard, without interpreting the contents per `01-protocol/11-dos-guard-and-client-puzzles.md`.
* Holding unadmitted sessions in bounded isolation, including bounded buffering and bounded concurrent challenged sessions.
* Terminating, throttling, or pausing bastion sessions based on DoS Guard directives from `01-protocol/11-dos-guard-and-client-puzzles.md` and hard limits.

Constraints:

* The Bastion Engine must not perform cryptographic verification or decryption of protocol envelopes.
* The Bastion Engine must not parse protocol semantics beyond minimal framing required to run the admission exchange, preserving the envelope opacity described in `01-protocol/03-serialization-and-envelopes.md`.
* The Bastion Engine must not forward any payload to State Manager, Graph Manager, ACL Manager, or Storage Manager.
* Challenge payloads are opaque. The Bastion Engine must not interpret puzzle content, difficulty, or correctness, per `01-protocol/11-dos-guard-and-client-puzzles.md`.
* A session is not admitted unless DoS Guard explicitly allows it, satisfying `01-protocol/11-dos-guard-and-client-puzzles.md`.

### 4.3 Incoming Engine

The Incoming Engine owns all inbound communication after successful bastion admission.

Responsibilities:

* Receiving inbound envelopes from admitted peers on the admitted surface or admitted sessions, depending on transport configuration, while preserving the envelope shapes defined in `01-protocol/03-serialization-and-envelopes.md`.
* Enforcing post-admission limits, including maximum envelope size, maximum per-connection rate, and maximum buffering.
* Performing full transport framing validation for admitted traffic, ensuring compliance with `01-protocol/08-network-transport-requirements.md`.
* Invoking the Key Manager to verify envelope signatures and bind the envelope to a signer identity, exactly as defined in `01-protocol/04-cryptography.md` and `01-protocol/05-keys-and-identity.md`.
* Invoking the Key Manager to decrypt envelopes addressed to the local node, when encryption is used, following `01-protocol/04-cryptography.md`.
* Constructing an internal delivery unit that contains:

  * the plaintext envelope bytes intended for the State Manager
  * verified signer identity
  * transport metadata and admission context required for downstream policy and telemetry
* Forwarding only fully verified and decrypted packages to the State Manager, preserving sync semantics defined in `01-protocol/07-sync-and-consistency.md`.

Constraints:

* Data from unadmitted sessions must never reach the Incoming Engine.
* Partially verified, unverifiable, or undecipherable payloads must not be forwarded, consistent with `01-protocol/04-cryptography.md`.
* Authorization, schema validation, graph evaluation, reconciliation, and state mutation are forbidden.
* The Incoming Engine must not implement retry, reordering, or deduplication.

### 4.4 Outgoing Engine

The Outgoing Engine owns all outbound communication after successful bastion admission.

Responsibilities:

* Establishing and maintaining outbound sessions to admitted peers, as requested by the State Manager, while respecting the transport abstractions in `01-protocol/08-network-transport-requirements.md`.
* Performing bastion admission for outbound session attempts via the Bastion Engine path, before any admitted-data transmission, as required by `01-protocol/11-dos-guard-and-client-puzzles.md`.
* Requesting outbound envelopes from the State Manager, including any required destination metadata and transport hints, and ensuring the envelopes remain compliant with `01-protocol/03-serialization-and-envelopes.md` and `01-protocol/07-sync-and-consistency.md`.
* Invoking the Key Manager to sign and encrypt outbound envelopes as required, following `01-protocol/04-cryptography.md`.
* Applying transport framing and transmitting envelopes over admitted sessions without mutating the package bytes defined in `01-protocol/03-serialization-and-envelopes.md`.
* Enforcing outbound limits, including per-peer rate caps, per-session buffering caps, and concurrency caps.
* Emitting explicit transmission outcomes and connection state changes as events, without promising delivery.

Constraints:

* Outbound traffic to unadmitted peers is forbidden.
* The Outgoing Engine must not persist outbound messages for retry. If persistence or resend is required, it belongs to State Manager and its sync policy, not the Network Manager, to keep `01-protocol/08-network-transport-requirements.md` best-effort semantics intact.
* Implicit retry, replay, or backoff behavior is forbidden unless explicitly defined by the protocol and invoked by the State Manager.
* Cryptographic failure or transport failure must fail closed for that envelope. The envelope is not modified and not retried by this manager, satisfying `01-protocol/04-cryptography.md` and `01-protocol/09-errors-and-failure-modes.md`.

## 5. Transport surfaces and onion service lifecycle

This section exists to reconcile legacy “Network Engine” responsibilities into the modern engine model, without introducing a separate manager-owned engine. Transport surface behavior must remain consistent with `01-protocol/08-network-transport-requirements.md`.  

### 5.1 Transport surface types

The Network Manager may expose one or more transport surfaces, depending on configuration:

* Bastion ingress surface, used only for unauthenticated admission flows.
* Admitted data surface, used only for admitted peer traffic.

If a single surface is configured, the Bastion and admitted flows share the same underlying listener, but the Bastion boundary remains mandatory and must still be enforced before admitted traffic is processed.

If distinct surfaces are configured, the admitted data surface must not accept unauthenticated traffic, and the Bastion ingress surface must not carry admitted payload traffic.

### 5.2 Onion service lifecycle

Where onion services are used, the Network Startup Engine and transport adapter must support the following lifecycle operations as required by configuration and failure handling:

* create service
* start service
* stop service
* revoke service
* close sessions associated with a service

Rules:

* Revocation immediately invalidates the service for new inbound sessions and forces closure of affected sessions.
* If a bastion ingress service is revoked due to abuse pressure, existing admitted sessions on a distinct admitted surface may remain active, subject to DoS Guard directives and resource limits. This preserves the legacy isolation goal without reintroducing deprecated puzzle ownership into this manager. 
* Service lifecycle changes must be emitted as explicit events and reflected in Health Manager readiness signals.
* Publishing new reachable endpoints to peers, if required, is not owned by the Network Manager. The Network Manager may only surface the new endpoint facts to the appropriate manager for publication.

## 6. Admission and DoS Guard integration

Admission control semantics are defined in `01-protocol/11-dos-guard-and-client-puzzles.md`. The Network Manager acts as the transport boundary that supplies telemetry to DoS Guard and executes DoS Guard directives. 

### 6.1 Bastion to DoS Guard inputs

The Bastion Engine must provide, at minimum:

* Connection identifier.
* Transport type and listener or surface identifier.
* Transport addressing metadata where available.
* Connection timing, including start time and last activity.
* Byte and message counters, including pre-admission buffering usage.
* Local resource pressure indicators relevant to admission safety.
* Admission request type, inbound or outbound.
* Advisory peer references and observed routing metadata.

### 6.2 DoS Guard to Bastion outputs

The DoS Guard Manager returns one of:

* Allow admission.
* Deny admission.
* Require challenge.

Optional directives may include:

* Opaque challenge payload and validity window.
* Throttling parameters.
* Logging severity classification.
* Session termination instructions.

Constraints:

* Admission requires explicit allow.
* Challenge content is opaque to the Network Manager.
* Puzzle ownership resides exclusively with the DoS Guard Manager.
* Telemetry and directives must not be repurposed as identity evidence.

## 7. Connection lifecycle and state transitions

Each network session must exist in exactly one state:

* created
* bastion-held
* challenged
* admitted
* active-incoming
* active-outgoing
* closing
* closed

Allowed transitions:

* created to bastion-held
* bastion-held to challenged
* challenged to admitted
* admitted to active-incoming
* admitted to active-outgoing
* any state to closing
* closing to closed

Forbidden transitions:

* bastion-held directly to active-incoming or active-outgoing
* challenged directly to active-incoming or active-outgoing
* any state directly to State Manager delivery
* closed to any other state

Additional constraints:

* A single underlying transport session must not be concurrently treated as both bastion-held and admitted.
* If the transport reuses a single TCP-like connection for admission and then admitted traffic, the transition from bastion-held to admitted must include an explicit internal state flip, and any pre-admission buffers must be cleared or strictly bounded before admitted traffic is accepted.

## 8. Manager interactions

This section defines the integration contracts in terms of inputs, outputs, and trust boundaries, without importing responsibilities from other managers.

### 8.1 Key Manager interaction

Inbound:

* Incoming Engine requests signature verification for an envelope and receives:

  * verified signer identity, or failure
* Incoming Engine requests decryption for an envelope addressed to the local node and receives:

  * plaintext envelope bytes, or failure

Outbound:

* Outgoing Engine requests signing of an outbound envelope and receives:

  * signed envelope bytes, or failure
* Outgoing Engine requests encryption of an outbound envelope for a peer and receives:

  * ciphertext envelope bytes, or failure

Rules:

* The Network Manager never reads private keys.
* A cryptographic operation failure is treated as a hard failure for that envelope and fails closed.

These interactions implement the cryptographic boundary described in `01-protocol/04-cryptography.md` and uphold the identity rules in `01-protocol/05-keys-and-identity.md`.

### 8.2 State Manager interaction

Inbound delivery:

* Incoming Engine delivers only verified, decrypted packages to the State Manager, with signer identity and preserved transport metadata.

Outbound transmission:

* Outgoing Engine receives outbound packages from the State Manager in a form that is already envelope-complete at the protocol level.
* The Network Manager may apply only cryptographic wrapping and transport framing, not protocol rewriting.

Rules:

* The Network Manager does not decide what to sync or when to sync. It only transmits what State Manager requests and delivers what the transport provides after checks.
* Any retry policy belongs to State Manager.

This contract preserves the envelope semantics in `01-protocol/03-serialization-and-envelopes.md` and the ordering guarantees in `01-protocol/07-sync-and-consistency.md`.

### 8.3 DoS Guard interaction

* Bastion emits telemetry for admission decisions and executes directives for allow, deny, and challenge.
* DoS Guard unavailability causes fail-closed behavior for new admissions.

All telemetry exchanges and directives must match the API defined in `01-protocol/11-dos-guard-and-client-puzzles.md`.

### 8.4 Event Manager interaction

The Network Manager emits events for:

* listener and service lifecycle changes
* admission outcomes and challenge timeouts
* connection state transitions
* transport failures and disconnects
* cryptographic verification failures at the boundary
* envelope rejection statistics at coarse granularity

Event rules:

* Events must not leak private key material, decrypted payloads, or sensitive internal topology details.

### 8.5 Health Manager interaction

The Network Manager exposes two signals:

* Liveness, indicates the Network Manager loop is running and engines are responsive.
* Readiness, indicates required transport surfaces are live and bastion admission can be executed.

Readiness must be false when:

* required listener or onion service is not started
* the Bastion Engine is not able to execute admission
* DoS Guard dependency is unavailable for new admissions, unless the system is explicitly configured to run in isolated mode without networking

Readiness may be degraded, but not true, when:

* existing admitted sessions are maintained but new admissions are fail-closed due to DoS Guard unavailability

## 9. Inputs and outputs

### 9.1 Inputs

The Network Manager accepts:

* Raw inbound byte streams from supported transports.
* Outbound transmission requests and payloads from the State Manager.
* Configuration from Config Manager.
* Admission and challenge directives from DoS Guard Manager.
* Startup and shutdown signals from the runtime environment.
* Liveness and readiness probes from Health Manager.

All inbound transport data is untrusted.

### 9.2 Outputs

The Network Manager produces:

* Verified inbound packages forwarded to the State Manager.
* Outbound network transmissions of State Manager provided packages.
* Explicit rejection, throttling, and challenge responses at the bastion boundary.
* Connection termination actions.
* Events emitted to the Event Manager.
* Liveness and readiness updates to the Health Manager.
* Admission telemetry emitted to DoS Guard.

## 10. Allowed and forbidden behaviors

### 10.1 Explicitly allowed behaviors

The Network Manager may:

* Maintain concurrent bastion-held and admitted sessions within configured limits.
* Enforce hard transport limits even if DoS Guard would allow more.
* Terminate sessions unilaterally on failure, shutdown, or limit breach.
* Support multiple transport surfaces, including the dual onion service model, as a configuration of transport surfaces, not as a change to trust rules. 
* Emit detailed admission and transport lifecycle events.

### 10.2 Explicitly forbidden behaviors

The Network Manager must not:

* Forward any payload from an unadmitted session beyond the Bastion Engine boundary.
* Deliver any inbound package to State Manager without successful verification, and successful decryption when required.
* Treat transport-level peer identifiers as authenticated identity.
* Interpret, create, solve, or verify client puzzles, or choose puzzle difficulty. 
* Modify envelope contents, reorder fields, normalize bytes, or synthesize protocol metadata.
* Persist raw network input, decrypted payloads, or outbound payloads for retry.
* Implement implicit retry, replay, deduplication, or reordering semantics.
* Perform ACL evaluation, schema validation, graph mutation, or sync policy decisions.

## 11. Failure and rejection behavior

Failure handling maps each condition to the symbolic error classes defined in `01-protocol/09-errors-and-failure-modes.md` and must preserve the fail-closed posture described there.

### 11.1 Invalid input and malformed framing

On malformed input:

* Reject immediately at the earliest boundary that can detect the issue.
* Avoid allocation proportional to untrusted input size.
* Do not forward downstream.
* Emit a bounded event and increment counters, without logging raw payload bytes.

### 11.2 Admission failure and challenge timeout

On deny or challenge timeout:

* Terminate the bastion session.
* Emit an admission failure event.
* Apply throttling if instructed, bounded by hard limits.

These rejections fall under the resource and puzzle failure classes described in `01-protocol/09-errors-and-failure-modes.md`.

### 11.3 DoS Guard unavailability

If DoS Guard is unavailable:

* Fail closed for new admissions.
* Maintain existing admitted sessions, subject to resource pressure and local limits.
* Mark readiness as false or degraded, as defined in the Health Manager interaction section.
* Emit a critical failure event.

This behavior is required by `01-protocol/11-dos-guard-and-client-puzzles.md`.

### 11.4 Onion service or listener failure

On listener or onion service startup failure:

* Do not declare readiness.
* Fail closed for new admissions.
* Emit failure events and surface the failed surface identifier.
* Require explicit recovery or restart as defined by operational policy outside this file.

On runtime listener or onion service failure:

* Close affected sessions.
* Fail closed for new admissions on the affected surface.
* Preserve admitted sessions on unaffected surfaces if configured separately and if limits allow.

Surface lifecycle handling must preserve the invariants established in `01-protocol/08-network-transport-requirements.md`.

### 11.5 Resource exhaustion

On resource pressure:

* Reject new bastion sessions first.
* Reduce concurrency for challenged sessions.
* Prefer preserving admitted sessions over bastion-held sessions.
* If limits are exceeded, fail closed for new admissions and shed load via termination of the lowest-trust sessions first.

### 11.6 Cryptographic failure

On verification or decryption failure:

* Treat the envelope as invalid.
* Do not forward it.
* Emit a bounded event and counters, without leaking plaintext or key material.

These outcomes map to the cryptographic error class defined in `01-protocol/09-errors-and-failure-modes.md` and rely on the primitives specified in `01-protocol/04-cryptography.md`.

## 12. Configuration and mandatory limits

The Network Manager enforces mandatory limits, including:

* maximum concurrent bastion-held sessions
* maximum concurrent challenged sessions
* maximum concurrent admitted sessions
* maximum envelope size
* maximum per-session inbound buffering
* maximum per-session message rate
* maximum global inbound and outbound rate, if configured

These limits are mandatory and cannot be disabled.

They enforce the hard-cap guidance from `01-protocol/08-network-transport-requirements.md`, surface the resource-failure semantics described in `01-protocol/09-errors-and-failure-modes.md`, and feed the telemetry inputs consumed by `01-protocol/11-dos-guard-and-client-puzzles.md`.

## 13. Security considerations

* The Network Manager is a primary external attack surface and must be implemented to fail fast and fail closed.
* Bastion isolation must prevent amplification, resource pinning, and unbounded buffering.
* Cryptographic binding must precede any delivery to State Manager.
* Events and error responses must avoid leaking sensitive topology and internal state.
* The dual-surface configuration, when enabled, must preserve the bastion boundary invariants and must not allow admitted traffic to reach the bastion surface or unauthenticated traffic to reach the admitted surface. 
