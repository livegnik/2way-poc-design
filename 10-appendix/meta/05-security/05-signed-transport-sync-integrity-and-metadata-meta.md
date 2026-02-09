



# 05 Signed transport, sync integrity, and metadata

## 1. Purpose and scope

Defines signed envelope integrity, replay protection, and sync validation rules.

This specification references:

* [05-security/05-signed-transport-sync-integrity-and-metadata.md](../../../05-security/05-signed-transport-sync-integrity-and-metadata.md)
* [01-protocol/03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
* [02-architecture/managers/09-state-manager.md](../../../02-architecture/managers/09-state-manager.md)

## 2. Responsibilities and boundaries

This specification is responsible for:

* Declaring integrity checks for sync and transport metadata.

This specification does not cover:

* Transport routing or discovery mechanisms.
