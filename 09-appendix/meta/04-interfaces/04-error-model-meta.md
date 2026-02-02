



# 04 Error model

## 1. Purpose and scope

Defines the canonical error shape, categories, and transport mapping for 2WAY. It establishes a uniform error representation across managers and interfaces.

This document references:

* [01-protocol/10-errors-and-failure-modes.md](../01-protocol/10-errors-and-failure-modes.md)
* [04-interfaces/01-local-http-api.md](01-local-http-api.md)
* [04-interfaces/02-websocket-events.md](02-websocket-events.md)

## 2. Responsibilities and boundaries

This specification is responsible for the following:

* Defining the ErrorDetail shape and canonical codes.
* Establishing error categories and precedence.
* Mapping manager errors to interface responses.

This specification does not cover the following:

* UI presentation or end-user messaging.
* Non-deterministic debugging or logging formats.
