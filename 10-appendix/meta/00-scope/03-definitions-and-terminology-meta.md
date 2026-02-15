



# 03 Definitions and terminology

## 1. Purpose and scope

This file defines the normative terminology used across the 2WAY PoC design repository. It standardizes names for core entities and concepts so that other documents can be read and reviewed without ambiguity.

This file does not define APIs, wire formats, database schemas, or protocol flows. Where a term depends on a formal structure, this file constrains meaning only and defers structure to the owning specification.

Previous drafts used SBPS, IRS, SOS, OCS and 'app service/app service' terminology. These are now system services (Setup Service, Identity Service, Sync Service, Admin Service) and app services.

## 2. Responsibilities

This specification defines:

- Canonical meanings for repository-level terms.
- Canonical names for the fundamental object types and related concepts.
- Names and scopes for terms used for apps, types, and domains.
- Security vocabulary needed to interpret authorization, signing, rotation, and revocation rules.

This specification does not define:

- How managers execute validation, enforcement, or persistence.
- Database schema, table layouts, or indexes.
- Envelope fields, request formats, or network message layouts.
- App-specific schemas or app-specific type catalogs.
