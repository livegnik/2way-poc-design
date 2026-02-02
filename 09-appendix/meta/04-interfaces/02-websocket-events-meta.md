



# 02 WebSocket events

## 1. Purpose and scope

Defines the local WebSocket session posture for 2WAY, including authentication gating and the reserved event envelope shape.

This document references:

* [02-architecture/managers/04-auth-manager.md](../02-architecture/managers/04-auth-manager.md)
* [04-error-model.md](04-error-model.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Declaring the authentication requirement for WS sessions.
* Establishing the session identity binding.
* Defining a reserved event envelope shape.

This specification does not cover the following:

* Remote peer transport (see [01-protocol/08-network-transport-requirements.md](../01-protocol/08-network-transport-requirements.md)).
* Event catalog semantics beyond the reserved envelope.
