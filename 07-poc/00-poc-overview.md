



# 00 PoC overview

This section defines the proof-of-concept scope for 2WAY, including its goals, the minimal feature set, how it is built and tested, demo scenarios, and acceptance criteria. It is aligned with the authoritative build plan and acceptance requirements.

References:

* [BUILD-PLAN.md](../../BUILD-PLAN.md)
* [POC-ACCEPTANCE.md](../../POC-ACCEPTANCE.md)
* [POC-APPS.md](../../POC-APPS.md)
* [IMPLEMENTATION-CHOICES.md](../../IMPLEMENTATION-CHOICES.md)

For the meta specifications, see [00-poc-overview-meta.md](../09-appendix/meta/07-poc/00-poc-overview-meta.md).

## 1. Purpose

The PoC demonstrates that the protocol and architecture can be implemented with strict ordering, fail-closed behavior, and deterministic state evolution. It prioritizes correctness, traceability, and testability over UI polish or production performance.

## 2. Scope summary

The PoC includes:

* A single-process backend with Storage, Schema, ACL, Graph, and supporting managers.
* A service layer that orchestrates managers and implements system and app services.
* Minimal HTTP and WebSocket interfaces for local use.
* Two example app domains: messaging and social feed.
* Tests that cover ordering, validation, and fail-closed behavior, including integration flows.

The PoC excludes:

* Production deployment, scaling, and high-availability concerns.
* UI workflows beyond the defined frontend scaffold.
* Nonessential external integrations.

## 3. Document index

The PoC specification set consists of:

1) PoC definition and goals.
2) Feature matrix.
3) Build and run guidance.
4) Test plan.
5) Demo scenarios.
6) Known limitations.
7) Acceptance criteria.
