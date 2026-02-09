



# 11 Versioning and compatibility

## 1. Purpose and scope

This document defines protocol versioning and compatibility rules for 2WAY. It specifies how protocol versions are represented, how peers determine compatibility, and how version mismatches are handled. This file applies strictly to the protocol layer. It does not define application versioning, [schema evolution](../../../02-architecture/managers/05-schema-manager.md), [storage migrations](../../../03-data/01-sqlite-layout.md), API versioning, or deployment concerns.

This specification references:

- [03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)
- [06-access-control-model.md](../../../01-protocol/06-access-control-model.md)
- [07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
- [10-errors-and-failure-modes.md](../../../01-protocol/10-errors-and-failure-modes.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

- Defining the protocol version identifier and its interpretation.
- Defining compatibility requirements between peers.
- Defining allowed and forbidden interactions across protocol versions.
- Defining mandatory failure behavior when versions are incompatible.
- Mapping version incompatibility rejections to error codes and transport outcomes.
- Preserving protocol safety, determinism, and security guarantees across versions.

This specification does not cover the following:

- Schema compatibility or schema migration rules (see [02-architecture/managers/05-schema-manager.md](../../../02-architecture/managers/05-schema-manager.md)).
- Application or service feature negotiation.
- Backend or frontend API versioning.
- Database layout evolution (see [03-data/01-sqlite-layout.md](../../../03-data/01-sqlite-layout.md)).
- Transport negotiation or transport versioning (see [08-network-transport-requirements.md](../../../01-protocol/08-network-transport-requirements.md)).
- Upgrade orchestration or rollout strategy.

## 3. Guarantees

No additional guarantees are implied.
