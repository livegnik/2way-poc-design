



# 08 Network transport requirements

Defines transport-layer responsibilities and envelope handling for 2WAY. Specifies transport invariants, permitted behavior, and failure signaling. Defines boundaries, trust assumptions, and compliance criteria for transport implementations.

For the meta specifications, see [08-network-transport-requirements meta](../09-appendix/meta/01-protocol/08-network-transport-requirements-meta.md).

## 1. Position in the system

The network transport layer provides best effort delivery of opaque envelopes between peers.

It operates:

- Below [envelope verification](03-serialization-and-envelopes.md), [signature validation](04-cryptography.md), [ACL enforcement](06-access-control-model.md), [schema validation](../02-architecture/managers/05-schema-manager.md), [sync state management](07-sync-and-consistency.md), and [graph mutation](../02-architecture/managers/07-graph-manager.md).
- Above raw network connectivity and routing substrates.

The transport layer is not a trust boundary and must be treated as adversarial by all consuming components.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

- Sending opaque envelopes to a specified peer endpoint.
- Receiving opaque envelopes attributed to a peer endpoint.
- Preserving envelope boundaries exactly.
- Preserving envelope byte integrity.
- Signaling connection establishment and termination.
- Signaling delivery failure, timeout, or disconnect.
- Supporting multiple concurrent peer connections.
- Producing connection-level telemetry (byte and message counters, timing samples, resource pressure indicators) required for [DoS Guard](09-dos-guard-and-client-puzzles.md) and observability tooling while preserving envelope opacity.
- Operating over untrusted and potentially anonymous networks as required by the PoC.

This specification does not cover the following:

- Authenticating peer identity (see [05-keys-and-identity.md](05-keys-and-identity.md)).
- Authorizing operations (see [06-access-control-model.md](06-access-control-model.md)).
- [Verifying cryptographic signatures](04-cryptography.md).
- [Encrypting](04-cryptography.md) or decrypting payloads.
- Enforcing replay protection (see [07-sync-and-consistency.md](07-sync-and-consistency.md)).
- Enforcing ordering or deduplication (see [07-sync-and-consistency.md](07-sync-and-consistency.md)).
- Inspecting or interpreting [envelope contents](03-serialization-and-envelopes.md).
- Applying [schema](../02-architecture/managers/05-schema-manager.md), [ACL](06-access-control-model.md), or [domain rules](07-sync-and-consistency.md).
- Persisting envelopes beyond transient buffering required for delivery.
- Performing [sync](07-sync-and-consistency.md) reconciliation or state repair.

All correctness and security guarantees are enforced above this layer, including those in [03-serialization-and-envelopes.md](03-serialization-and-envelopes.md) and [07-sync-and-consistency.md](07-sync-and-consistency.md).

## 3. Invariants and guarantees

The transport layer must maintain the following invariants:

- Envelope contents are never modified.
- Envelope byte order is preserved.
- Envelope boundaries are preserved.
- No synthetic envelopes are generated.
- No semantic interpretation of envelopes occurs.

The transport layer provides only the following guarantees:

- Best effort delivery attempt.
- Explicit signaling of failure or disconnect when detectable.

The transport layer provides no guarantees of:

- Reliable delivery.
- Global or per-peer ordering (see [07-sync-and-consistency.md](07-sync-and-consistency.md)).
- Uniqueness of delivery.
- Latency bounds.
- Availability.
- Peer honesty or correctness.

## 4. Transport abstraction requirements

Any transport implementation used by the PoC must expose the following abstract capabilities:

- Send an opaque envelope to a peer reference.
- Receive an opaque envelope with an associated peer reference.
- Notify higher layers of connection lifecycle events.
- Notify higher layers of delivery failure or timeout.

Peer references provided by the transport are advisory only and must not be treated as [identity assertions](05-keys-and-identity.md).

## 5. Allowed behaviors

The transport layer is permitted to:

- Drop envelopes silently.
- Delay delivery arbitrarily.
- Duplicate envelope delivery.
- Disconnect peers without explanation.
- Apply coarse connection level rate limiting (see [09-dos-guard-and-client-puzzles.md](09-dos-guard-and-client-puzzles.md)).
- Operate over routed, proxied, or anonymized networks.

All higher layers must remain correct under these behaviors.

## 6. Forbidden behaviors

The transport layer must not:

- Modify envelope payloads or metadata.
- Inspect envelope contents beyond size and framing (see [03-serialization-and-envelopes.md](03-serialization-and-envelopes.md)).
- Filter envelopes based on semantic meaning.
- Enforce [access control](06-access-control-model.md) decisions.
- Perform [cryptographic verification](04-cryptography.md).
- Infer trust, reputation, or intent.
- Persist envelope contents for analysis or replay.

## 7. Trust boundaries

All data received from the transport layer crosses an untrusted boundary.

Transport level peer identifiers:

- Must not be treated as authenticated identity (see [05-keys-and-identity.md](05-keys-and-identity.md)).
- Must not be used for authorization decisions (see [06-access-control-model.md](06-access-control-model.md)).
- May be used only for connection management, rate analysis, and routing.

All binding between envelopes and identities occurs through [cryptographic verification](04-cryptography.md) at higher layers.

## 8. Interaction with other components

### 8.1 Inputs

The transport layer accepts:

- Opaque envelopes for outbound delivery.
- Peer addressing or routing references.
- Connection lifecycle directives from the [Network Manager](../02-architecture/managers/10-network-manager.md).

### 8.2 Outputs

The transport layer emits:

- Opaque inbound envelopes.
- Advisory peer references.
- Connection state events.
- Delivery failure or timeout events.
- Connection telemetry including byte counters, message counters, timing samples, and resource pressure metrics suitable for [DoS Guard Manager](../02-architecture/managers/14-dos-guard-manager.md) analysis and [Event Manager](../02-architecture/managers/11-event-manager.md) observability. All telemetry remains advisory and unauthenticated.

### 8.3 Consumers

Transport outputs may be consumed only by:

- [Network Manager](../02-architecture/managers/10-network-manager.md).
- [State Manager](../02-architecture/managers/09-state-manager.md) for sync coordination.
- [DoS Guard Manager](../02-architecture/managers/14-dos-guard-manager.md) mechanisms for behavioral analysis.

No other component may directly access the transport.

### 8.4 Telemetry propagation

- Transport implementations must surface connection lifecycle events, delivery failures, timeouts, disconnects, and associated telemetry so that the [Network Manager](../02-architecture/managers/10-network-manager.md) can forward them to [Event Manager](../02-architecture/managers/11-event-manager.md) and [DoS Guard Manager](../02-architecture/managers/14-dos-guard-manager.md) without mutation.
- Telemetry may include byte counters, message counters, routing metadata, latency samples, and local resource pressure indicators. All such data is advisory and must not be treated as authenticated identity or authorization evidence.
- [State Manager](../02-architecture/managers/09-state-manager.md) consumes only the verified package deliveries supplied by [Network Manager](../02-architecture/managers/10-network-manager.md); telemetry shared with State Manager is limited to the readiness signals necessary for [sync](07-sync-and-consistency.md) scheduling and may not expose raw transport payloads.

## 9. Failure and rejection handling

On delivery failure:

- The transport layer must signal failure to the caller.
- No retries are implied or performed by the transport.
- Envelopes must not be mutated.

On malformed input at the transport framing level:

- Data may be dropped.
- No correction or interpretation may be attempted.

On peer misbehavior:

- Connections may be closed.
- Rate limiting may be applied.
- No attribution, punishment, or blacklist semantics are permitted.

All recovery, retry, reconciliation, and penalty logic is defined above the transport layer.

## 10. Security assumptions

The transport layer is assumed to be:

- Observable by adversaries.
- Subject to message injection and replay.
- Subject to traffic analysis.
- Subject to partial or total failure.

All protocol security properties defined elsewhere must hold under these assumptions without relying on transport guarantees.

## 11. Compliance criteria

A transport implementation is compliant with this specification if and only if:

- All responsibilities and invariants defined here are satisfied.
- No forbidden behaviors are present.
- No implicit trust assumptions are introduced.
- All failure conditions are surfaced explicitly to higher layers.
