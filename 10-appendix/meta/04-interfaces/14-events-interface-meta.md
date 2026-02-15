



# 14 Events Interface

## 1. Purpose and scope

Defines event envelope and channel families delivered over local WebSocket.

This document references:

* [02-architecture/managers/11-event-manager.md](../../../02-architecture/managers/11-event-manager.md)
* [04-interfaces/02-websocket-events.md](../../../04-interfaces/02-websocket-events.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Declaring event envelope and channel families.
* Declaring payload size bounds for event envelopes.
* Declaring client frames for subscriptions and resume behavior.
* Defining error event envelopes and close reason mappings.
* Enumerating auth-related error codes for event errors, including token expiry and revocation.
* Defining rejection behavior for invalid resume and ack frames.

This specification does not cover the following:

* Internal Event Manager engine behavior.
