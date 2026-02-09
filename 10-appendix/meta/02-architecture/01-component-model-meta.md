



# 01 Component model

## 1. Purpose and scope

This document defines the backend component model of the 2WAY system as implemented in the proof of concept (PoC). It specifies component categories, responsibilities, invariants, allowed and forbidden interactions, trust boundaries, and failure behavior.

This document is normative for backend structure and behavior. It does not define APIs, wire formats, schemas, storage layout, or runtime topology except where required to establish component correctness and boundaries. Frontend components are out of scope except as external callers.

This specification references:

* [01-protocol/**](../01-protocol/)
* [02-architecture/00-architecture-overview.md](../../../02-architecture/00-architecture-overview.md)
* [02-architecture/02-runtime-topologies.md](../../../02-architecture/02-runtime-topologies.md)
* [02-architecture/03-trust-boundaries.md](../../../02-architecture/03-trust-boundaries.md)
* [02-architecture/04-data-flow-overview.md](../../../02-architecture/04-data-flow-overview.md)
* [02-architecture/managers/**](managers/)
* [02-architecture/services-and-apps/**](services-and-apps/)
* [04-interfaces/**](../04-interfaces/)

## 2. Component model overview

The 2WAY backend is composed of managers and services running within a single long-lived backend process as described in [00-architecture-overview.md](../../../02-architecture/00-architecture-overview.md).

Managers form the protocol kernel. They implement all protocol-enforced behavior and invariants defined in [01-protocol/**](../01-protocol/).

Services implement domain logic on top of managers. Services never define protocol rules and never bypass managers, consistent with [02-architecture/04-data-flow-overview.md](../../../02-architecture/04-data-flow-overview.md).

The component model enforces the following system-wide rules:

- All persistent state mutation flows through managers.
- All protocol invariants are enforced by managers, not services.
- Services may coordinate behavior but cannot weaken or override manager guarantees.
- No component accesses another component's internal state directly.
