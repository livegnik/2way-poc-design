



# 00 Security overview

This section defines the security posture of the 2WAY PoC. It describes how trust is established, how state changes are protected, and how the system resists abuse, censorship, and data tampering. The security posture assumes the PoC already operates as specified.

References:

* [01-protocol/**](../01-protocol/)
* [02-architecture/**](../02-architecture/)
* [03-data/**](../03-data/)
* [04-interfaces/**](../04-interfaces/)
* [06-flows/**](../06-flows/)

For the meta specifications, see [00-security-overview-meta.md](../10-appendix/meta/05-security/00-security-overview-meta.md).

## 1. Security objectives

* **Autonomy**: Nodes operate without central trust dependencies.
* **Censorship resistance**: No single intermediary can rewrite or suppress accepted history.
* **Integrity**: All accepted state changes are authenticated, ordered, and replayable.
* **Containment**: App domains and trust boundaries prevent cross-app interference.
* **Availability**: Early rejection and admission controls protect the kernel from abuse.
* **Auditability**: All accepted changes are traceable and verifiable.

## 2. Root of trust

Identity is the root of trust. All authorship, authorization, and sync acceptance trace back to identity keys and their graph representation. Parents and attributes bind identity identifiers to public key material and delegation state.

## 3. Kernel boundary

Managers form the kernel. They enforce the validation pipeline, persist state, and define the only allowed mutation paths. Services and interfaces are untrusted clients of the kernel and cannot bypass validation or storage controls.

## 4. Data integrity posture

* All writes are represented as graph message envelopes.
* Schema and ACL checks execute before any write commits.
* Global ordering is enforced via `global_seq` and is monotonic.

## 5. Availability posture

* DoS Guard and Network Manager enforce admission control.
* Early rejection prevents expensive processing for invalid inputs.
* Rate limits and puzzles protect ingress surfaces.

## 6. Privacy posture

* Selective sync prevents over-sharing.
* Visibility rules are enforced by ACL and domain scoping.
* Metadata exposure is minimized by design.

## 7. Auditability posture

* Accepted operations are globally ordered and replayable.
* Provenance links each object to its author and operation context.
* Forensics rely on deterministic replay rather than mutable state.

## 8. Requirement ID anchors

This section is the canonical requirement anchor list for generated security posture references.

R020-R066, R126, R177-R184.
