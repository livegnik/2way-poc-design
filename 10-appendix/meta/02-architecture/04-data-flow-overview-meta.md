



# 04 Data flow overview

## 1. Purpose and scope

This document defines the authoritative data flow model for the 2WAY system as implemented in the PoC. It specifies how data enters, moves through, mutates, and exits the system, including bootstrap, user provisioning, validation, authorization, sequencing, persistence, event emission, synchronization, rejection handling, and visibility suppression. It is limited to data flow semantics and boundaries and does not define schemas, envelopes, storage layouts, network formats, or UI behavior except where required for correctness.

This specification references:

* [01-protocol/**](../01-protocol/)
* [02-architecture/00-architecture-overview.md](../../../02-architecture/00-architecture-overview.md)
* [02-architecture/01-component-model.md](../../../02-architecture/01-component-model.md)
* [02-architecture/02-runtime-topologies.md](../../../02-architecture/02-runtime-topologies.md)
* [02-architecture/03-trust-boundaries.md](../../../02-architecture/03-trust-boundaries.md)
* [02-architecture/managers/**](managers/)
* [02-architecture/services-and-apps/**](services-and-apps/)
* [04-interfaces/**](../04-interfaces/)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining all allowed data flow paths between frontend, services, managers, storage, and network layers described in [01-component-model.md](../../../02-architecture/01-component-model.md).
* Defining the required ordering of bootstrap, provisioning, validation, authorization, sequencing, persistence, and emission aligned to [02-architecture/00-architecture-overview.md](../../../02-architecture/00-architecture-overview.md).
* Defining trust boundaries crossed during data movement as described in [02-architecture/03-trust-boundaries.md](../../../02-architecture/03-trust-boundaries.md).
* Defining allowed and forbidden data movements.
* Defining rejection and failure propagation behavior.
* Defining visibility suppression semantics via Rating objects defined in [01-protocol/02-object-model.md](../../../01-protocol/02-object-model.md).

This specification does not cover the following:

* Envelope structure or serialization details ([01-protocol/03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)).
* Schema definitions or schema evolution rules ([01-protocol/02-object-model.md](../../../01-protocol/02-object-model.md)).
* ACL rule syntax or policy composition ([01-protocol/06-access-control-model.md](../../../01-protocol/06-access-control-model.md)).
* Database schemas, indices, or query strategies.
* Transport protocols, routing, or discovery mechanisms ([01-protocol/08-network-transport-requirements.md](../../../01-protocol/08-network-transport-requirements.md)).
* UI level behavior or frontend state management ([04-interfaces/**](../04-interfaces/)).

## 3. Data flow classification

No other data flow categories are permitted.
