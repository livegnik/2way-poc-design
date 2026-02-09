



# 04 Contact and profile flow

This flow defines how contact and profile information is created and updated for identities.

For the meta specifications, see [04-contact-and-profile-flow-meta.md](../10-appendix/meta/06-flows/04-contact-and-profile-flow-meta.md).

## 1. Inputs

* Authenticated request from a frontend app.
* OperationContext for the requesting identity.
* Envelope containing profile or contact mutations.

## 2. Flow

1) Auth Manager resolves the requester identity and constructs OperationContext.

2) Graph Manager processes the envelope using the standard write flow.

3) Schema Manager validates profile/contact schema.

4) ACL Manager enforces:

   * Only an identity owner may modify their own profile objects.
   * Shared or public contact objects may be written only by authorized identities.

5) Storage Manager persists the new profile or contact objects.

6) Event Manager emits profile/contact update events after commit.

## 3. Allowed behavior

* Profile updates by the owning identity.
* Contact creation under an app-scoped namespace.

## 4. Forbidden behavior

* Modifying another identity's profile without explicit ACL permission.
* Writing profile/contact data outside Graph Manager.

## 5. Failure behavior

* Unauthorized updates are rejected without side effects.
* Storage errors roll back the entire envelope.
* When surfaced to a transport that returns `ErrorDetail`, the following mappings apply:

| Condition | Owner | ErrorDetail.code | ErrorDetail.category | Transport status |
| --- | --- | --- | --- | --- |
| Malformed profile/contact request or envelope | Interface layer | `envelope_invalid` | `structural` | `400` |
| Invalid identity or object identifiers | Interface layer | `identifier_invalid` | `structural` | `400` |
| Target profile/contact object not found | Graph Manager | `object_invalid` | `structural` | `400` |
| Unauthorized update attempt | ACL Manager | `acl_denied` | `acl` | `400` |
| Schema violation for profile/contact types | Schema Manager | `schema_validation_failed` | `schema` | `400` |
| Persistence failure | Storage Manager | `storage_error` | `storage` | `400` |
| Unexpected internal failure | Owning manager | `internal_error` | `internal` | `500` |
