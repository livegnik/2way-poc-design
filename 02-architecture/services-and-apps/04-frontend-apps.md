



# 04 Frontend Apps

## 1. Purpose and scope

Frontend applications are the only components that interpret 2WAY state on behalf of end users and translate their intent into requests that the backend can evaluate. They operate entirely outside the backend process, run on untrusted devices, and must consume published APIs, sync surfaces, and envelopes without inventing bespoke shortcuts. This overview defines the implementation-ready contract for frontend apps so every surface behaves consistently regardless of product, framework, or deployment.

The document establishes how frontend apps participate in [OperationContext](05-operation-context.md) construction, authenticate, honor backend admission decisions, respect ACL limits, handle offline behavior, and report telemetry. It prescribes local storage rules, error handling posture, configuration, release and update mechanics, and secure UX expectations so any conforming frontend can be audited alongside backend components. The specification also enumerates the obligations frontend apps inherit when interacting with system services, app extensions, sync flows, and peer devices.

This overview references:

* [00-scope/**](../../00-scope/)
* [01-protocol/**](../../01-protocol/)
* [02-architecture/01-component-model.md](../01-component-model.md)
* [02-architecture/04-data-flow-overview.md](../04-data-flow-overview.md)
* [02-architecture/managers/**](managers/)
* [02-architecture/managers/00-managers-overview.md](../managers/00-managers-overview.md)
* [02-architecture/services-and-apps/**](./)
* [02-architecture/services-and-apps/01-services-vs-apps.md](01-services-vs-apps.md)
* [02-architecture/services-and-apps/02-system-services.md](02-system-services.md)
* [02-architecture/services-and-apps/03-app-backend-extensions.md](03-app-backend-extensions.md)
* [02-architecture/services-and-apps/05-operation-context.md](05-operation-context.md)
* [04-interfaces/**](../../04-interfaces/)
* [05-security/**](../../05-security/)
* [06-flows/**](../../06-flows/)


### 1.1 Responsibilities and boundaries

This overview is responsible for the following:

* Defining the canonical frontend app model, including layers, execution contexts, and how each context interacts with backend services and managers.
* Describing how frontend apps assemble [OperationContext](05-operation-context.md) inputs, authenticate users and devices, request capabilities, and respect ACL policy.
* Detailing transport, sync, configuration, storage, and offline requirements so apps cannot weaken protocol guarantees.
* Capturing observability, telemetry, logging, and diagnostics obligations for frontend behavior so operators can audit requests end-to-end.
* Outlining security, privacy, release, and supply-chain controls for distributing and updating frontend apps across devices.

This overview does not cover the following:

* Backend manager or service implementation details ([02-architecture/managers/**](../managers/), [02-architecture/services-and-apps/02-system-services.md](02-system-services.md), [02-architecture/services-and-apps/03-app-backend-extensions.md](03-app-backend-extensions.md)).
* Interface definitions already captured in [04-interfaces/**](../../04-interfaces/**), except where this document must declare missing shapes to keep frontend development unblocked.
* Product-specific UX copy, visual design, or marketing requirements.

### 1.2 Invariants and guarantees

Across all frontend apps, the following invariants must hold:

* Frontend apps are untrusted clients. Every request they emit must tolerate backend rejection and must never assume privileged access beyond published capabilities ([01-protocol/00-protocol-overview.md](../../01-protocol/00-protocol-overview.md)).
* [OperationContext](05-operation-context.md) inputs (user identity, device identity, app_id, capability intent, trust posture, correlation metadata) are collected and transmitted exactly as defined in [02-architecture/services-and-apps/05-operation-context.md](05-operation-context.md). Frontends never fabricate server-side context.
* All backend interactions traverse the published HTTP/WebSocket/sync surfaces in [04-interfaces/**](../../04-interfaces/**) and inherit the authentication, ACL, schema, and ordering rules codified in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md), [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md), [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md), and [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md). DoS Guard enforcement and puzzle handling remain entirely on the backend. No direct database, filesystem, or socket manipulation occurs.
* Inputs are validated locally before being sent so malformed payloads never reach the backend, preventing resource abuse and ensuring deterministic error handling per [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Frontend storage is non-authoritative. Only graph commits acknowledged by the backend count as truth, cached state can be dropped and regenerated at any time, matching the graph authority rules in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md).
* Offline or background automation follows the same signing, authentication, and replay rules as interactive usage ([01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md)). Automation cannot invent capabilities or attempt to bypass backend DoS controls defined in [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md); it simply respects backend throttling decisions.
* Sensitive material (keys, tokens, PII) is handled according to [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md) and [05-security/**](../../05-security/**) guidance, encrypted at rest when stored locally, never logged in plaintext, and scoped to the owning app.

## 2. Frontend application model

### 2.1 Architectural definition

* **Frontend app**: Any executable (native desktop/mobile, web SPA, CLI, daemon, automation bot) that communicates with the 2WAY backend through published interfaces using an assigned `app_id`.
* **Surface**: A concrete entry point delivered to users (UI screen, CLI command, automation hook) that issues backend requests via HTTP, WebSocket, or sync packages.
* **Runtime context**: The execution container for a surface (browser tab, native view controller, background worker, scheduled automation). Each context must enforce the same [OperationContext](05-operation-context.md) and security rules.

Frontends decompose into the following layers:

| Layer                | Responsibilities                                                                                                                          | Mandatory inputs                                                   |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Presentation         | Rendering UI, collecting input, presenting errors, guiding users through backend admission responses                                      | Schema metadata, localization bundles, deterministic error catalog |
| Client orchestration | Managing sessions, tokens, request queues, retries, background sync, offline caches                                                       | [OperationContext](05-operation-context.md) fields, capability map, sync manifests            |
| Transport adapters   | Translating orchestration intents into HTTP/WebSocket/sync calls defined in [04-interfaces/**](../../04-interfaces/**), encrypting payloads, verifying signatures | Auth credentials, request metadata                                 |
| Storage adapters     | Persisting local caches, attachments, and pending writes using encrypted stores                                                           | Schema definitions, ACL filters, retention policy                  |

Every frontend app must document which layers it implements and how they map to frameworks or libraries so reviewers can trace compliance.

### 2.2 Execution contexts

Different surfaces share the same guarantees:

* **Interactive contexts** (UI, CLI) must collect user consent for each capability invocation, surface backend admission errors or waits clearly, and display backend errors verbatim.
* **Automation contexts** (background workers, scheduled tasks) must run under automation-specific [OperationContext](05-operation-context.md) entries (`actor_type=automation`), publish schedule manifests, and respect backend throttling decisions communicated via standard error responses ([01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md)).
* **Embedded contexts** (widgets, plugins) inherit the host container's capability posture but still identify themselves to the backend via their own app_id.

### 2.3 Mandatory components

| Component                | Requirement                                                                                                                                 |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Session Manager          | Maintains authenticated sessions, refresh tokens, and device attestations. Must isolate multiple identities using per-user vaults.          |
| [OperationContext](05-operation-context.md) Builder | Assembles immutable request metadata: `user_id`, `device_id`, `app_id`, capability verb, correlation ID, locale, client version. |
| Request Queue            | Batches writes, manages retries, enforces ordering for dependent operations, and cancels in-flight work on logout.                          |
| Sync Controller          | Interfaces with [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md) flows, schedules pulls and pushes, and validates package signatures.               |
| Storage Adapter          | Provides encrypted local persistence for caches and pending writes, enforces retention rules, and segregates app domains.                   |
| Telemetry Adapter        | Streams structured logs and optional metrics to operator-approved sinks without leaking sensitive material.                                 |
| Capability Catalog       | Mirrors backend-provided capability list so UI can enable or disable features deterministically.                                            |

## 3. Identity, registration, and [OperationContext](05-operation-context.md)

### 3.1 Application identity

* Every frontend build is registered with [App Manager](../managers/08-app-manager.md), resulting in a slug and permanent `app_id` as defined in [01-protocol/01-identifiers-and-namespaces.md](../../01-protocol/01-identifiers-and-namespaces.md).
* Builds embed the slug, semantic version, and minimum backend compatibility version (`requires.platform.min_version`) inside signed metadata. Apps with mismatched versions must fail closed, prompting users to upgrade or downgrade before continuing.
* Multi-surface apps (web plus native) share the same `app_id` but may ship different binaries. Each binary must advertise its surface identifier for telemetry.

### 3.2 User and device identity capture

* Device enrollment flows follow [06-flows/bootstrap/**](../../06-flows/bootstrap/**) guidance and the identity binding guarantees in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md). Frontends must store device credentials in secure enclaves or OS-provided key stores.
* Each session binds `user_id`, `device_id`, and `app_id`. Swapping any element requires reconstructing [OperationContext](05-operation-context.md) from scratch, session reuse across devices is forbidden.
* Device fingerprints, attestation proofs, and hardware posture data must be collected before the first privileged call so [Auth Manager](../managers/04-auth-manager.md) can bind them to [OperationContext](05-operation-context.md), satisfying the identity requirements described in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md).

### 3.3 [OperationContext](05-operation-context.md) contribution

Frontends must supply the following fields on every request before the backend can admit the call:

| Field                | Source                | Notes                                                                     |
| -------------------- | --------------------- | ------------------------------------------------------------------------- |
| `app_id`             | Build metadata        | Immutable per installation.                                               |
| `app_version`        | Build metadata        | Allows backend compatibility enforcement.                                 |
| `user_id`            | Authenticated session | Empty only for anonymous bootstrap endpoints explicitly marked as such.   |
| `device_id`          | Device enrollment     | Must match [Auth Manager](../managers/04-auth-manager.md)'s record.                                         |
| `capability`         | Capability catalog    | One verb per request, multi-step workflows decompose into separate calls. |
| `actor_type`         | Context               | Values: `user`, `service`, `automation`.                                  |
| `correlation_id`     | Client generated UUID | Unique per request chain, logged locally and remotely.                    |
| `locale`, `timezone` | User settings         | Optional but recommended for UX-driven validations.                       |

[OperationContext](05-operation-context.md) objects are immutable snapshots. Once transmitted, the frontend must not reuse or mutate them for retries, new retries reconstruct the context to guarantee deterministic tracing, matching the ordering posture in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).

### 3.4 Capability negotiation

* At authentication, the backend returns capability summaries scoped to the requesting identity and app. Frontends cache them but must re-fetch on ACL changes, session refresh, or `ERR_CAPABILITY_REVOKED` responses ([01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md)).
* Capabilities are hierarchical (`system.feed.read`, `app.crm.ticket.create`). Frontends must request the most specific verb required and must not degrade into super verbs.
* UI must hide or disable controls for missing capabilities but still allow users to discover the required permissions by referencing documentation provided by Identity Service or [App Manager](../managers/08-app-manager.md).

## 4. Interface consumption

### 4.1 HTTP and WebSocket usage

* APIs are defined in [04-interfaces/http/**](../../04-interfaces/http/**) and [04-interfaces/websocket/**](../../04-interfaces/websocket/**). Frontends must import generated clients or schemas from those specs rather than re-deriving shapes.
* Requests include:

  * Auth envelope or session token issued by [Auth Manager](../managers/04-auth-manager.md) per [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
  * [OperationContext](05-operation-context.md) payload serialized according to [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Responses must be parsed using the canonical error catalog in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md). Unknown fields must not crash the client, they must be ignored while preserving the signed body for optional logging.
* WebSocket clients must implement backpressure aligned with [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md), if the backend signals `slow_client`, the frontend pauses subscriptions until it drains local queues.

### 4.2 Sync packages

* Sync flows follow [01-protocol/07-sync-and-consistency.md](../../01-protocol/07-sync-and-consistency.md). Frontends request packages by domain and range, validate signatures, ensure schema compatibility, and apply only after local policy approves.
* Pending mutations are queued in deterministic order, signed locally, and submitted when connectivity allows. Each pending mutation references the schema ID and parent objects used so [Graph Manager](../managers/07-graph-manager.md) can verify structure without contacting the frontend again, honoring [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) and [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* Conflicts are surfaced in UI with actionable options (retry later, discard, inspect details). Automatic merges are permitted only when deterministic rules exist and are documented.

### 4.3 Background jobs and push channels

* Push notifications or background fetches must be relayed through the backend interface layer. Direct peer connections initiated by the frontend are forbidden by the transport boundaries in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md).
* Background jobs advertise their cadence, maximum run time, and expected [OperationContext](05-operation-context.md) capability to the backend via registration endpoints so backend schedulers can throttle or pause them as needed.
* Jobs must obey exponential backoff when encountering `429` or other resource exhaustion responses, deferring work until the backend signals readiness again.

### 4.4 Attachments and large payloads

* Uploads use signed URLs or chunked flows defined in [04-interfaces/http/upload.md](../../04-interfaces/http/upload.md). Clients must hash chunks, include digests, and resume interrupted uploads without restarting entire files.
* Downloads verify digests against metadata before exposing content to users. Unverified blobs must be quarantined or discarded.

## 5. Authentication, authorization, and trust

### 5.1 Session establishment

* Authentication flows (password, passkey, device token) are documented in [04-interfaces/auth/**](../../04-interfaces/auth/**) and must produce the identity proofs described in [01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md). Clients must implement multi-factor prompts when required by policy.
* Session tokens include expiration and scope. Clients renew sessions before expiration and destroy tokens on logout, version downgrade, or detected compromise.
* Device revocation is enforced immediately. When the backend returns `ERR_DEVICE_REVOKED`, clients must erase local caches, pending writes, and credentials without prompting for confirmation.

### 5.2 Transport hardening and admission feedback

* DoS Guard enforcement and client puzzles are implemented entirely by the backend per [01-protocol/09-dos-guard-and-client-puzzles.md](../../01-protocol/09-dos-guard-and-client-puzzles.md). Frontends never solve puzzles or generate proofs; they simply relay opaque admission data when instructed (for example, forwarding signed envelopes) and wait for the backend to accept or reject the request.
* When the backend returns `ERR_RESOURCE_*` or any admission delay, frontends surface clear messaging, pause retries, and give the user control to wait or cancel. No additional computation occurs on the client.
* TLS or Noise transports defined in [01-protocol/08-network-transport-requirements.md](../../01-protocol/08-network-transport-requirements.md) are mandatory. Clients must validate certificates or static keys pinned by the deployment.

### 5.3 Capability enforcement

* Frontends never attempt a call without first verifying that the session holds the required capability, per the capability edge rules in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md). Attempting unauthorized calls intentionally is a violation logged as abuse.
* Delegations (acting on behalf of another user or app) require explicit consent flows and distinct [OperationContext](05-operation-context.md) entries (`actor_type=delegation`). Delegation tokens carry expirations and scoping rules identical to capability edges described in [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

### 5.4 Privacy and PII handling

* Personally identifiable data is encrypted at rest using OS-level APIs or audited crypto libraries. Keys are derived via platform key stores, raw keys never live in application bundles.
* Crash dumps and telemetry scrub PII unless the user opts into diagnostic uploads vetted by [05-security/**](../../05-security/**).
* Clipboard access is opt-in and accompanied by warnings when data leaves the app boundary.

## 6. Local storage and state management

### 6.1 Storage classes

| Class                   | Usage                                          | Requirements                                                      |
| ----------------------- | ---------------------------------------------- | ----------------------------------------------------------------- |
| Ephemeral memory        | UI state, short-lived caches                   | Cleared on logout, never persists secrets.                        |
| Durable encrypted store | Pending writes, offline data, user preferences | AES-256 or OS equivalent encryption, keyed per user, device, app. |
| Attachment cache        | Large blobs, media                             | Stored under sandbox paths, deduplicated by digest, TTL enforced. |

### 6.2 Schema alignment

* Local caches must conform to the schemas defined by [Schema Manager](../managers/05-schema-manager.md) and the object grammar in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md). Each cached object carries `schema_version` and `app_id`. When [Schema Manager](../managers/05-schema-manager.md) reports a new version, clients invalidate incompatible cached entries.
* Derived views must be recomputable solely from cached graph data plus deterministic transforms. If recomputation fails, clients must drop derived data and rebuild after the next sync.

### 6.3 Pending write log

* All outbound mutations live in a write-ahead log storing: payload, schema ID, parent selectors, [OperationContext](05-operation-context.md) snapshot, submission timestamp, attempt counter, and status so they can be replayed deterministically per [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* The log enforces FIFO ordering within each parent object unless the interface contract specifies idempotent commutation, satisfying the ordering expectations in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* On success, entries are marked committed and eventually pruned once the backend acknowledges the global sequence number. On failure, entries record canonical error codes and user choices (retry or discard) for auditability.

### 6.4 Secret handling

* Secrets (session tokens, private keys, capability grants) remain in platform key stores. The app retrieves them only when signing or authenticating requests per [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md), zeroing memory afterward.
* Debug builds may expose key material only under explicit developer flags and must never be distributed to production users.

## 7. Offline behavior and synchronization

### 7.1 Operation lifecycle offline

1. User composes data locally. Client validates shape and schema constraints immediately.
2. Client appends the mutation to the pending write log with a generated correlation ID.
3. When connectivity returns, the request queue replays pending writes in deterministic order, re-signing with fresh timestamps and [OperationContext](05-operation-context.md) snapshots.
4. If schema or ACL changes render a pending write invalid, the client prompts the user with context and recommended actions, honoring [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md) and [01-protocol/06-access-control-model.md](../../01-protocol/06-access-control-model.md).

### 7.2 Sync scheduling

* Clients estimate resource budgets per sync (expected bytes, attachments, CPU cost) and publish them via scheduler manifests so backend schedulers can plan execution. No client-side throttling logic is required.
* Sync cadence adapts to device posture: aggressive when on power plus Wi-Fi, conservative when on battery or metered networks.
* Devices must expose user controls for pausing sync per app domain without uninstalling the app.

### 7.3 Conflict handling

* When the backend rejects a mutation with `ERR_OBJECT_VERSION` or equivalent ([01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md)), the client fetches the latest object, highlights conflicting fields, and allows the user to reapply or discard changes.
* Automated merges are allowed only when the schema marks fields as commutative or last-writer-wins and the app documents the policy.

## 8. Error handling and resilience

### 8.1 Canonical error catalog

Clients must map backend error codes (from [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md)) to UI states:

| Error class              | Client response                                                       |
| ------------------------ | --------------------------------------------------------------------- |
| `ERR_AUTH_*`             | Force re-authentication, clear sensitive caches.                      |
| `ERR_ACL_*`              | Display permission error, offer request access workflow if supported. |
| `ERR_SCHEMA_*`           | Highlight invalid fields, prevent resubmission until corrected.       |
| `ERR_SYNC_*`             | Retry with exponential backoff, surface diagnostics link.             |
| `ERR_RESOURCE_*`         | Inform the user about admission delays and pause retries until allowed. |
| `ERR_CAPABILITY_REVOKED` | Refresh capability catalog, disable affected UI.                      |

### 8.2 Retry strategy

* Retries follow per-endpoint budgets defined in [04-interfaces/**](../../04-interfaces/**). Clients respect `Retry-After` headers and any backend-provided admission window.
* Exponential backoff parameters: base delay 500 ms, multiplier 2x, jitter +/- 20%, capped at 2 minutes unless interface docs state otherwise.
* Users can manually retry after fatal failures, manual retries reset the backoff sequence.

### 8.3 Input validation

* Validation runs locally using schema definitions (JSON Schema, Protobuf, or generated types). Missing required fields, length violations, or invalid references are blocked before sending to the backend.
* Localization ensures error strings are user-friendly but still reference canonical fields to aid debugging.

## 9. Observability and diagnostics

### 9.1 Structured logging

* Logs include timestamp, severity, correlation ID, [OperationContext](05-operation-context.md) summary (redacted), request and response identifiers, and error codes so backend auditors can map them to the canonical error catalog in [01-protocol/10-errors-and-failure-modes.md](../../01-protocol/10-errors-and-failure-modes.md).
* Sensitive payloads are redacted, replaced with stable tokens so operators can correlate logs without exposing content.
* Logs are stored locally until uploaded via Operations Console diagnostics endpoints. Users must opt in before uploads occur.

### 9.2 Metrics and health signals

* Clients sample metrics such as request latency, cache hit ratio, pending write count, and sync backlog size.
* When backend surfaces support it, clients publish aggregated metrics via `POST /system/ops/clients/telemetry` (to be documented in [04-interfaces/http/ops.md](../../04-interfaces/http/ops.md)).

### 9.3 Crash and issue reporting

* Crash reports include anonymized stack traces, app version, platform details, and correlation IDs for the last failed request. They exclude raw payloads unless the user opts into enhanced diagnostics.
* Reports are signed and encrypted before upload so backend services can verify authenticity.

## 10. Distribution, release, and updates

### 10.1 Packaging

* Builds embed manifest data: slug, `app_id`, semantic version, supported platforms, minimum backend version, capability catalog checksum, and commit hash so compatibility checks align with [01-protocol/10-versioning-and-compatibility.md](../../01-protocol/10-versioning-and-compatibility.md).
* Packages are signed. Native apps use platform-specific signing (CodeSign, APK Signature Scheme, etc.). Web apps publish subresource integrity hashes for critical bundles.

### 10.2 Update strategy

* Clients check for updates via [App Manager](../managers/08-app-manager.md)-provided endpoints, applying the negotiation rules in [01-protocol/10-versioning-and-compatibility.md](../../01-protocol/10-versioning-and-compatibility.md). Autoupdate policies respect user settings and enterprise controls.
* When backend minimum versions increase, clients detect incompatibility pre-login and display blocking screens with upgrade instructions.
* Rollbacks follow signed package verification, clients maintain at least one known-good build for offline recovery.

### 10.3 Device lifecycle

* Installation registers the device with Device Manager via bootstrap flows ([01-protocol/05-keys-and-identity.md](../../01-protocol/05-keys-and-identity.md)).
* Uninstallation triggers deregistration calls when connectivity exists, otherwise, the next bootstrap attempt must detect orphaned entries and clean up.
* Wipes remove all local data, keys, caches, and pending writes, leaving nothing recoverable without re-authentication.

## 11. Security posture

### 11.1 Threat model alignment

* Frontend threat assumptions mirror [05-security/**](../../05-security/**) and the crypto/posture controls in [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md), the device may be compromised, but the app must minimize secrets at rest, detect tampering where possible, and fail safely when invariants break.
* Tamper detection includes verifying bundle signatures, runtime integrity checks (optional), and refusing to run on rooted or jailbroken devices if policy demands.

### 11.2 Permissions and sandboxing

* Clients request the minimal OS permissions needed (filesystem, contacts, notifications). Access to sensors or PII requires explicit justification documented in release notes.
* Sandboxing features (App Sandbox, Android Scoped Storage) are mandatory when available. Shared storage is used only for user-exported artifacts.

### 11.3 Supply-chain controls

* Dependencies are pinned with checksums, verified at build time, and scanned per [05-security/dependency-policy.md](../../05-security/dependency-policy.md).
* Build pipelines produce reproducible artifacts where feasible so auditors can verify shipped binaries match source.

### 11.4 Data export and interoperability

* Exports occur via backend-approved flows (for example, zipped graph slices). Clients never bypass the backend to read raw storage, preserving the ordering and authorship guarantees in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md).
* When offering offline exports, clients encrypt archives and require user-provided passphrases, following the key-handling rules in [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md). Keys are never reused.

## 12. Backend integration semantics

### 12.1 System service interactions

* Frontends must obey service-specific requirements from [02-architecture/services-and-apps/02-system-services.md](02-system-services.md). For example:

  * Bootstrap flows call SBPS endpoints sequentially, verifying each stage before advancing.
  * Identity actions follow Identity Service ACL prompts, ensuring capability edges exist before exposing contact management UI.
  * Feed experiences honor Base Feed Service pagination, moderation flows, and cost hints.

### 12.2 App extension coordination

* When an app extension exposes new APIs, the frontend must fetch the manifest (version, capability list, schema requirements) from [App Manager](../managers/08-app-manager.md) before calling them.
* Extension unavailability is normal. Clients detect it by observing `503 ExtensionDisabled` errors and degrade gracefully (hide UI, queue operations, or reroute to fallback services).

### 12.3 [OperationContext](05-operation-context.md) verification

* Frontends log the [OperationContext](05-operation-context.md) hash the backend echoes in responses to prove end-to-end traceability, preserving the envelope commitments in [01-protocol/03-serialization-and-envelopes.md](../../01-protocol/03-serialization-and-envelopes.md). Hash mismatches trigger alerts and block further operations until resolved.
* For long-running workflows (multi-step forms), the client stores interim [OperationContext](05-operation-context.md) templates to ensure the final submission matches the initial capability intent.

## 13. Application configuration and build lifecycle

### 13.1 Configuration contract

* App configuration lives in graph-backed objects owned by the app and mirrored in [Config Manager](../managers/01-config-manager.md) under `app.<slug>.*`, following the ownership rules in [01-protocol/02-object-model.md](../../01-protocol/02-object-model.md). Frontends must expose UI or CLI to edit documented keys, validate input locally, and submit mutations via the same manager pipeline system services use (schema -> ACL -> graph).
* Each configuration key declares: datatype, validation rules, required capability for mutation, default value, and rollout semantics (static, hot-reloadable, experiment gated). Documentation belongs inside the app manifest so [App Manager](../managers/08-app-manager.md) can expose it to operators.
* Configuration snapshots are versioned. Clients include the current config hash in [OperationContext](05-operation-context.md) metadata so backend services can reject stale assumptions with `ERR_CONFIG_STALE`.
* Sensitive configuration (API secrets, federation tokens) never travels through plaintext UI flows. Instead, clients request pre-signed upload slots that encrypt the value client side per [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md), produce an object reference, and store only handles in configuration entries.

### 13.2 Build and packaging workflow

* Build pipelines ingest schemas, capability catalogs, and configuration defaults from the graph, generate strongly typed clients from [04-interfaces/**](../../04-interfaces/**), and embed immutable manifests plus compatibility metadata directly into artifacts.
* Source control tags must map 1:1 with shipped versions. Build metadata includes commit hash, dependency lockfile hash, and manifest version so backend telemetry can trace requests to reproducible builds.
* Continuous integration executes lint, unit, schema validation, and [OperationContext](05-operation-context.md) assembly tests on every change. Builds fail if generated interface clients differ from checked-in versions, preventing drift from backend contracts.
* Release automation signs artifacts (per [01-protocol/04-cryptography.md](../../01-protocol/04-cryptography.md)), pushes them to distribution channels, and publishes manifest updates to [App Manager](../managers/08-app-manager.md) so nodes can verify compatibility before accepting the new build.

### 13.3 Environment and configuration separation

* Development, staging, and production builds use distinct `app_id` values or `app_variant` markers when shared `app_id` is unavoidable. Mixing environments is forbidden because the backend treats `app_id` as an isolation boundary.
* Environment-specific configuration (API endpoints, telemetry sinks, feature flags) is injected via signed config bundles, not by editing source code per environment. Bundles are validated by [Config Manager](../managers/01-config-manager.md) and hashed for attestation.
* Rooted or jailbroken detection thresholds and logging verbosity may differ by environment, but admission requirements, [OperationContext](05-operation-context.md) structure, and capability enforcement remain identical to ensure staging faithfully exercises production rules.

### 13.4 Developer tooling and testing

* SDKs expose helpers for [OperationContext](05-operation-context.md) assembly, schema validation, pending-write journaling, and admission feedback handling so app developers cannot bypass required behavior accidentally.
* Local development tools spin up mock backends by replaying signed fixtures derived from the canonical specs. Tools must never turn off ACL or schema validation; instead they provide deterministic fixtures for faster iteration.
* Automated test suites cover:

  * Capability checks per surface (UI plus API) to confirm missing permissions disable functionality.
  * Schema evolution handling: load previous cache snapshots, apply new schema definitions, ensure incompatible entries purge deterministically.
  * Config rollouts: apply staged configuration snapshots, confirm clients detect hash changes, reload values, and update UI or automation accordingly.
* Release gates require integration tests against the target backend version, verifying interface compatibility, sync behavior, and [OperationContext](05-operation-context.md) logging before publication.

## 14. Implementation checklist

1. **App identity**: Slug, `app_id`, manifest, and compatibility matrix registered with [App Manager](../managers/08-app-manager.md).
2. **[OperationContext](05-operation-context.md) discipline**: Every request includes immutable [OperationContext](05-operation-context.md) data derived from authenticated sessions and build metadata, retries rebuild context.
3. **Capability gating**: UI and automation surfaces inspect current capability catalogs before enabling actions, revoked capabilities disable controls immediately.
4. **Transport compliance**: HTTP or WebSocket clients honor [04-interfaces/**](../../04-interfaces/**) contracts, enforce TLS or Noise, surface backend admission feedback, and implement structured retries.
5. **Local storage**: Pending writes, caches, and secrets stored in encrypted containers, bounded by schema versions, and wiped on logout or device removal.
6. **Offline handling**: Pending write log with deterministic ordering, conflict prompts, and schema-aware validation, sync scheduler respecting power and network posture.
7. **Error handling**: Canonical error mapping to UX, deterministic logging, and exponential backoff aligned with interface hints.
8. **Observability**: Structured logs, metrics sampling, crash diagnostics, and optional telemetry uploads wired through documented endpoints with user consent.
9. **Security**: Key handling, sandboxing, dependency pinning, tamper detection, and supply-chain checks aligned with [05-security/**](../../05-security/**).
10. **Distribution**: Signed packages, auto-update policies, rollback capability, and manifest embedding to ensure compatibility enforcement.
11. **Integration**: Service-specific behaviors implemented per system service specs, extension manifests respected, and [OperationContext](05-operation-context.md) hashes verified end to end.
12. **Testing**: Automated tests cover [OperationContext](05-operation-context.md) assembly, capability gating, schema validation, pending write ordering, sync conflict handling, admission-feedback handling, and error rendering.

Meeting this checklist ensures frontend apps uphold the same structural guarantees as backend components, letting any deployment trust that user intent, access control, and state transitions remain verifiable from UI to graph commit.
