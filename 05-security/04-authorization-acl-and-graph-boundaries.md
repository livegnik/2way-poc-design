



# 04 Authorization, ACL, and graph boundaries

This document defines the authorization model, validation pipeline, and boundaries that prevent cross-app interference.

For the meta specifications, see [04-authorization-acl-and-graph-boundaries-meta.md](../10-appendix/meta/05-security/04-authorization-acl-and-graph-boundaries-meta.md).

## 1. Validation pipeline ordering

* Structural validation occurs first.
* Schema validation occurs before ACL evaluation.
* ACL authorization occurs before any storage commit.
* Graph Manager enforces this ordering for all writes.

## 2. ACL layering and trust radius

* ACL decisions are app-scoped and domain-scoped.
* Degrees of separation and trust radius are encoded in ACL rules.
* Trust may be delegated but remains bounded by capability scopes.

## 3. App isolation

* Each app has its own domain and schema namespace.
* Cross-app reads and writes are denied by default.
* Explicit edges or ACL rules are required for cross-app references.

## 4. Append-only domains and immutability

* No deletes exist in the PoC; suppression uses Ratings.
* Ownership is immutable; changes are expressed as new objects.
* Domains are append-only and ordered by global_seq.

## 5. Sybil resistance through structure

* Membership and rating edges define trust relationships.
* ACL policies limit the influence of untrusted identities.
* Sybil defenses rely on graph structure, not identity scarcity.

## 6. Failure posture

* Unauthorized or ambiguous operations are rejected.
* Validation failures do not mutate state.
* Rejections are surfaced to the caller and are auditable.
