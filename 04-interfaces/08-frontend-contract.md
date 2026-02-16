



# 10 Frontend Contract

Defines the frontend-facing interface contract implied by the PoC specs. This document lists allowed surfaces, forbidden surfaces, and required client behavior without introducing new APIs.

For the meta specifications, see [04-frontend-apps meta](../10-appendix/meta/02-architecture/services-and-apps/04-frontend-apps-meta.md).

## 1. Purpose and scope

This contract specifies what frontend apps may call, the required payload discipline, and forbidden surfaces.

## 2. Allowed HTTP routes

Frontend apps may call only the routes defined in:

* [01-local-http-api.md](01-local-http-api.md) (`/health`, `/graph/envelope`, `/graph/read`, `/apps/{slug}/list`, `/apps/{slug}/read`)
* [09-system-services-http.md](09-system-services-http.md) system service routes (`/system/*`) when authorized by ACL and capability.
* [06-app-lifecycle.md](06-app-lifecycle.md) app lifecycle routes (`/api/system/apps/*`) when authorized.
* [11-ops-http.md](11-ops-http.md) and [12-upload-http.md](12-upload-http.md) when explicitly allowed by capability.
* [13-auth-session.md](13-auth-session.md) identity registration route.

Admin-only routes (`/admin/health`, `/system/ops/*`) require the admin capability (`system.admin`) and explicit capability grants.

## 3. Allowed WebSocket surfaces

* Authenticated local WebSocket session as defined in [02-websocket-events.md](02-websocket-events.md) and event envelopes in [14-events-interface.md](14-events-interface.md).

## 4. Forbidden surfaces

Frontend apps MUST NOT:

* Call internal manager APIs.
* Access storage directly.
* Use sync transport internals not exposed through documented interfaces.

## 5. Payload constraints and validation

* Frontends must validate payload shape locally before sending, using the schema and object model constraints in [01-protocol/02-object-model.md](../01-protocol/02-object-model.md).
* All write requests must use graph envelopes defined in [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md).
* Frontends must supply required [OperationContext](../02-architecture/services-and-apps/05-operation-context.md) fields and must not fabricate server-side identity bindings.

## 6. Error handling (UI-visible mapping)

Frontend apps must surface canonical error categories from [04-error-model.md](04-error-model.md) without inventing new codes. Unknown error codes are treated as `internal_error` and displayed as a generic failure.

## 7. Auth, upload, ops, and events surfaces

Frontend apps may call only the interfaces explicitly listed above. Any surface not listed there is forbidden.

No mixed auth invariant:

* Frontend passwords are local-only and MUST NOT be sent to the backend.
* Backend authentication is only via signature-based registration and opaque tokens.
