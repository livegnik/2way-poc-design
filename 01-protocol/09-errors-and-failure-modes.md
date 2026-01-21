



## 09. Errors and Failure Modes

### 1. Purpose and scope

This document defines the errors and failure modes of the 2WAY protocol at the protocol boundary. It specifies how invalid input, rejected operations, and failure conditions are classified, detected, and reported. The scope is limited to protocol-level error semantics and observable behavior. It does not define transport formats, API payloads, logging, or user-facing presentation.

This specification references:

* [01-identifiers-and-namespaces.md](01-identifiers-and-namespaces.md)
* [02-object-model.md](02-object-model.md)
* [03-serialization-and-envelopes.md](03-serialization-and-envelopes.md)
* [04-cryptography.md](04-cryptography.md)
* [05-keys-and-identity.md](05-keys-and-identity.md)
* [06-access-control-model.md](06-access-control-model.md)
* [07-sync-and-consistency.md](07-sync-and-consistency.md)
* [08-network-transport-requirements.md](08-network-transport-requirements.md)
* [11-dos-guard-and-client-puzzles.md](11-dos-guard-and-client-puzzles.md)

### 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining the canonical set of protocol-level error classes and symbolic error codes.
* Defining when an operation, [envelope](03-serialization-and-envelopes.md), or [sync package](07-sync-and-consistency.md) must be rejected.
* Defining invariants around rejection behavior and state safety.
* Defining guarantees about side effects in the presence of failure.
* Defining how failures are surfaced across trust boundaries (see [08-network-transport-requirements.md](08-network-transport-requirements.md)).

This specification does not cover the following:

* UI error messages or localization.
* HTTP status codes or [transport-specific representations](08-network-transport-requirements.md).
* Internal logging formats or telemetry.
* Retry strategies, backoff policies, or scheduling.
* Component-internal exceptions that do not cross protocol boundaries.

### 3. Invariants and guarantees

The following invariants apply to all failures defined in this file:

* No rejected operation produces persistent state changes.
* No rejected operation advances global or domain sequence counters.
* Validation failures are deterministic for identical inputs and state.
* Rejection reason depends only on [envelope](03-serialization-and-envelopes.md) content and local state.
* Rejected remote input is never re-broadcast or re-synced (see [07-sync-and-consistency.md](07-sync-and-consistency.md)).

The protocol guarantees:

* Structural invalidity is detected before [authorization](06-access-control-model.md) checks.
* Authorization failure is detected before any write attempt.
* [Sync integrity](07-sync-and-consistency.md) violations are detected before [object](02-object-model.md) materialization.
* [Revocation state](05-keys-and-identity.md) takes precedence over ordering and freshness.

### 4. Allowed and forbidden behaviors

#### 4.1 Allowed behaviors

The protocol allows:

* Silent rejection of invalid remote input.
* Early rejection without expensive validation.
* Disconnection of peers that repeatedly trigger fatal failures.
* Independent local enforcement of rejection rules per node.

#### 4.2 Forbidden behaviors

The protocol forbids:

* Partial application of an invalid operation.
* Automatic correction or mutation of invalid input.
* Acceptance of objects with unverifiable authorship (see [05-keys-and-identity.md](05-keys-and-identity.md)).
* Acceptance of operations signed by revoked keys (see [05-keys-and-identity.md](05-keys-and-identity.md)).
* Acceptance of out-of-order or replayed [sync packages](07-sync-and-consistency.md).

### 5. Error classification

Errors are classified by the validation stage that detects them. Each operation or sync package may produce at most one protocol-level error.

#### 5.1 Structural errors

Structural errors indicate that an [envelope](03-serialization-and-envelopes.md) or [package](07-sync-and-consistency.md) is not well-formed.

* Missing required envelope fields. `ERR_STRUCT_MISSING_FIELD`
* Invalid object types or unknown object kinds. `ERR_STRUCT_INVALID_TYPE`
* Invalid encoding or representation markers. `ERR_STRUCT_INVALID_ENCODING`
* Invalid or missing identifiers. `ERR_STRUCT_INVALID_IDENTIFIER`

Structural errors are terminal for the input and must be rejected immediately.

#### 5.2 Cryptographic and identity errors

Cryptographic errors indicate that identity or authorship cannot be verified (see [04-cryptography.md](04-cryptography.md) and [05-keys-and-identity.md](05-keys-and-identity.md)).

* Invalid or unverifiable signature. `ERR_CRYPTO_INVALID_SIGNATURE`
* Missing author identity reference. `ERR_CRYPTO_MISSING_AUTHOR`
* Public key not present or not bound to the author [Parent](02-object-model.md). `ERR_CRYPTO_KEY_NOT_BOUND`
* Signature mismatch with declared author. `ERR_CRYPTO_AUTHOR_MISMATCH`
* Use of a revoked or superseded key. `ERR_CRYPTO_KEY_REVOKED`

Cryptographic errors are terminal and indicate untrusted input.

#### 5.3 Schema and domain errors

Schema errors indicate that an operation violates [schema](../02-architecture/managers/05-schema-manager.md) or domain constraints.

* Object type not allowed in the declared app or domain. `ERR_SCHEMA_TYPE_NOT_ALLOWED`
* Attribute value does not match declared representation. `ERR_SCHEMA_INVALID_VALUE`
* Edge type not permitted between the referenced Parents. `ERR_SCHEMA_EDGE_NOT_ALLOWED`
* Operation targets an immutable object. `ERR_SCHEMA_IMMUTABLE_OBJECT`
* Operation violates append-only domain constraints. `ERR_SCHEMA_APPEND_ONLY_VIOLATION`

Schema errors are terminal for the operation.

#### 5.4 Authorization errors

Authorization errors indicate that the author identity lacks permission (see [06-access-control-model.md](06-access-control-model.md)).

* Write attempted on an object not owned by the author. `ERR_AUTH_NOT_OWNER`
* ACL evaluation denies the requested action. `ERR_AUTH_ACL_DENIED`
* Device key exceeds its delegated authority. `ERR_AUTH_SCOPE_EXCEEDED`
* Domain visibility rules deny access. `ERR_AUTH_VISIBILITY_DENIED`

Authorization errors are terminal and must not leak additional state.

#### 5.5 Sync integrity errors

Sync integrity errors indicate invalid replication behavior (see [07-sync-and-consistency.md](07-sync-and-consistency.md)).

* Declared sequence ranges do not match package contents. `ERR_SYNC_RANGE_MISMATCH`
* Sequence numbers regress or overlap previously accepted ranges. `ERR_SYNC_SEQUENCE_INVALID`
* Package attempts to rewrite existing objects. `ERR_SYNC_REWRITE_ATTEMPT`
* Package omits required dependency objects. `ERR_SYNC_MISSING_DEPENDENCY`
* Package violates domain sync boundaries. `ERR_SYNC_DOMAIN_VIOLATION`

Sync integrity errors invalidate the entire package.

#### 5.6 Resource and load errors

Resource errors indicate local inability to process input safely (see [11-dos-guard-and-client-puzzles.md](11-dos-guard-and-client-puzzles.md)).

* Rate limits exceeded. `ERR_RESOURCE_RATE_LIMIT`
* Peer exceeds allowed request frequency. `ERR_RESOURCE_PEER_LIMIT`
* Client puzzle requirements not satisfied. `ERR_RESOURCE_PUZZLE_FAILED`

Resource errors may be transient but never permit partial processing.

### 6. Failure handling behavior

#### 6.1 Rejection behavior

On any failure:

* The input is rejected in full.
* No objects are created, modified, or deleted.
* No sequence counters are advanced.
* No derived or secondary actions are triggered.

#### 6.2 Failure precedence

When multiple violations are present:

* Structural errors take precedence over all others.
* Cryptographic errors take precedence over [schema](../02-architecture/managers/05-schema-manager.md) and [authorization](06-access-control-model.md).
* [Revocation state](05-keys-and-identity.md) takes precedence over ordering and freshness.
* [Schema](../02-architecture/managers/05-schema-manager.md) errors take precedence over authorization errors.

The first applicable failure class determines the rejection.

#### 6.3 Interaction with components

Failures are detected at specific trust boundaries:

* [Graph Manager](../02-architecture/managers/07-graph-manager.md) detects structural and [ownership](02-object-model.md) violations.
* [Schema Manager](../02-architecture/managers/05-schema-manager.md) detects schema and domain violations.
* [ACL Manager](../02-architecture/managers/06-acl-manager.md) detects authorization violations.
* [State Manager](../02-architecture/managers/09-state-manager.md) detects sync integrity violations.
* [Network Manager](../02-architecture/managers/10-network-manager.md) enforces rate and peer-level constraints.

Each component may reject input only within its responsibility boundary.

### 7. Peer-facing behavior

For remote peers:

* Rejected input may be silently dropped.
* Repeated fatal violations may result in peer disconnect.
* Nodes are not required to explain rejection reasons.
* Nodes must not echo rejected input back to the sender.

For local callers:

* Rejection reason must be surfaced explicitly using the symbolic error code.
* No side effects may be observable after rejection.

### 8. Absence of recovery semantics

This specification defines no automatic recovery behavior.

* Recovery from failure is external to the protocol.
* Rejected input must be corrected and resubmitted.
* Sync resumes only after invalid packages are discarded.

Key recovery and revocation semantics are defined in [05-keys-and-identity.md](05-keys-and-identity.md) and are not redefined here.

### 9. Explicit exclusions

The following are explicitly out of scope:

* User-facing error descriptions.
* Transport-specific failure codes.
* Logging verbosity or retention.
* Debug or diagnostic interfaces.
