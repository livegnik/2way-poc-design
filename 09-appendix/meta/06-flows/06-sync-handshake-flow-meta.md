



# 06 Sync handshake flow

## 1. Purpose and scope

Defines the handshake required before any sync ingress or egress. Establishes peer identity, protocol version, and domain compatibility.

This specification references:

* [06-flows/06-sync-handshake-flow.md](../../../06-flows/06-sync-handshake-flow.md)
* [01-protocol/07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/08-network-transport-requirements.md](../../../01-protocol/08-network-transport-requirements.md)

## 2. Responsibilities and boundaries

This specification is responsible for:

* Defining the validation steps before enabling sync.
* Declaring the allowed handshake inputs and failure behavior.

This specification does not cover:

* Transport implementation details.
* UI representation of sync status.
