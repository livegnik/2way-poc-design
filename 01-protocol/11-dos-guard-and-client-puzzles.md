


# 11. DoS Guard and client puzzle requirements

## 1. Purpose and scope

This document defines the normative requirements for the DoS Guard Manager and the client puzzle mechanism within the 2WAY protocol. It specifies how admission control operates at the network boundary, which inputs are consumed, which directives are emitted, and how puzzles are issued, validated, and expired. It also defines the trust and failure posture of the DoS Guard Manager. This specification does not redefine transport behavior, cryptographic verification, or sync semantics already covered in other protocol files.

## 2. Position in the system

The DoS Guard Manager sits logically between the adversarial transport abstraction (`01-protocol/08-network-transport-requirements.md`) and the cryptographic boundary owned by Network Manager (`02-architecture/managers/10-network-manager.md`). It has no direct access to graph envelopes and never bypasses Network Manager; instead it consumes telemetry and provisional metadata, applies policy, and instructs Network Manager to allow, deny, or challenge a connection prior to cryptographic processing.

## 3. Responsibilities and boundaries

The DoS Guard Manager is responsible for:

- Owning admission control policy for all inbound and outbound peer connections.
- Consuming transport-level telemetry (byte counters, message counters, latency samples, resource pressure indicators, provisional peer references) to detect abusive or anomalous behavior.
- Applying configurable and adaptive rate limits per peer, subnet, onion endpoint, and system-wide resource class.
- Determining when client puzzles are required, selecting work factors, constructing puzzle payloads, and validating puzzle responses.
- Emitting explicit directives to Network Manager (`allow`, `deny`, or `require_challenge`) for each admission request.
- Tracking challenge lifetime, expiry, reuse, and replay protection.
- Emitting telemetry and abuse events to the Event Manager for observability and audit.
- Exposing readiness and health status to the Health Manager when admission control becomes degraded or unavailable.

The DoS Guard Manager explicitly does **not**:

- Perform cryptographic verification or decryption of packages.
- Interpret graph envelopes, schema semantics, ACL rules, or application data.
- Assign identity to peers solely from transport metadata or puzzle responses.
- Persist envelopes or mutate state outside of its own counters and policy state.
- Make authorization, sync ordering, or storage decisions.

## 4. Invariants and guarantees

- Every admission request receives exactly one directive: allow, deny, or require challenge.
- Client puzzles are opaque to Network Manager; only DoS Guard Manager interprets their structure.
- A puzzle response is valid only for the challenge that produced it, for its declared validity window, and for the peer that originally received it.
- Puzzle difficulty is monotonically non-decreasing while the triggering condition persists. It may decrease only after policy signals relief.
- Admission decisions are deterministic for a given telemetry snapshot, policy configuration, and puzzle response.
- Rejected or expired puzzles do not mutate protocol state beyond their own counters and do not leak internal heuristics.
- Failure of DoS Guard Manager results in fail-closed behavior: no new admissions, existing admitted connections remain active if safe, and Network Manager marks readiness degraded.

## 5. Inputs

### 5.1 Telemetry inputs

DoS Guard Manager consumes the following telemetry from Network Manager, as defined in `01-protocol/08-network-transport-requirements.md`:

- Connection identifier and transport type.
- Advisory peer references and routing metadata (for example, onion service id, IP + port, or Tor circuit id).
- Byte counters, message counters, and per-connection throughput samples.
- Connection timing information (handshake duration, idle time, lifetime).
- Local resource pressure indicators (CPU saturation flags, memory pressure, socket pool usage).

Telemetry is advisory and unauthenticated; it may be used only for admission policy, not for identity binding or authorization.

### 5.2 Configuration and policy inputs

DoS Guard Manager receives policy definitions from Config Manager, including:

- Baseline rate limits per peer class.
- Burst and decay windows for resource buckets.
- Puzzle enablement flags per transport or peer class.
- Maximum concurrent challenges per peer and system-wide.
- Abuse classification thresholds and logging verbosity.

Policy updates must be applied atomically; partial updates are forbidden.

## 6. Outputs

DoS Guard Manager emits:

- Admission directives: `allow`, `deny`, or `require_challenge`.
- Optional throttling parameters (reduced rate, backoff window) to accompany allow directives.
- Puzzle challenges containing the fields defined in Section 7.
- Abuse and telemetry events routed to Event Manager.
- Health state and readiness signals to Health Manager when policy is degraded.

Outputs must be delivered through the Network Manager API; no other component may directly consume DoS Guard directives.

## 7. Client puzzle lifecycle

### 7.1 Challenge structure

Every challenge issued by DoS Guard Manager MUST include:

- `challenge_id`: unique identifier within the local node.
- `difficulty`: a numeric work factor, expressed as the minimum number of leading zero bits (or equivalent) required in the solution hash.
- `expires_at`: signed timestamp indicating when the challenge becomes invalid.
- `context_binding`: opaque bytes supplied by DoS Guard Manager tying the challenge to the requesting connection (for example, truncated peer reference hash plus salt).
- `payload`: opaque bytes that the requester must include unchanged when responding (for example, random nonce).
- `algorithm`: identifier of the proof-of-work or puzzle algorithm in use (for PoC, a SHA-256 preimage proof is sufficient).

Challenges must be serializable without leaking internal statistics. Network Manager treats the payload as opaque and merely transports it to the peer.

### 7.2 Response verification

When Network Manager submits a puzzle response, DoS Guard Manager must verify:

- The referenced `challenge_id` exists, has not expired, and was issued to the requesting connection.
- The solution satisfies the declared `difficulty` according to the `algorithm`.
- The response includes the original `payload` and `context_binding` unmodified.
- The response has not already been accepted (replay protection).

On success, the admission decision upgrades to `allow`; on failure, DoS Guard Manager returns `deny` or issues a new challenge with updated difficulty.

### 7.3 Difficulty selection

- Difficulty MUST increase when aggregate resource usage crosses high-water marks or when peer behavior indicates abuse.
- Difficulty MAY decrease when usage falls below configured low-water marks.
- Difficulty adjustments must be bounded to avoid integer overflow or trivialization of puzzles.
- Config Manager provides minimum and maximum difficulty caps.

### 7.4 Expiration and cleanup

- Challenges expire automatically after `expires_at` or when the underlying connection closes, whichever occurs first.
- Expired challenges are purged without side effects other than emitting a telemetry event.
- Puzzle responses received after expiration are rejected with `ERR_RESOURCE_PUZZLE_FAILED` (see `01-protocol/09-errors-and-failure-modes.md`).

## 8. Admission decision matrix

- **Allow**: Network Manager may proceed to Bastion admission and cryptographic verification. The decision may include throttling parameters (for example, maximum messages per second) that Network Manager must enforce.
- **Require challenge**: Network Manager must hold the connection at the Bastion boundary until a valid puzzle response is validated. No payload data may flow inward during this phase.
- **Deny**: Network Manager must terminate the connection immediately and emit a rejection event with the provided reason code.

Admission decisions must be logged with sufficient metadata (challenge id, peer reference hash, resource counters) for auditing, but logs must not store private payloads.

## 9. Integration boundaries

- Network Manager is the sole caller of the DoS Guard Manager API for runtime admission decisions.
- Event Manager receives abuse events, challenge issuance, and resolution telemetry for observability.
- Health Manager is informed when admission control is degraded (for example, policy storage unavailable or challenge generation failure).
- Config Manager supplies policy snapshots. DoS Guard Manager must reject admission requests if policy is unknown or corrupted.
- State Manager receives no direct data from DoS Guard Manager; it only benefits from the reduced abusive traffic.

## 10. Failure behavior

- **Policy load failure**: Fail closed, emit a critical event, and require administrative remediation before resuming admissions.
- **Telemetry backlog**: Drop telemetry samples rather than delay admission decisions. Lack of telemetry must bias toward stricter decisions (challenge or deny).
- **Puzzle generation failure**: Emit `ERR_RESOURCE_PUZZLE_FAILED`, deny the request, and mark readiness degraded.
- **Storage exhaustion of tracking tables**: Evict least-recently used challenges only after expiration; otherwise deny new admissions.
- **Internal errors**: Halt new admissions, preserve existing admitted connections if safe, and escalate via Event Manager.

## 11. Compliance criteria

A DoS Guard Manager implementation is compliant if and only if:

- It consumes only the telemetry and configuration inputs defined here and never infers identity from transport metadata.
- It issues, tracks, and validates puzzles solely through the lifecycle defined in Section 7.
- It emits one of three directives (allow, deny, require challenge) for every admission request and never bypasses Network Manager.
- It enforces deterministic behavior for identical inputs and policy, ensuring reproducible admission outcomes.
- It fails closed on internal errors, policy corruption, or puzzle generation failures.
- It logs abuse and policy decisions without leaking private puzzle payloads or peer secrets.
