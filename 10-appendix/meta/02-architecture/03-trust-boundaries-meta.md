



# 03 Trust boundaries

## 1. Purpose and scope

This document defines the trust boundaries enforced by the 2WAY architecture as implemented in the PoC. It specifies where trust is explicitly assumed, where it is explicitly rejected, and which guarantees are enforced at each boundary.

This file covers architectural trust boundaries only. It does not define cryptographic primitives, schema semantics, ACL rule syntax, sync algorithms, or transport protocols. Those are defined elsewhere and are referenced here only where required to define boundary behavior.

This specification references:

* [01-protocol/**](../01-protocol/)
* [02-architecture/00-architecture-overview.md](../../../02-architecture/00-architecture-overview.md)
* [02-architecture/01-component-model.md](../../../02-architecture/01-component-model.md)
* [02-architecture/02-runtime-topologies.md](../../../02-architecture/02-runtime-topologies.md)
* [02-architecture/04-data-flow-overview.md](../../../02-architecture/04-data-flow-overview.md)
* [02-architecture/managers/**](managers/)
* [02-architecture/services-and-apps/**](services-and-apps/)
* [04-interfaces/**](../04-interfaces/)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining architectural trust boundaries between frontend, apps, services, managers, storage, network, and remote peers as framed in [01-component-model.md](../../../02-architecture/01-component-model.md) and [02-runtime-topologies.md](../../../02-architecture/02-runtime-topologies.md).
* Defining which interactions are allowed and forbidden across those boundaries aligned to [02-architecture/04-data-flow-overview.md](../../../02-architecture/04-data-flow-overview.md).
* Defining rejection, failure, and containment behavior at boundary violations aligned to [01-protocol/10-errors-and-failure-modes.md](../../../01-protocol/10-errors-and-failure-modes.md).

This specification does not cover the following:

* Cryptographic algorithms, formats, or key derivation ([01-protocol/04-cryptography.md](../../../01-protocol/04-cryptography.md)).
* ACL rule structure or evaluation semantics ([01-protocol/06-access-control-model.md](../../../01-protocol/06-access-control-model.md)).
* Schema declaration syntax or validation rules ([01-protocol/02-object-model.md](../../../01-protocol/02-object-model.md)).
* Sync algorithms, conflict resolution, or domain definitions ([01-protocol/07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)).
* Transport encoding, routing, or discovery mechanisms ([01-protocol/08-network-transport-requirements.md](../../../01-protocol/08-network-transport-requirements.md)).
