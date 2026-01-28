



# 05 Operation Context

## 1. Purpose and scope

OperationContext is the immutable per-request envelope that binds identity, application, capability intent, trust posture, execution origin, and trace metadata to every backend action. It is the single authoritative structure used by managers to enforce authorization, app isolation, auditability, and local versus remote semantics. No service, extension, or manager that executes request-scoped work may be invoked without a complete and valid OperationContext.

This overview defines the required fields, construction rules, lifecycle behavior, and consumption requirements for OperationContext across frontend requests, system services, app backend extensions, automation jobs, internal engines, and remote synchronization handling. It is the canonical source for OperationContext semantics referenced throughout the protocol and architecture, aligned with the component responsibilities in [02-architecture/01-component-model.md](../01-component-model.md) and the data flow posture in [02-architecture/04-data-flow-overview.md](../04-data-flow-overview.md), and complemented by manager and service specifications under [02-architecture/managers/**](../managers/) and [02-architecture/services-and-apps/**](./).

This overview references:

* [01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md)
* [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md)
* [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md)
* [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md)
* [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md)
* [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md)
* [02-architecture/01-component-model.md](../01-component-model.md)
* [02-architecture/04-data-flow-overview.md](../04-data-flow-overview.md)
* [02-architecture/managers/**](managers/)
* [02-architecture/managers/04-auth-manager.md](../managers/04-auth-manager.md)
* [02-architecture/managers/06-acl-manager.md](../managers/06-acl-manager.md)
* [02-architecture/managers/07-graph-manager.md](../managers/07-graph-manager.md)
* [02-architecture/managers/08-app-manager.md](../managers/08-app-manager.md)
* [02-architecture/managers/09-state-manager.md](../managers/09-state-manager.md)
* [02-architecture/managers/10-network-manager.md](../managers/10-network-manager.md)
* [02-architecture/managers/11-event-manager.md](../managers/11-event-manager.md)
* [02-architecture/managers/12-log-manager.md](../managers/12-log-manager.md)
* [02-architecture/managers/14-dos-guard-manager.md](../managers/14-dos-guard-manager.md)
* [02-architecture/services-and-apps/**](./)
* [02-architecture/services-and-apps/01-services-vs-apps.md](01-services-vs-apps.md)
* [02-architecture/services-and-apps/03-app-backend-extensions.md](03-app-backend-extensions.md)
* [02-architecture/services-and-apps/04-frontend-apps.md](04-frontend-apps.md)

### 1.1 Responsibilities and boundaries

This overview is responsible for the following:

* Defining the canonical OperationContext structure and the semantics of every field.
* Declaring deterministic construction rules for local execution paths and remote sync paths.
* Defining immutability rules and lifecycle guarantees.
* Specifying how services and internal engines may derive enriched contexts without mutating identity bindings, aligned with identity and key rules in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).
* Defining how OperationContext is consumed by [Graph Manager](../managers/07-graph-manager.md), [ACL Manager](../managers/06-acl-manager.md), [State Manager](../managers/09-state-manager.md), [Event Manager](../managers/11-event-manager.md), and [Log Manager](../managers/12-log-manager.md).
* Defining failure and rejection posture for malformed or incomplete contexts.

This overview does not cover the following:

* Schema definitions, ACL rule syntax, or envelope serialization formats.
* Cryptographic verification, handshake protocols, or transport-level concerns.
* Application UX behavior or frontend configuration beyond required context fields.
