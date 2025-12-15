



## 09. Errors and Failure Modes

### 1. Purpose and scope

This document defines the errors and failure modes of the 2WAY protocol at the protocol boundary. It specifies how invalid input, rejected operations, and failure conditions are classified, detected, and reported. The scope is limited to protocol-level error semantics and observable behavior. It does not define transport formats, API payloads, logging, or user-facing presentation.

### 2. Responsibilities

This specification is responsible for the following:

* Defining the canonical set of protocol-level error classes and symbolic error codes.
* Defining when an operation, envelope, or sync package must be rejected.
* Defining invariants around rejection behavior and state safety.
* Defining guarantees about side effects in the presence of failure.
* Defining how failures are surfaced across trust boundaries.

This specification does not cover the following:

* UI error messages or localization.
* HTTP status codes or transport-specific representations.
* Internal logging formats or telemetry.
* Retry strategies, backoff policies, or scheduling.
* Component-internal exceptions that do not cross protocol boundaries.

### 3. Invariants and guarantees

The following invariants apply to all failures defined in this file:

* No rejected operation produces persistent state changes.
* No rejected operation advances global or domain sequence counters.
* Validation failures are deterministic for identical inputs and state.
* Rejection reason depends only on envelope content and local state.
* Rejected remote input is never re-broadcast or re-synced.

The protocol guarantees:

* Structural invalidity is detected before authorization checks.
* Authorization failure is detected before any write attempt.
* Sync integrity violations are detected before object materialization.
* Revocation state takes precedence over ordering and freshness.

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
* Acceptance of objects with unverifiable authorship.
* Acceptance of operations signed by revoked keys.
* Acceptance of out-of-order or replayed sync packages.

### 5. Error classification

Errors are classified by the validation stage that detects them. Each operation or sync package may produce at most one protocol-level error.

#### 5.1 Structural errors

Structural errors indicate that an envelope or package is not well-formed.

* Missing required envelope fields. `ERR_STRUCT_MISSING_FIELD`
* Invalid object types or unknown object kinds. `ERR_STRUCT_INVALID_TYPE`
* Invalid encoding or representation markers. `ERR_STRUCT_INVALID_ENCODING`
* Invalid or missing identifiers. `ERR_STRUCT_INVALID_IDENTIFIER`

Structural errors are terminal for the input and must be rejected immediately.

#### 5.2 Cryptographic and identity errors

Cryptographic errors indicate that identity or authorship cannot be verified.

* Invalid or unverifiable signature. `ERR_CRYPTO_INVALID_SIGNATURE`
* Missing author identity reference. `ERR_CRYPTO_MISSING_AUTHOR`
* Public key not present or not bound to the author Parent. `ERR_CRYPTO_KEY_NOT_BOUND`
* Signature mismatch with declared author. `ERR_CRYPTO_AUTHOR_MISMATCH`
* Use of a revoked or superseded key. `ERR_CRYPTO_KEY_REVOKED`

Cryptographic errors are terminal and indicate untrusted input.

#### 5.3 Schema and domain errors

Schema errors indicate that an operation violates schema or domain constraints.

* Object type not allowed in the declared app or domain. `ERR_SCHEMA_TYPE_NOT_ALLOWED`
* Attribute value does not match declared representation. `ERR_SCHEMA_INVALID_VALUE`
* Edge type not permitted between the referenced Parents. `ERR_SCHEMA_EDGE_NOT_ALLOWED`
* Operation targets an immutable object. `ERR_SCHEMA_IMMUTABLE_OBJECT`
* Operation violates append-only domain constraints. `ERR_SCHEMA_APPEND_ONLY_VIOLATION`

Schema errors are terminal for the operation.

#### 5.4 Authorization errors

Authorization errors indicate that the author identity lacks permission.

* Write attempted on an object not owned by the author. `ERR_AUTH_NOT_OWNER`
* ACL evaluation denies the requested action. `ERR_AUTH_ACL_DENIED`
* Device key exceeds its delegated authority. `ERR_AUTH_SCOPE_EXCEEDED`
* Domain visibility rules deny access. `ERR_AUTH_VISIBILITY_DENIED`

Authorization errors are terminal and must not leak additional state.

#### 5.5 Sync integrity errors

Sync integrity errors indicate invalid replication behavior.

* Declared sequence ranges do not match package contents. `ERR_SYNC_RANGE_MISMATCH`
* Sequence numbers regress or overlap previously accepted ranges. `ERR_SYNC_SEQUENCE_INVALID`
* Package attempts to rewrite existing objects. `ERR_SYNC_REWRITE_ATTEMPT`
* Package omits required dependency objects. `ERR_SYNC_MISSING_DEPENDENCY`
* Package violates domain sync boundaries. `ERR_SYNC_DOMAIN_VIOLATION`

Sync integrity errors invalidate the entire package.

#### 5.6 Resource and load errors

Resource errors indicate local inability to process input safely.

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
* Cryptographic errors take precedence over schema and authorization.
* Revocation state takes precedence over ordering and freshness.
* Schema errors take precedence over authorization errors.

The first applicable failure class determines the rejection.

#### 6.3 Interaction with components

Failures are detected at specific trust boundaries:

* Graph Manager detects structural and ownership violations.
* Schema Manager detects schema and domain violations.
* ACL Manager detects authorization violations.
* State Manager detects sync integrity violations.
* Network Manager enforces rate and peer-level constraints.

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

Key recovery and revocation semantics are defined in the security specification and are not redefined here.

### 9. Explicit exclusions

The following are explicitly out of scope:

* User-facing error descriptions.
* Transport-specific failure codes.
* Logging verbosity or retention.
* Debug or diagnostic interfaces.
