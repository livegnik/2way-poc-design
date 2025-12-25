



# 09 State Manager

## 1. Purpose and scope

This document specifies the State Manager component within the 2WAY architecture. The State Manager coordinates the canonical local state that results from accepted graph envelopes, maintains protocol-mandated sync metadata, and enforces the ordering, durability, and recovery semantics required by the 2WAY protocol. Per `01-protocol/00-protocol-overview.md`, it is the only component permitted to originate outbound sync packages or ingest inbound sync packages, and it ensures that remote envelopes reach Graph Manager in the same deterministic order that they were authored.

This specification covers state handling semantics, sync state tracking, remote envelope routing, durability, and recovery. It does not redefine schema behavior, ACL rules, cryptographic verification, transport mechanics, or storage implementation details except where boundaries are needed to uphold protocol requirements.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

- Maintaining the authoritative record of committed graph state metadata (including `global_seq`, sync participation flags, and domain eligibility markers) produced by Graph Manager, consistent with the canonical object categories defined in `01-protocol/02-object-model.md`.
- Tracking per-peer, per-domain `sync_state` (highest accepted sequence, observed gaps, revocation status, and domain visibility) as mandated by `01-protocol/07-sync-and-consistency.md`.
- Serializing inbound remote envelopes after Network Manager verification, validating ordering metadata, constructing the required remote `OperationContext`, and submitting each envelope to Graph Manager for structural validation, schema validation, authorization, and persistence.
- Building outbound sync packages from committed envelopes, ensuring each package contains only persisted data, monotonic sequence ranges, and the metadata required by the receiving peer to advance its `sync_state`.
- Coordinating durable persistence of `sync_state`, commit markers, and recovery checkpoints through Storage Manager.
- Providing read-only state surfaces (such as snapshot queries, domain visibility tables, and sync progress monitors) to trusted internal components without exposing partially applied data.
- Managing rollback boundaries and refusing new mutations when ordering, durability, or sync guarantees cannot be met.
- Reconstructing state and sync metadata after restart exclusively from persisted storage.

This specification does not cover the following:

- Cryptographic verification, message authentication, or envelope signature handling; those responsibilities belong to Network Manager (`01-protocol/04-cryptography.md` and `01-protocol/05-keys-and-identity.md`).
- Schema resolution, authorization evaluation, or semantic validation of graph operations, which remain the responsibilities of Schema Manager, ACL Manager, and Graph Manager per their respective specifications.
- Direct mutation of canonical graph objects; per `01-protocol/00-protocol-overview.md` and `02-architecture/managers/07-graph-manager.md`, Graph Manager is the sole write path for Parents, Attributes, Edges, Ratings, and ACL structures.
- Assigning `global_seq` values or defining envelope structure; those rules are defined in `01-protocol/03-serialization-and-envelopes.md` and enforced by Graph Manager.
- Network transport, peer discovery, or policy decisions around peer throttling beyond the state gating required to protect ordering guarantees.
- Business logic, application-specific semantics, or derived analytics beyond deterministic, protocol-required state surfaces.

## 3. State domain and ownership

### 3.1 Canonical graph state

Canonical state consists of the persisted Parents, Attributes, Edges, Ratings, and ACL representations defined by `01-protocol/02-object-model.md`, along with the immutable metadata assigned at commit time (`app_id`, `owner_identity`, `global_seq`, `sync_flags`). Graph Manager is the only component that mutates this state. The State Manager consumes commit notifications and Storage Manager checkpoints to mirror the authoritative state height, to ensure sequencing metadata stays aligned, and to gate remote and local consumers on fully committed data only.

### 3.2 Sync metadata

For each `(peer_id, sync_domain)` pair the State Manager maintains:

- Highest accepted `global_seq`.
- Gap detection flags indicating whether a package was skipped.
- Known revocation or suspension status affecting the peer's eligibility.
- Domain visibility and export policy bindings.
- Outbound progress markers describing the last range transmitted.

This metadata is durably stored via Storage Manager, is authoritative for acceptance decisions per `01-protocol/07-sync-and-consistency.md`, and is never derived from unvalidated inputs.

### 3.3 Derived views and caches

The State Manager may maintain deterministic derived indices (for example, per-domain backlog queues or snapshot summaries) needed for correctness or performance. These structures:

- Are computed from committed canonical state and sync metadata only.
- Are immutable once persisted except through recomputation driven by Graph Manager commits.
- Can be rebuilt entirely from persisted graph and sync data during recovery.
- Never expose semantics that contradict the canonical object model or the access-control decisions enforced elsewhere.

## 4. Ordering and determinism

### 4.1 Local sequencing

Graph Manager enforces serialized writes and assigns monotonic `global_seq` values per `01-protocol/00-protocol-overview.md`. The State Manager does not allocate sequences; it observes the commit order and records the resulting sequence height, ensuring that every downstream consumer sees a single total order of committed envelopes. Local mutation requests are admitted only while the serialized write path is healthy, and the State Manager refuses to serve derived snapshots that would include partially committed state.

### 4.2 Per-peer sync ordering

For each remote peer and domain, the State Manager enforces:

- Strict monotonic advancement of the peer's declared `global_seq`.
- Rejection of envelopes that would replay, overlap, regress, or skip the expected next sequence, as required by `01-protocol/07-sync-and-consistency.md`.
- Deterministic rejection semantics so that identical inputs and identical local state always yield the same accept or reject result.

Incoming envelopes that violate ordering are rejected before Graph Manager is invoked, and the peer's sync stream is halted until the inconsistency is resolved or administrative intervention occurs.

### 4.3 Sync state advancement

Sync state advances only when Graph Manager reports that an envelope has been fully accepted, persisted, and assigned a `global_seq`. Rejected envelopes, failed structural validations, authorization denials, or persistence failures do not advance `sync_state` and do not mutate any canonical state, consistent with `01-protocol/07-sync-and-consistency.md` and `01-protocol/09-errors-and-failure-modes.md`. Any error surfaced while applying a remote envelope is recorded against the offending package but has no side effects beyond logging and peer health accounting.

## 5. Remote envelope handling

### 5.1 Inbound path

Inbound sync packages flow through the following stages:

1. Network Manager performs transport handling, signature verification, optional decryption, and identity resolution, per `01-protocol/04-cryptography.md` and `01-protocol/05-keys-and-identity.md`.
2. State Manager validates package metadata (peer identity, domain, declared sequence range) against local `sync_state`, rejects any package that violates ordering or policy, and buffers admissible packages per peer/domain.
3. For each envelope in a package, State Manager constructs an `OperationContext` flagged as remote, with `is_remote`, `sync_domain`, `remote_node_identity`, and trace identifiers populated exactly as described in `01-protocol/03-serialization-and-envelopes.md` and `02-architecture/managers/07-graph-manager.md`.
4. The envelope and constructed `OperationContext` are submitted to Graph Manager, which performs structural validation, schema validation, authorization, sequencing, and persistence.
5. Upon successful commit, the State Manager updates `sync_state`, records the acceptance outcome, and notifies outbound scheduling if new data must be relayed further. On failure, the package is marked rejected, `sync_state` remains unchanged, and the peer is signaled with the canonical error class without leaking additional internal state.

The State Manager never bypasses Graph Manager for remote inputs and never trusts transport metadata that was not validated via the Network Manager and local key material.

### 5.2 Outbound path

For outbound replication:

- The State Manager selects committed envelopes eligible for each peer based on domain visibility and revocation state.
- It constructs monotonic ranges (`from_seq`, `to_seq`) and attaches the metadata required by `01-protocol/03-serialization-and-envelopes.md` and `01-protocol/07-sync-and-consistency.md`.
- It never includes envelopes that have not been persisted or that violate ACL export policies.
- Packages are handed to Network Manager for signing and optional encryption. Only after Network Manager confirms transmission does the outbound progress marker advance.

### 5.3 Replay protection and auditing

All accepted and rejected packages are logged with peer identifiers, declared ranges, and resulting decision codes. These logs allow deterministic replay of acceptance decisions for auditing, consistent with the rejection behavior defined in `01-protocol/09-errors-and-failure-modes.md`.

## 6. Persistence and recovery

### 6.1 Durable sources

The State Manager relies on:

- Canonical graph data persisted through Storage Manager transactions driven by Graph Manager.
- Sync metadata tables persisted through Storage Manager.
- Checkpoints describing the last successfully exported or imported sequence per peer and domain.

No additional write path to storage is permitted.

### 6.2 Restart and recovery

On restart:

- The State Manager replays persisted sync metadata and reconstructs derived caches.
- It interrogates Storage Manager to determine the highest committed `global_seq` and validates that the stored sync metadata matches that height.
- Any divergence between persisted graph state and sync metadata results in a fail-fast condition that requires administrative repair; no guessing or inference of missing metadata is allowed, per the forbidden behavior listed in `01-protocol/00-protocol-overview.md`.

### 6.3 Rollback boundaries

If Storage Manager reports a failed transaction or if Graph Manager reports a persistence failure, the State Manager treats the envelope as not applied, retains the previous `sync_state`, and records the failure for diagnostics. There is no partial rollback; state either reflects the last committed version or the recovery process halts.

## 7. State access and exposure

### 7.1 Read-only surfaces

State Manager exposes read-only snapshots of:

- Sync progress per peer and domain.
- Domain visibility and export policy tables.
- Commit height and checkpoint metadata.

These surfaces are available only to trusted managers (for example, Network Manager for scheduling, Observability services, or administrative tooling) and never bypass ACL or schema rules governing the underlying graph data.

### 7.2 External visibility constraints

State Manager never exposes raw object payloads to remote peers. Remote peers receive only the envelope data already committed and authorized through Graph Manager, wrapped in sync packages whose metadata is constrained to the minimum required for ordering.

## 8. Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants hold:

- Graph Manager remains the sole writer of canonical graph objects. State Manager never mutates graph storage directly.
- The State Manager is the sole conduit for remote envelopes entering Graph Manager and for outbound sync packages, as mandated by `01-protocol/00-protocol-overview.md`.
- `sync_state` is authoritative, monotonic per peer and domain, and never regresses.
- Sync state advances only after successful Graph Manager commits; rejections or failures leave both canonical state and sync metadata unchanged.
- Outbound packages contain only committed envelopes and correct sequence ranges; no package skips a committed `global_seq` that the peer is authorized to receive.
- All state surfaces (local or exported) are derived from committed data and remain consistent after restarts because they can be reconstructed solely from persisted storage.

These guarantees must hold regardless of caller, execution context, input source, or peer behavior.

## 9. Explicitly allowed behaviors

The following behaviors are explicitly allowed:

- Buffering validated remote envelopes per peer while waiting for Graph Manager capacity, provided ordering is preserved.
- Temporarily suspending outbound or inbound sync for a peer when required to maintain ordering or durability guarantees.
- Replaying acceptance logs to audit or debug state divergence, without mutating state.
- Serving read-only sync progress summaries to internal observability or administrative tooling.
- Rebuilding derived caches or indices at startup or during maintenance windows using only persisted data.
- Rejecting remote envelopes that violate ordering, schema eligibility, or authorization once Graph Manager signals a rejection.

## 10. Explicitly forbidden behaviors

The following behaviors are explicitly forbidden:

- Applying mutations to canonical graph state outside Graph Manager or assigning `global_seq` values within State Manager.
- Advancing `sync_state` or transmitting sequence acknowledgments after a rejection or failure, contrary to `01-protocol/07-sync-and-consistency.md`.
- Guessing missing metadata, inferring remote intent, or attempting to repair ordering gaps by fabricating envelopes or sequence numbers, all of which are prohibited by `01-protocol/00-protocol-overview.md`.
- Accepting remote packages that have not passed Network Manager cryptographic verification.
- Exposing partially applied or speculative state to internal or external consumers.
- Allowing multiple writers to mutate `sync_state` concurrently or permitting untrusted components to observe mutable state without authorization.
- Including uncommitted envelopes, raw private key material, or schema definitions inside outbound packages.

## 11. Component interactions

### 11.1 Inputs

State Manager consumes:

- Validated sync packages from Network Manager, including peer identity, domain, and declared sequence ranges.
- Commit notifications and sequence assignments from Graph Manager.
- Transactional storage handles from Storage Manager to persist `sync_state` and derived metadata.
- Configuration data from Config Manager describing peer policies, domain visibility, and durability requirements.

### 11.2 Outputs

State Manager produces:

- Remote `OperationContext` instances and associated envelopes for Graph Manager.
- Outbound sync packages delivered to Network Manager.
- Sync progress and backlog metrics to Event Manager, Observability, or administrative tooling.
- Rejection or failure signals routed back to Network Manager for peer notification.

### 11.3 Trust boundaries

State Manager trusts:

- Network Manager for cryptographic authenticity and confidentiality of remote packages.
- Graph Manager for schema validation, authorization, and transactional persistence.
- Storage Manager for durable commits.

State Manager treats remote peers and transport metadata as untrusted, enforces protocol rules before forwarding anything to Graph Manager, and never accepts directives that would weaken those guarantees.

## 12. Failure handling

### 12.1 Ordering violations

Packages that regress, overlap, or skip the expected sequence are rejected with the sync error class defined in `01-protocol/09-errors-and-failure-modes.md`. The rejection is logged, `sync_state` remains unchanged, and the peer must resend the correct package.

### 12.2 Structural or semantic failures

If Graph Manager reports a structural, schema, ACL, or authorization failure while applying a remote envelope, the State Manager records the rejection reason, surfaces the canonical error code to the peer, and does not advance `sync_state`. Future envelopes from the peer continue from the last committed sequence.

### 12.3 Persistence failures

If Storage Manager or Graph Manager reports a persistence failure, the State Manager treats the envelope as not applied, halts inbound processing for that peer and domain, and raises an internal alert. Processing resumes only after storage health is restored.

### 12.4 Degraded operation

When durability guarantees cannot be met (for example, the storage subsystem is unavailable or checkpoints cannot be written), the State Manager refuses to accept new remote envelopes and halts outbound sync. Previously committed state may continue to be exposed in read-only form if it is safe to do so.

### 12.5 Recovery faults

Any mismatch detected during recovery between persisted `sync_state` and the canonical graph commit height results in a fatal startup failure that requires administrative repair. Silent divergence is not permitted.

## 13. Security considerations

The State Manager is a core integrity boundary. Violations of ordering, atomicity, or determinism can cause state divergence, replay vulnerabilities, or exposure of unauthorized data. The component must never weaken cryptographic, authorization, or schema guarantees enforced upstream, must not leak additional state through rejection surfaces, and must ensure that peer behavior cannot coerce it into mutating state outside the protocol-defined rules.

## 14. Compliance criteria

An implementation complies with this specification if it:

- Routes all remote envelopes through the Network Manager ➔ State Manager ➔ Graph Manager pipeline described above.
- Maintains `sync_state` exactly as defined in `01-protocol/07-sync-and-consistency.md`, advancing it only after Graph Manager commits.
- Never mutates canonical graph objects outside Graph Manager and never assigns `global_seq` values internally.
- Reconstructs state exclusively from persisted data after restart and rejects mismatches instead of guessing.
- Emits outbound packages that contain only committed, authorized envelopes with correct metadata.
- Enforces all forbidden behaviors listed in Section 10.

Failure to satisfy any of these criteria renders the implementation non-compliant with the protocol.
