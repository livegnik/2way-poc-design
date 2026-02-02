



# 03 Internal APIs between components

Defines the internal API contracts between managers and services in the 2WAY backend. These APIs are in-process, strongly ordered, and are not exposed externally.

For the meta specifications, see [03-internal-apis-between-components meta](../09-appendix/meta/04-interfaces/03-internal-apis-between-components-meta.md).

## 1. Purpose and scope

These APIs define how managers coordinate to implement protocol guarantees. They are designed to be deterministic, testable, and fail closed. All inputs are validated at the appropriate layer; no internal API may bypass required validation stages.

## 2. Cross-cutting contracts

### 2.1 OperationContext

All write paths must bind to an [OperationContext](../02-architecture/services-and-apps/05-operation-context.md) containing:

* `app_id`
* `actor_type`
* `is_remote`
* `trace_id`
* `requester_identity_id` or `remote_node_identity_id` as applicable

### 2.2 ErrorDetail

All manager-level failures use `ErrorDetail` from [04-error-model.md](04-error-model.md). Exceptions wrap ErrorDetail and are mapped to transport errors by interface layers.

## 3. Manager-level interfaces

### 3.1 Config Manager

**Responsibilities:** startup configuration loading, runtime reloads.

**Key API surface:**

* `load_startup()` -> returns validated snapshot.
* `load_reload()` -> returns validated snapshot and diff.

### 3.2 Storage Manager

**Responsibilities:** database lifecycle, migrations, persistence primitives.

**Key API surface:**

* `open()` / `close()`
* `transaction()` -> context manager returning a SQLite connection.
* `allocate_global_seq(conn)` -> int
* `enforce_app_limits(conn, app_id, ops_by_kind, payload_bytes)` -> None
* `get_sync_state(peer_id, domain)` / `set_sync_state(...)`
* `set_domain_seq(peer_id, domain, seq)`
* `create_app_tables(app_id)`
* `backup_to(path)` / `restore_from(path)`

### 3.3 Schema Manager

**Responsibilities:** schema compilation, type registry resolution.

**Key API surface:**

* `get_schema(app_id)` -> schema snapshot
* `resolve_type_id(app_id, kind, type_key)` -> int
* `resolve_type_key(app_id, kind, type_id)` -> str

### 3.4 ACL Manager

**Responsibilities:** authorization for graph writes.

**Key API surface:**

* `authorize_write(ctx, owner_identity)` -> None (raises on deny)

### 3.5 Graph Manager

**Responsibilities:** single write path, strict ordering (structural -> schema -> ACL -> storage).

**Key API surface:**

* `apply_envelope(ctx, raw_envelope)` -> `global_seq`

### 3.6 State Manager

**Responsibilities:** sync ingestion and ordering.

**Key API surface:**

* `ingest_sync(peer_id, raw_sync)` -> `global_seq`

### 3.7 Key Manager

**Responsibilities:** identity keys, signing, verification, and optional encryption.

**Key API surface:**

* `generate_identity_keypair(identity_id)` -> public key record
* `sign(identity_id, payload_bytes)` -> signature
* `verify(identity_id, payload_bytes, signature)` -> bool
* `encrypt(recipient_public_key_b64, payload_bytes)` -> ciphertext (optional)

### 3.8 DoS Guard Manager

**Responsibilities:** admission decisions and puzzle lifecycle.

**Key API surface:**

* `admit(telemetry, is_ready)` -> admission decision
* `verify_puzzle(response)` -> decision

### 3.9 Network Manager

**Responsibilities:** transport orchestration, admission, verification, and outbound preparation.

**Key API surface:**

* `start()` / `shutdown()`
* `admit_connection(telemetry)` -> admission
* `verify_challenge(response)` -> decision
* `receive_sync(telemetry, raw_sync)` -> `global_seq`
* `prepare_outbound(session, package)` -> outbound result

### 3.10 Auth Manager

**Responsibilities:** resolve session tokens into identities.

**Key API surface:**

* `authenticate_http(headers, route)` -> AuthResult
* `authenticate_ws(token, route)` -> AuthResult

## 4. Forbidden behaviors

* Calling Storage Manager from any component other than Graph Manager or State Manager.
* Applying envelopes without Schema Manager and ACL validation.
* Advancing sync cursors without successful persistence.
* Accepting untrusted identities not resolved by Auth Manager.
