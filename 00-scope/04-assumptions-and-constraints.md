



# 01 Scope and goals

## 1. Purpose and scope

This document defines the scope boundaries and goals of the 2WAY proof of concept design. It constrains what the PoC must implement and what is explicitly excluded. It defines repository level invariants that all components must honor. Detailed protocol, data model, APIs, and security properties are defined in their respective design files and are only referenced here.

## 2. Responsibilities

This specification defines:

- What the PoC includes at the system boundary level.
- The goals that determine PoC completeness.
- Repository wide invariants and constraints that other design files assume.
- What is allowed and forbidden at the scope level.
- Failure handling in terms of design compliance, not runtime behavior.

This specification does not define:

- Protocol wire formats, message envelopes, or sync package schemas.
- Database schemas or table layouts.
- Detailed manager interfaces or internal flows.
- Security mechanisms beyond scope level constraints.

## 3. Scope definition

### 3.1 In scope

The PoC design includes the following major elements:
- A backend composed of managers and services only.
- A frontend that hosts all apps.
- A graph based persistence model using SQLite for backend storage.
- A local API surface consisting of HTTP endpoints and a WebSocket channel for event pushes.
- A network transport model that operates over Tor for peer connectivity.
- A cryptographic model for signing and encryption using secp256k1 signatures and ECIES for confidentiality where required.
- A sync model driven by monotonic global sequence ordering and explicit sequence ranges.
- A security model rooted in graph anchored identities, schema validation, ACL enforcement, and domain scoping.

### 3.2 Out of scope

Non goals and exclusions are specified in `/00-scope/02-non-goals-and-out-of-scope.md`. This file adds only the following hard exclusions because they materially affect PoC boundary correctness:
- No direct database writes by apps or services.
- No manager bypass through alternative persistence paths.
- No reliance on transport level security as a correctness requirement.
- No assumptions of peer trust beyond what the graph and ACLs encode.

## 4. Goals

### 4.1 Primary PoC goals

The PoC is complete only if it satisfies all of the following:
- Enforces the manager and service separation and prevents raw persistence access outside Graph Manager controlled writes.
- Enforces schema validation and ACL enforcement for every graph mutation.
- Ensures all operations are bound to an explicit author identity and are verifiable against stored public keys.
- Implements a working local API surface that exercises core graph mutations and read paths through the defined validation pipeline.
- Implements peer sync over Tor with signature verification and sequence ordering constraints.
- Preserves app isolation through app scoped types, schemas, and domain rules.

### 4.2 Secondary PoC goals

The PoC should also satisfy the following where defined elsewhere in this repository:
- Maintain deterministic rejection behavior for invalid, malformed, or unauthorized operations.
- Maintain stable persistence guarantees under process restart and partial failure.
- Support selective sync and scoping controls as defined by sync domains and ACL visibility rules.

## 5. Repository wide invariants and guarantees

### 5.1 Invariants

The following invariants are mandatory across the PoC:
- Backend code consists of managers and services only.
- Frontend hosts all apps.
- Apps may ship backend extensions, but all backend logic must still use manager interfaces.
- All graph writes occur via Graph Manager.
- All access control occurs via ACL Manager.
- All schema definitions originate from the graph and are compiled and served by Schema Manager.
- All sync state and sync application occur via State Manager.
- All network traffic flows through Network Manager.
- All WebSocket push events flow through Event Manager.

### 5.2 Scope level guarantees

Given adherence to the invariants in this file and the detailed specifications elsewhere, the PoC design guarantees the following at the scope level:
- There is a single enforced write path to persistent state.
- There is a single enforced authorization gate for mutations.
- There is a single enforced schema validation gate for type and relation correctness.
- No app can directly mutate or reinterpret another app’s objects through backend bypass.
- Peer input is treated as untrusted and is subject to the same validation and authorization pipeline as local input.

## 6. Allowed behaviors

The following behaviors are explicitly allowed within the PoC scope:
- Nodes may operate offline indefinitely and remain internally consistent.
- Peers may be malicious, unreliable, or non cooperative.
- Sync relationships may be partial, asymmetric, and selective by domain.
- Multiple apps may interpret the same underlying graph objects differently, provided they do not violate schema and app scoping rules.
- A node may reject remote operations without providing a remote visible explanation.

## 7. Forbidden behaviors

The following behaviors are explicitly forbidden within the PoC scope:
- Any persistent write that does not pass through Graph Manager.
- Any authorization decision made outside ACL Manager.
- Any acceptance of graph mutations that skip Schema Manager validation.
- Any implicit trust derived from transport properties, network location, or peer claims not anchored to graph identities.
- Any cross app mutation or cross app semantic reinterpretation at the backend layer.
- Any storage API that allows apps or services to write arbitrary tables or bypass graph invariants.

## 8. Trust boundaries

### 8.1 Inputs

The system treats the following as untrusted inputs:
- All network delivered packages, envelopes, and payloads.
- All frontend initiated requests and submitted objects.
- All app provided data and app provided backend extension logic inputs.

### 8.2 Trusted components

Within the PoC scope, the following are treated as trusted to enforce correctness, provided the local execution environment assumptions hold:
- Backend managers.
- Validation pipeline ordering across Graph Manager, Schema Manager, and ACL Manager.
- Storage Manager as a persistence primitive accessible only through manager controlled paths.

## 9. Failure and rejection handling

### 9.1 Scope compliance failure

If an implementation violates any invariant or forbidden behavior in this file, the implementation is non compliant with this design repository. Non compliance is a correctness failure, not a degraded mode.

### 9.2 Operational rejection behavior

When an operation, envelope, or request violates a constraint assumed by this scope, the system must reject it before any persistent mutation occurs. Detailed rejection rules are specified in the protocol, API, and security design files. This file requires that rejection be deterministic and that no partial writes occur.

### 9.3 Assumption violation

If execution environment assumptions do not hold, including host compromise, key exfiltration, or backend modification, the security properties described in this repository do not apply. Recovery mechanisms and revocation semantics are defined in the security design files and are not redefined here.
