



# 10 Auditability, provenance, and tamper detection

This document defines auditability guarantees and how tampering is detected.

For the meta specifications, see [10-auditability-provenance-and-tamper-detection-meta.md](../09-appendix/meta/05-security/10-auditability-provenance-and-tamper-detection-meta.md).

## 1. Provenance

* Every object records its author identity and global_seq.
* Envelopes and signatures bind operations to authorship.
* OperationContext is recorded in logs for traceability.

## 2. Global ordering

* The global sequence is monotonic and append-only.
* Replay of history yields the same state deterministically.

## 3. Forensics

* Logs and graph history provide full change provenance.
* Rejected operations are auditable.
* Tampering attempts are detectable via signature and ordering checks.

## 4. Failure posture

* Missing provenance data rejects writes.
* Ordering violations are treated as integrity failures.
