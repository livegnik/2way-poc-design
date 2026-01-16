



# 05 Operation Context

## 1. Purpose and scope

OperationContext is the immutable per-request envelope that binds identity, application, capability intent, trust posture, execution origin, and trace metadata to every backend action. It is the single authoritative structure used by managers to enforce authorization, app isolation, auditability, and local versus remote semantics. No service, extension, or manager that executes request-scoped work may be invoked without a complete and valid OperationContext.

This specification defines the required fields, construction rules, lifecycle behavior, and consumption requirements for OperationContext across frontend requests, system services, app backend extensions, automation jobs, internal engines, and remote synchronization handling. It is the canonical source for OperationContext semantics referenced throughout the protocol and architecture.

### 1.1 Responsibilities and boundaries

This specification is responsible for the following:

* Defining the canonical OperationContext structure and the semantics of every field.
* Declaring deterministic construction rules for local execution paths and remote sync paths.
* Defining immutability rules and lifecycle guarantees.
* Specifying how services and internal engines may derive enriched contexts without mutating identity bindings.
* Defining how OperationContext is consumed by Graph Manager, ACL Manager, State Manager, Event Manager, Log Manager, and Health Manager.
* Defining failure and rejection posture for malformed or incomplete contexts.

This specification does not cover the following:

* Schema definitions, ACL rule syntax, or envelope serialization formats.
* Cryptographic verification, handshake protocols, or transport-level concerns.
* Application UX behavior or frontend configuration beyond required context fields.

### 1.2 Invariants and guarantees

Across all components, execution paths, and managers that use OperationContext, the following invariants and guarantees hold:

* Every request-scoped manager invocation receives a complete OperationContext.
* OperationContext is immutable after construction. In-place mutation is forbidden.
* Identity binding is authoritative and originates only from trusted managers.
* `app_id` is always present and correctly bound.
* Local and remote semantics are explicitly distinguished and never inferred.
* Remote OperationContexts are never derived from client-supplied metadata.
* Trace identifiers are present and stable for the lifetime of the operation.
* Missing or malformed OperationContexts are rejected before schema or ACL evaluation.

These guarantees hold regardless of caller, execution engine, transport, or peer behavior unless explicitly stated otherwise.

---

## 2. OperationContext model

### 2.1 Definition and role

OperationContext is the per-request execution contract that binds:

* **Who is acting**: identity, device, delegation, or peer.
* **On behalf of which app**: application identity and version.
* **What capability is invoked**: explicit verb evaluated by ACL.
* **How execution entered the system**: local, remote, automated.
* **How the action is observed**: traceability and audit scope.

Managers treat OperationContext as authoritative metadata. No manager infers missing information from envelopes, payloads, schema content, or transport details.

### 2.2 Context variants

OperationContext exists in the following variants:

| Variant        | Origin                                           | Characteristics                                 |
| -------------- | ------------------------------------------------ | ----------------------------------------------- |
| Local request  | HTTP or WebSocket entrypoint after Auth Manager  | `is_remote=false`, requester identity bound     |
| Remote sync    | State Manager after Network Manager verification | `is_remote=true`, remote peer identity bound    |
| Automation job | Service-owned scheduler or internal engine       | Synthetic actor identity, controlled capability |

All variants share the same structural fields. Differences exist only in field population and trusted source.

---

## 3. Field catalog

All fields use lowercase snake_case. All required fields must be present at construction time.

| Field                     | Required    | Source                       | Semantics                                                           |
| ------------------------- | ----------- | ---------------------------- | ------------------------------------------------------------------- |
| `app_id`                  | Yes         | App Manager or routing layer | Owning application identity. System services use `app_0`.           |
| `requester_identity_id`   | Local only  | Auth Manager                 | Local user or delegated identity; nullable for explicit public endpoints. |
| `device_id`               | Optional    | Auth Manager                 | Bound device identity for local users.                              |
| `delegated_key_id`        | Optional    | Auth Manager                 | Delegated signing key reference.                                    |
| `actor_type`              | Yes         | Entry layer or service       | `user`, `app_service`, `app_automation` (alias: `automation`), `delegate`, `remote_peer`. |
| `capability`              | Local only  | Service or engine            | Explicit verb evaluated by ACL.                                     |
| `is_admin`                | Optional    | Auth Manager                 | Administrative gating flag. Never bypasses ACL.                     |
| `is_remote`               | Yes         | Construction layer           | Local or remote execution flag.                                     |
| `sync_domain`             | Remote only | State Manager                | Domain being synchronized.                                          |
| `remote_node_identity_id` | Remote only | State Manager                | Verified peer identity.                                             |
| `trace_id`                | Yes         | Entry layer or State Manager | Stable trace identifier.                                            |
| `correlation_id`          | Optional    | Client or service            | Cross-request workflow identifier.                                  |
| `app_version`             | Optional    | Frontend or service          | Diagnostic metadata.                                                |
| `locale`                  | Optional    | Frontend                     | Non-authoritative UX metadata.                                      |
| `timezone`                | Optional    | Frontend                     | Non-authoritative UX metadata.                                      |
| `dos_cost_class`          | Optional    | Service or engine            | DoS Guard cost hint.                                                |

Field completeness is validated at construction time. Missing required fields result in immediate rejection.

---

## 4. Construction and lifecycle

### 4.1 Local HTTP and WebSocket requests

Construction flow:

1. Interface authenticates request via Auth Manager.
2. Auth Manager resolves requester identity, device, delegation, and admin gating.
3. Interface binds `app_id`, sets `is_remote=false`, and generates `trace_id`.
4. Service or interface middleware assigns `capability` and `actor_type`.
5. OperationContext is constructed and frozen.
6. OperationContext is passed to all downstream managers.

OperationContext must never be created before authentication succeeds.

### 4.2 Service and engine enrichment

Services and internal engines may derive enriched OperationContexts only by creating a new instance that copies identity and app bindings.

Permitted enrichment:

* Capability specialization.
* Actor type refinement for automation or delegation.
* DoS Guard cost classification.
* Correlation metadata.

Forbidden actions:

* Replacing identity bindings.
* Modifying `app_id`.
* Mutating an existing context.

### 4.3 Remote sync ingestion

Remote OperationContext construction is owned exclusively by State Manager after Network Manager verification.

Rules:

* `is_remote=true`
* `remote_node_identity_id` bound from verified peer identity.
* `sync_domain` bound from sync metadata.
* `trace_id` copied from envelope if present, otherwise generated.

Remote contexts never include local requester identity fields.

### 4.4 Automation jobs and internal execution

Automation and scheduled work execute under synthetic OperationContexts.

Rules:

* `actor_type` set to `app_service` or `app_automation`.
* `capability` explicitly defined.
* `requester_identity_id` set only when acting on behalf of a user.
* Each execution builds a fresh OperationContext.

Reuse of contexts across runs is forbidden.

### 4.5 Immutability and retries

OperationContext is immutable.

Retry behavior:

* New `trace_id` generated.
* Original `correlation_id` preserved if present.
* No field reuse via mutation.

---

## 5. Field semantics and validation

### 5.1 Identity binding

* Local identity is authoritative only when bound by Auth Manager.
* Remote identity is authoritative only when bound by State Manager.
* Device and delegated identifiers participate in ACL evaluation but do not replace identity.

### 5.2 Capability and actor type

* `capability` must name the exact action being attempted.
* `actor_type` distinguishes human, service, automation, delegation, and peer traffic.
* `remote_peer` actor type is reserved exclusively for remote sync contexts.
* Remote sync contexts may omit `capability`; authorization relies on identity, app, and schema constraints.

### 5.3 Trace and correlation identifiers

* `trace_id` is mandatory for all contexts.
* If present in an envelope, it must be copied verbatim.
* `correlation_id` is optional and never authoritative.

### 5.4 Local and remote field separation

* Local contexts must not include remote-only fields.
* Remote contexts must not include local-only fields (`requester_identity_id`, `device_id`, `delegated_key_id`, `capability`).
* Violations result in immediate rejection.

---

## 6. Manager consumption requirements

Managers consume OperationContext as follows:

* **Graph Manager** enforces app isolation, ownership, and remote sync constraints.
* **ACL Manager** evaluates identity, delegation, device, capability, and app bindings.
* **State Manager** uses context to gate sync application and domain enforcement.
* **Event Manager** applies visibility filtering and audience scoping.
* **Log Manager** records immutable context snapshots for audit trails.
* **Health Manager** uses `is_admin` only for access gating, never as an ACL bypass.
* **DoS Guard Manager** does not rely on OperationContext for admission decisions; cost hints are service metadata passed through the interface layer.

Managers must reject any invocation lacking required context fields.

---

## 7. Failure handling and rejection posture

* Missing or malformed OperationContext is a structural failure.
* Structural failures are rejected before schema or ACL evaluation.
* Attempted mutation after construction is logged and rejected.
* Remote contexts missing required remote fields are rejected by State Manager.
* Errors must use canonical classifications defined in protocol error specifications.

---

## 8. Observability and auditing

* Every audited action records a full OperationContext snapshot.
* `trace_id`, `app_id`, actor type, and remote flags are always preserved.
* Sensitive cryptographic material is never logged.
* Context-derived metadata may be embedded in events where required.

---

## 9. Implementation checklist

1. Auth Manager binds identity before context construction.
2. State Manager constructs all remote contexts.
3. All call paths supply required fields.
4. OperationContext is immutable everywhere.
5. Capabilities are explicit and specific.
6. Remote and local fields are never mixed.
7. All audited actions include context snapshots.
