



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

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Owning all inbound and outbound listeners, sessions, and connection state machines for supported transports, consolidating the consumer boundary defined in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).
* Abstracting transport implementations while preserving peer context and transport metadata, exactly as required by [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).
* Providing ordered startup and shutdown sequencing for all network surfaces, including onion service lifecycle where configured, so that surfaces mandated by [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md) are either ready or explicitly failed closed.
* Enforcing hard transport-level limits for size, rate, concurrency, and buffering independently of any DoS policy, satisfying the resource-failure constraints defined in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md) and [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Providing staged admission via a Bastion Engine that isolates unauthenticated peers and coordinates with [DoS Guard Manager](14-dos-guard-manager.md) for allow, deny, and challenge flows per [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Executing challenge transport as an opaque exchange, without interpreting puzzle content, difficulty, or verification logic, which are owned by [DoS Guard Manager](14-dos-guard-manager.md) and defined in [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Performing peer discovery for first-degree peers, including:
  * requesting peer identity and node endpoint attributes from the [State Manager](09-state-manager.md)
  * resolving candidate endpoints for connectivity
  * scheduling and initiating outbound session attempts
  * maintaining reachability state used only for connection scheduling
* Selecting endpoints deterministically and applying failure-based fallback and cooldown.
* Scheduling outbound connection attempts fairly and safely, enforcing global and per-peer caps, and preventing connection storms.
* Reusing existing admitted sessions when possible, and preventing redundant parallel connections, keyed by verified peer identity.
* Binding transport sessions to cryptographic identity only through [Key Manager](03-key-manager.md) verification, never through transport-provided identifiers, preserving the identity model in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Verifying signatures and decrypting inbound envelopes addressed to the local node, and attaching verified signer identity to the delivered package, exactly as mandated by [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md) and [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Signing and encrypting outbound envelopes as required by protocol rules and configuration, via the [Key Manager](03-key-manager.md), following the algorithms defined in [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md).
* Delivering only admitted and cryptographically verified inbound packages to the [State Manager](09-state-manager.md), preserving the envelope semantics of [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md) and the sync ordering rules of [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md).
* Transmitting outbound packages received from the [State Manager](09-state-manager.md), without adding retry semantics or persistence, thus honoring the best-effort semantics of [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).
* Emitting explicit connection lifecycle events, discovery and reachability events, admission outcomes, transport failures, and health signals to the [Event Manager](11-event-manager.md) and [Health Manager](13-health-manager.md), and emitting admission telemetry to [DoS Guard Manager](14-dos-guard-manager.md) as required by [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md) and [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md).
* Supporting multiple transport surfaces when configured, including the dual-surface model where a bastion surface is separated from an admitted data surface, without changing the trust boundary rules mandated in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).
* Surfacing network reachability facts to the [State Manager](09-state-manager.md) and [Event Manager](11-event-manager.md) without performing graph writes.

This specification does not cover the following:

* Definition of cryptographic primitives, algorithms, key formats, key rotation, or key storage.
* Definition of envelope schemas, sync semantics, replay rules, reconciliation logic, or ordering guarantees.
* ACL evaluation, schema validation, graph mutation logic, conflict handling, or any state write behavior.
* DoS policy decisions, puzzle creation, puzzle verification, difficulty selection, reputation scoring, or abuse classification.
* Multi-hop relay policy, overlay routing, or topology optimization beyond direct peer connectivity.
* Any user-facing APIs, UI behavior, or admin workflows.
