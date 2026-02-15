



# 02 Non-goals and out-of-scope

Defines excluded behaviors, assumptions, and guarantees for the 2WAY PoC. Specifies non-goals, forbidden interactions, and rejection expectations. Constrains trust dependencies and enforcement boundaries for excluded features.

For the meta specifications, see [02-non-goals-and-out-of-scope meta](../10-appendix/meta/00-scope/02-non-goals-and-out-of-scope-meta.md).

## 1. Responsibilities, invariants, and guarantees

### 1.1 Responsibilities

- Define excluded behaviors and guarantees at the system and protocol boundary.
- Define forbidden interactions that violate the manager, service, and app separation.
- Define rejection expectations when excluded assumptions are relied upon.

### 1.2 Invariants

- Any behavior not specified in the design documents must be treated as unsupported.
- No component may assume properties that are excluded by this document.
- Apps and app services must not change, bypass, or redefine backend invariants.

### 1.3 Guarantees

- The system provides no hidden functionality beyond what is specified in the scope documents and referenced design files.
- Excluded behaviors are not relied upon by any manager or service.
- Violations of exclusions are treated as non-compliance, not as optional app services.

## 2. Non-goals

### 2.1 Centralized trust anchors and external identity binding

The protocol does not define or require any centralized authority for identity verification.

- There is no requirement for KYC, biometric verification, or government identity binding.
- There is no global identity registry.
- Cryptographic identity is defined by keys represented in the graph, not by external attestations.

### 2.2 Protocol-level Sybil prevention

The protocol does not provide global Sybil prevention mechanisms.

- There is no proof-of-work, proof-of-stake, or proof-of-personhood mechanism in the protocol.
- Sybil resistance is structural and local, based on graph relationships and app-defined rules.
- The protocol does not claim to prevent creation of many identities by one actor.

### 2.3 Global consensus and a single canonical state

The protocol does not define global consensus.

- There is no global total order across all nodes.
- There is no requirement that all nodes converge to identical state.
- Correctness is enforced locally by each node according to validation and access control rules.

### 2.4 Backend extensibility that modifies the kernel

The backend does not support arbitrary app service modification of core behavior.

- There is no concept of backend apps that can redefine core behavior.
- There is no arbitrary module execution model in the backend.
- App services do not define the protocol, do not modify core services, and do not alter backend invariants.

### 2.5 Unmediated access to persistence or key material

The design does not permit direct access to persistent storage or private keys outside the defined manager interfaces.

- Apps and app services must not write to storage except through [Graph Manager](../02-architecture/managers/07-graph-manager.md) mediated flows.
- Apps and app services must never access raw database connections.
- Apps and app services must never access private keys through any interface that bypasses the [Key Manager](../02-architecture/managers/03-key-manager.md) and authorization checks.

### 2.6 Transport-layer security as a dependency

The protocol does not rely on transport security guarantees.

- Confidentiality and integrity are defined at the protocol layer using signatures and encryption where required.
- The protocol must remain valid on untrusted networks.
- Use of Tor is a deployment choice for the PoC, not a protocol security dependency.

## 3. Out-of-scope behaviors and interactions

### 3.1 Allowed behaviors

The following are explicitly allowed within the scope of the PoC design.

- Apps define UI and workflows on the frontend and use backend HTTP and WebSocket APIs.
- Apps may ship app services to perform limited backend tasks.
- App services may read and write graph state only through manager interfaces and must pass through schema validation and ACL enforcement.

### 3.2 Forbidden behaviors

The following are explicitly forbidden.

- Any component bypassing [Graph Manager](../02-architecture/managers/07-graph-manager.md) for graph writes.
- Any component bypassing [ACL Manager](../02-architecture/managers/06-acl-manager.md) for authorization decisions on reads or writes.
- Any app or app service redefining schema semantics outside [Schema Manager](../02-architecture/managers/05-schema-manager.md) handling.
- Any app or app service accessing raw database handles.
- Any app or app service accessing or exporting private keys, or performing signing outside approved key usage paths defined by [Key Manager](../02-architecture/managers/03-key-manager.md).
- Any implementation depending on implicit identity, implicit trust, or network-origin trust.

## 4. Trust boundaries and dependencies

- This document defines design-time boundaries only.
- Inputs are repository design assumptions and constraints.
- Outputs are review constraints that apply to all components.
- Trust boundaries are enforced through the managers and their interfaces, and through the validation pipeline described in [01-protocol](../01-protocol/) and [02-architecture](../02-architecture/).
- This document does not define protocol formats or manager interfaces and must not be used as a substitute for those specifications.

## 5. Failure, rejection, and invalid assumptions

### 5.1 Design-time failure

If a design, component, or review depends on an excluded feature or guarantee, the result is non-compliance with the repository design.

- The dependency must be removed.
- The component must be redesigned to use only specified interfaces and guarantees.
- The review must treat the dependency as a correctness and security defect.

### 5.2 Runtime rejection expectation

Where an excluded assumption manifests as a runtime attempt, the system must reject the action at the appropriate validation boundary.

- Unauthorized operations are denied by ACL evaluation.
- Invalid structure and invariant violations are rejected by Graph and Schema validation.
- Attempts to bypass managers are not permitted by design, and must not exist in compliant implementations.
