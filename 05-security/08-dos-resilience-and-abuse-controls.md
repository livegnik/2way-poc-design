



# 08 DoS resilience and abuse controls

This document defines how the PoC resists abuse and resource exhaustion.

For the meta specifications, see [08-dos-resilience-and-abuse-controls-meta.md](../09-appendix/meta/05-security/08-dos-resilience-and-abuse-controls-meta.md).

## 1. Admission control

* Network Manager enforces admission prior to heavy processing.
* DoS Guard applies puzzles and rate limits based on telemetry.
* Missing telemetry defaults to stricter admission.

## 2. Early rejection

* Structural validation occurs before expensive validation.
* Unsupported protocol versions are rejected early.
* Oversized payloads are rejected before storage access.

## 3. Rate limits and throttling

* Per-identity and anonymous limits are enforced.
* Throttling can require puzzles for continued admission.
* Rate limit violations produce deterministic errors.

## 4. Failure posture

* Abuse signals do not relax validation.
* Rejection never mutates state.
