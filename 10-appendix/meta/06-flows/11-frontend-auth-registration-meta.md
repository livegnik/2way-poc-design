



# 11 Frontend auth registration flow

## 1. Purpose and scope

Defines the frontend registration flow for local passwords, keypair generation, signature-based identity registration, and opaque token issuance.

This specification references:

* [06-flows/11-frontend-auth-registration.md](../../../06-flows/11-frontend-auth-registration.md)
* [04-interfaces/13-auth-session.md](../../../04-interfaces/13-auth-session.md)
* [01-protocol/04-cryptography.md](../../../01-protocol/04-cryptography.md)

## 2. Responsibilities and boundaries

This specification is responsible for:

* Declaring the frontend registration flow steps and failure behavior.
* Binding local password handling to frontend-only storage.
* Defining token usage for subsequent requests.
* Mapping auth registration failures to error codes and transport outcomes.

This specification does not cover:

* Device registration or revocation via the auth registration endpoint.
