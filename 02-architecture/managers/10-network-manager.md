



No, you are right to be skeptical. That rewrite was **too compressed**, and yes, if you compare line by line you will find **important operational detail missing**. I over-collapsed sections instead of integrating additions while keeping full prior coverage. 

Here is the **full, implementation-ready file** with the **previous coverage preserved** and the **missing legacy responsibilities integrated** cleanly, without deleting detail.

---

# 10. Network Manager

## 1. Purpose and scope

This document specifies the Network Manager.

The Network Manager owns all peer-to-peer network I/O for a 2WAY node. It is the only component allowed to touch raw transport data. It defines transport abstraction, ordered startup and shutdown of network surfaces, staged admission through a bastion boundary, cryptographic binding at the network edge, peer discovery and outbound connection scheduling, reachability tracking, and integration with DoS Guard for abuse containment.

This specification defines internal engines and phases that together constitute the Network Manager. These engines, phases, and boundaries are normative and required for correct implementation.

This specification consumes the protocol contracts defined in:

* `01-protocol/08-network-transport-requirements.md`
* `01-protocol/03-serialization-and-envelopes.md`
* `01-protocol/04-cryptography.md`
* `01-protocol/05-keys-and-identity.md`
* `01-protocol/07-sync-and-consistency.md`
* `01-protocol/09-errors-and-failure-modes.md`
* `01-protocol/11-dos-guard-and-client-puzzles.md`

Those files remain normative for all behaviors described here.

This document does not define synchronization policy, graph semantics, authorization decisions, or DoS policy logic.

---

## 2. Responsibilities and boundaries

### 2.1 This specification is responsible for the following

* Owning all inbound and outbound listeners, sessions, and connection state machines for supported transports, consolidating the consumer boundary defined in `01-protocol/08-network-transport-requirements.md`.
* Abstracting transport implementations while preserving peer context and transport metadata, exactly as required by `01-protocol/08-network-transport-requirements.md`.
* Providing ordered startup and shutdown sequencing for all network surfaces, including onion service lifecycle where configured, so that surfaces mandated by `01-protocol/08-network-transport-requirements.md` are either ready or explicitly failed closed.
* Enforcing hard transport-level limits for size, rate, concurrency, and buffering independently of any DoS policy, satisfying the resource-failure constraints defined in `01-protocol/08-network-transport-requirements.md` and `01-protocol/09-errors-and-failure-modes.md`.
* Providing staged admission via a Bastion Engine that isolates unauthenticated peers and coordinates with DoS Guard for allow, deny, and challenge flows per `01-protocol/11-dos-guard-and-client-puzzles.md`.
* Executing challenge transport as an opaque exchange, without interpreting puzzle content, difficulty, or verification logic, which are owned by DoS Guard and defined in `01-protocol/11-dos-guard-and-client-puzzles.md`.
* Performing peer discovery for first-degree peers, including:

  * requesting peer identity and node endpoint attributes from the State Manager
  * resolving candidate endpoints for connectivity
  * scheduling and initiating outbound session attempts
  * maintaining reachability state used only for connection scheduling
* Selecting endpoints deterministically and applying failure-based fallback and cooldown.
* Scheduling outbound connection attempts fairly and safely, enforcing global and per-peer caps, and preventing connection storms.
* Reusing existing admitted sessions when possible, and preventing redundant parallel connections, keyed by verified peer identity.
* Binding transport sessions to cryptographic identity only through Key Manager verification, never through transport-provided identifiers, preserving the identity model in `01-protocol/05-keys-and-identity.md`.
* Verifying signatures and decrypting inbound envelopes addressed to the local node, and attaching verified signer identity to the delivered package, exactly as mandated by `01-protocol/04-cryptography.md` and `01-protocol/05-keys-and-identity.md`.
* Signing and encrypting outbound envelopes as required by protocol rules and configuration, via the Key Manager, following the algorithms defined in `01-protocol/04-cryptography.md`.
* Delivering only admitted and cryptographically verified inbound packages to the State Manager, preserving the envelope semantics of `01-protocol/03-serialization-and-envelopes.md` and the sync ordering rules of `01-protocol/07-sync-and-consistency.md`.
* Transmitting outbound packages received from the State Manager, without adding retry semantics or persistence, thus honoring the best-effort semantics of `01-protocol/08-network-transport-requirements.md`.
* Emitting explicit connection lifecycle events, discovery and reachability events, admission outcomes, transport failures, and health signals to the Event Manager and Health Manager, and emitting admission telemetry to DoS Guard as required by `01-protocol/08-network-transport-requirements.md` and `01-protocol/11-dos-guard-and-client-puzzles.md`.
* Supporting multiple transport surfaces when configured, including the dual-surface model where a bastion surface is separated from an admitted data surface, without changing the trust boundary rules mandated in `01-protocol/08-network-transport-requirements.md`.
* Surfacing network reachability facts to the State Manager and Event Manager without performing graph writes.

### 2.2 This specification does not cover the following

* Definition of cryptographic primitives, algorithms, key formats, key rotation, or key storage.
* Definition of envelope schemas, sync semantics, replay rules, reconciliation logic, or ordering guarantees.
* ACL evaluation, schema validation, graph mutation logic, conflict handling, or any state write behavior.
* DoS policy decisions, puzzle creation, puzzle verification, difficulty selection, reputation scoring, or abuse classification.
* Multi-hop relay policy, overlay routing, or topology optimization beyond direct peer connectivity.
* Any user-facing APIs, UI behavior, or admin workflows.

---

## 3. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

* All transport-derived input is untrusted until it passes bastion admission and cryptographic verification, consistent with `01-protocol/08-network-transport-requirements.md`.
* No inbound data reaches any manager other than the Network Manager without passing Bastion admission.
* No inbound package reaches the State Manager unless admission succeeded, signature verification succeeded, and decryption succeeded when required.
* Transport-provided peer references are advisory only. They are never treated as authenticated identity evidence.
* Identity binding occurs only after cryptographic verification, and is keyed to verified signer identity, not endpoint.
* Peer discovery and reachability do not imply trust, authorization, or sync eligibility.
* Envelope bytes retain the exact structure defined in `01-protocol/03-serialization-and-envelopes.md`. The Network Manager never rewrites them while verifying or forwarding packages.
* All cryptographic operations use the algorithms defined in `01-protocol/04-cryptography.md`, and signer identity binding follows `01-protocol/05-keys-and-identity.md`.
* Admission, deny, and challenge behaviors follow `01-protocol/11-dos-guard-and-client-puzzles.md`, including opacity of puzzles and the requirement to fail closed on DoS Guard unavailability.
* Trust escalation is explicit, monotonic, and irreversible across the boundaries defined in this file.
* The Network Manager never performs schema validation, ACL evaluation, graph mutation, sync ordering, or reconciliation.
* The Network Manager never introduces delivery, ordering, deduplication, retry, or persistence guarantees beyond what the transport provides, as mandated by `01-protocol/08-network-transport-requirements.md`.
* Failures at any trust boundary fail closed. When a required check cannot be performed, the input is rejected and not forwarded, matching the failure posture defined in `01-protocol/09-errors-and-failure-modes.md`.
* These guarantees hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

---

## 4. Internal engine structure

The Network Manager is composed of four mandatory internal engines. These engines define strict phase boundaries and must not be collapsed, reordered, or bypassed.

In addition, the Network Startup Engine owns two mandatory background phases, Peer Discovery and Reachability Tracking. These phases are internal to the Network Manager and must run under the same hard-limit and fail-closed constraints defined in this file.

### 4.1 Network Startup Engine

The Network Startup Engine governs ordered initialization, readiness gating, runtime loops, and teardown of all network subsystems.

Responsibilities:

* Loading network configuration and limits from Config Manager.
* Binding to Key Manager, DoS Guard Manager, State Manager, Event Manager, and Health Manager.
* Initializing transport adapters and registering transport error hooks.
* Validating that each adapter satisfies the send, receive, framing, and telemetry expectations defined in `01-protocol/08-network-transport-requirements.md` before it is exposed downstream.
* Creating and starting inbound transport surfaces in a defined order:

  * Bastion ingress surface.
  * Optional admitted data surface, if configured as a distinct surface.
* Starting engines in a defined order:

  * Bastion Engine.
  * Incoming Engine.
  * Outgoing Engine.
* Starting Network Manager background phases after bastion readiness:

  * Peer Discovery Phase.
  * Reachability Tracking Phase.
* Publishing readiness only after:

  * all required surfaces are live
  * the Bastion Engine is able to accept connections and execute admission
  * required DoS Guard dependencies are reachable, or explicitly configured out
* Starting runtime loop responsibilities that belong to this manager:

  * connection reaping and timeout enforcement
  * keepalive scheduling if the transport requires it
  * handshake maintenance that is strictly transport-level and does not alter protocol semantics
  * outbound dial scheduling and concurrency control
* Coordinating ordered shutdown and surfacing shutdown progress to Health Manager.
* Ensuring shutdown sets readiness false immediately, then drains, then sets liveness false at completion.

Startup sequencing rules:

* The bastion ingress surface must be started before any admitted data surface.
* No peer discovery outbound dial may be attempted until:

  * bastion admission is operational, and
  * DoS Guard is available for admission decisions, unless explicitly configured out.
* Inbound acceptance may begin once bastion ingress surface is live, but no inbound traffic may pass into the Incoming Engine until admission succeeds.

Constraints:

* The Startup Engine must not create, solve, interpret, or verify client puzzles.
* The Startup Engine must not access Storage Manager or Graph Manager.
* The Startup Engine must not trigger graph mutations to publish endpoint changes. It may only emit events and hand off endpoint facts to the appropriate manager.
* Partial initialization must not result in readiness. Startup failure must fail closed and prevent new admissions.

### 4.2 Bastion Engine

The Bastion Engine owns all unauthenticated and unadmitted connections. It is the only engine permitted to interact with unadmitted sessions.

Responsibilities:

* Accepting initial inbound sessions from external peers on the bastion ingress surface.
* Accepting outbound session attempts initiated by the Outgoing Engine or Peer Discovery Phase, treating them as unadmitted until admission succeeds.
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
* Emitting explicit admission outcomes as events, including allow, deny, challenge timeout, and abort.

Constraints:

* The Bastion Engine must not perform cryptographic verification or decryption of protocol envelopes.
* The Bastion Engine must not parse protocol semantics beyond minimal framing required to run the admission exchange, preserving the envelope opacity described in `01-protocol/03-serialization-and-envelopes.md`.
* The Bastion Engine must not forward any payload to State Manager, Graph Manager, ACL Manager, or Storage Manager.
* Challenge payloads are opaque. The Bastion Engine must not interpret puzzle content, difficulty, or correctness, per `01-protocol/11-dos-guard-and-client-puzzles.md`.
* A session is not admitted unless DoS Guard explicitly allows it, satisfying `01-protocol/11-dos-guard-and-client-puzzles.md`.
* If DoS Guard is unavailable, the Bastion Engine must fail closed for new admissions.

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
* Emitting bounded counters and events for rejected envelopes, without leaking payload content.

Constraints:

* Data from unadmitted sessions must never reach the Incoming Engine.
* Partially verified, unverifiable, or undecipherable payloads must not be forwarded, consistent with `01-protocol/04-cryptography.md`.
* Authorization, schema validation, graph evaluation, reconciliation, and state mutation are forbidden.
* The Incoming Engine must not implement retry, reordering, or deduplication.

### 4.4 Outgoing Engine

The Outgoing Engine owns all outbound communication after successful bastion admission.

Responsibilities:

* Establishing and maintaining outbound sessions to admitted peers, while respecting the transport abstractions in `01-protocol/08-network-transport-requirements.md`.
* Performing bastion admission for outbound session attempts via the Bastion Engine path, before any admitted-data transmission, as required by `01-protocol/11-dos-guard-and-client-puzzles.md`.
* Reusing existing admitted sessions where available, keyed by verified peer identity.
* Requesting outbound envelopes from the State Manager, including required destination metadata and transport hints, and ensuring the envelopes remain compliant with `01-protocol/03-serialization-and-envelopes.md` and `01-protocol/07-sync-and-consistency.md`.
* Invoking the Key Manager to sign and encrypt outbound envelopes as required, following `01-protocol/04-cryptography.md`.
* Applying transport framing and transmitting envelopes over admitted sessions without mutating the package bytes defined in `01-protocol/03-serialization-and-envelopes.md`.
* Enforcing outbound limits, including per-peer rate caps, per-session buffering caps, global concurrency caps, and global outbound rate caps.
* Emitting explicit transmission outcomes and connection state changes as events, without promising delivery.

Constraints:

* Outbound traffic to unadmitted peers is forbidden.
* The Outgoing Engine must not persist outbound messages for retry. If persistence or resend is required, it belongs to State Manager and its sync policy.
* Implicit retry, replay, or backoff behavior is forbidden unless explicitly defined by the protocol and invoked by the State Manager.
* Cryptographic failure or transport failure must fail closed for that envelope. The envelope is not modified and not retried by this manager.

---

## 5. Transport surfaces and onion service lifecycle

Transport surface behavior must remain consistent with `01-protocol/08-network-transport-requirements.md`.

### 5.1 Transport surface types

The Network Manager may expose one or more transport surfaces, depending on configuration:

* Bastion ingress surface, used only for unauthenticated admission flows.
* Admitted data surface, used only for admitted peer traffic.

If a single surface is configured, the bastion and admitted flows share the same underlying listener, but the Bastion boundary remains mandatory and must still be enforced before admitted traffic is processed.

If distinct surfaces are configured:

* The admitted data surface must not accept unauthenticated traffic.
* The bastion ingress surface must not carry admitted payload traffic.

### 5.2 Onion service lifecycle

Where onion services are used, the Network Startup Engine and transport adapter must support the following lifecycle operations as required by configuration and failure handling:

* create service
* start service
* stop service
* revoke service
* close sessions associated with a service

Rules:

* Revocation immediately invalidates the service for new inbound sessions and forces closure of affected sessions.
* If a bastion ingress service is revoked due to abuse pressure, existing admitted sessions on a distinct admitted surface may remain active, subject to DoS Guard directives and resource limits.
* Service lifecycle changes must be emitted as explicit events and reflected in Health Manager readiness signals.
* Publishing new reachable endpoints to peers is not owned by the Network Manager. The Network Manager may only surface endpoint facts to the State Manager for persistence and publication decisions.

---

## 6. Peer discovery, endpoint resolution, and reachability

Peer discovery is a Network Manager responsibility. It identifies candidate peers and attempts connectivity. It does not decide what data to sync, what to trust, or what to authorize.

### 6.1 Discovery scope and inputs

Discovery scope is limited to first-degree known peers.

The Network Manager requests from the State Manager:

* the set of first-degree peer identities eligible for attempted connection
* for each identity, the current set of node endpoint attributes, including onion addresses and transport hints

Rules:

* The Network Manager must treat attribute data as untrusted hints.
* The Network Manager must not mutate graph state or persist discovered endpoint data.
* The Network Manager must not expand discovery beyond first-degree peers.

### 6.2 Endpoint structural validation

The Network Manager performs structural validation only:

* address encoding and length checks
* transport-type compatibility checks
* basic sanity checks required to prevent obviously invalid dials

The Network Manager must not:

* infer authorization from presence of an endpoint
* infer identity from endpoint
* interpret endpoints as proof of peer availability

### 6.3 Endpoint selection and deterministic ordering

When multiple endpoints exist for a peer identity, the Network Manager must apply deterministic ordering.

At minimum, ordering must be stable given the same input set and the same reachability state.

Ordering inputs may include:

* last successful contact for an endpoint
* recent failure counts
* configured preference order by transport type

Ordering must not depend on non-deterministic timing.

### 6.4 Fallback and cooldown

When dialing a peer:

* The Network Manager attempts endpoints in deterministic order.
* On failure, it proceeds to the next endpoint.
* After exhausting endpoints, the peer enters cooldown before the next dial attempt.

Cooldown rules:

* Cooldown duration must be bounded and configurable.
* Cooldown must increase under repeated failure, but must have a maximum cap.
* Cooldown state must not be treated as a trust signal.

### 6.5 Reachability states

The Network Manager maintains a reachability state per peer identity and per endpoint:

* reachable
* temporarily-unreachable
* unreachable

Transitions are based on transport outcomes:

* successful admitted session establishes reachable
* timeouts, connection refusals, and service failures degrade reachability
* repeated failures may mark unreachable until a longer cooldown expires

Reachability rules:

* Reachability affects only connection scheduling and endpoint ordering.
* Reachability must never affect authorization, ACL evaluation, or sync decisions.
* Reachability may be emitted as events and may be surfaced to State Manager as advisory telemetry, without graph writes.

### 6.6 Probing and liveness

The Network Manager may perform bounded probing, limited to:

* verifying that an endpoint can be dialed and admitted
* verifying that an admitted session remains alive at the transport level

Probing must be bounded by hard rate limits and must not be used to generate additional traffic under load.

---

## 7. Outbound connection scheduling, fairness, and session reuse

### 7.1 Dial scheduler ownership

The Network Manager owns the dial scheduler.

The State Manager may request that a peer be connected, but it must not dictate immediate dialing or bypass scheduler constraints.

Scheduler inputs:

* discovery-driven candidates
* State Manager connection requests
* reconnect needs due to disconnects
* cooldown and reachability state

### 7.2 Concurrency and fairness

The scheduler must enforce:

* global maximum concurrent outbound dials
* per-peer maximum concurrent dials
* global maximum concurrent admitted outbound sessions
* per-peer maximum admitted sessions, typically one unless transport requires more

Fairness requirements:

* Scheduling must prevent starvation across peers.
* Reconnect attempts must not starve discovery dials indefinitely, and vice versa.
* Under resource pressure, the scheduler must reduce outbound dialing before shedding admitted sessions.

### 7.3 Session reuse and affinity

Rules:

* If an admitted session exists for a verified peer identity, it must be reused for outbound transmissions whenever compatible with transport framing and security requirements.
* Redundant parallel sessions to the same peer identity are forbidden unless required by transport semantics, and must be explicitly configured.
* Session affinity is keyed by verified peer identity, not endpoint or transport-provided identifiers.
* Endpoint churn is permitted without changing peer identity. Identity remains cryptographically bound.

### 7.4 Preventing connection storms

The scheduler must include storm prevention:

* bounded dial rate
* bounded reconnect frequency per peer
* jittered scheduling when many peers enter eligible state simultaneously
* strict backoff on repeated failure

---

## 8. Admission and DoS Guard integration

Admission control semantics are defined in `01-protocol/11-dos-guard-and-client-puzzles.md`. The Network Manager acts as the transport boundary that supplies telemetry to DoS Guard and executes DoS Guard directives.

### 8.1 Bastion to DoS Guard inputs

The Bastion Engine must provide, at minimum:

* Connection identifier.
* Transport type and listener or surface identifier.
* Transport addressing metadata where available.
* Connection timing, including start time and last activity.
* Byte and message counters, including pre-admission buffering usage.
* Local resource pressure indicators relevant to admission safety.
* Admission request type, inbound or outbound.
* Advisory peer references and observed routing metadata.
* Scheduler context for outbound attempts, when applicable, including whether the attempt is discovery-driven or State-driven.

### 8.2 DoS Guard to Bastion outputs

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

---

## 9. Connection lifecycle and state transitions

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

---

## 10. Manager interactions

This section defines integration contracts in terms of inputs, outputs, and trust boundaries, without importing responsibilities from other managers.

### 10.1 Key Manager interaction

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

### 10.2 State Manager interaction

Inbound delivery:

* Incoming Engine delivers only verified, decrypted packages to the State Manager, with signer identity and preserved transport metadata and admission context.

Outbound transmission:

* Outgoing Engine receives outbound packages from the State Manager in a form that is already envelope-complete at the protocol level.
* State Manager may include destination identity and optional transport hints derived from node attributes.
* The Network Manager may apply only cryptographic wrapping and transport framing, not protocol rewriting.

Discovery and endpoint inputs:

* The Network Manager requests from State Manager:

  * first-degree peer identities eligible for connection attempts
  * node endpoint attributes associated with those identities

Discovery and reachability outputs:

* The Network Manager may provide advisory telemetry to State Manager:

  * per-peer reachability state
  * last successful contact timestamps
  * last failure timestamps and coarse failure classes

Rules:

* The Network Manager does not decide what to sync or when to sync.
* The State Manager does not dictate immediate dialing or bypass scheduler constraints.
* Any retry or resend policy belongs to State Manager.

### 10.3 DoS Guard interaction

* Bastion emits telemetry for admission decisions and executes directives for allow, deny, and challenge.
* DoS Guard unavailability causes fail-closed behavior for new admissions.

All telemetry exchanges and directives must match the API defined in `01-protocol/11-dos-guard-and-client-puzzles.md`.

### 10.4 Event Manager interaction

The Network Manager emits events for:

* listener and service lifecycle changes
* admission outcomes and challenge timeouts
* discovery cycles and discovery outcomes
* reachability transitions and cooldown triggers
* connection state transitions
* transport failures and disconnects
* cryptographic verification failures at the boundary
* envelope rejection statistics at coarse granularity

Event rules:

* Events must not leak private key material, decrypted payloads, raw payload bytes, or sensitive internal topology details beyond what is necessary for operators.

### 10.5 Health Manager interaction

The Network Manager exposes two signals:

* Liveness, indicates the Network Manager loop is running and engines are responsive.
* Readiness, indicates required transport surfaces are live, Bastion admission can be executed, and required dependencies are present.

Readiness must be false when:

* required listener or onion service is not started
* the Bastion Engine is not able to execute admission
* DoS Guard dependency is unavailable for new admissions, unless explicitly configured out

Readiness must not be blocked by:

* peers being unreachable
* discovery cycles failing to find endpoints
* lack of admitted sessions

Readiness may be degraded, but not true, when:

* existing admitted sessions are maintained but new admissions are fail-closed due to dependency failure

---

## 11. Inputs and outputs

### 11.1 Inputs

The Network Manager accepts:

* Raw inbound byte streams from supported transports.
* Outbound transmission requests and payloads from the State Manager.
* Configuration from Config Manager.
* Admission and challenge directives from DoS Guard Manager.
* Startup and shutdown signals from the runtime environment.
* Liveness and readiness probes from Health Manager.

All inbound transport data is untrusted.

### 11.2 Outputs

The Network Manager produces:

* Verified inbound packages forwarded to the State Manager.
* Outbound network transmissions of State Manager provided packages.
* Explicit rejection, throttling, and challenge responses at the bastion boundary.
* Connection establishment and termination actions.
* Discovery-driven outbound connection attempts.
* Reachability and lifecycle events emitted to the Event Manager.
* Liveness and readiness updates to the Health Manager.
* Admission telemetry emitted to DoS Guard.
* Advisory reachability telemetry surfaced to State Manager.

---

## 12. Allowed and forbidden behaviors

### 12.1 Explicitly allowed behaviors

The Network Manager may:

* Maintain concurrent bastion-held and admitted sessions within configured limits.
* Enforce hard transport limits even if DoS Guard would allow more.
* Terminate sessions unilaterally on failure, shutdown, or limit breach.
* Support multiple transport surfaces, including the dual onion service model, as a configuration of transport surfaces, not as a change to trust rules.
* Emit detailed admission, discovery, reachability, and transport lifecycle events.
* Perform bounded probing for reachability and liveness, under strict rate limits.
* Reorder endpoint dialing attempts for a peer deterministically based on reachability state.

### 12.2 Explicitly forbidden behaviors

The Network Manager must not:

* Forward any payload from an unadmitted session beyond the Bastion Engine boundary.
* Deliver any inbound package to State Manager without successful verification, and successful decryption when required.
* Treat transport-level peer identifiers or endpoints as authenticated identity.
* Interpret, create, solve, or verify client puzzles, or choose puzzle difficulty.
* Modify envelope contents, reorder envelope fields, normalize bytes, or synthesize protocol metadata.
* Persist raw network input, decrypted payloads, endpoint attributes, or outbound payloads for retry.
* Implement implicit retry, replay, deduplication, or reordering semantics.
* Perform ACL evaluation, schema validation, graph mutation, sync decisions, or trust scoring.
* Expand discovery beyond first-degree peers.
* Treat reachability as an authorization or trust input.

---

## 13. Failure and rejection behavior

Failure handling maps each condition to symbolic error classes defined in `01-protocol/09-errors-and-failure-modes.md` and must preserve the fail-closed posture described there.

### 13.1 Invalid input and malformed framing

On malformed input:

* Reject immediately at the earliest boundary that can detect the issue.
* Avoid allocation proportional to untrusted input size.
* Do not forward downstream.
* Emit a bounded event and increment counters, without logging raw payload bytes.

### 13.2 Admission failure and challenge timeout

On deny or challenge timeout:

* Terminate the bastion session.
* Emit an admission failure event.
* Apply throttling if instructed, bounded by hard limits.

### 13.3 DoS Guard unavailability

If DoS Guard is unavailable:

* Fail closed for new admissions and new outbound dials requiring admission.
* Maintain existing admitted sessions, subject to resource pressure and local limits.
* Mark readiness false or degraded as specified in Health Manager interaction.
* Emit a critical failure event.

### 13.4 Onion service or listener failure

On listener or onion service startup failure:

* Do not declare readiness.
* Fail closed for new admissions.
* Emit failure events and surface the failed surface identifier.

On runtime listener or onion service failure:

* Close affected sessions.
* Fail closed for new admissions on the affected surface.
* Preserve admitted sessions on unaffected surfaces if configured separately and if limits allow.

### 13.5 Resource exhaustion

On resource pressure:

* Reject new bastion sessions first.
* Reduce concurrency for challenged sessions.
* Reduce outbound dial rate and concurrency before shedding admitted sessions.
* Prefer preserving admitted sessions over bastion-held sessions.
* If limits are exceeded, shed lowest-trust sessions first, with lowest-trust defined purely by lifecycle state:

  * bastion-held and challenged are lower than admitted

### 13.6 Cryptographic failure

On verification or decryption failure:

* Treat the envelope as invalid.
* Do not forward it.
* Emit a bounded event and counters, without leaking plaintext or key material.

### 13.7 Discovery and reachability failure

Discovery failures must not affect readiness.

On discovery resolution failure for a peer:

* Record failure class for reachability ordering and cooldown.
* Emit a bounded event.
* Apply cooldown before retry.

On repeated dial failures:

* Apply bounded exponential backoff with a hard cap.
* Do not increase dial rate under failure.
* Do not attempt all peers simultaneously, enforce fairness and jitter.

---

## 14. Configuration and mandatory limits

The Network Manager enforces mandatory limits, including:

* maximum concurrent bastion-held sessions
* maximum concurrent challenged sessions
* maximum concurrent admitted sessions
* maximum concurrent outbound dials
* maximum admitted sessions per peer identity
* maximum envelope size
* maximum per-session inbound buffering
* maximum per-session outbound buffering
* maximum per-session message rate
* maximum global inbound rate
* maximum global outbound rate
* maximum discovery cycle rate
* maximum probe rate for reachability checks
* cooldown and backoff bounds, including minimum and maximum

These limits are mandatory and cannot be disabled.

They enforce hard-cap guidance from `01-protocol/08-network-transport-requirements.md`, preserve resource-failure semantics described in `01-protocol/09-errors-and-failure-modes.md`, and feed telemetry inputs consumed by `01-protocol/11-dos-guard-and-client-puzzles.md`.

---

## 15. Security considerations

* The Network Manager is a primary external attack surface and must be implemented to fail fast and fail closed.
* Bastion isolation must prevent amplification, resource pinning, and unbounded buffering.
* Cryptographic binding must precede any delivery to State Manager.
* Events and error responses must avoid leaking sensitive topology and internal state.
* The dual-surface configuration, when enabled, must preserve bastion boundary invariants and must not allow admitted traffic to reach the bastion surface or unauthenticated traffic to reach the admitted surface.
* Peer discovery and endpoint resolution must treat all endpoint attributes as untrusted hints until admission and cryptographic verification succeed.
* Reachability must never be used as trust, authorization, or sync eligibility input.
