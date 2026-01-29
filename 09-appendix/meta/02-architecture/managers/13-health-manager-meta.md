



# 13 Health Manager

## 1. Purpose and scope

The Health Manager is the authoritative component that evaluates, aggregates, and publishes the liveness and readiness state of the 2WAY node runtime. It collects health signals from all managers, internal services, and runtime subsystems; enforces the fail-closed posture defined in the protocol; and exposes a single source of truth to operators, diagnostic tools, and optionally Event Manager when critical transitions occur. Health Manager does not mutate graph state or perform remediation. Its role is detection, classification, and publication.

This specification defines the health classification model, responsibilities, input and output contracts, internal engines, configuration surface, and interactions with other managers. It references only the protocol contracts defined in:

* [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md)
* [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md)
* [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md)
* [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md)
* [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md)

Those files remain normative for all behaviors described here.
