



# 08 Key rotation flow

## 1. Purpose and scope

Defines how identities rotate keys without rewriting history, including authorization and revocation handling.

This specification references:

* [06-flows/08-key-rotation-flow.md](../../../06-flows/08-key-rotation-flow.md)
* [01-protocol/05-keys-and-identity.md](../../../01-protocol/05-keys-and-identity.md)
* [01-protocol/04-cryptography.md](../../../01-protocol/04-cryptography.md)

## 2. Responsibilities and boundaries

This specification is responsible for:

* Defining the ordering of key rotation steps.
* Declaring the required ownership checks for rotation.

This specification does not cover:

* Hardware key storage implementations.
* UI workflows for key recovery.
