



# 15 Debug logger utility

## 1. Purpose and scope

Defines the minimal debug logging utility used for developer-only diagnostics when structured logging is unnecessary or unavailable.

This specification references:

* [02-architecture/15-debug-logger.md](../../../02-architecture/15-debug-logger.md)
* [02-architecture/managers/01-config-manager.md](../../../02-architecture/managers/01-config-manager.md)
* [02-architecture/managers/12-log-manager.md](../../../02-architecture/managers/12-log-manager.md)

## 2. Responsibilities and boundaries

This specification is responsible for:

* Defining the debug logger API surface and behavior.
* Declaring config and environment-based enablement rules.
* Declaring restrictions to prevent debug logging from replacing structured logs.

This specification does not cover:

* Structured logging or audit requirements (owned by Log Manager).
* Persistence, retention, or log query behaviors.
