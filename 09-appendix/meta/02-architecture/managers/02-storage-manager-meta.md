



# 02 Storage Manager

## 1. Purpose and scope

The Storage Manager is the authoritative component responsible for the scope described below. Storage Manager is the sole authority for durable persistence in the 2WAY backend. It owns the SQLite database lifecycle, schema materialization, per-app table provisioning, transactional boundaries, and persistence primitives consumed by all other managers and services.

This specification defines the complete responsibilities, internal structure, invariants, APIs, and failure posture of Storage Manager. It is an implementation-facing design specification. It does not define higher-level graph semantics, ACL logic, schema meaning, sync policy, or network behavior, except where storage guarantees are required to support them. Storage Manager is a passive subsystem. It never interprets protocol meaning. It persists state exactly as instructed by higher-level managers defined in [01-component-model.md](../01-component-model.md) and guarantees durability, ordering, isolation, and integrity. Storage Manager enforces the canonical data and sequencing rules defined by the protocol corpus; those references are listed explicitly below.

This specification consumes the protocol contracts defined in:

* [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md)
* [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md)
* [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md)

Those files remain normative for all behaviors described here.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Owning the single backend SQLite database file and its WAL lifecycle, keeping persistence centralized per the manager boundaries established in [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md).
* Creating, migrating, and validating all global tables so canonical metadata defined in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) and [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) always has an authoritative store.
* Creating and maintaining per-app table families for every registered app, matching the namespace guarantees described in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md) and [App Manager](08-app-manager.md).
* Enforcing transactional isolation, atomicity, and write serialization.
* Persisting all graph objects exactly as provided by [Graph Manager](07-graph-manager.md).
* Persisting monotonic sequence counters, including `global_seq` and `domain_seq`.
* Persisting sync progress and peer replication state.
* Persisting system metadata such as settings, peers, and app registry data.
* Providing typed, constrained persistence helpers to all managers and services defined in [02-architecture/services-and-apps/**](../services-and-apps/).
* Guaranteeing that every stored graph row carries the immutable metadata fields required by [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) and that callers cannot mutate those fields post insert.
* Preserving the envelope transaction boundary described in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) so that each accepted envelope maps to exactly one SQLite transaction commit.
* Enforcing the strict `global_seq` and `domain_seq` ordering discipline mandated by [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) by co-locating sequence persistence with the data rows they gate.
* Preventing all raw database access outside this manager.
* Providing observability, maintenance, and integrity tooling hooks.
* Failing closed on corruption, partial initialization, or invariant violations.

This specification does not cover the following:

* Schema validation semantics, which belong to [Schema Manager](05-schema-manager.md) per [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* ACL evaluation or permission enforcement, which belong to [ACL Manager](06-acl-manager.md) per [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).
* Graph semantics, object meaning, or lifecycle interpretation.
* Network transport, peer connectivity, or message handling.
* Sync policy, domain logic, or replication strategy.
* Cryptographic key custody, signing, or encryption.
* Application-level business logic or service behavior.
