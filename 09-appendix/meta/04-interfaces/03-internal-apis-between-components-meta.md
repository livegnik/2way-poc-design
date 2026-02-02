



# 03 Internal APIs between components

## 1. Purpose and scope

Defines the internal, in-process APIs between managers and services. It establishes call contracts and ordering without prescribing implementation details.

This document references:

* [02-architecture/managers/**](../02-architecture/managers/)
* [02-architecture/services-and-apps/**](../02-architecture/services-and-apps/)
* [04-error-model.md](04-error-model.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Declaring key manager-to-manager call surfaces.
* Defining shared cross-cutting contracts like OperationContext and ErrorDetail.

This specification does not cover the following:

* Specific SQL schema details (see [03-data/**](../03-data/)).
* Transport or network topology (see [01-protocol/08-network-transport-requirements.md](../01-protocol/08-network-transport-requirements.md)).
