



# 2WAY System PoC Design Repository

## 1. Purpose and scope

This repository defines the complete normative design of the 2WAY system proof of concept (PoC). It specifies protocol rules, architectural constraints, security properties, data models, and component responsibilities required to implement and review a 2WAY proof of concept.

This repository is a design specification. It does not contain implementation code, deployment artifacts, or operational tooling. All documents in this repository are intended to be read as binding design constraints.

The scope is limited to the PoC design and its required guarantees. Topics are included only where they materially affect correctness, security, or interoperability.

## 2. Document authority and interpretation

This repository is internally self consistent.

The following rules apply:

- All documents in this repository are normative unless explicitly marked as informational.
- Lower numbered sections override higher numbered sections within the same file.
- More specific documents override more general documents when conflicts exist.
- Architecture Decision Records override earlier design text for the decisions they cover.

No external documents are required to interpret or implement this design.

## 3. Repository organization

The repository is structured by conceptual dependency order.

- Scope, assumptions, and constraints.
- Protocol definition.
- Architecture and component model.
- Data layout and interfaces.
- Security model.
- End to end flows.
- PoC definition, testing, and acceptance criteria.
- Architecture decisions.
- Appendices and reference material.
- Examples of apps.

Each directory is self contained. Cross references are explicit. No implicit dependencies exist.

## 4. Design responsibilities

This repository defines:

- The protocol governing identity, authorship, validation, and synchronization.
- The architectural separation between managers, services, apps, and frontends.
- The security invariants enforced under partial compromise.
- The graph based data model and persistence rules.
- The allowed and forbidden interactions between components.
- Failure handling and rejection semantics.

This repository does not define:

- User interfaces or user experience.
- Performance optimizations beyond stated constraints.
- Deployment, orchestration, or infrastructure automation.
- Monitoring systems beyond logging semantics.

## 5. Global invariants

The following invariants apply across the entire system unless explicitly overridden:

- Every operation is bound to a verifiable cryptographic identity.
- No graph mutation bypasses Graph Manager, Schema Manager, and ACL Manager.
- Ownership of Parents is immutable.
- Persistent ordering is derived solely from monotonically increasing sequence numbers.
- Accepted history is never rewritten.
- Apps are isolated by schema and domain boundaries.
- Backend managers form a trusted kernel and are not extensible by apps.

Violation of any invariant constitutes a correctness failure.

## 6. Allowed and forbidden behaviors

### 6.1 Allowed behaviors

- Nodes validate, reject, and store operations independently.
- Peers exchange signed and optionally encrypted sync envelopes.
- Apps define domain specific semantics through schemas.
- Identities delegate scoped authority via explicit graph structure.
- Nodes operate offline and resume synchronization incrementally.

### 6.2 Forbidden behaviors

- Implicit trust based on network location or transport.
- Direct persistent storage access outside Graph Manager.
- Cross app reinterpretation of objects.
- Retroactive modification of owned objects.
- Global trust or reputation assumptions.
- Privilege escalation through synchronization.

Any forbidden behavior is a protocol violation.

## 7. Component interaction model

Components interact only through defined inputs and outputs.

- Frontend apps submit operations through documented APIs.
- Services operate with explicit, limited manager references.
- Managers communicate through internal interfaces only.
- Network input always crosses a trust boundary and is treated as untrusted.
- Persistent storage is reachable only through Graph Manager.

Trust boundaries are explicit and enforced at every interface.

## 8. Failure and rejection behavior

The system fails closed.

- Invalid input is rejected before persistence.
- Unauthorized operations are rejected without side effects.
- Malformed envelopes are discarded.
- Replayed or out of order sync data is ignored.
- Revoked keys invalidate subsequent operations immediately.

Failures are logged. Partial state application is not permitted.

## 9. Conformance

An implementation conforms to this design if and only if:

- All invariants defined in this repository hold under all allowed operations.
- All forbidden behaviors are structurally impossible.
- All security properties defined in the security documentation are enforced.
- All protocol rules are implemented without deviation.

Any deviation requires an explicit Architecture Decision Record.
