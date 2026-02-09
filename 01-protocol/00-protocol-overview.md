



# 00 Protocol overview

Defines the protocol posture and lifecycle for 2WAY graph mutations and sync. Specifies validation ordering, authorization gates, and sync sequencing requirements. Summarizes required guarantees, forbidden paths, and compatibility rules.

For the meta specifications, see [00-protocol-overview meta](../10-appendix/meta/01-protocol/00-protocol-overview-meta.md).

## 1. Protocol posture and guiding principles

* All graph mutations use [graph message envelopes](03-serialization-and-envelopes.md), including local writes, so local and remote paths share the same validation and persistence pipeline.
* [Graph Manager](../02-architecture/managers/07-graph-manager.md) is the only write path. [Storage Manager](../02-architecture/managers/02-storage-manager.md) is the only raw database path. No component may bypass these boundaries.
* The network is untrusted. Trust is established only via [cryptographic verification](04-cryptography.md) and local policy enforcement.
* Authorization is deterministic and local. It is enforced before persistence and before advancing [sync state](07-sync-and-consistency.md).
* Synchronization is incremental and sequence-anchored. A receiver must reject replayed, out-of-order, malformed, or policy-violating packages without side effects (see [07-sync-and-consistency.md](07-sync-and-consistency.md)).
* App namespaces are isolated. Each app defines its own types, ratings, and domain semantics, and those semantics cannot spill into other apps without explicit interpretation by a consuming app.

## 2. Operation lifecycle

### 2.1 Authoring and local submission

* A local frontend request authenticates via an auth token.
* [Auth Manager](../02-architecture/managers/04-auth-manager.md) resolves the auth token to an `identity_id`.
* The HTTP layer constructs an [OperationContext](../02-architecture/services-and-apps/05-operation-context.md) containing, at minimum, requester identity, `app_id`, a remote or local flag, and a trace id.
* The caller submits a [graph message envelope](03-serialization-and-envelopes.md) for all writes, even locally.
* Local automation jobs or internal services construct an [OperationContext](../02-architecture/services-and-apps/05-operation-context.md) with `is_remote=false` before submitting envelopes, following the same authorization and ordering rules as interactive requests.

### 2.2 Envelope construction and structural validation

* An [envelope](03-serialization-and-envelopes.md) contains one or more operations with supervised operation identifiers, using lowercase snake_case naming conventions.
* Structural validation runs before [schema validation](../02-architecture/managers/05-schema-manager.md) and before [ACL evaluation](06-access-control-model.md).
* Structural validation must reject malformed envelopes without allocating expensive resources or taking write locks.

### 2.3 Schema validation and authorization

* [Schema Manager](../02-architecture/managers/05-schema-manager.md) validates that referenced types belong to the declared app namespace, that values match their declared representation, and that relations respect allowed edge constraints.
* [ACL Manager](../02-architecture/managers/06-acl-manager.md) evaluates permissions using [OperationContext](../02-architecture/services-and-apps/05-operation-context.md), schema defaults, object-level overrides, and ownership semantics.
* If the envelope declares an author identity, the implementation must enforce that the author identity used for enforcement is explicit and consistent with the authenticated context, and must not be inferred from transport metadata.

### 2.4 Sequencing and persistence

* [Graph Manager](../02-architecture/managers/07-graph-manager.md) assigns a monotonic `global_seq` during successful application.
* Envelope application is transactional. Either the entire envelope is applied or none of it is.
* Persistence occurs only through [Storage Manager](../02-architecture/managers/02-storage-manager.md) after successful structural validation, schema validation, and authorization.

### 2.5 Remote synchronization

* [State Manager](../02-architecture/managers/09-state-manager.md) is the only producer of outbound sync packages and the only consumer of inbound sync packages.
* Remote sync uses the same [graph message envelope](03-serialization-and-envelopes.md) format as local writes, wrapped with sync metadata, including sender identity, sync domain name, and a declared sequence range such as `from_seq` and `to_seq`.
* [DoS Guard Manager](../02-architecture/managers/14-dos-guard-manager.md) enforces admission control and client puzzles before [Network Manager](../02-architecture/managers/10-network-manager.md) processes inbound connections, per [09-dos-guard-and-client-puzzles.md](09-dos-guard-and-client-puzzles.md).
* [Network Manager](../02-architecture/managers/10-network-manager.md) handles transport and cryptography, including signature creation and verification, and ECIES encryption where confidentiality is required (see [04-cryptography.md](04-cryptography.md)).
* The receiver enforces per-peer, per-domain ordering rules and must reject packages that are replayed, out of order, malformed, or inconsistent with known sync state.

## 3. Guarantees and invariants

* Every accepted envelope is validated structurally, validated against [schema rules](../02-architecture/managers/05-schema-manager.md), authorized via [ACL evaluation](06-access-control-model.md), and applied transactionally.
* [Graph Manager](../02-architecture/managers/07-graph-manager.md) is the only write path for Parents, Attributes, Edges, Ratings, and ACL-related mutations.
* All accepted writes receive a monotonic `global_seq`.
* [Sync ordering](07-sync-and-consistency.md) is monotonic per peer and per domain. Sync state advances only after successful envelope application.
* [Cryptographic verification](04-cryptography.md) precedes semantic processing for remote input. Unsigned or invalidly signed packages are rejected.
* Private keys are not serialized into the graph and are not emitted inside sync packages.

## 4. Allowed and forbidden behaviors

### 4.1 Allowed

* Local writes via HTTP using [graph message envelopes](03-serialization-and-envelopes.md), with authorization based on [OperationContext](../02-architecture/services-and-apps/05-operation-context.md).
* Remote sync via [State Manager](../02-architecture/managers/09-state-manager.md) using signed and optionally encrypted packages carrying graph envelopes and domain sequence metadata (see [04-cryptography.md](04-cryptography.md)).
* Multiple keys per identity and multi-device operation, provided authorization and key binding rules are enforced per the [identity specification](05-keys-and-identity.md).
* Silent rejection of invalid remote input while continuing to process other peers.

### 4.2 Forbidden

* Any mutation path that bypasses [graph message envelopes](03-serialization-and-envelopes.md) or bypasses [Graph Manager](../02-architecture/managers/07-graph-manager.md).
* Any direct database write outside [Storage Manager](../02-architecture/managers/02-storage-manager.md).
* Any authorization decision based on transport metadata or remote assertions not validated against local identity and [ACL state](06-access-control-model.md).
* Partial application of an envelope, or advancing sync state after a rejection.
* Accepting remote packages without [cryptographic verification](04-cryptography.md), or attempting to "guess" missing metadata to recover from failures.

## 5. Failure posture

* Rejection is atomic. A rejected envelope or package produces no state changes and does not advance sync state.
* Failures are classified by the earliest stage that detects them, including structural, cryptographic, schema, authorization, [sync ordering](07-sync-and-consistency.md), and resource constraints.
* Precedence is strict. Structural failures preempt schema and [ACL checks](06-access-control-model.md). Cryptographic failures preempt semantic processing. [Revocation decisions](05-keys-and-identity.md) override freshness decisions and must be applied before processing additional envelopes where applicable.
* Debugging and inspection surfaces are read-only and must remain behind administrative authorization.

## 6. Compatibility and evolution

* Protocol versions use `(major, minor, patch)` tuples.
* Major mismatches are fatal. Version negotiation occurs before trust or state exchange.
* No implicit downgrade, feature guessing, or fallback mode is permitted.
* Naming conventions for envelopes, domains, and events are normative and must remain consistent to preserve compatibility across nodes and tools.
