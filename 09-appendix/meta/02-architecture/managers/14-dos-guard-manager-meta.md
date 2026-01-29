



# 14 DoS Guard Manager

## 1. Purpose and scope

The DoS Guard Manager is the authoritative component responsible for the scope described below. The DoS Guard Manager is the sole authority responsible for protecting the 2WAY backend from denial-of-service attacks and abusive clients. It enforces admission control policies, issues and verifies client puzzles, tracks per-identity and per-peer difficulty levels, and coordinates with Network Manager and Health Manager to throttle or deny traffic when required. DoS Guard Manager never mutates graph state, it operates entirely within the boundaries defined by the protocol.

This specification defines DoS Guard responsibilities, inputs and outputs, internal engines, configuration, and interactions with other managers. It references the following protocol files:

* [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md)
* [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md)
* [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md)
* [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md)
* [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md)

Those files remain normative for admission control and puzzle semantics.
