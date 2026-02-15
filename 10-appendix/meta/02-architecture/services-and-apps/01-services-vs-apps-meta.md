



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

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining separation rules between system services, app services, and frontend apps.
* Defining how callers handle service availability failures, including `ERR_SVC_APP_*` behavior on unavailable app services.

This specification does not cover the following:

* Endpoint-specific transport mappings, which are owned by [04-interfaces/**](../../04-interfaces/).
