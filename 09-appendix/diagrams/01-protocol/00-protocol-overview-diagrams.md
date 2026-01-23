# 00 Protocol overview diagrams

This file mirrors `01-protocol/00-protocol-overview.md`.
It focuses on boundaries, ordering, and the envelope path.
Referenced from: `01-protocol/00-protocol-overview.md`

## Table of contents

- [1. Purpose and scope](#1-purpose-and-scope)
- [2. Responsibilities and boundaries](#2-responsibilities-and-boundaries)
  - [2.1 Responsibility split](#21-responsibility-split)
  - [2.2 Authority boundaries](#22-authority-boundaries)
- [3. Protocol posture and guiding principles](#3-protocol-posture-and-guiding-principles)
  - [3.1 Shared write path (local and remote)](#31-shared-write-path-local-and-remote)
  - [3.2 Trust and authorization posture](#32-trust-and-authorization-posture)
- [4. Protocol layers and companion specs](#4-protocol-layers-and-companion-specs)
  - [4.1 Layer map](#41-layer-map)
  - [4.2 Namespace isolation](#42-namespace-isolation)
- [5. Operation lifecycle](#5-operation-lifecycle)
  - [5.1 Authoring and local submission](#51-authoring-and-local-submission)
  - [5.2 Author identity binding](#52-author-identity-binding)
  - [5.3 Local write lifecycle](#53-local-write-lifecycle)
  - [5.4 Envelope construction and validation gates](#54-envelope-construction-and-validation-gates)
  - [5.5 Sequencing and persistence](#55-sequencing-and-persistence)
  - [5.6 Remote synchronization ingress](#56-remote-synchronization-ingress)
  - [5.7 Sync package metadata](#57-sync-package-metadata)
  - [5.8 Sync state advancement](#58-sync-state-advancement)
- [6. Envelope shapes](#6-envelope-shapes)
  - [6.1 Envelope structure diagram](#61-envelope-structure-diagram)
- [7. Validation order](#7-validation-order)
  - [7.1 Precedence ladder](#71-precedence-ladder)
  - [7.2 Validation and rejection order](#72-validation-and-rejection-order)
- [8. Guarantees and invariants](#8-guarantees-and-invariants)
  - [8.1 Invariant summary](#81-invariant-summary)
  - [8.2 Sync monotonicity](#82-sync-monotonicity)
- [9. Allowed and forbidden behaviors](#9-allowed-and-forbidden-behaviors)
  - [9.1 Allowed](#91-allowed)
  - [9.2 Forbidden](#92-forbidden)
- [10. Failure posture](#10-failure-posture)
  - [10.1 Rejection atomicity](#101-rejection-atomicity)
  - [10.2 Remote rejection posture](#102-remote-rejection-posture)
  - [10.3 Ordering vs revocation](#103-ordering-vs-revocation)
- [11. Compatibility and evolution](#11-compatibility-and-evolution)
  - [11.1 Version negotiation](#111-version-negotiation)
  - [11.2 Naming conventions](#112-naming-conventions)

## 1. Purpose and scope

This appendix expresses the protocol overview as ASCII UML diagrams. It is a map, not a restatement of rules. Use it alongside `01-protocol/00-protocol-overview.md` for the narrative and `02-architecture/00-architecture-overview.md` for component placement.

This overview references:

- `01-protocol/01-identifiers-and-namespaces.md`
- `01-protocol/02-object-model.md`
- `01-protocol/03-serialization-and-envelopes.md`
- `01-protocol/04-cryptography.md`
- `01-protocol/05-keys-and-identity.md`
- `01-protocol/06-access-control-model.md`
- `01-protocol/07-sync-and-consistency.md`
- `01-protocol/08-network-transport-requirements.md`
- `01-protocol/09-errors-and-failure-modes.md`
- `01-protocol/10-versioning-and-compatibility.md`
- `01-protocol/11-dos-guard-and-client-puzzles.md`
- `02-architecture/01-component-model.md`
- `02-architecture/04-data-flow-overview.md`
- `02-architecture/services-and-apps/05-operation-context.md`

## 2. Responsibilities and boundaries

### 2.1 Responsibility split

Diagram: Protocol responsibilities vs non-responsibilities
```text
+----------------------------------------+----------------------------------------+
| In scope (protocol overview)           | Out of scope (backend/client layers)   |
+----------------------------------------+----------------------------------------+
| Envelope submission path               | Backend storage layout                 |
| Identity binding + auth ordering       | Transport encoding + routing           |
| Validation ordering + rejection        | Discovery + deployment topology        |
| Sync sequencing posture                | Client/UI workflows + app logic        |
| Mandatory invariants                   | Domain semantics in apps               |
+----------------------------------------+----------------------------------------+
```

### 2.2 Authority boundaries

Diagram: Protocol authority boundaries
```text
Local write + remote sync ingress
----------------------------------------------------------------------

+--------------------------+        +--------------------------+
| HTTP layer               |        | Local services           |
| (local entrypoint)       |        | (system or app)          |
+--------------------------+        +--------------------------+
            |                                   |
            v                                   v
+--------------------------+        +--------------------------+
| Auth Manager             |        | OperationContext         |
| resolves identity_id     |        | identity + app_id        |
|                          |        | trace_id                |
+--------------------------+        +--------------------------+
            \                              /
             \                            /
              v                          v
        +--------------------------------------+
        | Graph Manager                        |
        | only write path                      |
        | envelope-only writes                 |
        | authorize before persist             |
        +--------------------------------------+
        | ..> Schema Manager                   |
        | ..> ACL Manager                      |
        | ..> Storage Manager                  |
        | no direct DB writes                  |
        +--------------------------------------+

+------------------+     +------------------+     +------------------+
| Remote peer      | --> | DoS Guard Manager| --> | Network Manager  |
+------------------+     +------------------+     +------------------+
                         | admission +      |     | crypto verify +  |
                         | client puzzles   |     | encrypt          |
                         |                  |     | signed packages  |
                         +------------------+     +------------------+
                                                          |
                                                          v
                                                  +------------------+
                                                  | State Manager    |
                                                  | only sync pkg IO |
                                                  | sequence gate    |
                                                  | reject replay    |
                                                  | out-of-order     |
                                                  +------------------+
                                                          |
                                                          v
                                                  +------------------+
                                                  | Graph Manager    |
                                                  +------------------+
```

This view is the same authority split described in `02-architecture/01-component-model.md`. It shows Graph Manager as the single write path and State Manager as the only sync package boundary.

## 3. Protocol posture and guiding principles

### 3.1 Shared write path (local and remote)

Diagram: Envelope-first write path
```text
+------------------+     +------------------+
| Local write      |     | Remote write     |
+------------------+     +------------------+
          |                      |
          v                      v
+------------------+     +------------------+
| Graph envelope   |     | Sync package     |
+------------------+     +------------------+
          |                      |
          |                      v
          |              +------------------+
          |              | Graph envelope   |
          |              +------------------+
          |                      |
          |                      v
          |              +------------------+
          |              | Crypto verify    |
          |              | (remote only)    |
          |              +------------------+
          +---------+------------+
                    v
             +------------------+
             | Graph Manager    |
             +------------------+
                    |
                    v
             +------------------+     +------------------+
             | Structural check | --> | Reject: malformed|
             +------------------+     +------------------+
                    |
                    v
             +------------------+     +------------------+
             | Schema validation| --> | Reject: invalid  |
             +------------------+     +------------------+
                    |
                    v
             +------------------+     +------------------+
             | ACL evaluation   | --> | Reject: denied   |
             +------------------+     +------------------+
                    |
                    v
             +------------------+
             | Storage commit   |
             +------------------+
                    |
                    v
             +------------------+
             | Assign global_seq|
             +------------------+
                    |
                    v
             +------------------+
             | All ops or none  |
             +------------------+
                    |
                    v
             +------------------+
             | Sync advance     |
             | (remote only)    |
             +------------------+
```

### 3.2 Trust and authorization posture

Diagram: Trust boundary and enforcement order
```text
+------------------------+
| Untrusted input        |
+------------------------+
            |
            v
+------------------------+
| Cryptographic verify   |
| (remote only)          |
+------------------------+
            |
            v
+------------------------+
| Structural validation  |
+------------------------+
            |
            v
+------------------------+
| Schema validation      |
+------------------------+
            |
            v
+------------------------+
| ACL evaluation         |
+------------------------+
            |
            v
+------------------------+
| Persist + sequence     |
+------------------------+
```

## 4. Protocol layers and companion specs

### 4.1 Layer map

Diagram: Layered protocol ownership
```text
+-------------------------------+
| Identifiers + namespaces      |
+-------------------------------+
               |
               v
+-------------------------------+
| Object model                  |
+-------------------------------+
               |
               v
+-------------------------------+
| Serialization + envelopes     |
+-------------------------------+
               |
               v
+-------------------------------+
| Cryptography                  |
+-------------------------------+
               |
               v
+-------------------------------+
| Keys + identity               |
+-------------------------------+
               |
               v
+-------------------------------+
| Access control                |
+-------------------------------+
               |
               v
+-------------------------------+
| Sync + consistency            |
+-------------------------------+
               |
               v
+-------------------------------+
| Network transport             |
+-------------------------------+
               |
               v
+-------------------------------+
| Errors + failure modes        |
+-------------------------------+
               |
               v
+-------------------------------+
| Versioning                    |
+-------------------------------+
               |
               v
+-------------------------------+
| DoS guard + puzzles           |
+-------------------------------+
```

### 4.2 Namespace isolation

Diagram: App namespace boundaries
```text
+---------------------+     +---------------------+
| app_id = 10         |     | app_id = 22         |
+---------------------+     +---------------------+
| type_key: 10:post   |     | type_key: 22:post   |
| type_key: 10:vote   |     | type_key: 22:edge   |
+---------------------+     +---------------------+
          |                           |
          v                           v
+-------------------------------------------------+
| Schema Manager: rejects cross-namespace types   |
+-------------------------------------------------+
```

## 5. Operation lifecycle

### 5.1 Authoring and local submission

Diagram: Local authoring path (OperationContext)
```text
+--------------------+
| Frontend/service   |
+--------------------+
          |
          v
+--------------------+
| Auth Manager       |
+--------------------+
          |
          v
+--------------------+
| OperationContext   |
| identity, app_id,  |
| is_remote=false,   |
| trace_id           |
+--------------------+
          |
          v
+--------------------+
| Graph envelope     |
+--------------------+
```

### 5.2 Author identity binding

Diagram: Explicit identity binding
```text
+--------------------+     +--------------------+
| Auth context       |     | Envelope author    |
+--------------------+     +--------------------+
| identity_id        | --> | author_identity_id |
| app_id             |     | app_id             |
+--------------------+     +--------------------+
          |
          v
+------------------------------+
| No transport metadata trust  |
+------------------------------+
```

### 5.3 Local write lifecycle

Diagram: Local write lifecycle
```text
+------------------+
| Frontend app     |
+------------------+
          |
          v
+------------------+        +------------------+
| HTTP layer       | -----> | Auth Manager     |
+------------------+        +------------------+
          |                          |
          | <------------------------+
          | requester_identity_id
          v
+------------------+        +------------------+
| Graph Manager    | -----> | Schema Manager   |
+------------------+        +------------------+
          |                          |
          | <------------------------+
          | schema ok or reject
          v
+------------------+        +------------------+
| Graph Manager    | -----> | ACL Manager      |
+------------------+        +------------------+
          |                          |
          | <------------------------+
          | allow or deny
          v
+------------------+        +------------------+
| Graph Manager    | -----> | Storage Manager  |
+------------------+        +------------------+
          |                          |
          | <------------------------+
          | commit + global_seq
          v
+------------------+
| HTTP layer       |
+------------------+
```

### 5.4 Envelope construction and validation gates

Diagram: Structural validation before expensive work
```text
+------------------------+
| Envelope received      |
+------------------------+
            |
            v
+------------------------+
| Structural validation  |
+------------------------+
            |
            v
+------------------------+
| Schema validation      |
+------------------------+
            |
            v
+------------------------+
| ACL evaluation         |
+------------------------+
            |
            v
+------------------------+
| Transactional apply    |
+------------------------+
```

### 5.5 Sequencing and persistence

Diagram: Transactional application
```text
+------------------------+
| Envelope accepted      |
+------------------------+
            |
            v
+------------------------+
| Assign global_seq      |
+------------------------+
            |
            v
+------------------------+
| Storage commit         |
+------------------------+
            |
            v
+------------------------+
| All ops applied or none|
+------------------------+
```

### 5.6 Remote synchronization ingress

Diagram: Remote sync ingress ordering
```text
+------------------+        +------------------+
| Remote peer      | -----> | DoS Guard Manager|
+------------------+        +------------------+
          |                          |
          |                          v
          |                  +------------------+
          |                  | Network Manager  |
          |                  +------------------+
          |                          |
          |                          v
          |                  +------------------+
          |                  | Key Manager      |
          |                  +------------------+
          |                          |
          | <------------------------+
          | verified package bytes
          v
+------------------+        +------------------+
| State Manager    | -----> | Graph Manager    |
+------------------+        +------------------+
          |                          |
          |                          v
          |                  +------------------+
          |                  | Schema Manager   |
          |                  +------------------+
          |                          |
          | <------------------------+
          | schema ok or reject
          v
+------------------+        +------------------+
| Graph Manager    | -----> | ACL Manager      |
+------------------+        +------------------+
          |                          |
          | <------------------------+
          | allow or deny
          v
+------------------+        +------------------+
| Graph Manager    | -----> | Storage Manager  |
+------------------+        +------------------+
          |                          |
          | <------------------------+
          | commit + global_seq
          v
+------------------+
| State Manager    |
+------------------+
```

### 5.7 Sync package metadata

Diagram: Sync package envelope fields
```text
+-----------------------------------+
| SyncPackageEnvelope               |
+-----------------------------------+
| sender_identity: int              |
| sync_domain: string               |
| from_seq: int                     |
| to_seq: int                       |
| envelope: GraphMessageEnvelope    |
| signature: string                 |
+-----------------------------------+
```

### 5.8 Sync state advancement

Diagram: Apply then advance
```text
+------------------+     +------------------+
| Package received | --> | Verify signature |
+------------------+     +------------------+
          |                      |
          v                      v
+------------------+     +------------------+
| Apply envelope   | --> | Assign global_seq|
+------------------+     +------------------+
          |
          v
+------------------+
| Advance sync     |
| from_seq/to_seq  |
+------------------+
```

## 6. Envelope shapes

### 6.1 Envelope structure diagram

Diagram: Envelope structures
```text
+---------------------------+
| GraphMessageEnvelope      |
+---------------------------+
| ops: Operation[]          |
| trace_id: string?         |
+---------------------------+

+---------------------------+
| Operation                 |
+---------------------------+
| op: string                |
| app_id: int               |
| type_key: string?         |
| type_id: int?             |
| owner_identity: int       |
| payload: object           |
+---------------------------+
```

These shapes match `01-protocol/03-serialization-and-envelopes.md`. Identity binding follows `01-protocol/05-keys-and-identity.md`.

## 7. Validation order

### 7.1 Precedence ladder

Diagram: Failure precedence
```text
+------------------------+      +---------------------+
| Cryptographic failure  | ---> | Reject, no effects  |
+------------------------+      +---------------------+
            |
            v
+------------------------+      +---------------------+
| Structural failure     | ---> | Reject, no effects  |
+------------------------+      +---------------------+
            |
            v
+------------------------+      +---------------------+
| Schema failure         | ---> | Reject, no effects  |
+------------------------+      +---------------------+
            |
            v
+------------------------+      +---------------------+
| ACL failure            | ---> | Reject, no effects  |
+------------------------+      +---------------------+
            |
            v
+------------------------+      +---------------------+
| Ordering failure       | ---> | Reject, no effects  |
+------------------------+      +---------------------+
            |
            v
+------------------------+      +---------------------+
| Resource failure       | ---> | Reject, no effects  |
+------------------------+      +---------------------+
            |
            v
+------------------------+
| Persist + advance      |
+------------------------+
```

### 7.2 Validation and rejection order

Diagram: Validation and rejection order
```text
+---------------------+
| Envelope submitted  |
+---------------------+
           |
           v
+---------------------+      +------------------+
| Structural checks   | ---> | Reject: malformed|
+---------------------+      +------------------+
           |
           v
+---------------------+      +------------------+
| Schema validation   | ---> | Reject: invalid  |
+---------------------+      +------------------+
           |
           v
+---------------------+      +------------------+
| ACL evaluation      | ---> | Reject: denied   |
+---------------------+      +------------------+
           |
           v
+---------------------+      +------------------+
| Sequenced + stored  | ---> | Accepted         |
+---------------------+      +------------------+
```

## 8. Guarantees and invariants

### 8.1 Invariant summary

Diagram: Mandatory invariants
```text
+--------------------------------------------+
| Mandatory invariants                       |
+--------------------------------------------+
| Graph Manager is the only write path       |
| Storage Manager is the only DB writer      |
| Every accepted envelope gets global_seq    |
| Sync ordering monotonic per peer/domain    |
| Crypto verify before semantics (remote)    |
| No private keys in graph or sync payloads  |
+--------------------------------------------+
```

### 8.2 Sync monotonicity

Diagram: Per-peer, per-domain monotonicity
```text
Peer A, domain X:
+------+   +------+   +------+
| 101  |-->| 102  |-->| 103  |  ok
+------+   +------+   +------+

Peer A, domain X (out of order):
+------+   +------+
| 103  |-->| 102  |  reject
+------+   +------+

Peer B, domain X:
+------+   +------+
| 44   |-->| 45   |  ok (separate track)
+------+   +------+

Peer A, domain Y:
+------+   +------+
| 9    |-->| 10   |  ok (separate domain)
+------+   +------+
```

## 9. Allowed and forbidden behaviors

### 9.1 Allowed

Diagram: Allowed paths
```text
+------------------+     +------------------+     +------------------+
| HTTP layer       | --> | Graph Manager    | --> | Storage Manager  |
+------------------+     +------------------+     +------------------+

+------------------+ --> +------------------+ --> +------------------+
| Remote peer      |     | DoS Guard        |     | Network Manager  |
+------------------+     +------------------+     +------------------+
                                                          |
                                                          v
                                                  +------------------+
                                                  | State Manager    |
                                                  +------------------+
                                                          |
                                                          v
                                                  +------------------+
                                                  | Graph Manager    |
                                                  +------------------+
                                                          |
                                                          v
                                                  +------------------+
                                                  | Storage Manager  |
                                                  +------------------+
```

### 9.2 Forbidden

Diagram: Forbidden paths
```text
X +------------------+     +------------------+
  | Direct DB write  | --> | Storage Manager  |
  +------------------+     +------------------+

X +------------------+     +------------------+
  | Bypass envelope  | --> | Graph Manager    |
  +------------------+     +------------------+

X +------------------+     +------------------+
  | Transport auth   | --> | Authorization    |
  +------------------+     +------------------+

X +------------------+     +------------------+
  | Partial apply    | --> | Sync advance     |
  +------------------+     +------------------+

X +------------------+     +------------------+
  | No crypto verify | --> | Accept package   |
  +------------------+     +------------------+
```

## 10. Failure posture

### 10.1 Rejection atomicity

Diagram: Reject without side effects
```text
+------------------+     +------------------+
| Rejected         | --> | No state change  |
+------------------+     +------------------+
          |
          v
+------------------+
| No sync advance  |
+------------------+
```

### 10.2 Remote rejection posture

Diagram: Reject and continue peers
```text
+------------------+     +------------------+
| Reject package   | --> | Keep peer state  |
+------------------+     +------------------+
          |
          v
+------------------+     +------------------+
| Log error        | --> | Process others   |
+------------------+     +------------------+
```

### 10.3 Ordering vs revocation

Diagram: Revocation overrides freshness
```text
+------------------+     +------------------+
| Revoked key?     | --> | Reject           |
+------------------+     +------------------+
          |
          v
+------------------+     +------------------+
| Freshness check  | --> | Continue         |
+------------------+     +------------------+
```

## 11. Compatibility and evolution

### 11.1 Version negotiation

Diagram: Compatibility gates
```text
+------------------+     +------------------+
| Local version    |     | Remote version   |
+------------------+     +------------------+
          |                      |
          +----------+-----------+
                     v
             +------------------+
             | Major mismatch?  |
             +------------------+
                |          |
                v          v
    +---------------+  +----------------------+
    | Reject        |  | Proceed to exchange  |
    +---------------+  +----------------------+
```

### 11.2 Naming conventions

Diagram: Normative naming stability
```text
+----------------------------------------+
| Envelope names + domain names + events |
+----------------------------------------+
| Must remain consistent across nodes    |
| and tools to preserve compatibility    |
+----------------------------------------+
```
