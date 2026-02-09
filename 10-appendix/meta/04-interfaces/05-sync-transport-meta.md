



# 05 Sync Transport Interface

## 1. Purpose and scope

Defines the transport-facing sync surface implied by protocol and manager specifications, without fixing a concrete transport.

This document references:

* [01-protocol/03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/08-network-transport-requirements.md](../../../01-protocol/08-network-transport-requirements.md)
* [02-architecture/managers/09-state-manager.md](../../../02-architecture/managers/09-state-manager.md)
* [02-architecture/managers/10-network-manager.md](../../../02-architecture/managers/10-network-manager.md)
* [02-architecture/managers/14-dos-guard-manager.md](../../../02-architecture/managers/14-dos-guard-manager.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Declaring sync package transport requirements and admission ordering.
* Recording replay protection and rejection behavior tied to sync cursors.
* Declaring transport error mapping for ordering and admission failures.

This specification does not cover the following:

* Transport selection beyond the PoC HTTP endpoint described in the interface spec.
* UI semantics or frontend behavior.
