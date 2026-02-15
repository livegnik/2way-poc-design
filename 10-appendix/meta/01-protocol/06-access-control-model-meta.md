



# 06 Access Control Model

## 1. Purpose and scope

This document defines the access control model of the 2WAY protocol as implemented in the PoC. It specifies how permissions are expressed, evaluated, and enforced at the protocol level. It covers authorization semantics only. [Authentication](../../../01-protocol/05-keys-and-identity.md), [identity representation](../../../01-protocol/05-keys-and-identity.md), [cryptographic verification](../../../01-protocol/04-cryptography.md), [schema definition](../../../02-architecture/managers/05-schema-manager.md), [sync behavior](../../../01-protocol/07-sync-and-consistency.md), and [storage mechanics](../../../03-data/01-sqlite-layout.md) are defined elsewhere and are referenced but not restated.

This specification references:

- [01-identifiers-and-namespaces.md](../../../01-protocol/01-identifiers-and-namespaces.md)
- [02-object-model.md](../../../01-protocol/02-object-model.md)
- [04-cryptography.md](../../../01-protocol/04-cryptography.md)
- [05-keys-and-identity.md](../../../01-protocol/05-keys-and-identity.md)
- [04-error-model.md](../../../04-interfaces/04-error-model.md)
- [07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
- [09-dos-guard-and-client-puzzles.md](../../../01-protocol/09-dos-guard-and-client-puzzles.md)
- [10-errors-and-failure-modes.md](../../../01-protocol/10-errors-and-failure-modes.md)
- [05-operation-context.md](../../../02-architecture/services-and-apps/05-operation-context.md)

This document is normative for the PoC.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

- Determining whether an authenticated identity is permitted to perform a specific operation on a specific graph object.
- Enforcing ownership, schema rules, and explicit access control constraints.
- Enforcing app and domain isolation during [graph mutations](../../../02-architecture/managers/07-graph-manager.md) and reads.
- Producing deterministic authorization decisions based solely on local state.
- Defining the canonical ACL and capability object schemas used for authorization.
- Defining the ACL enforcement matrix, including owner, admin, system data, and sync egress rules.

This specification does not cover the following:

- Authenticate identities or verify [cryptographic signatures](../../../01-protocol/04-cryptography.md).
- Perform [schema compilation](../../../02-architecture/managers/05-schema-manager.md) or migration.
- Resolve conflicts during [sync](../../../01-protocol/07-sync-and-consistency.md).
- Enforce rate limits or denial of service protections (see [09-dos-guard-and-client-puzzles.md](../../../01-protocol/09-dos-guard-and-client-puzzles.md)).
- Persist audit logs beyond standard error reporting (see [02-architecture/managers/12-log-manager.md](../../../02-architecture/managers/12-log-manager.md)).

These concerns are defined in other documents.
