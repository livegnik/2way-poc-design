



# 10 Network Manager

## 1. Purpose and scope

The Network Manager is the authoritative component responsible for the scope described below. This document specifies the Network Manager.

The Network Manager owns all peer-to-peer network I/O for a 2WAY node. It is the only component allowed to touch raw transport data. It defines transport abstraction, ordered startup and shutdown of network surfaces, staged admission through a bastion boundary, cryptographic binding at the network edge, peer discovery and outbound connection scheduling, reachability tracking, and integration with DoS Guard for abuse containment. This specification defines internal engines and phases that together constitute the Network Manager. These engines, phases, and boundaries are normative and required for correct implementation.

This specification consumes the protocol contracts defined in:

* [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md)
* [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md)
* [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md)
* [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md)
* [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md)

Those files remain normative for all behaviors described here.

This document does not define synchronization policy, graph semantics, authorization decisions, or DoS policy logic.
