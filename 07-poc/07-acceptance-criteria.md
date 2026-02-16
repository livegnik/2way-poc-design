



# 07 Acceptance criteria

This specification is the canonical acceptance-criteria source used to generate [POC-ACCEPTANCE.md](../../docs-build/hybrid/POC-ACCEPTANCE.md).

For the meta specifications, see [07-acceptance-criteria-meta.md](../10-appendix/meta/07-poc/07-acceptance-criteria-meta.md).

## 1. Canonical acceptance criteria

### AC-01 Graph write path order

**Steps:**

1. Submit a valid local envelope through `/graph/envelope`.
2. Verify structural validation, schema validation, and ACL checks run before commit.

**Expected output:**

* Envelope is accepted and committed after all validations pass.

**Requirement IDs:** R046-R060.
**Test reference:** `backend/tests/system/test_poc_acceptance.py::test_ac01_graph_write_order`.

### AC-02 Fail-closed behavior

**Steps:**

1. Submit an envelope with an invalid identifier or missing required field.
2. Observe rejection and confirm no partial persistence or sequence advancement.

**Expected output:**

* Error response and no state mutation.

**Requirement IDs:** R020-R024, R045, R060.
**Test reference:** `backend/tests/system/test_poc_acceptance.py::test_ac02_fail_closed`.

### AC-03 Deterministic ordering

**Steps:**

1. Apply the same envelope sequence twice on a clean node.
2. Compare resulting `global_seq` assignments and object states.

**Expected output:**

* Identical ordering and state results.

**Requirement IDs:** R025-R030, R046-R057.
**Test reference:** `backend/tests/system/test_poc_acceptance.py::test_ac03_deterministic_ordering`.

### AC-04 Protocol envelope integrity

**Steps:**

1. Send envelopes with invalid fields or forbidden fields.
2. Send a valid envelope.

**Expected output:**

* Invalid envelopes rejected; valid envelope accepted.

**Requirement IDs:** R046-R060.
**Test reference:** `backend/tests/system/test_poc_acceptance.py::test_ac04_envelope_integrity`.

### AC-05 Crypto verification

**Steps:**

1. Submit a sync package with a valid signature.
2. Submit a sync package with an invalid signature.

**Expected output:**

* Valid signature accepted; invalid signature rejected without partial processing.

**Requirement IDs:** R058-R062.
**Test reference:** `backend/tests/system/test_poc_acceptance.py::test_ac05_crypto_verification`.

### AC-06 App namespace isolation

**Steps:**

1. Attempt to create or reference objects across app namespaces.
2. Submit a valid same-app operation.

**Expected output:**

* Cross-app references rejected; same-app operations accepted.

**Requirement IDs:** R007-R009, R031-R044.
**Test reference:** `backend/tests/system/test_poc_acceptance.py::test_ac06_app_isolation`.

### AC-07 Sync convergence

**Steps:**

1. Run a two-node handshake and exchange sync packages.
2. Replay accepted packages on each node.

**Expected output:**

* Both nodes converge on identical graph state.

**Requirement IDs:** R058-R063.
**Test reference:** `backend/tests/system/test_poc_acceptance.py::test_ac07_sync_convergence`.

### AC-08 Replayability

**Steps:**

1. Persist a sequence of accepted envelopes.
2. Rebuild state by replaying the sequence in order.

**Expected output:**

* Replayed state matches the original state.

**Requirement IDs:** R025-R030, R046-R057.
**Test reference:** `backend/tests/system/test_poc_acceptance.py::test_ac08_replayability`.

### AC-09 DoS admission

**Steps:**

1. Trigger admission control thresholds.
2. Verify challenge issuance and difficulty increase.

**Expected output:**

* Challenges include required fields and difficulty escalates under abuse.

**Requirement IDs:** R064-R065.
**Test reference:** `backend/tests/system/test_poc_acceptance.py::test_ac09_dos_admission`.

### AC-10 Observability and audit

**Steps:**

1. Cause a rejection (invalid identifier or envelope).
2. Verify a log entry is recorded.

**Expected output:**

* Rejections are logged and traceable.

**Requirement IDs:** R024.
**Test reference:** `backend/tests/system/test_poc_acceptance.py::test_ac10_observability_audit`.

### AC-11 Auth registration and token usage

**Steps:**

1. Register an identity via `/auth/identity/register` with a valid signature.
2. Verify the response signature and store the returned token.
3. Register the same public key again and verify idempotent behavior.
4. Attempt a replay of the same `(public_key, nonce)` payload and confirm rejection.

**Expected output:**

* Registration returns `identity_id` and opaque `token`.
* Response signature verifies and `expires_at` is present.
* Duplicate registration returns the same `identity_id` and a fresh token.
* Replayed registration payload is rejected.

**Requirement IDs:** R160-R168, R175-R179, R184.
**Test reference:** `backend/tests/system/test_poc_acceptance.py::test_ac11_auth_registration`.

### AC-12 Marketplace app discovery and install

**Steps:**

1. Open the marketplace UI and list available apps.
2. Install the market app (or another available app) via the app lifecycle routes.
3. Verify the app appears in the installed list and can be enabled or disabled.

**Expected output:**

* Marketplace lists available apps deterministically.
* Install/register succeeds via app lifecycle routes.
* Enable/disable transitions are enforced and reflected in listings.

**Requirement IDs:** R112, R116, R118, R131, R136.
**Test reference:** `backend/tests/system/test_poc_acceptance.py::test_ac12_marketplace_install`.

### AC-13 End-to-end smoke (backend + frontend)

**Steps:**

1. Bootstrap a clean backend (install + admin identity) and start the frontend against it.
2. Register a frontend identity via `/auth/identity/register` and store the token.
3. Create a messaging thread and a message via `/graph/envelope`, then read it back via `/apps/messaging/read`.
4. Create a social post via `/graph/envelope`, then read it back via `/apps/social/read`.

**Expected output:**

* All requests succeed with deterministic `global_seq` ordering.
* Read results include the created objects and no cross-app leakage.
* Frontend remains authenticated for the duration of the flow.

**Requirement IDs:** R105.
**Test reference:** `backend/tests/system/test_poc_acceptance.py::test_e2e_smoke`.

## 2. Test mapping policy

Each canonical acceptance criterion maps to at least one system-level black-box test and must remain runnable per the build plan Phase 9 suites.
