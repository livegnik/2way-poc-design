



# 00 Managers Overview

## 1. Purpose and scope

This document provides an implementation-ready overview of every backend manager in 2WAY and explains how the manager fabric fits together across responsibilities, invariants, lifecycle dependencies, and shared execution flows. It complements the detailed component specifications and the rest of the architecture corpus by aggregating the big-picture guidance needed before diving into the per-manager files. It does not redefine the individual contracts; instead it stitches them together so engineers and reviewers can see the system-wide shape and enforce the same fail-closed posture everywhere.

This overview references:

* [01-protocol/**](../../01-protocol/)
* [02-architecture/00-architecture-overview.md](../../../../02-architecture/00-architecture-overview.md)
* [02-architecture/01-component-model.md](../../../../02-architecture/01-component-model.md)
* [02-architecture/02-runtime-topologies.md](../../../../02-architecture/02-runtime-topologies.md)
* [02-architecture/03-trust-boundaries.md](../../../../02-architecture/03-trust-boundaries.md)
* [02-architecture/04-data-flow-overview.md](../../../../02-architecture/04-data-flow-overview.md)
* [02-architecture/managers/**](../managers/)
* [02-architecture/services-and-apps/**](../services-and-apps/)
* [04-interfaces/**](../../04-interfaces/)

This specification consumes the protocol contracts defined in:

* [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md)
* [01-protocol/01-identifiers-and-namespaces.md](../../../../01-protocol/01-identifiers-and-namespaces.md)
* [01-protocol/02-object-model.md](../../../../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/04-cryptography.md](../../../../01-protocol/04-cryptography.md)
* [01-protocol/05-keys-and-identity.md](../../../../01-protocol/05-keys-and-identity.md)
* [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/08-network-transport-requirements.md](../../../../01-protocol/08-network-transport-requirements.md)
* [01-protocol/09-dos-guard-and-client-puzzles.md](../../../../01-protocol/09-dos-guard-and-client-puzzles.md)
* [01-protocol/10-errors-and-failure-modes.md](../../../../01-protocol/10-errors-and-failure-modes.md)
* [01-protocol/11-versioning-and-compatibility.md](../../../../01-protocol/11-versioning-and-compatibility.md)

Those files remain normative for all behaviors described here.

If you are building or auditing the backend, start here to understand the manager fabric before diving into the dedicated specifications:

| Section | Description |
| --- | --- |
| Section 2 | Cross-cutting invariants that every manager must uphold. |
| Section 3 | Manager catalog, lifecycle stages, and dependency graph. |
| Section 4 | Critical execution flows (write path, read path, sync path, configuration reload, observability). |
| Section 5 | Detailed per-manager summaries ([Config Manager](../../../../02-architecture/managers/01-config-manager.md) through [DoS Guard Manager](../../../../02-architecture/managers/14-dos-guard-manager.md)). |
| Section 6 | Startup and shutdown ordering. |
| Section 7 | [OperationContext](../../../../02-architecture/services-and-apps/05-operation-context.md) and trust-boundary enforcement across managers. |
| Section 8 | Observability, readiness, and failure-handling posture. |
| Section 9 | Implementation checklist for engineers wiring the managers together. |

## 2. Implementation checklist example

A short example checklist for wiring the managers together or reviewing an implementation:

1. **Configuration**: Are all managers reading configuration exclusively via [Config Manager](../../../../02-architecture/managers/01-config-manager.md) snapshots? Are settings keys registered with reload policies and owner namespaces?
2. **Start order**: Does the runtime enforce the startup sequence from Section 6? Are dependencies checked before readiness?
3. **[OperationContext](../../../../02-architecture/services-and-apps/05-operation-context.md) usage**: Does every entrypoint authenticate via [Auth Manager](../../../../02-architecture/managers/04-auth-manager.md) (local) or the [Network Manager](../../../../02-architecture/managers/10-network-manager.md) + [State Manager](../../../../02-architecture/managers/09-state-manager.md) pipeline (remote) before invoking [Graph Manager](../../../../02-architecture/managers/07-graph-manager.md)/[ACL Manager](../../../../02-architecture/managers/06-acl-manager.md)?
4. **[Graph Manager](../../../../02-architecture/managers/07-graph-manager.md) write path**: Does every mutation route through [Graph Manager](../../../../02-architecture/managers/07-graph-manager.md) and maintain the structural -> schema -> [ACL Manager](../../../../02-architecture/managers/06-acl-manager.md) -> persistence order?
5. **Sync**: Are inbound envelopes admitted only after [DoS Guard Manager](../../../../02-architecture/managers/14-dos-guard-manager.md) admission and signature verification at the transport boundary (with decryption via [Key Manager](../../../../02-architecture/managers/03-key-manager.md) when required), and is [State Manager](../../../../02-architecture/managers/09-state-manager.md) coordinating ordering before [Graph Manager](../../../../02-architecture/managers/07-graph-manager.md)?
6. **Logging/events**: Are logs routed only through [Log Manager](../../../../02-architecture/managers/12-log-manager.md), and are event descriptors emitted only post-commit? Are [Event Manager](../../../../02-architecture/managers/11-event-manager.md) queues bounded with enforceable limits?
7. **Security**: Are keys confined to [Key Manager](../../../../02-architecture/managers/03-key-manager.md)? Are DoS puzzles opaque to other managers? Are [ACL Manager](../../../../02-architecture/managers/06-acl-manager.md) decisions centralized?
8. **Observability**: Are [Config Manager](../../../../02-architecture/managers/01-config-manager.md) reloads, health transitions, network admissions, [ACL Manager](../../../../02-architecture/managers/06-acl-manager.md) denials, and schema reloads emitting logs/events per spec?
9. **Failure handling**: Does every manager fail closed on dependency loss (for example, [DoS Guard Manager](../../../../02-architecture/managers/14-dos-guard-manager.md) forcing `deny`, [Health Manager](../../../../02-architecture/managers/13-health-manager.md) forcing readiness false, [Config Manager](../../../../02-architecture/managers/01-config-manager.md) veto halting reload)?
10. **Testing hooks**: Are bootstrap/diagnostic modes limited and still enforced via [OperationContext](../../../../02-architecture/services-and-apps/05-operation-context.md) + [ACL Manager](../../../../02-architecture/managers/06-acl-manager.md), with no shortcuts that bypass these managers?
