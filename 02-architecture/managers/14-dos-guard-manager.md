



# 14 DoS Guard Manager

Defines admission decisions, puzzle issuance and verification, and abuse mitigation.
Specifies telemetry inputs, decision outputs, policy evaluation, and engine behavior.
Defines failure handling, configuration, and trust boundaries for DoS protection.

Defines admission control, puzzle issuance, and abuse mitigation for network connections.
Specifies inputs, decisions, telemetry, and integration with Network and Health Managers.
Defines configuration, failure handling, and trust boundaries for DoS protection.

## 1. Invariants and guarantees

Across all relevant contexts defined here, the following invariants and guarantees hold:

* Every inbound connection must pass through DoS Guard before reaching [Network Manager](10-network-manager.md)'s admitted surfaces.
* Client puzzles are opaque to [Network Manager](10-network-manager.md). DoS Guard generates and verifies them entirely within its own boundary.
* Admission decisions (`allow`, `deny`, `require_challenge`) are deterministic given the same telemetry and configuration per [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Puzzle difficulty increases monotonically for abusive identities until they return to compliant behavior, matching Section 7.3 of [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Puzzle responses are validated before any resource-intensive processing, respecting [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).
* Failure of DoS Guard to reach a decision results in `deny` to maintain fail-closed posture per [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Puzzle issuance and validation never rely on graph state or [OperationContext](../services-and-apps/05-operation-context.md), they operate solely on transport metadata and DoS heuristics, and they never infer identity from telemetry as required by [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* When DoS Guard issues a `deny` directive for a connection, [Network Manager](10-network-manager.md) must apply it immediately, terminate the connection, and must not route further traffic for that connection per Section 8 of [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).

These guarantees must hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 2. Admission lifecycle

[DoS Guard Manager](14-dos-guard-manager.md) enforces a fixed admission lifecycle aligned with [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md):

1. **Telemetry intake**: [Network Manager](10-network-manager.md) provides connection metadata defined in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md) (transport type, advisory peer reference, byte/message counters, throughput samples, resource pressure indicators).
2. **Policy evaluation**: DoS Guard compares telemetry against configured thresholds and historical behavior for the connection's identity or endpoint.
3. **Decision**: DoS Guard emits `allow`, `deny`, or `require_challenge` along with optional throttle parameters per Section 8 of [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
4. **Puzzle issuance (if required)**: DoS Guard generates challenges defined in Section 7 of [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md) using [Key Manager](03-key-manager.md)-provided randomness or HMAC keys and returns them to [Network Manager](10-network-manager.md) for transport to the client.
5. **Puzzle verification**: Puzzle responses are submitted to DoS Guard for verification. DoS Guard validates `challenge_id`, expiration, `context_binding`, payload integrity, replay status, algorithm selection, and solution difficulty. Successful responses yield an `allow`, failures may escalate difficulty or emit `deny`.
6. **Telemetry update**: Admission outcomes update per-identity and global statistics to influence future decisions.

In addition to the fixed lifecycle above, DoS Guard shifts posture toward `deny` or `require_challenge` if telemetry or [Health Manager](13-health-manager.md) signals indicate the node cannot safely continue admitting traffic.

## 3. Inputs and outputs

### 3.1 Inputs

* Connection telemetry from [Network Manager](10-network-manager.md) defined in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md): `{ connection_id, transport_type, advisory_peer_reference, bytes_in, bytes_out, message_rate, throughput_samples, pressure_indicators, outstanding_challenges }`.
* [Health Manager](13-health-manager.md) readiness, liveness, and capacity signals to adjust global policy (for example, more aggressive throttling when the node is `not_ready`).
* Configuration snapshots from [Config Manager](01-config-manager.md) (`dos.*` namespace) containing thresholds, difficulty schedules, burst/decay windows, enablement flags, and concurrent challenge caps. Updates are applied atomically per Section 5.2 of [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Puzzle responses from [Network Manager](10-network-manager.md) containing `{ challenge_id, solution, connection_id, opaque_payload }` so DoS Guard can replay the validation defined in Section 7.2 of [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Resource pressure signals from [Network Manager](10-network-manager.md) (CPU saturation, memory pressure, socket pool usage) that inform adaptive throttling but never provide identity binding ([01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md)).

### 3.2 Outputs

* Admission decision objects: `{ connection_id, decision, throttle_params?, challenge_spec? }` returned to [Network Manager](10-network-manager.md)'s Bastion Engine per Sections 6 and 8 of [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* `deny` directives that require [Network Manager](10-network-manager.md) to terminate the connection immediately (no payload forwarding).
* Telemetry records routed to [Log Manager](12-log-manager.md) describing challenges issued, solutions validated, denials, throttle parameters, and abuse-suspect identities.
* [Event Manager](11-event-manager.md) notifications for critical security events (`security.dos_abuse_detected`, `security.dos_policy_changed`) when enabled by configuration.
* Configuration acknowledgements to [Config Manager](01-config-manager.md) (success or veto).

## 4. Policy evaluation model

DoS Guard evaluates policies using a hierarchy of heuristics:

* **Global caps**: Maximum concurrent admitted connections, puzzles in flight, and puzzle validation rate. Exceeding these caps forces new connections into `require_challenge` or `deny`.
* **Per-identity limits**: Each peer identity (if authenticated) has allowed connection counts and message rates. Exceeding them raises difficulty or issues `deny`.
* **Anonymous limits**: Connections without identity (for example, initial handshake) are handled per transport source. Rate-based heuristics apply until identity is established, but advisory transport metadata is never treated as authenticated identity per [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* **Adaptive difficulty**: Difficulty increases with repeated `require_challenge` failures or high message rates, it decays over time once behavior normalizes.
* **Health-aware throttling**: When [Health Manager](13-health-manager.md) indicates `not_ready`, DoS Guard automatically raises difficulty or denies new connections to prevent overload.

Policies are configured via `dos.*` keys and must align with the invariants in [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).

## 5. Puzzle generation and verification

Puzzles follow the structure defined in [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md):

* DoS Guard requests puzzle seeds or HMAC keys from [Key Manager](03-key-manager.md). Seeds never leave DoS Guard after derivation.
* Each challenge includes `{ challenge_id, difficulty_bits, expires_at, context_binding, payload, algorithm }`. The `context_binding` ties the challenge to the requesting connection, and the payload remains opaque to [Network Manager](10-network-manager.md).
* Solutions are validated by recomputing the hash function and comparing against the difficulty threshold selected by the Policy Engine.
* Puzzles expire after `dos.puzzle.ttl_ms`. Expired puzzles result in `ERR_RESOURCE_PUZZLE_FAILED` per [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md) and may increase difficulty for the associated connection.

Puzzle issuance and verification rules:

* DoS Guard must bound puzzle issuance per source so puzzle generation cannot be used to exhaust internal resources.
* DoS Guard must bound puzzle verification throughput so repeated invalid solutions cannot starve other admission work.
* Puzzle validation must confirm `challenge_id`, expiration, `context_binding`, payload fidelity, declared algorithm, and replay status before checking difficulty per Section 7.2 of [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Puzzle validation must be cheap compared to the work the puzzle imposes, and must run before any admitted routing.

## 6. Configuration surface (`dos.*`)

Key configuration entries include:

| Key                               | Type    | Reloadable | Description                                                               |
| --------------------------------- | ------- | ---------- | ------------------------------------------------------------------------- |
| `dos.global.max_connections`      | Integer | Yes        | Hard cap on concurrently admitted connections.                            |
| `dos.global.max_puzzles`          | Integer | Yes        | Cap on concurrent outstanding puzzles.                                    |
| `dos.identity.rate_limit`         | Integer | Yes        | Allowed messages per second per authenticated identity.                   |
| `dos.anonymous.rate_limit`        | Integer | Yes        | Allowed messages per second per unauthenticated source (advisory source identifiers only). |
| `dos.difficulty.base_bits`        | Integer | Yes        | Baseline puzzle difficulty in bits.                                       |
| `dos.difficulty.max_bits`         | Integer | Yes        | Maximum difficulty.                                                       |
| `dos.difficulty.decay_ms`         | Integer | Yes        | Time window after which difficulty decays toward baseline.                |
| `dos.puzzle.ttl_ms`               | Integer | Yes        | Puzzle expiration time.                                                   |
| `dos.health.readiness_multiplier` | Float   | Yes        | Multiplier applied to difficulty when [Health Manager](13-health-manager.md) reports `not_ready`. |
| `dos.telemetry.events_enabled`    | Boolean | Yes        | Enables [Event Manager](11-event-manager.md) notifications.                                      |

Configuration reloads use [Config Manager](01-config-manager.md)'s prepare and commit flow. DoS Guard must verify that new values are within safe ranges before acknowledging, and it must apply or reject the entire snapshot atomically per Section 5.2 of [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).

## 7. Internal engines

DoS Guard is implemented as coordinated engines:

### 7.1 Telemetry Intake Engine

* Receives connection telemetry from [Network Manager](10-network-manager.md) per [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).
* Enforces queue limits and drops oldest anonymous telemetry if the queue overflows, biasing future decisions toward `require_challenge`.
* Tags telemetry with receipt timestamps for SLA tracking.
* Consumes resource pressure indicators surfaced by [Network Manager](10-network-manager.md) (CPU saturation flags, memory pressure, socket pool usage).

### 7.2 Policy Engine

* Evaluates global and per-identity thresholds.
* Determines whether to issue `allow`, `deny`, or `require_challenge`.
* Computes puzzle difficulty based on current abuse signals and configuration.
* Escalates to `deny` when puzzle generation fails or telemetry indicates abuse, matching Section 10 of [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).

### 7.3 Puzzle Engine

* Generates puzzles using [Key Manager](03-key-manager.md) seeds.
* Tracks outstanding puzzles and expiration.
* Verifies puzzle solutions and informs the Policy Engine of outcomes.

### 7.4 Publication Engine

* Communicates decisions to [Network Manager](10-network-manager.md) using the interface defined in [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Emits telemetry to [Log Manager](12-log-manager.md) and [Event Manager](11-event-manager.md) when enabled.
* Applies health-aware throttling by consuming [Health Manager](13-health-manager.md) signals.
* Attaches the correct reason codes (for example, `ERR_RESOURCE_PUZZLE_FAILED`) to `deny` directives before [Network Manager](10-network-manager.md) closes the connection.

## 8. Startup and shutdown responsibilities

### 8.1 Startup

On startup, [DoS Guard Manager](14-dos-guard-manager.md) must:

* Load `dos.*` configuration via [Config Manager](01-config-manager.md).
* Initialize in-memory state for:

  * per-identity counters and rolling windows.
  * per-source counters and rolling windows for anonymous sources.
  * outstanding challenges and expiration tracking.
  * resource pressure baselines used to interpret telemetry.
* Register its decision interface with [Network Manager](10-network-manager.md)'s Bastion Engine so all admitted surfaces route through DoS Guard, as mandated by [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Default to a conservative posture until initial [Health Manager](13-health-manager.md) state is available. If [Health Manager](13-health-manager.md) state is unavailable, DoS Guard must behave as if the node is `not_ready`.

### 8.2 Shutdown

On shutdown, [DoS Guard Manager](14-dos-guard-manager.md) must:

* Stop issuing new puzzles.
* Mark outstanding puzzles as invalid for future validation.
* Emit a final telemetry snapshot to [Log Manager](12-log-manager.md).
* Instruct [Network Manager](10-network-manager.md) to stop admitting new connections on protected surfaces so admission remains fail-closed per [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).

## 9. Readiness, liveness, and operational guarantees

[DoS Guard Manager](14-dos-guard-manager.md) must provide the following signals for consumption by [Health Manager](13-health-manager.md):

* **Readiness**: DoS Guard is ready when:

  * configuration is loaded and validated.
  * [Key Manager](03-key-manager.md) dependencies required for puzzle generation are available, or DoS Guard has switched to deny-only mode explicitly and reported it.
  * the admission decision interface is registered with [Network Manager](10-network-manager.md).
* **Liveness**: DoS Guard is live when:

  * the Telemetry Intake Engine is draining inputs.
  * the Policy Engine is producing decisions within configured bounds.
  * the Publication Engine can deliver decisions to [Network Manager](10-network-manager.md).

If DoS Guard is not ready, [Network Manager](10-network-manager.md) must treat protected surfaces as not admissible and must not bypass DoS Guard.

## 10. Component interactions

* **[Network Manager](10-network-manager.md)**: Provides telemetry and transports puzzles and responses. [Network Manager](10-network-manager.md) must obey `allow`, `deny`, and `require_challenge` directives immediately and is the sole runtime caller of the DoS Guard API per Section 9 of [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* **[Key Manager](03-key-manager.md)**: Supplies seeds or HMAC keys for puzzle generation. Private keys never leave [Key Manager](03-key-manager.md).
* **[Config Manager](01-config-manager.md)**: Provides `dos.*` configuration snapshots. DoS Guard validates and applies them.
* **[Health Manager](13-health-manager.md)**: Supplies readiness state and optional metrics to influence difficulty.
* **[Log Manager](12-log-manager.md)**: Receives structured logs for every decision, puzzle issuance, puzzle failure, and associated throttle parameters.
* **[Event Manager](11-event-manager.md)**: Receives notifications when abuse is detected or policy changes occur.

## 11. Failure handling

* If Telemetry Intake fails (queue overflow), DoS Guard logs the event and treats new connections as `require_challenge` until capacity returns, matching Section 10 of [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* If Policy Engine encounters an error, decisions default to `deny` and [Network Manager](10-network-manager.md) terminates the connection.
* If Puzzle Engine cannot generate puzzles (for example, [Key Manager](03-key-manager.md) unavailable), DoS Guard emits `ERR_RESOURCE_PUZZLE_FAILED`, sets decisions to `deny`, and logs `critical` errors per [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* If Publication Engine cannot reach [Network Manager](10-network-manager.md), DoS Guard retries with exponential backoff and informs [Health Manager](13-health-manager.md). After exceeding retry limits, DoS Guard fails closed so [Network Manager](10-network-manager.md) cannot bypass admission.

Additional failure rules:

* If DoS Guard cannot obtain [Health Manager](13-health-manager.md) state, DoS Guard must apply the readiness multiplier as if the node is `not_ready`.

## 12. Security and trust boundaries

* DoS Guard treats all connection telemetry as untrusted until validated.
* Puzzles are opaque to other managers and clients. Only DoS Guard verifies solutions.
* Decision APIs require mutual authentication with [Network Manager](10-network-manager.md) to prevent injection.
* DoS Guard never accepts instructions from services or apps. Only Protocol managers may supply telemetry.

Forbidden behaviors:

* [Network Manager](10-network-manager.md) routing any protected surface request to deeper processing without a DoS Guard decision.
* Any manager other than DoS Guard issuing puzzles, accepting puzzle solutions, or modifying puzzle difficulty state.
* DoS Guard using graph state, schema state, or ACL state as an input to admission decisions.
* DoS Guard inferring identity from telemetry, transport metadata, or puzzle payloads ([01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md)).

## 13. Observability

DoS Guard emits:

* Counts of `allow`, `deny`, and `require_challenge` directives per transport surface.
* Puzzle issuance and completion histograms (difficulty, latency).
* Abuse detection events with anonymized identifiers.
* Configuration reload results.
* Counts of `deny` directives issued and applied.
* Counts of throttle directives issued (`require_challenge` transitions, throttle parameters) and applied, broken down by reason.

These metrics are delivered to [Log Manager](12-log-manager.md) and optionally to [Event Manager](11-event-manager.md) for real-time monitoring.

## 14. Compliance checklist

Implementations must demonstrate:

* Every connection passes through the admission lifecycle.
* Puzzle generation and validation align with [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md), including challenge structure, validation rules, and expiry handling.
* Failures default to `deny` (or `ERR_RESOURCE_PUZZLE_FAILED` when relevant) in accordance with [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Configuration reloads follow [Config Manager](01-config-manager.md)'s prepare/commit contract and apply atomically per [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* No manager other than DoS Guard issues puzzles or admission directives.
* [Network Manager](10-network-manager.md) obeys `deny` and `require_challenge` directives immediately and does not re-admit a terminated connection without a new admission decision.
