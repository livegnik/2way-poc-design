



# 01 Threat model (PoC)

This document enumerates the threats considered in the PoC and the guarantees that mitigate them.

For the meta specifications, see [01-threat-model-poc-meta.md](../10-appendix/meta/05-security/01-threat-model-poc-meta.md).

## 1. Assumed adversaries

* Malicious frontend clients (local or remote).
* Compromised devices or identities.
* Malicious peers attempting to inject or replay data.
* Resource exhaustion attackers (DoS, flood, oversized payloads).
* Colluding identities (Sybil attempts).

## 2. Out of scope adversaries

* Physical seizure of the host without OS-level hardening.
* State-level adversaries with full network visibility.
* Side-channel attacks on hardware or OS keystore.

## 3. Primary threats and mitigations

| Threat | Mitigation |
| --- | --- |
| Unauthorized writes | Schema + ACL enforcement before commit. |
| Replay attacks | Global sequence ordering and sync state checks. |
| Envelope tampering | Signed envelopes and strict validation. |
| Sybil infiltration | Graph structure, membership edges, and ACL policies. |
| Cross-app data leakage | Domain scoping and app isolation by default. |
| Abuse and flooding | DoS Guard admission, rate limits, puzzles. |
| Silent history rewriting | Append-only graph + global ordering + replayability. |

## 4. Sybil resistance posture

Sybil resistance is not achieved by identity scarcity. It relies on the graph structure and trust policies encoded in ACLs, ratings, and membership edges. Trust radius and degrees of separation are enforced at the ACL layer.

## 5. Censorship and autonomy

Nodes are autonomous and can operate offline. Accepted history can be replayed locally without remote dependencies. Sync convergence does not require a central coordinator.

## 6. Adversarial test scope

Adversarial tests MUST attempt:

* malformed envelope submission (structural and type errors)
* ACL bypass attempts on reads and writes
* cross-app namespace violations
* replay and out-of-order sync submissions
* oversized payloads that exceed configured limits
