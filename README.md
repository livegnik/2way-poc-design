



# 2WAY System Design PoC Repository

## 1. Purpose and scope

This repository defines the complete normative design of the 2WAY proof of concept (PoC) system. It specifies the protocol, architecture, security model, data structures, and component boundaries required to implement and evaluate a 2WAY proof of concept.

This repository is a design specification, not an implementation. It describes required behavior, invariants, and constraints. All documents are binding unless explicitly marked otherwise.

The scope is limited to what is required to build a correct, secure, interoperable PoC.

## 2. System overview

2WAY is a local first, identity anchored, graph based system for peer to peer interaction between users, devices, and applications.

The system models all actors and data as typed graph objects with immutable authorship and explicit ownership. Identity is the root of trust. Every operation is signed. Every mutation is validated. All access control is enforced structurally rather than implicitly.

Each node maintains its own authoritative state. Nodes exchange data through signed, ordered synchronization envelopes. No node is required to trust remote peers, transports, or infrastructure. Consistency is achieved through deterministic validation, strict ordering, and explicit sync rules rather than global coordination.

The system is designed to operate under partial compromise. Individual apps, devices, peers, or identities may become hostile without compromising the integrity of unrelated state.

## 3. Design principles

The design adheres to the following principles:

- Identity is explicit, cryptographic, and first class.
- All state transitions are verifiable.
- Trust is minimized and distributed.
- Authority is scoped and delegated explicitly.
- History is append only and tamper evident.
- Isolation is enforced between apps and domains.
- Validation precedes persistence.
- Failure modes are explicit and closed by default.

These principles are enforced structurally and are not optional.

## 4. Document authority and interpretation

This repository is internally self consistent.

The following rules apply:

- All documents are normative unless explicitly marked as informational.
- Lower numbered sections override higher numbered sections within the same file.
- More specific documents override more general documents when conflicts exist.
- Architecture Decision Records override earlier design text for the decisions they cover.

No external documents are required to interpret or implement this design.

## 5. Repository organization

Documents are ordered by conceptual dependency.

- Scope, assumptions, and constraints.
- Protocol definition.
- Architecture and component model.
- Data layout and interfaces.
- Security model.
- End to end flows.
- PoC definition, testing, and acceptance.
- Architecture decisions.
- Appendices and reference material.

Each directory is self contained. Cross references are explicit.

## 6. Design responsibilities

This repository defines:

- The protocol governing identity, authorship, validation, and synchronization.
- The architectural separation between managers, services, apps, and frontends.
- The security invariants enforced under adversarial conditions.
- The graph based data model and persistence rules.
- Allowed and forbidden component interactions.
- Failure handling and rejection semantics.

This repository does not define:

- User interface behavior.
- Performance optimizations beyond stated constraints.
- Deployment or infrastructure automation.
- Operational monitoring beyond logging semantics.

## 7. Global invariants

The following invariants apply system wide unless explicitly overridden:

- Every operation is bound to a verifiable cryptographic identity.
- No graph mutation bypasses Graph Manager, Schema Manager, and ACL Manager.
- Ownership of Parents is immutable.
- Persistent ordering derives solely from monotonically increasing sequence numbers.
- Accepted history is never rewritten.
- Apps are isolated by schema and domain boundaries.
- Backend managers form a trusted kernel and are not extensible by apps.

Violation of any invariant constitutes a correctness failure.

## 8. Allowed and forbidden behaviors

### 8.1 Allowed behaviors

- Nodes validate, reject, and store operations independently.
- Peers exchange signed and optionally encrypted sync envelopes.
- Apps define domain specific semantics through schemas.
- Identities delegate scoped authority through explicit graph structure.
- Nodes operate offline and resume synchronization incrementally.

### 8.2 Forbidden behaviors

- Implicit trust based on network location or transport.
- Direct persistent storage access outside Graph Manager.
- Cross app reinterpretation of objects.
- Retroactive modification of owned objects.
- Global trust or reputation assumptions.
- Privilege escalation through synchronization.

Any forbidden behavior is a protocol violation.

## 9. Component interaction model

Components interact only through defined inputs and outputs.

- Frontend apps submit operations through documented APIs.
- Services operate with explicit, limited manager references.
- Managers communicate through internal interfaces only.
- Network input always crosses a trust boundary and is treated as untrusted.
- Persistent storage is reachable only through Graph Manager.

Trust boundaries are explicit and enforced at every interface.

## 10. Failure and rejection behavior

The system fails closed.

- Invalid input is rejected before persistence.
- Unauthorized operations are rejected without side effects.
- Malformed envelopes are discarded.
- Replayed or out of order sync data is ignored.
- Revoked keys invalidate subsequent operations immediately.

Failures are logged. Partial state application is not permitted.

## 11. Conformance

An implementation conforms to this design if and only if:

- All invariants defined in this repository hold under all allowed operations.
- All forbidden behaviors are structurally impossible.
- All security properties defined in the security documentation are enforced.
- All protocol rules are implemented without deviation.

Any deviation requires an explicit Architecture Decision Record.
