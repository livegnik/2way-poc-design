



# 01 First-run and identity bootstrap

This flow defines the first-run installation and Server Graph initialization sequence. It runs exactly once per node and establishes the initial node identity, admin identity, and device bindings.

For the meta specifications, see [01-first-run-and-identity-bootstrap-meta.md](../10-appendix/meta/06-flows/01-first-run-and-identity-bootstrap-meta.md).

## 1. Inputs

* First-run invocation with no existing persistent state.
* Bootstrap capability token (local-only) issued by the installation surface.
* Node metadata (node name, optional metadata).

## 2. Preconditions

* Database exists but contains no Server Graph objects.
* Required system tables and migrations are present.
* Bootstrap capability is valid and unexpired.

## 3. Flow

1) Interface layer or CLI invokes bootstrap service with node and admin details.

2) Bootstrap service constructs an OperationContext with:

   * app_id = 0
   * actor_type = service
   * capability = system.bootstrap.install

3) Key Manager generates the admin identity keypair.

4) Graph Manager applies bootstrap envelopes that create:

   * Server node parent object.
   * Admin identity parent object.
   * Device parent object.
   * Device ownership edge linking device -> identity.
   * Capability definition `system.admin` (if not already present) and a `capability.edge` granting it to the admin identity.
   * Created_at and node_name attributes.

5) Schema Manager validates bootstrap objects against system schema.

6) ACL Manager assigns initial ownership and default ACL bindings.

7) Storage Manager persists all objects atomically and seeds global sequence.

8) Event Manager emits installation milestones after commit.

9) Health Manager marks the node as ready.

## 4. Allowed behavior

* Single execution per node.
* Only Server Graph root objects are created.
* Admin identity is created before any app data.

## 5. Forbidden behavior

* Creating user or app graphs during bootstrap.
* Re-running bootstrap after any Server Graph object exists.
* Writing data outside Graph Manager.

## 6. Failure behavior

* Any validation or authorization failure aborts the flow.
* Partial bootstrap state is not persisted.
* No events are emitted on failure.
* When surfaced to a transport that returns `ErrorDetail`, the following mappings apply:

| Condition | Owner | ErrorDetail.code | ErrorDetail.category | Transport status |
| --- | --- | --- | --- | --- |
| Missing or invalid bootstrap token | Bootstrap Service | `ERR_BOOTSTRAP_ACL` | `acl` | `400` |
| Malformed bootstrap payload structure | Bootstrap Service | `envelope_invalid` | `structural` | `400` |
| Bootstrap schema validation failure | Bootstrap Service | `ERR_BOOTSTRAP_SCHEMA` | `schema` | `400` |
| Device attestation failure | Bootstrap Service | `ERR_BOOTSTRAP_DEVICE_ATTESTATION` | `auth` | `400` |
| Node already installed | Bootstrap Service | `ERR_BOOTSTRAP_ACL` | `acl` | `400` |
| Persistence failure | Storage Manager | `storage_error` | `storage` | `400` |
| Unexpected internal failure | Owning manager | `internal_error` | `internal` | `500` |
