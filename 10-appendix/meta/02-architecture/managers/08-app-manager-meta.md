



# 08 App Manager

## 1. Purpose and scope

The App Manager is the authoritative component responsible for the scope described below. This document specifies the App Manager component. The App Manager is responsible for defining, registering, resolving, and wiring applications within the backend. It establishes applications as first class system entities, assigns them stable identifiers, binds them to cryptographic identities, initializes their storage namespaces, and controls the loading and isolation of app services.

This specification applies strictly to backend application lifecycle management and application identity resolution. It defines no frontend behavior, no schemas, no access control rules, no network behavior, and no application domain logic.

This specification consumes the protocol contracts defined in:

* [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md)
* [01-protocol/01-identifiers-and-namespaces.md](../../../../01-protocol/01-identifiers-and-namespaces.md)
* [01-protocol/02-object-model.md](../../../../01-protocol/02-object-model.md)
* [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md)
* [01-protocol/05-keys-and-identity.md](../../../../01-protocol/05-keys-and-identity.md)
* [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md)

Those files remain normative for all behaviors described here.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Maintaining the authoritative registry of locally installed applications, providing the declaration-before-use guarantees required by [01-protocol/01-identifiers-and-namespaces.md](../../../../01-protocol/01-identifiers-and-namespaces.md).
* Assigning stable, monotonic numeric `app_id` values exactly as mandated by [01-protocol/01-identifiers-and-namespaces.md](../../../../01-protocol/01-identifiers-and-namespaces.md).
* Binding application slugs to application identities in the graph so that identity guarantees in [01-protocol/05-keys-and-identity.md](../../../../01-protocol/05-keys-and-identity.md) remain enforceable.
* Validating app registration artifacts (manifest and detached signature) using slug-first identity rules before `app_id` assignment.
* Resolving `publisher_public_key` from install artifacts against existing graph identities and requiring publisher trust before registration proceeds.
* Persisting and enforcing lifecycle metadata (`lifecycle_state`, `enabled`, `version`) in addition to immutable identity metadata (`app_id`, `slug`).
* Enforcing the lifecycle transition matrix used by app lifecycle interfaces.
* Initializing per application storage structures without violating the per-app isolation constraints in [01-protocol/02-object-model.md](../../../../01-protocol/02-object-model.md).
* Ensuring application identity presence and consistency in the system graph according to the identity and key rules in [01-protocol/05-keys-and-identity.md](../../../../01-protocol/05-keys-and-identity.md).
* Loading, wiring, and isolating app services without letting them bypass the authorization posture defined in [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md).
* Requiring `app-service/` payloads for `service`/`hybrid` apps and starting staged app services only after validation and commit succeed.
* Providing application metadata and resolution services to other backend components so the `app_id` semantics required by [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md) and the [OperationContext](../../../../02-architecture/services-and-apps/05-operation-context.md) construction rules in [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md) stay deterministic.
* Enforcing strict application isolation at the manager wiring level, restating the namespace isolation guarantees in [01-protocol/01-identifiers-and-namespaces.md](../../../../01-protocol/01-identifiers-and-namespaces.md) and [01-protocol/02-object-model.md](../../../../01-protocol/02-object-model.md).
* Declaring application identifiers before they may appear in schemas, [OperationContext](../../../../02-architecture/services-and-apps/05-operation-context.md) instances, or graph envelopes, satisfying [01-protocol/01-identifiers-and-namespaces.md](../../../../01-protocol/01-identifiers-and-namespaces.md), [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md), and [01-protocol/03-serialization-and-envelopes.md](../../../../01-protocol/03-serialization-and-envelopes.md).
* Ensuring application lifecycle ordering relative to other managers during startup and shutdown so [OperationContext](../../../../02-architecture/services-and-apps/05-operation-context.md) binding and request handling stay consistent with [01-protocol/00-protocol-overview.md](../../../../01-protocol/00-protocol-overview.md).

This specification does not cover the following:

* Schema definition, compilation, or validation, which remain the responsibility of [Schema Manager](../../../../02-architecture/managers/05-schema-manager.md) and the object and schema semantics referenced by [01-protocol/02-object-model.md](../../../../01-protocol/02-object-model.md).
* Access control evaluation or policy definition, which are governed by [01-protocol/06-access-control-model.md](../../../../01-protocol/06-access-control-model.md).
* Graph mutation logic.
* HTTP or WebSocket routing logic.
* Network transport or peer interaction.
* Cryptographic operations beyond delegation to [Key Manager](../../../../02-architecture/managers/03-key-manager.md), which remain governed by [01-protocol/04-cryptography.md](../../../../01-protocol/04-cryptography.md) and [01-protocol/05-keys-and-identity.md](../../../../01-protocol/05-keys-and-identity.md).
* Frontend application lifecycle, UI, or user workflows.
* Application business logic or domain semantics.
