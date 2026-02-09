



# 13 Auth Identity Registration Interface

## 1. Purpose and scope

Defines local identity registration and token issuance endpoints consumed by Auth Manager.

This document references:

* [02-architecture/managers/04-auth-manager.md](../../../02-architecture/managers/04-auth-manager.md)
* [04-interfaces/04-error-model.md](../../../04-interfaces/04-error-model.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Declaring the identity registration endpoint and payloads.
* Declaring canonical signing rules for the registration payload and response signature fields.
* Declaring rejection behavior for signature and replay/skew failures.

This specification does not cover the following:

* External identity provider flows.
* Device enrollment or revocation via the auth registration endpoint.
