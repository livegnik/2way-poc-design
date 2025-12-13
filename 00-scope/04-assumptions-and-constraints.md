



# 04 Assumptions and constraints

## 1. Purpose and scope

This document defines the explicit assumptions and hard constraints under which the 2WAY system design is valid. These assumptions are treated as axioms for the rest of the design repository. Violating them invalidates security, correctness, or consistency guarantees described elsewhere. This document does not define behavior. It defines the conditions under which defined behavior is meaningful.

## 2. Assumptions

### 2.1 Execution environment assumptions

The system assumes the following properties of the local execution environment:

- The node has exclusive control over its local persistent storage.
- The node can perform cryptographic operations correctly using standard primitives.
- Local process isolation is enforced by the host operating system.
- The backend process is not modified at runtime by untrusted code.
- The local clock may be inaccurate but is monotonic within a single process lifetime.

No assumptions are made about network reliability, latency, ordering, or trustworthiness.

### 2.2 Cryptographic assumptions

The security model assumes:

- secp256k1 signatures are unforgeable under chosen-message attack.
- ECIES provides confidentiality and integrity under standard threat models.
- Hash functions used for object addressing and integrity are collision-resistant.
- Private keys stored locally are not exfiltrated unless the local environment is compromised.

The system does not attempt to remain secure under cryptographic primitive failure.

### 2.3 Identity assumptions

The system assumes:

- Each identity corresponds to at least one valid cryptographic keypair.
- An identity controls its private keys at the time it issues an operation.
- Identities do not share private keys unless explicitly modeled through delegation.
- Loss of all keys for an identity without a valid recovery path results in permanent loss of control over that identity.

No assumption is made that identities are unique, human, verified, or non-malicious.

### 2.4 Trust assumptions

The system assumes:

- Local validation logic is correct and uncompromised.
- Remote peers may be malicious, faulty, or adversarial.
- No remote peer is inherently trusted beyond what is expressed in the graph.
- Applications interpret graph data according to their own schemas and rules.

There is no global trust anchor.

## 3. Constraints

### 3.1 Architectural constraints

The design enforces the following constraints:

- All persistent state mutations occur through the Graph Manager.
- All access control decisions occur through the ACL Manager.
- All schema validation occurs through the Schema Manager.
- All network input is treated as untrusted.
- All backend managers operate as a closed internal kernel.

By design, no component may bypass these constraints.

### 3.2 Data model constraints

The data model is constrained as follows:

- Parents are immutable once created.
- Ownership of a Parent cannot be reassigned.
- Attributes, Edges, and Ratings are always associated with a Parent.
- All objects are typed and scoped to an application domain.
- Global sequence numbers are strictly monotonic per node.

Objects that violate these constraints are rejected.

### 3.3 Sync and ordering constraints

The sync model enforces:

- Operations are applied in global sequence order per node.
- Sync packages must declare explicit sequence ranges.
- Replayed or out-of-order operations are rejected.
- A node never rewrites its own history.

The system does not guarantee global total ordering across nodes.

### 3.4 Access control constraints

Access control is constrained by:

- Explicit ACL evaluation for every write operation.
- Default-deny behavior when no ACL rule applies.
- No implicit privilege inheritance outside defined graph edges.
- Device and delegated keys may only act within their declared authority.

ACL enforcement is mandatory and non-optional.

### 3.5 Application isolation constraints

Application isolation is enforced by the following constraints:

- Applications cannot mutate objects outside their declared schema.
- Ratings, trust edges, and semantics are app-scoped.
- Cross-app interpretation is forbidden unless explicitly implemented by an app.
- Backend services cannot reinterpret app data.

Violations result in operation rejection.

## 4. Guarantees

Given the stated assumptions and constraints, the system guarantees:

- Authorship of all accepted operations is verifiable.
- Unauthorized graph mutations are rejected deterministically.
- History cannot be silently rewritten.
- Compromise is locally containable through revocation and scoping.
- Malformed or adversarial input does not corrupt persistent state.

No guarantee is made about availability, global consistency, or fairness.

## 5. Allowed behaviors

The design explicitly allows:

- Malicious identities to exist in the graph.
- Nodes to operate offline indefinitely.
- Partial, selective, and asymmetric sync relationships.
- Multiple independent interpretations of the same graph structure by different apps.
- Local rejection of remote data without explanation.

These behaviors are considered normal and expected.

## 6. Forbidden behaviors

The design explicitly forbids:

- Implicit trust based on network location or transport.
- Direct database access by applications or services.
- Cross-app mutation or reinterpretation of objects.
- Silent acceptance of invalid, unauthorized, or malformed operations.
- Automatic escalation of privileges.

Any implementation permitting these behaviors is non-compliant.

## 7. Failure and rejection behavior

When assumptions are violated or inputs are invalid:

- Operations are rejected before persistent state mutation.
- Rejected operations do not affect sequence numbering.
- No partial writes occur.
- The node remains internally consistent.
- Remote peers are not implicitly penalized beyond rate-limiting or disconnection.

Failure handling is local, deterministic, and non-recovering unless explicitly defined elsewhere.

## 8. Out-of-scope considerations

This document does not define:

- User experience implications.
- Legal or regulatory compliance.
- Performance optimization strategies.
- Economic incentives or reputation weighting.
- Human identity verification or uniqueness.

These topics are intentionally excluded.
