



# 01 PoC definition

This document defines the PoC's goals, guarantees, and non-goals.

For the meta specifications, see [01-poc-definition-meta.md](../09-appendix/meta/07-poc/01-poc-definition-meta.md).

## 1. Goals

* Demonstrate end-to-end graph mutation ordering: structural -> schema -> ACL -> commit.
* Prove fail-closed behavior under invalid inputs and dependency failures.
* Enforce deterministic sequencing with monotonic global_seq.
* Validate messaging and social app flows on top of the graph.
* Demonstrate two-node sync convergence for PoC scenarios.

## 2. Guarantees

* All writes are graph message envelopes and pass through Graph Manager.
* All authorization decisions pass through ACL Manager.
* All schema checks pass through Schema Manager.
* All database access goes through Storage Manager.
* OperationContext is immutable and authoritative for authorization.
* Sync ordering and replay protection are enforced by State Manager.

## 3. Non-goals

* Production-grade UI, deployment, or scaling.
* Full automation or background job orchestration beyond required flows.

## 4. Implementation constraints

* Single-process backend.
* SQLite storage for persistence.
* Flask + SQLAlchemy for the frontend scaffold.
* No Docker or external services required for tests.
