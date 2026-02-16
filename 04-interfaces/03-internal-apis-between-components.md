



# 03 Internal APIs between components

Defines the internal API contracts between managers and services in the 2WAY backend. These APIs are in-process, strongly ordered, and are not exposed externally.

For the meta specifications, see [03-internal-apis-between-components meta](../10-appendix/meta/04-interfaces/03-internal-apis-between-components-meta.md).

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
* Derived cache helpers (create/read/write/drop) for non-authoritative cache tables as defined in [03-data/09-derived-cache-tables.md](../03-data/09-derived-cache-tables.md).

### 3.3 Schema Manager

**Responsibilities:** schema compilation, type registry resolution.
**Key API surface:**
* `get_schema(app_id)` -> schema snapshot
* `resolve_type_id(app_id, kind, type_key)` -> int
* `resolve_type_key(app_id, kind, type_id)` -> str

### 3.4 ACL Manager

**Responsibilities:** authorization for graph reads and writes.
**Key API surface:**
* `authorize_write(ctx, owner_identity)` -> None (raises on deny)
* `authorize_read(ctx, read_request)` -> `AclDecision`
* `authorize_sync_read(ctx, read_request)` -> `AclDecision`

### 3.5 Graph Manager

**Responsibilities:** single write path, strict ordering (structural -> schema -> ACL -> storage).
**Key API surface:**
* `apply_envelope(ctx, raw_envelope)` -> `global_seq`
* `read_graph(ctx, read_request)` -> `GraphReadResult`

`read_graph(ctx, read_request)` is the canonical controlled-read execution path for integration flows before HTTP read routes are exposed.

### 3.6 State Manager

**Responsibilities:** sync ingestion and ordering.
**Key API surface:**
* `ingest_sync(peer_id, raw_sync)` -> `global_seq`

### 3.7 Key Manager

**Responsibilities:** identity keys, signing, and optional encryption/decryption using private keys.
**Key API surface:**
* `generate_identity_keypair(identity_id)` -> public key record
* `sign(identity_id, payload_bytes)` -> signature
* `encrypt(recipient_public_key_b64, payload_bytes)` -> ciphertext (optional)

Note: Signature verification is performed by the caller using public key material; it is not a Key Manager API.

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

Failure mapping (outbound preparation):

* `network_rejected` when transport is not ready, admission is denied, or the peer is unavailable.
* `envelope_invalid` when the outbound package is malformed.
* `internal_error` for unexpected failures.

### 3.10 Auth Manager

**Responsibilities:** resolve auth tokens into identities.
**Key API surface:**
* `authenticate_http(headers, route)` -> AuthResult
* `authenticate_ws(token, route)` -> AuthResult

## 4. Forbidden behaviors

* Calling Storage Manager for authoritative graph reads or writes from any component other than Graph Manager or State Manager. Services may use Storage Manager only for derived cache tables or other explicitly sanctioned non-graph helpers.
* Applying envelopes without Schema Manager and ACL validation.
* Advancing sync cursors without successful persistence.
* Accepting untrusted identities not resolved by Auth Manager.

## 5. Payload schemas

Unknown fields are rejected for every object defined below unless explicitly noted.
Validation failures for internal API payloads must raise `ErrorDetail` with `code=envelope_invalid`, except identifier violations which must use `code=identifier_invalid`.

### 5.1 RouteContext (Auth Manager inputs)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `path` | Yes | string | Must match a route listed in `ROUTES.md`. |
| `method` | No | string | Uppercase HTTP method when applicable. |
| `app_id` | Yes | int | Valid app_id per `01-protocol/01-identifiers-and-namespaces.md`. |
| `auth_required` | Yes | boolean | True if the route requires authentication. |
| `admin_only` | Yes | boolean | True if the route requires admin gating. |

### 5.2 AuthResult (Auth Manager outputs)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `state` | Yes | string | `authenticated`, `unauthenticated`, or `rejected`. |
| `requester_identity_id` | No | integer or null | Required when `state=authenticated`. |
| `is_admin` | Yes | boolean | Admin eligibility for the route. |
| `rejection` | No | string | Required when `state=rejected`; must be one of the rejection categories in `02-architecture/managers/04-auth-manager.md` Section 7.2. |

### 5.2.1 GraphReadRequest (Graph Manager inputs)

Graph read requests are structured descriptors for complex, bounded reads. They are not envelopes and are never persisted. The request MUST be evaluated under the caller's [OperationContext](../02-architecture/services-and-apps/05-operation-context.md), and all results MUST be filtered through [ACL Manager](../02-architecture/managers/06-acl-manager.md) per [01-protocol/06-access-control-model.md](../01-protocol/06-access-control-model.md).

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `app_id` | Yes | int | Valid app_id per `01-protocol/01-identifiers-and-namespaces.md`. |
| `target` | Yes | string | `parent`, `attr`, `edge`, or `rating`. |
| `parent_type` | Cond | string | Required when `target` is `parent` or `attr`; schema type key. |
| `attr_type` | Cond | string | Required when `target` is `attr`; schema type key. |
| `rating_type` | Cond | string | Required when `target` is `rating`; schema type key. |
| `include` | No | array | 0-4 values: `parent`, `attr`, `edge`, `rating` (related objects only). |
| `select_attrs` | No | array | 0-32 attribute type keys to return for `parent` targets. |
| `filters` | No | array | List of `GraphReadFilter` entries (0-32). |
| `exclude` | No | array | List of `GraphReadFilter` entries (0-32). |
| `limit` | Yes | int | 1-1000. |
| `offset` | No | int | 0-100000; mutually exclusive with `cursor`. |
| `cursor` | No | string | Opaque pagination cursor; mutually exclusive with `offset`. |
| `snapshot_seq` | No | int | If present, read is bounded to `global_seq <= snapshot_seq`. |
| `order_by` | No | string | `created_at`, `updated_at`, or `global_seq`. |
| `order_dir` | No | string | `asc` or `desc`. |
| `distinct_on` | No | string | One of: `parent_id`, `attr_id`, `edge_id`, `rating_id`. |
| `rating_scope` | No | string | `any`, `latest`, or `max` (applies to rating filters). |
| `edge_traversal` | No | object | `EdgeTraversal` with bounded traversal constraints. |
| `time_range` | No | object | `TimeRange` with `created_after`/`created_before` RFC3339 timestamps. |

EdgeTraversal:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `edge_type` | Yes | string | Schema edge type key. |
| `max_depth` | Yes | int | 1-3. |
| `max_nodes` | Yes | int | 1-1000. |

TimeRange:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `created_after` | No | string | RFC3339 timestamp. |
| `created_before` | No | string | RFC3339 timestamp. |

GraphReadFilter:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `op` | Yes | string | One of: `attr_exists`, `attr_equals`, `attr_in`, `attr_prefix`, `parent_field_equals`, `parent_field_in`, `parent_field_prefix`, `parent_id_equals`, `parent_id_in`, `rating_min`, `rating_max`, `rating_equals`, `rating_from_group`, `edge_exists`, `group_member_of`, `group_member_exclude`, `author_in_group`, `degree_max`, `degree_min`. |
| `field` | No | string | Required for `attr_*` ops; schema attribute type key. |
| `parent_field` | No | string | Required for `parent_field_*`; schema field key for the Parent payload. |
| `parent_id` | No | string | Required for `parent_id_equals`; parent id string. |
| `parent_ids` | No | array | Required for `parent_id_in`; 1-64 parent id strings. |
| `value` | No | string | Required for `attr_equals` and `parent_field_equals`. |
| `values` | No | array | Required for `attr_in` and `parent_field_in`; 1-32 strings. |
| `prefix` | No | string | Required for `attr_prefix` and `parent_field_prefix`. |
| `min` | No | number | Required for `rating_min`. |
| `max` | No | number | Required for `rating_max`. |
| `group_parent_id` | No | string | Required for `rating_from_group`, `group_member_of`, `group_member_exclude`. |
| `edge_type` | No | string | Required for `edge_exists`; schema edge type key. |
| `author_group_parent_id` | No | string | Required for `author_in_group`. |
| `max_degree` | No | int | Required for `degree_max`; 1-3. |
| `min_degree` | No | int | Required for `degree_min`; 0-3. |

Rules:

* Filters are evaluated in order and combined with logical AND.
* `exclude` filters are applied after `filters` and remove any matching results.
* `offset` and `cursor` are mutually exclusive.
* `select_attrs` is valid only when `target=parent` or `include` contains `parent`.
* `parent_field_*` filters are valid only when `target=parent` and `parent_type` is set.
* `parent_id_*` filters are valid only when `target=parent`.
* `edge_traversal` is valid only when `target=parent` and uses the filtered parent result set as its start set.
* `edge_traversal` traverses only parent-to-parent edges of type `edge_type`; edges with `dst_attr_id` are ignored.
* `edge_traversal` uses a breadth-first expansion from the start set, emitting parents in deterministic order by depth then by `edge_id` ascending.
* `max_nodes` caps the total number of parents returned after traversal (including the start set); excess nodes are truncated in traversal order.
* `degree_max` and `degree_min` apply to the requester identity in the OperationContext and compute degrees over `contact.link` edges in `app.contacts` only. If `app_id` is not `app.contacts`, the request is rejected.
* Requests using `degree_max` or `degree_min` with `app_id` other than `app.contacts` MUST return `ErrorDetail.code=envelope_invalid`.
* The requester identity is mapped to a `contact.profile` Parent by matching `contact.profile.identity_id` to `OperationContext.requester_identity_id`. If no match exists, degree filters yield no results.
* `rating_from_group`, `group_member_of`, `group_member_exclude`, and `author_in_group` resolve group membership against `system.group` Parents and `system.group_member` Edges in `app_0`.
* `rating_from_group` filters ratings whose author identity is a member of the specified group parent.
* `group_member_exclude` excludes results whose relevant identity is in the specified group.
* Unknown filter ops or missing required fields cause rejection.

### 5.2.2 GraphReadResult (Graph Manager outputs)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `rows` | Yes | array | Result rows (0-`limit`). |
| `next_offset` | No | int | Present when more rows are available. |
| `snapshot_seq` | Yes | int | Snapshot bound applied to the read. |

GraphReadRow (when `target=parent`):

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `parent_id` | Yes | string | Parent id. |
| `type_key` | Yes | string | Schema type key. |
| `owner_identity_id` | Yes | int | Identity id of author. |
| `value` | No | object | Schema payload (`value_json`) or null. |
| `attrs` | No | array | Present only when `include` contains `attr`; array of GraphReadAttrRow. |
| `edges` | No | array | Present only when `include` contains `edge`; array of GraphReadEdgeRow. |
| `ratings` | No | array | Present only when `include` contains `rating`; array of GraphReadRatingRow. |

GraphReadRow (when `target=attr`):

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `attr_id` | Yes | string | Attribute id. |
| `parent_id` | Yes | string | Parent id. |
| `type_key` | Yes | string | Schema type key. |
| `owner_identity_id` | Yes | int | Identity id of author. |
| `value` | No | object | Schema payload (`value_json`) or null. |

GraphReadRow (when `target=edge`):

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `edge_id` | Yes | string | Edge id. |
| `src_parent_id` | Yes | string | Source Parent id. |
| `dst_parent_id` | No | string | Destination Parent id (exclusive with `dst_attr_id`). |
| `dst_attr_id` | No | string | Destination Attribute id (exclusive with `dst_parent_id`). |
| `type_key` | Yes | string | Schema type key. |
| `owner_identity_id` | Yes | int | Identity id of author. |
| `value` | No | object | Schema payload (`value_json`) or null. |

GraphReadRow (when `target=rating`):

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `rating_id` | Yes | string | Rating id. |
| `target_parent_id` | No | string | Target Parent id (exclusive with `target_attr_id`). |
| `target_attr_id` | No | string | Target Attribute id (exclusive with `target_parent_id`). |
| `type_key` | Yes | string | Schema type key. |
| `owner_identity_id` | Yes | int | Identity id of author. |
| `value` | No | object | Schema payload (`value_json`) or null. |

GraphReadAttrRow:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `attr_id` | Yes | string | Attribute id. |
| `parent_id` | Yes | string | Parent id. |
| `type_key` | Yes | string | Schema type key. |
| `value` | No | object | Schema payload (`value_json`) or null. |

GraphReadEdgeRow:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `edge_id` | Yes | string | Edge id. |
| `src_parent_id` | Yes | string | Source Parent id. |
| `dst_parent_id` | No | string | Destination Parent id (exclusive with `dst_attr_id`). |
| `dst_attr_id` | No | string | Destination Attribute id (exclusive with `dst_parent_id`). |
| `type_key` | Yes | string | Schema type key. |
| `value` | No | object | Schema payload (`value_json`) or null. |

GraphReadRatingRow:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `rating_id` | Yes | string | Rating id. |
| `target_parent_id` | No | string | Target Parent id (exclusive with `target_attr_id`). |
| `target_attr_id` | No | string | Target Attribute id (exclusive with `target_parent_id`). |
| `type_key` | Yes | string | Schema type key. |
| `value` | No | object | Schema payload (`value_json`) or null. |

### 5.2.3 AclReadRequest (ACL Manager inputs)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `app_id` | Yes | int | Valid app_id per `01-protocol/01-identifiers-and-namespaces.md`. |
| `target` | Yes | string | `parent`, `attr`, `edge`, or `rating`. |
| `target_id` | Yes | string | Target object id for the request. |
| `owner_identity_id` | No | int | Required when evaluating owner-specific rules. |
| `intent` | Yes | string | `read` or `sync_read`. |

### 5.2.4 AclDecision (ACL Manager outputs)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `allowed` | Yes | boolean | True if access is granted. |
| `rejection` | No | string | Required when `allowed=false`; must map to an ACL rejection category. |

### 5.3 ConfigSnapshot (Config Manager outputs)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `cfg_seq` | Yes | integer | Monotonic configuration sequence. |
| `namespaces` | Yes | object | Map of namespace -> `ConfigNamespaceSnapshot`. |

ConfigNamespaceSnapshot:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `namespace` | Yes | string | Namespace key (for example, `node`, `storage`, `service.bootstrap`). |
| `values` | Yes | object | Map of config key -> typed value; each value must conform to the owning manager's registered schema in `02-architecture/managers/01-config-manager.md`. |

### 5.4 ConfigDiff (Config Manager reload outputs)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `changes` | Yes | array | List of `ConfigChange` entries. |

ConfigChange:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `key` | Yes | string | Fully qualified config key. |
| `old_value` | Yes | any | Previous typed value. |
| `new_value` | Yes | any | New typed value. |

### 5.5 Envelope and sync package (Graph/State Manager inputs)

* `raw_envelope` MUST be an envelope object conforming to `01-protocol/03-serialization-and-envelopes.md`.
* `raw_sync` MUST be a sync package conforming to `01-protocol/07-sync-and-consistency.md`.
* Invalid or malformed `raw_envelope` inputs MUST raise `ErrorDetail.code=envelope_invalid` (or `identifier_invalid` for identifier violations).
* Invalid or malformed `raw_sync` inputs MUST raise `ErrorDetail.code=envelope_invalid` or `sequence_error` when sync ordering or range rules fail.

### 5.5.1 Sync cursor records (Storage/State Manager)

SyncState:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `peer_id` | Yes | string | 1-64 chars. |
| `sync_domain` | Yes | string | 1-64 chars. |
| `last_global_seq` | Yes | integer | Non-negative. |
| `state_flags` | No | array | 0-16 strings, 1-64 chars. |

DomainSeq:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `peer_id` | Yes | string | 1-64 chars. |
| `sync_domain` | Yes | string | 1-64 chars. |
| `last_global_seq` | Yes | integer | Non-negative. |

Unknown fields are rejected for both record types.
Invalid sync cursor records MUST raise `ErrorDetail.code=envelope_invalid` (or `identifier_invalid` for identifier violations).

### 5.5.2 Limit enforcement inputs (Storage Manager)

EnforceAppLimitsInput:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `app_id` | Yes | integer | Positive. |
| `ops_by_kind` | Yes | object | Map of kind -> count; counts are non-negative integers. |
| `payload_bytes` | Yes | integer | Non-negative. |

Unknown fields are rejected.

### 5.6 Admission telemetry (DoS Guard / Network Manager)

Telemetry object:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `connection_id` | Yes | string | Opaque identifier from Network Manager. |
| `transport_type` | Yes | string | Transport label from `01-protocol/08-network-transport-requirements.md`. |
| `advisory_peer_reference` | No | string | Optional advisory peer identifier; never treated as authenticated identity. |
| `bytes_in` | Yes | integer | Non-negative. |
| `bytes_out` | Yes | integer | Non-negative. |
| `message_rate` | Yes | integer | Non-negative. |
| `throughput_samples` | No | array | Array of numeric samples (implementation-defined granularity). |
| `pressure_indicators` | No | object | Map of pressure metric -> numeric value. |
| `outstanding_challenges` | No | integer | Non-negative. |

Invalid telemetry inputs MUST raise `ErrorDetail.code=envelope_invalid` (or `identifier_invalid` for identifier violations).

### 5.7 Puzzle response and admission decision

PuzzleResponse:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `challenge_id` | Yes | string | Must match issued challenge. |
| `solution` | Yes | string | Opaque solution bytes (encoding defined in `01-protocol/09-dos-guard-and-client-puzzles.md`). |
| `connection_id` | Yes | string | Connection identifier from telemetry. |
| `opaque_payload` | No | string | Opaque payload, if required by the puzzle algorithm. |

AdmissionDecision:

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `decision` | Yes | string | `allow`, `deny`, or `require_challenge`. |
| `throttle_params` | No | object | Optional throttle settings per `01-protocol/09-dos-guard-and-client-puzzles.md`. |
| `challenge_spec` | No | object | Optional challenge spec per `01-protocol/09-dos-guard-and-client-puzzles.md`. |
