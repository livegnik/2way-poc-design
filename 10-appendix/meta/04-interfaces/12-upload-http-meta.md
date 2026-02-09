



# 12 Upload HTTP Interfaces

## 1. Purpose and scope

Defines local upload initiation, chunking, and completion endpoints referenced by frontend requirements.

This document references:

* [04-interfaces/04-error-model.md](../../../04-interfaces/04-error-model.md)
* [02-architecture/services-and-apps/05-operation-context.md](../../../02-architecture/services-and-apps/05-operation-context.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Declaring upload endpoint payloads and validation rules.
* Declaring chunk data encoding and size bounds.
* Declaring rejection behavior for invalid or expired upload sessions.

This specification does not cover the following:

* Storage backend implementation details.
