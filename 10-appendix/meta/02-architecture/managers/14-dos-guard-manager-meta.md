



## 1. Purpose and scope

The DoS Guard Manager is the authoritative component responsible for the scope described below. The DoS Guard Manager is the sole authority responsible for protecting the 2WAY backend from denial-of-service attacks and abusive clients. It enforces admission control policies, issues and verifies client puzzles, tracks per-identity and per-peer difficulty levels, and coordinates with Network Manager and Health Manager to throttle or deny traffic when required. DoS Guard Manager never mutates graph state, it operates entirely within the boundaries defined by the protocol.

This specification defines DoS Guard responsibilities, inputs and outputs, internal engines, configuration, and interactions with other managers. It references the following protocol files:

* [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md)
* [01-protocol/05-keys-and-identity.md](../../../../01-protocol/05-keys-and-identity.md)
* [01-protocol/08-network-transport-requirements.md](../../../../01-protocol/08-network-transport-requirements.md)
* [01-protocol/10-errors-and-failure-modes.md](../../../../01-protocol/10-errors-and-failure-modes.md)
* [01-protocol/09-dos-guard-and-client-puzzles.md](../../../../01-protocol/09-dos-guard-and-client-puzzles.md)

Those files remain normative for admission control and puzzle semantics.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Owning the admission decision loop for inbound and outbound connections, in accordance with [01-protocol/09-dos-guard-and-client-puzzles.md](../../../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Issuing, validating, and expiring client puzzles (proof-of-work challenges) without exposing puzzle secrets or private keys.
* Tracking request rates, connection counts, and transport-level telemetry to detect abusive behavior.
* Communicating `allow`, `deny`, and `require_challenge` decisions defined in [01-protocol/09-dos-guard-and-client-puzzles.md](../../../../01-protocol/09-dos-guard-and-client-puzzles.md) to [Network Manager](../../../../02-architecture/managers/10-network-manager.md)'s Bastion Engine without revealing backend implementation details.
* Ensuring `deny` directives cause [Network Manager](../../../../02-architecture/managers/10-network-manager.md) to terminate the relevant connection immediately, consistent with Section 8 of [01-protocol/09-dos-guard-and-client-puzzles.md](../../../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Publishing DoS telemetry and critical events to [Log Manager](../../../../02-architecture/managers/12-log-manager.md) and [Event Manager](../../../../02-architecture/managers/11-event-manager.md).
* Adjusting difficulty dynamically based on [Health Manager](../../../../02-architecture/managers/13-health-manager.md) signals and configured limits (`dos.*` namespace).

This specification does not cover the following:

* Cryptographic key management for puzzles. [Key Manager](../../../../02-architecture/managers/03-key-manager.md) owns all private keys per [01-protocol/05-keys-and-identity.md](../../../../01-protocol/05-keys-and-identity.md).
* Authorization decisions or [OperationContext](../../../../02-architecture/services-and-apps/05-operation-context.md) construction. Those remain with [Auth Manager](../../../../02-architecture/managers/04-auth-manager.md) and [ACL Manager](../../../../02-architecture/managers/06-acl-manager.md).
* Application-level rate limiting or QoS policies beyond what is mandated in the protocol.
* Any graph mutation, sync state mutation, or schema enforcement. Those remain with [Graph Manager](../../../../02-architecture/managers/07-graph-manager.md), [State Manager](../../../../02-architecture/managers/09-state-manager.md), [Schema Manager](../../../../02-architecture/managers/05-schema-manager.md), and [ACL Manager](../../../../02-architecture/managers/06-acl-manager.md).
* Inferring identity from transport metadata, puzzle metadata, or telemetry. Identity binding remains governed exclusively by [01-protocol/05-keys-and-identity.md](../../../../01-protocol/05-keys-and-identity.md).
