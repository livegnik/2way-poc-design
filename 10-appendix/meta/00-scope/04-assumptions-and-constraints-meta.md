



# 04 Assumptions and constraints

## 1. Purpose and scope

This document defines the assumptions and constraints that bound the 2WAY design. It constrains what this design must implement and what is explicitly excluded. It defines repository-level invariants that all components must honor. Detailed protocol, data model, APIs, and security properties are defined in their respective design files under [01-protocol](../01-protocol/), [02-architecture](../02-architecture/), and [03-data](../03-data/) and are only referenced here. Terminology is defined in [03-definitions-and-terminology.md](../../../00-scope/03-definitions-and-terminology.md).

## 2. Responsibilities

This specification defines:

- What this design includes at the system boundary level.
- The goals that determine design completeness.
- Repository-wide invariants and constraints that other design files assume.
- What is allowed and forbidden at the scope level.
- Failure handling in terms of design compliance, not runtime behavior.

This specification does not define:

- Protocol wire formats, message envelopes, or sync package schemas.
- Database schemas or table layouts.
- Detailed manager interfaces or internal flows.
- Security mechanisms beyond scope level constraints.
