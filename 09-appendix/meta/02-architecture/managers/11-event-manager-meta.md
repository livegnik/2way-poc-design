



# 11 Event Manager

## 1. Purpose and scope

The Event Manager is the authoritative component responsible for the scope described below. The Event Manager is the sole publication and subscription authority for backend events in the 2WAY node. It receives post commit facts from managers, normalizes them into immutable notifications, enforces audience and access constraints, and delivers them to subscribers over the single local WebSocket surface.

This specification defines the event model, internal engines, ordering and delivery guarantees, subscription semantics, configuration surface, and trust boundaries for the Event Manager. It does not redefine schema semantics, persistence rules, network transport encodings, or UI behavior.

This specification consumes the protocol contracts defined in:

* [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md)
* [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md)
* [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md)
* [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md)
* [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md)
* [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md)
* [01-protocol/11-versioning-and-compatibility.md](../../01-protocol/11-versioning-and-compatibility.md)

Those files remain normative for all behaviors described here and for every cross-manager interaction referenced by this document.
