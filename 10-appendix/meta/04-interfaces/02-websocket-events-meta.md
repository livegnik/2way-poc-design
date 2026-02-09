



# 02 WebSocket events

## 1. Purpose and scope

Defines the local WebSocket session posture for 2WAY, including authentication gating and the reserved event envelope shape.

This document references:

* [02-architecture/managers/04-auth-manager.md](../../../02-architecture/managers/04-auth-manager.md)
* [04-error-model.md](../../../04-interfaces/04-error-model.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Declaring the authentication requirement for WS sessions.
* Establishing the session identity binding.
* Defining the local WebSocket endpoint path.
* Defining a reserved event envelope shape.
* Declaring payload size bounds for event envelopes.
* Defining client subscription frames and rejection behavior for invalid or unauthorized subscriptions.
* Defining transport rejection behavior for authentication failures.
* Defining session handling when auth tokens expire or are revoked after connection establishment.

This specification does not cover the following:

* Remote peer transport (see [01-protocol/08-network-transport-requirements.md](../../../01-protocol/08-network-transport-requirements.md)).
* Event catalog semantics beyond the reserved envelope.
