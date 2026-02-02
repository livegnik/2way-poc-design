



# 06 Flows overview

This section defines the end-to-end operational flows for the 2WAY PoC. Each flow is an executable description of how data moves across interfaces, services, managers, and storage, and which invariants must hold before and after the flow completes.

These flows are authoritative for runtime behavior and are aligned with:

* [02-architecture/04-data-flow-overview.md](../02-architecture/04-data-flow-overview.md)
* [01-protocol/00-protocol-overview.md](../01-protocol/00-protocol-overview.md)
* [02-architecture/services-and-apps/**](../02-architecture/services-and-apps/)
* [04-interfaces/**](../04-interfaces/)

For the meta specifications, see [00-flows-overview-meta.md](../09-appendix/meta/06-flows/00-flows-overview-meta.md).

## 1. Common invariants

Across all flows in this section, the following invariants hold:

* All writes use graph message envelopes and pass through Graph Manager.
* Schema Manager validates all object types and constraints before commit.
* ACL Manager enforces authorization before any write persists.
* Storage Manager is the only component that touches the database.
* OperationContext is immutable once constructed.
* Fail-closed behavior is mandatory on validation or authorization failures.
* Events and logs are emitted only after successful commit.

## 2. Flow index

The flows defined in this section are:

1) First-run and identity bootstrap.
2) App install and permission provisioning.
3) Create/update/delete graph objects (write flow).
4) Contact and profile management.
5) Messaging flow.
6) Sync handshake flow.
7) Conflict resolution flow.
8) Key rotation flow.
9) Device add/remove flow.
10) Backup and restore flow.

No additional flows are permitted unless added to this section with matching meta specifications.
