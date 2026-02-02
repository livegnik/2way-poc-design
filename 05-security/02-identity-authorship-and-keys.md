



# 02 Identity, authorship, and keys

This document defines identity as the root of trust and how authorship is bound to keys and graph objects.

For the meta specifications, see [02-identity-authorship-and-keys-meta.md](../09-appendix/meta/05-security/02-identity-authorship-and-keys-meta.md).

## 1. Identity as root of trust

* Identities are represented as Parent objects in the graph.
* Public key material is bound to identity Parents via Attributes.
* All authorship and authorization traces to identity keys.

## 2. Authorship model

* Each graph operation declares an `owner_identity`.
* Immutable ownership is enforced by ACL and schema rules.
* All writes are append-only; ownership changes are expressed as new objects, not overwrites.

## 3. Key material and scopes

* Each identity may hold multiple keys for rotation and delegation.
* Key attributes include purpose, status, and validity window.
* Key Manager owns private keys; public keys are stored in the graph.

## 4. Multi-device and delegated signing

* Devices are represented as Parents and linked to identities by edges.
* Delegated signing uses scoped keys (capability-limited) bound to the identity graph.
* Delegation scope is enforced by ACL and capability checks.

## 5. Failure posture

* Invalid or missing key bindings reject writes.
* Ambiguous authorship is rejected by default.
