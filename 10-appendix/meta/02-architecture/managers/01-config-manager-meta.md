



# 01 Config Manager

## 1. Purpose and scope

The Config Manager is the authoritative component responsible for the scope described below. This specification defines the authoritative responsibilities, invariants, and interfaces of the Config Manager within the 2WAY backend.

Config Manager owns configuration ingestion, layering, validation, publication, controlled mutation, and change propagation for all runtime configuration that affects manager and service behavior. This specification covers configuration sources, precedence rules, storage model, consumer APIs, trust boundaries, startup and shutdown behavior, reload semantics, and fail closed behavior. This specification does not redefine protocol objects, graph schemas, ACL rules, transport encodings, or key custody beyond what is required to define configuration handling boundaries.

This specification consumes the protocol contracts defined in:

* [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md)
* [01-protocol/02-object-model.md](../../../../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/05-keys-and-identity.md](../../../../01-protocol/05-keys-and-identity.md)
* [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/09-dos-guard-and-client-puzzles.md](../../../../01-protocol/09-dos-guard-and-client-puzzles.md)
* [01-protocol/11-versioning-and-compatibility.md](../../../../01-protocol/11-versioning-and-compatibility.md)

Those files remain normative for all behaviors described here.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Load boot critical configuration from `.env` into an immutable in memory snapshot for the life of the process so bootstrap dependencies described in [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md) can initialize deterministically.
* Load persistent configuration from SQLite `settings` and merge it with defaults and `.env` according to deterministic precedence rules.
* Provide a single typed read interface for managers, services, and app backends to consume configuration, keeping all [OperationContext](../../../../02-architecture/services-and-apps/05-operation-context.md) consumers aligned with [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md).
* Provide a single controlled mutation interface for authorized callers to update SQLite backed configuration.
* Validate configuration values and structure before they become visible to any consumer.
* Maintain a schema registry for known keys, including types, constraints, defaults, reloadability, and export rules.
* Declare reserved namespaces even when no concrete keys exist.
* Publish per namespace immutable snapshots to managers during startup and during approved reloads.
* Coordinate safe change propagation via a two phase prepare and commit sequence with veto support by owning managers.
* Emit a monotonic configuration version identifier (`cfg_seq`) and associated provenance metadata for every committed snapshot.
* Supply DoS Guard policy snapshots (rate limits, burst windows, difficulty caps, abuse thresholds, telemetry verbosity) exactly as defined in [01-protocol/09-dos-guard-and-client-puzzles.md](../../../../01-protocol/09-dos-guard-and-client-puzzles.md), ensuring atomic visibility to [DoS Guard Manager](../../../../02-architecture/managers/14-dos-guard-manager.md).
* Supply the canonical locally declared protocol version tuple required by [01-protocol/11-versioning-and-compatibility.md](../../../../01-protocol/11-versioning-and-compatibility.md).
* Declare error mapping for configuration load, reload, update, and export failures.
* Provide explicit requirement-ID anchors consumed by generated configuration references.

This specification does not cover the following:

* Creating the database file, database migrations, or general storage lifecycle, these are owned by [Storage Manager](../../../../02-architecture/managers/02-storage-manager.md) per the persistence boundaries in [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md).
* Creating, storing, or exporting cryptographic secret material, these are owned by [Key Manager](../../../../02-architecture/managers/03-key-manager.md) or a dedicated secret store per [01-protocol/04-cryptography.md](../../../../01-protocol/04-cryptography.md).
* Defining graph schemas or ACL policies for protocol objects, these are owned by [Graph Manager](../../../../02-architecture/managers/07-graph-manager.md) and [ACL Manager](../../../../02-architecture/managers/06-acl-manager.md) per [01-protocol/02-object-model.md](../../../../01-protocol/02-object-model.md) and [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md).
* Network transport behavior, onion service lifecycle, peer discovery, or message routing, these are owned by [Network Manager](../../../../02-architecture/managers/10-network-manager.md) per [01-protocol/08-network-transport-requirements.md](../../../../01-protocol/08-network-transport-requirements.md).
* Installation flows, admin account creation, or app installation, these are owned by Installation and App related components. [Config Manager](../../../../02-architecture/managers/01-config-manager.md) only provides a controlled settings interface used by those components.
