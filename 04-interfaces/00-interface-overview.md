



# 00 Interface overview

Defines the external and internal interfaces of the 2WAY backend. This includes local HTTP entrypoints, WebSocket session behavior, and internal component boundaries. Interfaces are framework-agnostic and designed for a single-process PoC backend.

For the meta specifications, see [00-interface-overview meta](../10-appendix/meta/04-interfaces/00-interface-overview-meta.md).

## 1. Purpose and scope

This overview establishes how callers reach the backend and how components communicate internally. It is not a transport specification for peer-to-peer sync; that is defined in [01-protocol/08-network-transport-requirements.md](../01-protocol/08-network-transport-requirements.md).

## 2. Interface surfaces

2WAY exposes the following interface surfaces:

* **Local HTTP API** for graph envelope submission and health checks.
* **System service HTTP APIs** under `/system/*` for bootstrap, identity, feed, sync, and ops.
* **App lifecycle HTTP APIs** under `/api/system/apps/*` for app management.
* **Auth and upload HTTP APIs** for identity registration, token issuance, and attachment handling.
* **Local WebSocket** for authenticated, stateful sessions and future event delivery.
* **Internal manager APIs** for component-to-component calls within the backend process.

The HTTP and WebSocket interfaces are local-only and are not intended to be exposed to untrusted networks.

## 3. Authentication and identity binding

All interface surfaces rely on [Auth Manager](../02-architecture/managers/04-auth-manager.md) to resolve an opaque auth token into an identity. Authentication outcomes are explicit and fail closed. Callers must not bypass Auth Manager to construct their own identities.

Identity and permission checks flow through these layers:

1. Interface layer authenticates and builds an [OperationContext](../02-architecture/services-and-apps/05-operation-context.md).
2. Graph Manager validates structure, schema, and ACL before persistence.
3. Storage Manager persists on success only.

## 4. Error posture

All interface responses use the canonical error model described in [04-error-model.md](04-error-model.md). Invalid inputs are rejected before persistence. Transport responses are deterministic and must not leak internal stack traces.

## 5. Versioning and compatibility

Interface payloads that carry graph envelopes or sync envelopes must include protocol version metadata when required (see [01-protocol/11-versioning-and-compatibility.md](../01-protocol/11-versioning-and-compatibility.md)). Version incompatibility is fatal and must be rejected before any persistence.

Version incompatibility MUST be rejected with `ErrorDetail.code=envelope_invalid` and HTTP `400` (or an equivalent transport error) before any persistence.

## 6. Forbidden behaviors

The following behaviors are forbidden across all interfaces:

* Direct SQL access outside Storage Manager.
* Mutation paths that bypass Graph Manager or Schema Manager.
* Accepting untrusted identities or author information without Auth Manager validation.
* Any partial acceptance of envelopes or sync packages.
