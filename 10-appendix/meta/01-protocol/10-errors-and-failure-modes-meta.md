



# 10 Errors and Failure Modes

### 1. Purpose and scope

This document defines the errors and failure modes of the 2WAY protocol at the protocol boundary. It specifies how invalid input, rejected operations, and failure conditions are classified, detected, and reported. The scope is limited to protocol-level error semantics and observable behavior. It does not define [transport formats](../../../01-protocol/08-network-transport-requirements.md), API payloads, [logging](../../../02-architecture/managers/12-log-manager.md), or user-facing presentation.

This specification references:

* [01-identifiers-and-namespaces.md](../../../01-protocol/01-identifiers-and-namespaces.md)
* [02-object-model.md](../../../01-protocol/02-object-model.md)
* [03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)
* [04-cryptography.md](../../../01-protocol/04-cryptography.md)
* [05-keys-and-identity.md](../../../01-protocol/05-keys-and-identity.md)
* [06-access-control-model.md](../../../01-protocol/06-access-control-model.md)
* [07-sync-and-consistency.md](../../../01-protocol/07-sync-and-consistency.md)
* [08-network-transport-requirements.md](../../../01-protocol/08-network-transport-requirements.md)
* [09-dos-guard-and-client-puzzles.md](../../../01-protocol/09-dos-guard-and-client-puzzles.md)
* [04-error-model.md](../../../04-interfaces/04-error-model.md)

### 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining the canonical set of protocol-level error classes and symbolic error codes.
* Defining validation-stage order and deterministic precedence across failure classes.
* Defining a complete protocol `ERR_*` registry with rejection scope guidance.
* Defining when an operation, [envelope](../../../01-protocol/03-serialization-and-envelopes.md), or [sync package](../../../01-protocol/07-sync-and-consistency.md) must be rejected.
* Defining invariants around rejection behavior and state safety.
* Defining guarantees about side effects in the presence of failure.
* Defining how failures are surfaced across trust boundaries (see [08-network-transport-requirements.md](../../../01-protocol/08-network-transport-requirements.md)).
* Providing transport surfacing guidance to [04-error-model.md](../../../04-interfaces/04-error-model.md) where interface mapping is required.
* Distinguishing protocol-stage `ERR_*` symbols from interface service-availability families (`ERR_SVC_SYS_*`, `ERR_SVC_APP_*`) and forbidding bare family-root placeholders without specific suffixes.

This specification does not cover the following:

* UI error messages or localization.
* Authoritative [transport-specific representations](../../../01-protocol/08-network-transport-requirements.md) for each interface.
* Internal logging formats or [telemetry](../../../02-architecture/managers/11-event-manager.md).
* Retry strategies, backoff policies, or scheduling.
* Component-internal exceptions that do not cross protocol boundaries.

### 3. Absence of recovery semantics

Key recovery and revocation semantics are defined in [05-keys-and-identity.md](../../../01-protocol/05-keys-and-identity.md) and are not redefined here.

### 4. Explicit exclusions

The following are explicitly out of scope:

* User-facing error descriptions.
* [Transport-specific failure codes](../../../01-protocol/08-network-transport-requirements.md).
* [Logging verbosity](../../../02-architecture/managers/12-log-manager.md) or retention.
* Debug or diagnostic interfaces.
