



# 06 Known limitations

This document captures limitations that are intentional for the PoC and do not represent production behavior.

For the meta specifications, see [06-known-limitations-meta.md](../09-appendix/meta/07-poc/06-known-limitations-meta.md).

## 1. Protocol and data

* No delete semantics; suppression is represented by Ratings.
* Limited schema evolution and migration tooling.

## 2. Networking and sync

* Transport is limited to local testing and Tor for PoC runs.
* Multi-node sync supports PoC scenarios but does not target production-scale topologies.

## 3. Frontend

* Frontend is a scaffold; no production UX is provided.
* App marketplace and plugin UX are out of scope for the PoC.

## 4. Operational posture

* No production hardening, scaling, or monitoring.
* No automated background job orchestration beyond the defined flows.
