



# 02 App install and permissions

## 1. Purpose and scope

Defines the flow for app registration, schema provisioning, and initial permissions. This flow governs how apps enter the system and gain capabilities.

This specification references:

* [06-flows/02-app-install-and-permissions.md](../../../06-flows/02-app-install-and-permissions.md)
* [02-architecture/services-and-apps/03-app-services.md](../../../02-architecture/services-and-apps/03-app-services.md)
* [02-architecture/managers/08-app-manager.md](../../../02-architecture/managers/08-app-manager.md)
* [01-protocol/06-access-control-model.md](../../../01-protocol/06-access-control-model.md)

## 2. Responsibilities and boundaries

This specification is responsible for:

* Defining the ordering of app registration, schema validation, and ACL setup.
* Declaring the app install HTTP payload fields required by the interface contract.
* Declaring payload constraints for schema and ACL objects.
* Declaring package signature verification and extraction requirements for install.
* Declaring publisher trust requirements for app installation.
* Declaring allowed and forbidden app installation behaviors.
* Declaring failure mapping for app install errors.

This specification does not cover:

* App UI installation screens (documented in frontend app and PoC scope specs).
* Marketplace UX details beyond the app lifecycle and install contract.
* Package distribution channels outside the local install flow.
