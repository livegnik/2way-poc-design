



# 06 ACL Manager

## 1. Purpose and scope

The ACL Manager is the authoritative component responsible for the scope described below. The ACL Manager is the sole authority for access control decisions over graph objects within the 2WAY system, implementing the normative behaviors defined in `01-protocol/06-access-control-model.md` and the pipeline positioning described in `01-protocol/00-protocol-overview.md`. It determines whether a requester may read or mutate graph state based on identity, app context, schema-defined defaults, ownership rules, group and relationship constraints, object-level ACL overrides, execution context, and sync constraints.

This specification defines the responsibilities, boundaries, internal engines, execution phases, invariants, guarantees, inputs, outputs, and failure behavior of the ACL Manager. This specification defines authorization logic only. It does not define authentication, identity verification, graph mutation semantics, persistence, sync selection, transport behavior, encryption, signature verification, or logging implementation. Those concerns are handled by other protocol specifications such as [01-protocol/05-keys-and-identity.md](../../../../01-protocol/05-keys-and-identity.md), [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md), and [01-protocol/07-sync-and-consistency.md](../../../../01-protocol/07-sync-and-consistency.md).

This specification consumes the protocol contracts defined in:

* [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md)
* [01-protocol/01-identifiers-and-namespaces.md](../../../../01-protocol/01-identifiers-and-namespaces.md)
* [01-protocol/02-object-model.md](../../../../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/05-keys-and-identity.md](../../../../01-protocol/05-keys-and-identity.md)
* [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/10-errors-and-failure-modes.md](../../../../01-protocol/10-errors-and-failure-modes.md)

Those files remain normative for all behaviors described here.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Acting as the single authorization authority for all read and write access to graph objects, as mandated in [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md) and restated in [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md).
* Evaluating access decisions for all graph operations, including create, read, update, and delete, matching the supervised operation ordering in [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md) and the access layers in [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md).
* Enforcing authorization consistently for:
  * Local frontend requests.
  * Backend system services.
  * Backend app extension services.
  * [State Manager](../../../../02-architecture/managers/09-state-manager.md) driven remote sync application.
* Evaluating authorization using only:
  * Identity context.
  * App context.
  * Domain and sync domain context.
  * Schema-defined defaults and prohibitions.
  * Ownership semantics.
  * Group and relationship constraints derived from the graph.
  * Object-level ACL overrides.
* Enforcing app isolation and domain isolation per [01-protocol/01-identifiers-and-namespaces.md](../../../../01-protocol/01-identifiers-and-namespaces.md) and [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md).
* Enforcing remote execution restrictions during sync application, including the remote envelope rules in [01-protocol/07-sync-and-consistency.md](../../../../01-protocol/07-sync-and-consistency.md).
* Producing deterministic allow or deny decisions with stable rejection categories that map to [01-protocol/10-errors-and-failure-modes.md](../../../../01-protocol/10-errors-and-failure-modes.md).
* Failing closed on missing, ambiguous, malformed, or unsupported policy data, following the rejection posture in [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md) and [01-protocol/10-errors-and-failure-modes.md](../../../../01-protocol/10-errors-and-failure-modes.md).
* Participating in every graph mutation path before any persistent write occurs, consistent with the sequencing in [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md).
* Participating in every restricted read path where visibility is constrained by policy, as required by [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md).

This specification does not cover the following:

* Authentication or session resolution, owned by [Auth Manager](../../../../02-architecture/managers/04-auth-manager.md) per [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md).
* Identity verification or signature validation, governed by [01-protocol/05-keys-and-identity.md](../../../../01-protocol/05-keys-and-identity.md).
* Graph mutation ordering, sequencing, or persistence, which remain the responsibility of [Graph Manager](../../../../02-architecture/managers/07-graph-manager.md) and [Storage Manager](../../../../02-architecture/managers/02-storage-manager.md) per [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md).
* Schema definition, compilation, or validation defined in [01-protocol/02-object-model.md](../../../../01-protocol/02-object-model.md).
* Sync domain selection or package construction described in [01-protocol/07-sync-and-consistency.md](../../../../01-protocol/07-sync-and-consistency.md).
* Network transport, encryption, or peer authentication, governed by [Network Manager](../../../../02-architecture/managers/10-network-manager.md) and [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md).
* Event emission, logging storage, or audit pipelines.
