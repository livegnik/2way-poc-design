



# 01 Protocol

This folder defines the 2WAY protocol rules for graph mutation, validation ordering, authorization,
sequencing, and synchronization. It is the normative definition of how envelopes are structured,
verified, and either applied or rejected.

If protocol requirements conflict with other folders, record the exception as an ADR and treat this
folder as the authoritative source for protocol behavior.

## What lives here

- [`00-protocol-overview.md`](00-protocol-overview.md) - Protocol posture, lifecycle, guarantees, and forbidden paths.
- [`01-identifiers-and-namespaces.md`](01-identifiers-and-namespaces.md) - Identifier formats, namespaces, and scoping rules.
- [`02-object-model.md`](02-object-model.md) - Canonical graph object types and structural constraints.
- [`03-serialization-and-envelopes.md`](03-serialization-and-envelopes.md) - Envelope format and structural validation rules.
- [`04-cryptography.md`](04-cryptography.md) - Signature and encryption requirements.
- [`05-keys-and-identity.md`](05-keys-and-identity.md) - Key binding, identity rules, and revocation semantics.
- [`06-access-control-model.md`](06-access-control-model.md) - ACL semantics and authorization evaluation rules.
- [`07-sync-and-consistency.md`](07-sync-and-consistency.md) - Sync ordering, domain scoping, and replay rules.
- [`08-network-transport-requirements.md`](08-network-transport-requirements.md) - Transport constraints for sync traffic.
- [`09-dos-guard-and-client-puzzles.md`](09-dos-guard-and-client-puzzles.md) - Admission control and client puzzle requirements.
- [`10-errors-and-failure-modes.md`](10-errors-and-failure-modes.md) - Failure classification and rejection ordering.
- [`11-versioning-and-compatibility.md`](11-versioning-and-compatibility.md) - Versioning and compatibility rules.

Each document has a corresponding meta specification in [`10-appendix/meta/01-protocol/`](../10-appendix/meta/01-protocol/).

## How to read

1. Start with [`00-protocol-overview.md`](00-protocol-overview.md) for the end-to-end lifecycle and invariants.
2. Read [`02-object-model.md`](02-object-model.md), then [`03-serialization-and-envelopes.md`](03-serialization-and-envelopes.md) to learn structure and format.
3. Use [`04-cryptography.md`](04-cryptography.md) and [`05-keys-and-identity.md`](05-keys-and-identity.md) for trust and key rules.
4. Read [`06-access-control-model.md`](06-access-control-model.md) for authorization semantics.
5. Use [`07-sync-and-consistency.md`](07-sync-and-consistency.md) through [`10-errors-and-failure-modes.md`](10-errors-and-failure-modes.md) for sync and failure rules.
6. Finish with [`11-versioning-and-compatibility.md`](11-versioning-and-compatibility.md) for evolution constraints.

## Key guarantees this folder enforces

- App namespaces are isolated; app semantics do not implicitly cross boundaries.
- All writes use graph message envelopes, including local writes.
- Structural validation precedes schema validation and ACL enforcement.
- Cryptographic verification precedes semantic processing for remote input.
- Graph Manager is the only write path; Storage Manager is the only raw database path.
- All request-scoped work is bound to a complete [`OperationContext`](../02-architecture/services-and-apps/05-operation-context.md).
- Authorization is deterministic and local; transport metadata is not authoritative.
- Accepted writes are assigned a monotonic `global_seq` and applied transactionally.
- State Manager is the only producer and consumer of sync packages.
- DoS Guard admission control precedes Network Manager processing.
- Sync ordering is monotonic per peer and per domain; replay and out-of-order input is rejected.
- Rejection is atomic and produces no persistent changes or sync state advancement.
- Private keys are not serialized into the graph or emitted in sync packages.
- Version negotiation is strict; no implicit downgrade or feature guessing is permitted.

## Using this folder in reviews

- Treat any write path that bypasses envelopes or Graph Manager as non-compliant.
- Treat transport-derived authorization as a correctness defect.
- Ensure rejection order matches the protocol’s validation precedence.
