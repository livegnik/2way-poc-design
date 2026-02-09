



# 05 Messaging flow

This flow defines messaging behavior for the PoC messaging app schema.

For the meta specifications, see [05-messaging-flow-meta.md](../10-appendix/meta/06-flows/05-messaging-flow-meta.md).

## 1. Inputs

* Authenticated frontend request to create a conversation or send a message.
* OperationContext with app_id=messaging and capability `app.messaging.write`.
* Graph message envelope representing conversation/message objects.

## 2. Create conversation flow

1) Frontend submits a request with participant identities and optional title.

2) Messaging app service constructs a graph envelope:

   * conversation parent
   * created_at attribute
   * optional title attribute
   * conversation_participant edges for each participant

3) Graph Manager applies the envelope using the standard write flow.

4) Storage Manager persists the objects and assigns global_seq.

## 3. Send message flow

1) Frontend submits a request with conversation_id and message body.

2) Messaging app service constructs a graph envelope:

   * message parent
   * body + created_at attributes
   * message_in_conversation edge
   * message_author edge

3) Graph Manager applies the envelope using the standard write flow.

4) Event Manager emits message events after commit.

## 4. Read flow

1) Frontend requests inbox or conversation contents with capability `app.messaging.read`.

2) ACL Manager enforces that only conversation participants can read messages.

3) Storage Manager executes constrained read queries.

## 5. Failure behavior

* Non-participants are denied for reads and writes.
* Invalid conversation references are rejected.
* No partial writes are allowed.
* When surfaced to a transport that returns `ErrorDetail`, the following mappings apply:

| Condition | Owner | ErrorDetail.code | ErrorDetail.category | Transport status |
| --- | --- | --- | --- | --- |
| Malformed messaging request or envelope | Interface layer | `envelope_invalid` | `structural` | `400` |
| Invalid conversation or message identifiers | Interface layer | `identifier_invalid` | `structural` | `400` |
| Conversation not found | Graph Manager | `object_invalid` | `structural` | `400` |
| Non-participant access or write attempt | ACL Manager | `acl_denied` | `acl` | `400` |
| Schema violation for messaging types | Schema Manager | `schema_validation_failed` | `schema` | `400` |
| Persistence failure | Storage Manager | `storage_error` | `storage` | `400` |
| Unexpected internal failure | Owning manager | `internal_error` | `internal` | `500` |
