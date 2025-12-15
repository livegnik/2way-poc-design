



# 08. Network transport requirements

## 1. Purpose and scope

This document defines the normative requirements for the network transport layer of the 2WAY protocol. It specifies the responsibilities, invariants, guarantees, allowed behaviors, forbidden behaviors, and failure handling of the transport abstraction as required by the PoC build guide. It does not define concrete network implementations, routing mechanisms, cryptographic formats, or sync logic beyond transport level constraints. All higher level protocol semantics are defined elsewhere.

## 2. Position in the system

The network transport layer provides best effort delivery of opaque envelopes between peers.

It operates:

- Below envelope verification, signature validation, ACL enforcement, schema validation, sync state management, and graph mutation.
- Above raw network connectivity and routing substrates.

The transport layer is not a trust boundary and must be treated as adversarial by all consuming components.

## 3. Responsibilities and non-responsibilities

This specification is responsible for the following:

- Sending opaque envelopes to a specified peer endpoint.
- Receiving opaque envelopes attributed to a peer endpoint.
- Preserving envelope boundaries exactly.
- Preserving envelope byte integrity.
- Signaling connection establishment and termination.
- Signaling delivery failure, timeout, or disconnect.
- Supporting multiple concurrent peer connections.
- Operating over untrusted and potentially anonymous networks as required by the PoC.

This specification does not cover the following:

- Authenticating peer identity.
- Authorizing operations.
- Verifying cryptographic signatures.
- Encrypting or decrypting payloads.
- Enforcing replay protection.
- Enforcing ordering or deduplication.
- Inspecting or interpreting envelope contents.
- Applying schema, ACL, or domain rules.
- Persisting envelopes beyond transient buffering required for delivery.
- Performing sync reconciliation or state repair.

All correctness and security guarantees are enforced above this layer.

## 4. Invariants and guarantees

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
- Global or per-peer ordering.
- Uniqueness of delivery.
- Latency bounds.
- Availability.
- Peer honesty or correctness.

## 5. Transport abstraction requirements

Any transport implementation used by the PoC must expose the following abstract capabilities:

- Send an opaque envelope to a peer reference.
- Receive an opaque envelope with an associated peer reference.
- Notify higher layers of connection lifecycle events.
- Notify higher layers of delivery failure or timeout.

Peer references provided by the transport are advisory only and must not be treated as identity assertions.

## 6. Allowed behaviors

The transport layer is permitted to:

- Drop envelopes silently.
- Delay delivery arbitrarily.
- Duplicate envelope delivery.
- Disconnect peers without explanation.
- Apply coarse connection level rate limiting.
- Operate over routed, proxied, or anonymized networks.

All higher layers must remain correct under these behaviors.

## 7. Forbidden behaviors

The transport layer must not:

- Modify envelope payloads or metadata.
- Inspect envelope contents beyond size and framing.
- Filter envelopes based on semantic meaning.
- Enforce access control decisions.
- Perform cryptographic verification.
- Infer trust, reputation, or intent.
- Persist envelope contents for analysis or replay.

## 8. Trust boundaries

All data received from the transport layer crosses an untrusted boundary.

Transport level peer identifiers:

- Must not be treated as authenticated identity.
- Must not be used for authorization decisions.
- May be used only for connection management, rate analysis, and routing.

All binding between envelopes and identities occurs through cryptographic verification at higher layers.

## 9. Interaction with other components

### 9.1 Inputs

The transport layer accepts:

- Opaque envelopes for outbound delivery.
- Peer addressing or routing references.
- Connection lifecycle directives from the Network Manager.

### 9.2 Outputs

The transport layer emits:

- Opaque inbound envelopes.
- Advisory peer references.
- Connection state events.
- Delivery failure or timeout events.

### 9.3 Consumers

Transport outputs may be consumed only by:

- Network Manager.
- State Manager for sync coordination.
- DoS Guard Engine mechanisms for behavioral analysis.

No other component may directly access the transport.

## 10. Failure and rejection handling

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

## 11. Security assumptions

The transport layer is assumed to be:

- Observable by adversaries.
- Subject to message injection and replay.
- Subject to traffic analysis.
- Subject to partial or total failure.

All protocol security properties defined elsewhere must hold under these assumptions without relying on transport guarantees.

## 12. Compliance criteria

A transport implementation is compliant with this specification if and only if:

- All responsibilities and invariants defined here are satisfied.
- No forbidden behaviors are present.
- No implicit trust assumptions are introduced.
- All failure conditions are surfaced explicitly to higher layers.
