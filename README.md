



# 2WAY System Design PoC Repository

## 1. Purpose and scope

This repository defines the normative design for the 2WAY proof of concept (PoC) system. It specifies the protocol, architecture, security model, data structures, and component boundaries necessary to implement and evaluate the PoC.

This is a design specification, not an implementation. It outlines required behavior, invariants, and constraints. All documents are binding unless explicitly marked otherwise.

The scope is limited to the elements necessary for building a correct, secure, and interoperable PoC.

## 2. System overview

2WAY is a peer to peer application platform that provides identity, data ownership, access control, synchronization, and trust semantics as shared infrastructure rather than application specific logic.

Applications built on 2WAY do not operate on isolated databases or central backends. They operate on a shared, local first graph that represents users, devices, relationships, content, and app specific state under a single identity and permission model. This allows multiple independent apps to interoperate over the same data without sharing control or authority.

The platform enables applications to:

- Share user owned data across apps without central storage.
- Compose multiple applications over a common identity, contact, and trust graph.
- Enforce permissions and visibility structurally rather than through server side policy.
- Synchronize state directly between peers without trusted intermediaries.
- Operate offline with full local authority and reconcile state incrementally.
- Limit the influence of unknown or untrusted identities through graph structure.
- Provide verifiable authorship, provenance, and ordering for all application state.
- Recover from compromise or corruption using cryptographically anchored history.
- Delegate scoped authority to devices, services, or automated agents.
- Isolate application logic while reusing common identity, trust, and sync primitives.

All actors and data are represented as typed graph objects with immutable authorship and explicit ownership. Identity is the root of trust. Every operation may be cryptographically signed. Every mutation is validated. Access control is enforced through schema and graph boundaries rather than implicit context.

Each node maintains its own authoritative state. Nodes exchange data using signed, ordered synchronization envelopes. No node is required to trust remote peers, transports, or infrastructure. Consistency emerges from deterministic validation, strict ordering, and explicit synchronization rules rather than global coordination.

The system is designed to operate under partial compromise. Individual applications, devices, peers, or identities may become hostile without compromising unrelated state or violating global invariants.

## 3. Design principles

The design adheres to the following principles:

- Identity is explicit, cryptographic, and first class.
- All state transitions are verifiable.
- Trust is minimized and distributed.
- Authority is explicitly scoped and delegated.
- History is append only and tamper evident.
- Isolation is enforced between applications and domains.
- Validation precedes persistence.
- Failure modes are explicit and closed by default.

These principles are enforced structurally and are mandatory.

## 4. Document authority and interpretation

This repository is internally self consistent.

The following rules apply:

- All documents are normative unless explicitly marked as informational.
- Lower numbered sections override higher numbered sections within the same file.
- More specific documents override more general documents where conflicts exist.
- Architecture Decision Records override prior design text for the decisions they cover.

No external documents are required to interpret or implement this design.

## 5. Repository organization

Documents are organized by conceptual dependency. Earlier sections define constraints and rules that later sections rely on. Readers are expected to progress in this order when approaching the system for the first time.

The repository is structured as follows:

- Scope, assumptions, and system constraints.
- Protocol definition, including identity, object model, and synchronization rules.
- Architecture and component model, including managers, services, and trust boundaries.
- Data layout and interfaces, including persistence, APIs, and ordering guarantees.
- Security model, including threat assumptions, enforcement layers, and recovery mechanisms.
- End to end flows describing normative system behavior.
- PoC definition, build plan, testing strategy, and acceptance criteria.
- Architecture decisions that record resolved tradeoffs and deviations.
- Appendices and reference material.
- Examples of applications and platform usage.

Each directory is self contained. Cross references are explicit and normative.

## 6. Design responsibilities

This repository defines the normative behavior of the 2WAY system, including:

- The protocol governing identity, authorship, validation, authorization, and synchronization.
- The architectural separation and trust boundaries between managers, services, applications, and frontends.
- The security invariants enforced under adversarial and partially compromised conditions.
- The graph based data model, including object types, ownership rules, and persistence guarantees.
- The allowed and forbidden interactions between system components.
- Failure handling, rejection semantics, and error containment behavior.

This repository explicitly does not define:

- User interface behavior or presentation logic.
- Performance optimizations beyond stated resource and correctness constraints.
- Deployment, orchestration, or infrastructure automation.
- Operational monitoring or observability beyond logging semantics.

## 7. Global invariants

The following invariants apply system wide unless explicitly overridden by a more specific rule:

- Every operation is bound to a verifiable cryptographic identity.
- All graph mutations pass through Graph Manager, Schema Manager, and ACL Manager.
- Ownership of Parents is immutable for the lifetime of the object.
- Persistent ordering derives exclusively from monotonically increasing sequence numbers.
- Accepted history is never rewritten or retroactively altered.
- Applications are isolated through schema and domain boundaries.
- Backend managers form a trusted kernel and are not extensible or bypassable by applications.

Violation of any invariant constitutes a correctness failure and results in rejection of the violating operation.

## 8. Allowed and forbidden behaviors

This section defines behaviors that are explicitly permitted or prohibited by the design. Any behavior not listed as allowed is forbidden unless explicitly specified elsewhere.

### 8.1 Allowed behaviors

- Nodes validate, reject, and persist operations independently based on local state.
- Peers exchange signed and optionally encrypted synchronization envelopes.
- Applications define domain specific semantics exclusively through schemas and domain rules.
- Identities delegate scoped authority through explicit graph relationships.
- Nodes operate offline with full local authority and resume synchronization incrementally.
- Nodes selectively synchronize data according to domain and access control rules.

### 8.2 Forbidden behaviors

- Implicit trust based on network location, transport layer, or peer identity.
- Direct access to persistent storage outside Storage Manager.
- Direct acces to graph mutation outside Graph Manager.
- Cross application reinterpretation or mutation of objects.
- Retroactive modification or deletion of owned objects.
- Global trust, reputation, or authority assumptions.
- Privilege escalation through synchronization or envelope replay.

Any forbidden behavior constitutes a protocol violation and must be rejected.

## 9. Component interaction model

Components interact only through explicitly defined interfaces and trust boundaries.

- Frontend applications submit operations exclusively through documented APIs.
- Backend services operate with explicit and minimal manager references.
- Managers communicate only through internal interfaces and never bypass validation layers.
- All network input crosses a trust boundary and is treated as untrusted.
- Persistent storage is reachable exclusively through Storage Manager.
- All graph mutations occur exclusively through Graph Manager.

No component may infer authority or trust outside these interfaces. Trust boundaries are enforced structurally at every interaction point.

## 10. Failure and rejection behavior

The system fails closed under all error conditions.

- Invalid or malformed input is rejected before any persistent state change.
- Unauthorized operations are rejected without side effects.
- Malformed or unverifiable envelopes are discarded immediately.
- Replayed, out of order, or inconsistent sync data is ignored.
- Operations signed by revoked keys are rejected regardless of sequence order.

Failures are logged for audit and recovery purposes. Partial state application is not permitted.

## 11. Conformance

An implementation conforms to this design if and only if:

- All global and local invariants defined in this repository hold under all allowed operations.
- All forbidden behaviors are structurally impossible to execute.
- All security properties defined in the security documentation are enforced.
- All protocol rules are implemented exactly as specified.

Any deviation from this design requires an explicit Architecture Decision Record.
