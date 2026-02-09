



# 04 Auth Manager

## 1. Purpose and scope

The Auth Manager is the authoritative component responsible for the scope described below. The Auth Manager is the local authentication authority for the 2WAY backend. It resolves frontend-originated HTTP and WebSocket requests into authenticated backend identities and produces the identity-binding inputs required to construct a valid `OperationContext`.

Its scope ends at the local entrypoints. It never authenticates remote peers, handles sync provenance, or performs cryptographic verification of envelopes, and it never overlaps with authorization, graph mutation, or session lifecycle management. Those responsibilities belong to other managers.

This specification consumes the protocol contracts defined in:

* [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md)
* [01-protocol/02-object-model.md](../../../../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/05-keys-and-identity.md](../../../../01-protocol/05-keys-and-identity.md)
* [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/08-network-transport-requirements.md](../../../../01-protocol/08-network-transport-requirements.md)
* [01-protocol/10-errors-and-failure-modes.md](../../../../01-protocol/10-errors-and-failure-modes.md)

Those files remain normative for all behaviors described here.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Resolving a local frontend auth token into a backend `requester_identity_id`, in alignment with the [OperationContext](../../../../02-architecture/services-and-apps/05-operation-context.md) construction workflow in [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md).
* Producing an explicit authentication outcome for every local request so downstream managers can enforce the sequencing defined in [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md).
* Enforcing authentication before any backend manager or service is invoked so that authorization obeys the ordering defined in [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md).
* Supporting route-level admin gating based on trusted local configuration or identity metadata without bypassing the app and domain rules in [01-protocol/01-identifiers-and-namespaces.md](../../../../01-protocol/01-identifiers-and-namespaces.md).
* Binding authentication results into [OperationContext](../../../../02-architecture/services-and-apps/05-operation-context.md) inputs in a deterministic and immutable manner so envelope submission behaves exactly as described in [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md).
* Providing authenticated identity resolution for both HTTP and WebSocket entrypoints.
* Rejecting unauthenticated or malformed requests with explicit failure classification that maps to [01-protocol/10-errors-and-failure-modes.md](../../../../01-protocol/10-errors-and-failure-modes.md).
* Declaring mapping from rejection categories to ErrorDetail codes and transport statuses.
* Emitting authentication and admin-gating audit signals via [Log Manager](../../../../02-architecture/managers/12-log-manager.md) so that authentication-stage failures propagate into the observability posture described in [01-protocol/10-errors-and-failure-modes.md](../../../../01-protocol/10-errors-and-failure-modes.md).
* Operating as a strict trust boundary between untrusted frontend input and trusted backend execution, keeping remote identity handling with [Network Manager](../../../../02-architecture/managers/10-network-manager.md) per [01-protocol/08-network-transport-requirements.md](../../../../01-protocol/08-network-transport-requirements.md).
* Declaring the `auth.*` configuration surface used for admin gating inputs.

This specification does not cover the following:

* Authorization or permission evaluation. Owned by [ACL Manager](../../../../02-architecture/managers/06-acl-manager.md) per [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md).
* Graph mutation or schema validation. Owned by [Graph Manager](../../../../02-architecture/managers/07-graph-manager.md) and [Schema Manager](../../../../02-architecture/managers/05-schema-manager.md) per [01-protocol/02-object-model.md](../../../../01-protocol/02-object-model.md) and [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md).
* Frontend password handling, credential verification, or user onboarding. Owned by the frontend.
* Password handling, credential verification, or user onboarding. Owned by the frontend.
* Cryptographic signing or private-key access. Owned by [Key Manager](../../../../02-architecture/managers/03-key-manager.md). Signature verification is not exclusive to any single manager; any manager may verify signatures using public keys when required. [Network Manager](../../../../02-architecture/managers/10-network-manager.md) is responsible for verification at the transport boundary per [01-protocol/04-cryptography.md](../../../../01-protocol/04-cryptography.md) and [01-protocol/05-keys-and-identity.md](../../../../01-protocol/05-keys-and-identity.md).
* Remote peer authentication, handshake validation, or sync provenance. Owned by [Network Manager](../../../../02-architecture/managers/10-network-manager.md) and [State Manager](../../../../02-architecture/managers/09-state-manager.md) per [01-protocol/08-network-transport-requirements.md](../../../../01-protocol/08-network-transport-requirements.md) and [01-protocol/07-sync-and-consistency.md](../../../../01-protocol/07-sync-and-consistency.md).
* Rate limiting, client puzzles, or abuse mitigation. Owned by [DoS Guard Manager](../../../../02-architecture/managers/14-dos-guard-manager.md) and the interface layer.
