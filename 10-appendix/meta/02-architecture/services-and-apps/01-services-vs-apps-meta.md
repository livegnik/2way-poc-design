



# 01 Services vs Apps

## 1. Purpose and scope

This specification defines how backend services and applications relate inside the 2WAY PoC architecture. It explains why services and applications are separate architectural constructs, enumerates the invariants that keep them isolated, and provides implementation rules that every conforming backend must follow. It binds the component model, manager responsibilities, and OperationContext requirements into a single consumable contract that backend implementers must follow when writing system services, optional app services, or frontend applications that target this backend.

This document does not redefine schemas, ACL policy, serialization, cryptography, or other protocol-level mechanics. Those topics remain governed by their dedicated specifications, and this document consumes them without restating their guarantees.

This specification references the following documents:

* `01-protocol/**`
* `02-architecture/01-component-model.md`
* `02-architecture/managers/00-managers-overview.md`
* `02-architecture/managers/**`
* `02-architecture/services-and-apps/05-operation-context.md`

Those documents remain normative for their respective domains.
