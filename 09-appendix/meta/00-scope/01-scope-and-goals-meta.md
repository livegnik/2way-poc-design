



# 01 Scope and goals

## 1. Purpose and scope of this document

This document defines the scope and goals of the 2WAY system design repository. It specifies what the system is intended to do, what properties it must guarantee, and which behaviors are explicitly allowed or forbidden at the design level.

This document is normative. All other design documents in this repository must conform to the constraints, invariants, and boundaries defined here. Terminology is defined in [03-definitions-and-terminology.md](03-definitions-and-terminology.md).

This document defines scope and intent only. It does not define wire formats, schemas, APIs, or concrete implementations except where required to constrain correctness or security. Those details live in protocol and architecture specifications under [01-protocol](../01-protocol/) and [02-architecture](../02-architecture/), with storage details under [03-data](../03-data/).

## 2. Responsibilities of this specification

This specification is responsible for defining:

- The boundaries of the 2WAY system.
- Global invariants that apply to all components.
- Required guarantees for correctness and security.
- Allowed and forbidden behaviors at the system level.
- Expected behavior on failure or invalid input.

This specification is not responsible for defining:

- Detailed protocol encoding.
- Concrete database schemas.
- Application-specific semantics.
- Deployment or operational policy.
