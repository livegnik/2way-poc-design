



# 02 Sync Transport Interface

Defines the transport-facing sync surfaces implied by protocol and manager specs. This document is transport-agnostic and aligns sync package handling across interface surfaces.

For the meta specifications, see [08-network-transport-requirements meta](../10-appendix/meta/01-protocol/08-network-transport-requirements-meta.md).

## 1. Purpose and scope

This document specifies the expected sync transport behavior for exchanging sync package envelopes between nodes, including validation, admission, and replay protection.

## 2. Sync package structure

Sync package envelope structure is defined in [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md). Transport surfaces must carry the full sync package envelope unchanged.

## 3. Transport admission and verification

* All inbound sync traffic is admitted through [DoS Guard Manager](../02-architecture/managers/14-dos-guard-manager.md) and [Network Manager](../02-architecture/managers/10-network-manager.md) bastion flow.
* Signatures are verified before any package is forwarded to [State Manager](../02-architecture/managers/09-state-manager.md).
* Signature verification failures are terminal for the package and must not be partially processed.

## 4. Idempotency and replay protection

* Sync packages are validated for ordering and replay protection by [State Manager](../02-architecture/managers/09-state-manager.md) using `sync_state` and `domain_seq` cursors.
* Replayed or out-of-order packages are rejected.

## 5. Endpoints table

PoC transport endpoint (HTTP):

| Route | Method | Auth | Summary |
| --- | --- | --- | --- |
| `/system/sync/packages` | POST | Required | Submit a sync package envelope for inbound processing. |

### 5.1 POST /system/sync/packages

Request body:

```
{
  "package": {
    "sender_identity": <int>,
    "sync_domain": "<string>",
    "from_seq": <int>,
    "to_seq": <int>,
    "envelope": {
      "trace_id": "<string>",
      "ops": [ ... ]
    },
    "signature": "<string>"
  }
}
```

The `package` object MUST be a sync package envelope as defined in [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md) Section 7. Unknown fields are rejected.

Response:

```
{"ok": true}
```

Success-side effects (required):

* `{"ok": true}` is returned only after Network Manager admission succeeds and State Manager ingest commits successfully.
* Successful ingest must advance sync cursor state for the `(peer_id, sync_domain)` pair.
* Failed ingest must not advance sync cursor state or expose partial graph mutations.

Errors:

* `400` if structural validation fails (`envelope_invalid` or `network_rejected`).
* `400` (`network_rejected`) when signature verification fails.
* `400` (`network_rejected`) for sync domain violations or rejected transport admission.
* `400` (`sequence_error`) for replay or ordering violations.
* `400` (`dos_challenge_required`) when DoS Guard requires a puzzle. `ErrorDetail.data` MUST include `challenge_id`, `expires_at`, `context_binding`, and `algorithm` as defined in [01-protocol/09-dos-guard-and-client-puzzles.md](../01-protocol/09-dos-guard-and-client-puzzles.md).
* `400` (`storage_error`) when State Manager persistence or commit fails.
* `401` (`auth_required`, `auth_invalid`) if authentication fails.
* `401` (`ERR_AUTH_TOKEN_EXPIRED`, `ERR_AUTH_TOKEN_REVOKED`) if auth token is expired or revoked.
* `500` (`internal_error`) for internal errors.

Notes:

* This endpoint is a local-only PoC transport surface used for integration testing. Production transports may replace it with different mechanisms.

## 6. Security notes

* Transport metadata is never treated as authenticated identity.
* Sync packages remain untrusted until verified by [Network Manager](../02-architecture/managers/10-network-manager.md), with decryption delegated to [Key Manager](../02-architecture/managers/03-key-manager.md) when required.

## 7. Forbidden behaviors

* Accepting sync packages without DoS Guard admission and signature verification.
* Advancing sync cursors without successful commit.
