



# 02 Non-goals and out-of-scope

## 1. Purpose and scope

This document defines what 2WAY explicitly does not specify, implement, or guarantee. It constrains the design to prevent implicit dependencies on absent features and to bound security and correctness assumptions.

This document is normative for the repository. Implementations and reviews must treat excluded items as unsupported, even if they appear feasible. This document complements [00-scope-overview.md](../../../00-scope/00-scope-overview.md) and [01-scope-and-goals.md](../../../00-scope/01-scope-and-goals.md). Terminology is defined in [03-definitions-and-terminology.md](../../../00-scope/03-definitions-and-terminology.md).

## 2. Responsibilities

This specification is responsible for defining:

- The exclusion boundary between supported and unsupported behavior at the system and protocol layers.
- Forbidden interaction patterns that would break manager, system service, and app/app-service separation.
- The required rejection posture when excluded assumptions are used in design claims, interfaces, or runtime behavior.

This specification is not responsible for defining:

- Concrete manager API payloads or transport envelopes.
- Component-specific validation algorithms, persistence schemas, or migration behavior.
- App-specific feature semantics beyond whether they remain inside or outside the repository design boundary.

## 3. Document dependency and review application

- This specification defines design-time exclusion boundaries; it does not define runtime enforcement interfaces.
- Inputs are repository assumptions and scope constraints defined in scope and security documents.
- Outputs are review-time exclusion checks that determine whether a design claim is compliant.
- Trust-boundary enforcement is specified in the protocol and architecture manager/interface documents.
- This specification must be applied together with [01-protocol](../../../01-protocol/) and [02-architecture](../../../02-architecture/) during design and implementation review.

## 4. References

This document constrains, but does not restate, the following topics which are specified elsewhere.

- Manager, service, and app separation.
- Graph write pipeline and validation ordering.
- Key management, signing, and encryption requirements.
- Sync integrity, sequencing, and domain scoping rules.
- Security model and threat assumptions.
