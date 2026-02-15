



# 09 DoS Guard and client puzzle requirements

## 1. Purpose and scope

This document defines the normative requirements for the DoS Guard Manager and the client puzzle mechanism within the 2WAY protocol. It specifies how admission control operates at the network boundary, which inputs are consumed, which directives are emitted, and how puzzles are issued, validated, and expired. It also defines the trust and failure posture of the DoS Guard Manager. This specification does not redefine [transport behavior](../../../01-protocol/08-network-transport-requirements.md), [cryptographic verification](../../../01-protocol/04-cryptography.md), or [sync semantics](../../../01-protocol/07-sync-and-consistency.md) already covered in other protocol files.

This specification references:

- [04-cryptography.md](../../../01-protocol/04-cryptography.md)
- [04-error-model.md](../../../04-interfaces/04-error-model.md)
- [06-access-control-model.md](../../../01-protocol/06-access-control-model.md)
- [07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
- [08-network-transport-requirements.md](../../../01-protocol/08-network-transport-requirements.md)
- [10-errors-and-failure-modes.md](../../../01-protocol/10-errors-and-failure-modes.md)

## 2. Position in the system

The DoS Guard Manager sits logically between the adversarial transport abstraction ([08-network-transport-requirements.md](../../../01-protocol/08-network-transport-requirements.md)) and the cryptographic boundary owned by [Network Manager](../../../02-architecture/managers/10-network-manager.md). It has no direct access to graph envelopes and never bypasses Network Manager; instead it consumes telemetry and provisional metadata, applies policy, and instructs Network Manager to allow, deny, or challenge a connection prior to cryptographic processing.

## 3. Responsibilities and boundaries

The DoS Guard Manager is responsible for:

- Owning admission control policy for all inbound and outbound peer connections.
- Consuming transport-level telemetry (byte counters, message counters, latency samples, resource pressure indicators, provisional peer references) to detect abusive or anomalous behavior.
- Applying configurable and adaptive rate limits per peer, subnet, onion endpoint, and system-wide resource class.
- Determining when client puzzles are required, selecting work factors, constructing puzzle payloads, and validating puzzle responses.
- Emitting explicit directives to Network Manager (`allow`, `deny`, or `require_challenge`) for each admission request.
- Tracking challenge lifetime, expiry, reuse, and replay protection.
- Emitting telemetry and abuse events to the [Event Manager](../../../02-architecture/managers/11-event-manager.md) for observability and audit.
- Exposing readiness and health status to the [Health Manager](../../../02-architecture/managers/13-health-manager.md) when admission control becomes degraded or unavailable.

The DoS Guard Manager explicitly does **not**:

- Perform [cryptographic verification](../../../01-protocol/04-cryptography.md) or decryption of packages.
- Interpret [graph envelopes](../../../01-protocol/03-serialization-and-envelopes.md), [schema semantics](../../../02-architecture/managers/05-schema-manager.md), [ACL rules](../../../01-protocol/06-access-control-model.md), or application data.
- Assign identity to peers solely from [transport metadata](../../../01-protocol/08-network-transport-requirements.md) or puzzle responses.
- Persist envelopes or mutate state outside of its own counters and policy state.
- Make [authorization](../../../01-protocol/06-access-control-model.md), [sync ordering](../../../01-protocol/07-sync-and-consistency.md), or [storage decisions](../../../03-data/01-sqlite-layout.md).
