



# 00 PoC overview

This section defines the proof-of-concept scope for 2WAY, including its goals, the minimal feature set, how it is built and tested, demo scenarios, and acceptance criteria. It is aligned with the authoritative build plan and acceptance requirements.

References:

* [BUILD-PLAN.md](../../docs-build/manual/BUILD-PLAN.md)
* [POC-ACCEPTANCE.md](../../docs-build/hybrid/POC-ACCEPTANCE.md)
* [POC-APPS.md](../../docs-build/automated/POC-APPS.md)
* [IMPLEMENTATION-CHOICES.md](../../docs-build/manual/IMPLEMENTATION-CHOICES.md)

For the meta specifications, see [00-poc-overview-meta.md](../10-appendix/meta/07-poc/00-poc-overview-meta.md).

## 1. Purpose

The PoC demonstrates that the protocol and architecture can be implemented with strict ordering, fail-closed behavior, and deterministic state evolution. It prioritizes correctness, traceability, and testability over UI polish or production performance.

## 2. Scope summary

The PoC includes:

* A single-process backend with Storage, Schema, ACL, Graph, and supporting managers.
* A service layer that orchestrates managers and implements system and app services.
* Minimal HTTP and WebSocket interfaces for local use.
* Four example app domains: contact list, messaging, social feed, and market.
* An app marketplace UI that can discover and install apps via the documented lifecycle routes.
* Tests that cover ordering, validation, and fail-closed behavior, including integration flows.

Terminology:

* `Market app` is the PoC app domain that models listings, offers, contracts, and feedback in the graph.
* `Market apps` means any apps in the market domain, including the PoC `Market app`.
* `Marketplace` is the UI flow for discovering and installing apps via the documented app lifecycle routes. It is not the same thing as the market domain.
* PoC app domains are shipped by default but remain ordinary apps; they may be swapped out without altering system service contracts.

The PoC excludes:

* Production deployment, scaling, and high-availability concerns.
* UI workflows beyond the defined frontend scaffold and the marketplace flow.
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

## 4. Requirement ID anchors

This section is the canonical requirement anchor list for generated PoC app coverage references.

R007-R009, R013-R019, R025-R057, R060, R112, R116, R118, R131, R136, R217-R226.
