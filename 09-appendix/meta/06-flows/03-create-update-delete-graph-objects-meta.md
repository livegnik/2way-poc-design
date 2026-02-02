



# 03 Create, update, and delete graph objects

## 1. Purpose and scope

Defines the standard local write flow for graph objects, including update semantics and rating-based suppression in lieu of deletes.

This specification references:

* [06-flows/03-create-update-delete-graph-objects.md](../../../06-flows/03-create-update-delete-graph-objects.md)
* [01-protocol/03-serialization-and-envelopes.md](../../../01-protocol/03-serialization-and-envelopes.md)
* [02-architecture/04-data-flow-overview.md](../../../02-architecture/04-data-flow-overview.md)

## 2. Responsibilities and boundaries

This specification is responsible for:

* Declaring the write pipeline ordering (schema -> ACL -> storage).
* Defining update semantics and delete prohibitions.
* Establishing failure behavior for rejected writes.

This specification does not cover:

* App-specific object schemas.
* UI or frontend state handling.
