



# 02 Non-goals and out-of-scope

## 1. Purpose and scope

This document defines what 2WAY explicitly does not specify, implement, or guarantee. It constrains the PoC design to prevent implicit dependencies on absent features and to bound security and correctness assumptions.

This document is normative for the repository. Implementations and reviews must treat excluded items as unsupported, even if they appear feasible. This document complements [00-scope-overview.md](00-scope-overview.md) and [01-scope-and-goals.md](01-scope-and-goals.md). Terminology is defined in [03-definitions-and-terminology.md](03-definitions-and-terminology.md).

## 2. References

This document constrains, but does not restate, the following topics which are specified elsewhere.

- Manager, service, and app separation.
- Graph write pipeline and validation ordering.
- Key management, signing, and encryption requirements.
- Sync integrity, sequencing, and domain scoping rules.
- Security model and threat assumptions.
