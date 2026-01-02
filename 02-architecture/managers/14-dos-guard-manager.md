



# 14 DoS Guard Manager

## 1. Purpose and scope

The DoS Guard Manager is the sole authority responsible for protecting the 2WAY backend from denial-of-service attacks and abusive clients. It enforces admission control policies, issues and verifies client puzzles, tracks per-identity and per-peer difficulty levels, and coordinates with Network Manager and Health Manager to throttle or deny traffic when required. DoS Guard Manager never mutates graph state; it operates entirely within the boundaries defined by the protocol.

This specification defines DoS Guard responsibilities, inputs and outputs, internal engines, configuration, and interactions with other managers. It references the following protocol files:

* `01-protocol/00-protocol-overview.md`
* `01-protocol/05-keys-and-identity.md`
* `01-protocol/08-network-transport-requirements.md`
* `01-protocol/09-errors-and-failure-modes.md`
* `01-protocol/11-dos-guard-and-client-puzzles.md`

Those files remain normative for admission control and puzzle semantics.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Owning the admission decision loop for inbound and outbound connections, in accordance with `01-protocol/11-dos-guard-and-client-puzzles.md`.
* Issuing, validating, and expiring client puzzles (proof-of-work challenges) without exposing puzzle secrets or private keys.
* Tracking request rates, connection counts, and transport-level telemetry to detect abusive behavior.
* Communicating allow/deny/challenge decisions to Network Manager’s Bastion Engine without revealing backend implementation details.
* Publishing DoS telemetry and critical events to Log Manager and Event Manager.
* Adjusting difficulty dynamically based on Health Manager signals and configured limits (`dos.*` namespace).

This specification does not cover the following:

* Cryptographic key management for puzzles. Key Manager owns all private keys per `01-protocol/05-keys-and-identity.md`.
* Authorization decisions or OperationContext construction. Those remain with Auth Manager and ACL Manager.
* Application-level rate limiting or QoS policies beyond what is mandated in the protocol.

## 3. Invariants and guarantees

Across all relevant contexts defined here, the following invariants hold:

* Every inbound connection must pass through DoS Guard before reaching Network Manager’s admitted surfaces.
* Client puzzles are opaque to Network Manager. DoS Guard generates and verifies them entirely within its own boundary.
* Admission decisions (`allow`, `deny`, `challenge`) are deterministic given the same telemetry and configuration.
* Puzzle difficulty increases monotonically for abusive identities until they return to compliant behavior.
* Puzzle responses are validated before any resource-intensive processing, respecting `01-protocol/08-network-transport-requirements.md`.
* Failure of DoS Guard to reach a decision results in `deny` to maintain fail-closed posture per `01-protocol/09-errors-and-failure-modes.md`.
* Puzzle issuance and validation never rely on graph state or OperationContext; they operate solely on transport metadata and DoS heuristics.

## 4. Admission lifecycle

DoS Guard Manager enforces a fixed admission lifecycle aligned with `01-protocol/11-dos-guard-and-client-puzzles.md`:

1. **Telemetry intake**: Network Manager provides connection metadata (IP, Tor circuit ID, claimed peer identity, connection counts, byte rates).
2. **Policy evaluation**: DoS Guard compares telemetry against configured thresholds and historical behavior for the connection’s identity or endpoint.
3. **Decision**: DoS Guard emits `allow`, `deny`, or `challenge` along with optional puzzle parameters.
4. **Puzzle issuance (if required)**: DoS Guard generates puzzles using Key Manager-provided randomness or HMAC keys and returns them to Network Manager for transport to the client.
5. **Puzzle verification**: Puzzle responses are submitted to DoS Guard for verification. Successful responses yield an `allow`; failures may escalate difficulty or emit `deny`.
6. **Telemetry update**: Admission outcomes update per-identity and global statistics to influence future decisions.

## 5. Inputs and outputs

### 5.1 Inputs

* Connection telemetry from Network Manager: `{ connection_id, peer_identity_id (if known), transport_surface, ip_or_circuit_id, bytes_in, bytes_out, message_rate, outstanding_puzzles }`.
* Health Manager readiness/liveness signals to adjust global policy (e.g., more aggressive throttling when the node is `not_ready`).
* Configuration snapshots from Config Manager (`dos.*` namespace) containing thresholds, difficulty schedules, and circuit weighting rules.
* Puzzle responses from Network Manager containing `{ puzzle_id, solution, connection_id }`.

### 5.2 Outputs

* Admission decision objects: `{ connection_id, decision, difficulty, puzzle_spec? }` returned to Network Manager’s Bastion Engine.
* Telemetry records routed to Log Manager describing challenges issued, solutions validated, denials, and abuse-suspect identities.
* Event Manager notifications for critical security events (`security.dos_abuse_detected`, `security.dos_policy_changed`).
* Configuration acknowledgements to Config Manager (success or veto).

## 6. Policy evaluation model

DoS Guard evaluates policies using a hierarchy of heuristics:

* **Global caps**: Maximum concurrent admitted connections, puzzles in flight, and puzzle validation rate. Exceeding these caps forces new connections into `challenge` or `deny`.
* **Per-identity limits**: Each peer identity (if authenticated) has allowed connection counts and message rates. Exceeding them raises difficulty or issues `deny`.
* **Anonymous limits**: Connections without identity (e.g., initial handshake) are handled per transport source. Rate-based heuristics apply until identity is established.
* **Adaptive difficulty**: Difficulty increases with repeated `challenge` failures or high message rates; it decays over time once behavior normalizes.
* **Health-aware throttling**: When Health Manager indicates `not_ready`, DoS Guard automatically raises difficulty or denies new connections to prevent overload.

Policies are configured via `dos.*` keys and must align with the invariants in `01-protocol/11-dos-guard-and-client-puzzles.md`.

## 7. Puzzle generation and verification

Puzzles follow the structure defined in `01-protocol/11-dos-guard-and-client-puzzles.md`:

* DoS Guard requests puzzle seeds or HMAC keys from Key Manager. Seeds never leave DoS Guard after derivation.
* Each puzzle includes `{ puzzle_id, difficulty_bits, seed, expires_at }`.
* Solutions are validated by recomputing the hash function and comparing against the difficulty threshold.
* Puzzles expire after `dos.puzzle.ttl_ms`. Expired puzzles result in `challenge_timeout` events and may increase difficulty for the associated connection.

## 8. Configuration surface (`dos.*`)

Key configuration entries include:

| Key | Type | Reloadable | Description |
| --- | --- | --- | --- |
| `dos.global.max_connections` | Integer | Yes | Hard cap on concurrently admitted connections. |
| `dos.global.max_puzzles` | Integer | Yes | Cap on concurrent outstanding puzzles. |
| `dos.identity.rate_limit` | Integer | Yes | Allowed messages per second per authenticated identity. |
| `dos.anonymous.rate_limit` | Integer | Yes | Allowed messages per second per unauthenticated source. |
| `dos.difficulty.base_bits` | Integer | Yes | Baseline puzzle difficulty in bits. |
| `dos.difficulty.max_bits` | Integer | Yes | Maximum difficulty. |
| `dos.difficulty.decay_ms` | Integer | Yes | Time window after which difficulty decays toward baseline. |
| `dos.puzzle.ttl_ms` | Integer | Yes | Puzzle expiration time. |
| `dos.health.readiness_multiplier` | Float | Yes | Multiplier applied to difficulty when Health Manager reports `not_ready`. |
| `dos.telemetry.events_enabled` | Boolean | Yes | Enables Event Manager notifications. |

Configuration reloads use Config Manager’s prepare/commit flow. DoS Guard must verify that new values are within safe ranges before acknowledging.

## 9. Internal engines

DoS Guard is implemented as coordinated engines:

### 9.1 Telemetry Intake Engine

* Receives connection telemetry from Network Manager.
* Enforces queue limits and drops oldest anonymous telemetry if the queue overflows.
* Tags telemetry with receipt timestamps for SLA tracking.

### 9.2 Policy Engine

* Evaluates global and per-identity thresholds.
* Determines whether to issue `allow`, `deny`, or `challenge`.
* Computes puzzle difficulty based on current abuse signals and configuration.

### 9.3 Puzzle Engine

* Generates puzzles using Key Manager seeds.
* Tracks outstanding puzzles and expiration.
* Verifies puzzle solutions and informs the Policy Engine of outcomes.

### 9.4 Publication Engine

* Communicates decisions to Network Manager.
* Emits telemetry to Log Manager and Event Manager when enabled.
* Applies health-aware throttling by consuming Health Manager signals.

## 10. Component interactions

* **Network Manager**: Provides telemetry and transports puzzles/responses. Network Manager must obey decisions immediately.
* **Key Manager**: Supplies seeds or HMAC keys for puzzle generation. Private keys never leave Key Manager.
* **Config Manager**: Provides `dos.*` configuration snapshots. DoS Guard validates and applies them.
* **Health Manager**: Supplies readiness state and optional metrics to influence difficulty.
* **Log Manager**: Receives structured logs for every decision, puzzle issuance, and puzzle failure.
* **Event Manager**: Receives notifications when abuse is detected or policy changes occur.

## 11. Failure handling

* If Telemetry Intake fails (queue overflow), DoS Guard logs the event and treats new connections as `challenge` until capacity returns.
* If Policy Engine encounters an error, decisions default to `deny`.
* If Puzzle Engine cannot generate puzzles (e.g., Key Manager unavailable), DoS Guard sets decisions to `deny` and logs `critical` errors.
* If Publication Engine cannot reach Network Manager, DoS Guard retries with exponential backoff and informs Health Manager; after exceeding retry limits, DoS Guard fails closed.

## 12. Security and trust boundaries

* DoS Guard treats all connection telemetry as untrusted until validated.
* Puzzles are opaque to other managers and clients; only DoS Guard verifies solutions.
* Decision APIs require mutual authentication with Network Manager to prevent injection.
* DoS Guard never accepts instructions from services or apps. Only Protocol managers may supply telemetry.

## 13. Observability

DoS Guard emits:

* Counts of allows, denies, challenges per transport surface.
* Puzzle issuance and completion histograms (difficulty, latency).
* Abuse detection events with anonymized identifiers.
* Configuration reload results.

These metrics are delivered to Log Manager and optionally to Event Manager for real-time monitoring.

## 14. Compliance checklist

Implementations must demonstrate:

* Every connection passes through the admission lifecycle.
* Puzzle generation and validation align with `01-protocol/11-dos-guard-and-client-puzzles.md`.
* Failures default to `deny` in accordance with `01-protocol/09-errors-and-failure-modes.md`.
* Configuration reloads follow Config Manager’s prepare/commit contract.
* No manager other than DoS Guard issues puzzles or admission directives.
