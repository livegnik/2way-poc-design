



# 06 Encryption at rest and key storage

This document defines how keys are stored and how data-at-rest protection is handled in the PoC.

For the meta specifications, see [06-encryption-at-rest-and-key-storage-meta.md](../10-appendix/meta/05-security/06-encryption-at-rest-and-key-storage-meta.md).

## 1. Key storage boundaries

* Key Manager is the only component that handles private keys.
* Private keys are never stored in the graph.
* Public keys are stored as graph attributes for verification.

## 2. Data at rest

* The PoC uses SQLite without mandatory encryption at rest.
* Database file protection relies on OS permissions for the PoC.
* Future hardening may add encryption at rest without changing protocol semantics.

## 3. Failure posture

* Missing keys prevent signing or decryption.
* Key access failures reject operations that require cryptographic proof.
