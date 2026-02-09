



# 02 Runtime topologies

## 1. Purpose and scope

This document defines the valid runtime topologies for a 2WAY node as specified by the PoC build guide. It describes how backend managers, services, frontend apps, storage, keys, and network components are arranged and interact at runtime. It specifies trust boundaries, allowed and forbidden interactions, and required failure behavior. It does not define deployment tooling, packaging, orchestration, scaling, or operational automation.

This specification references:

* [01-protocol/**](../01-protocol/)
* [02-architecture/00-architecture-overview.md](../../../02-architecture/00-architecture-overview.md)
* [02-architecture/01-component-model.md](../../../02-architecture/01-component-model.md)
* [02-architecture/03-trust-boundaries.md](../../../02-architecture/03-trust-boundaries.md)
* [02-architecture/04-data-flow-overview.md](../../../02-architecture/04-data-flow-overview.md)
* [02-architecture/managers/**](managers/)
* [02-architecture/services-and-apps/**](services-and-apps/)
* [04-interfaces/**](../04-interfaces/)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

- Permitted runtime arrangements of backend managers, system services, app extension services, frontend apps, and network components defined in [01-component-model.md](../../../02-architecture/01-component-model.md) and [02-architecture/services-and-apps/**](services-and-apps/).
- Trust boundaries between backend, frontend, local storage, and remote peers as defined in [02-architecture/03-trust-boundaries.md](../../../02-architecture/03-trust-boundaries.md).
- Mandatory interaction paths between runtime components aligned to [02-architecture/04-data-flow-overview.md](../../../02-architecture/04-data-flow-overview.md).
- Runtime behavior under failure, rejection, or partial availability.

This specification does not cover the following:

- Container boundaries or operating system isolation.
- High availability, clustering, or replication strategies.
- Load balancing or horizontal scaling.
- User interface composition or frontend framework choices.
- Transport implementation details beyond manager responsibilities.

## 3. Runtime topology model

All conforming implementations must match one of the defined topologies or be a strict specialization that preserves all invariants.
