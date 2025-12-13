Let us walk through a concrete story.

We will use:

* Node A: your server
* Node B: remote server
* Domains:

  * `identities`
  * `messages`
  * `market.public_offers`

Apps:

* Node A has: identities, contacts, messages, market, rides
* Node B has: identities, contacts, messages, rides, but no market app

We assume:

* `change_seq` and `sync_flags` exist on Parent and Attr rows
* `sync_state(peer_id, domain, last_seq)` exists
* `SYNC_DOMAINS` is loaded from schema
* ACLManager and GraphManager already work

I will show:

1. Initial handshake
2. Initial pull sync
3. Local write and change_seq
4. Periodic pull
5. Optional push
6. Where ACLs fire
7. How we filter by installed apps

---

## 1. Handshake between nodes

### 1.1 Bastion handshake

Node B wants to connect to Node A.

1. B contacts A on Bastion onion.

2. A issues a puzzle challenge.

3. B solves it and sends back:

   * its server identity (pubkey, identity oid)
   * list of installed apps and supported sync domains, for example:

   ```json
   {
     "apps": ["identities", "contacts", "messages", "rides"],
     "sync_domains": ["identities", "messages", "rides.offers"]
   }
   ```

4. A verifies and stores B as a peer in the graph.

5. A records peer metadata in a local table:

   ```text
   peer_id = "pubkey_B"
   peer_apps = ["identities", "contacts", "messages", "rides"]
   peer_sync_domains = ["identities", "messages", "rides.offers"]
   ```

A does something similar to inform B of its own apps and sync domains.

Note:

* Node A may support `market.public_offers`, but B does not list that domain. So later there will be no syncing for `market.public_offers` with this peer.

---

## 2. Initial pull sync

Assume we start with **pull** as the baseline.

### 2.1 Messages domain example

B wants to pull messages from A.

1. B calls A’s `/sync/pull` endpoint with:

   ```json
   {
     "peer_id": "pubkey_B",
     "domain": "messages",
     "last_seq": 0
   }
   ```

2. On A:

   * Read `sync_state(peer_B, "messages")`. It is empty, treat `last_seq = 0`.

   * Look up `SYNC_DOMAINS["messages"]`. It says:

     ```json
     {
       "parent_types": ["messages.conversation", "messages.message"],
       "mode": "append_only"
     }
     ```

   * Node A also knows that messages are private between participants. So for this peer we only sync messages where B is a participant.

3. A builds a query for `messages.message` Parents:

   Simplified:

   ```sql
   SELECT *
   FROM app_messages_parent AS p
   JOIN app_messages_attr AS a_conv
     ON a_conv.parent_id = p.id
    AND a_conv.type = 'messages.message.conversation_parent_oid'
   JOIN app_messages_attr AS a_participants
     ON a_participants.parent_id = a_conv.value_parent_id
    AND a_participants.type = 'messages.conversation.participant_identity_oids'
   WHERE p.change_seq > :last_seq
     AND (p.sync_flags & :messages_mask) != 0
     AND :identity_oid_B IN parse_json(a_participants.value)
   ORDER BY p.change_seq
   LIMIT :batch_size;
   ```

   You will index this properly of course. I am showing logic, not exact SQL.

4. A also fetches the needed Attributes for those Parents.

5. A packages results into a package:

   ```json
   {
     "domain": "messages",
     "from_seq": 0,
     "to_seq": 1432,
     "objects": [
       { "type": "parent", "app_id": messages_app_id, ... },
       { "type": "attr", ... },
       ...
     ],
     "signature": "..."
   }
   ```

6. ACLs here:

   * When constructing the set, A implicitly enforces:

     * only objects where peer B has read rights.
       For messages we have a rule: participants of the conversation have read access.
       That rule is baked into MessagesService or into ACL templates for message Parents.
   * A can also run ACLManager.check_access_for_remote(subject = B, object_oid, operation = "sync_read").
     For performance you usually encode this as schema rule and avoid per row calls.

7. A sends the package to B and updates:

   ```sql
   INSERT OR REPLACE INTO sync_state(peer_id, domain, last_seq)
   VALUES ('pubkey_B', 'messages', 1432);
   ```

8. On B:

   * B verifies the package signature via KeyManager.

   * For each object, B builds an OpContext:

     ```python
     op_ctx = OpContext(
       requester_pubkey_attr_id = server_A_pubkey_attr_id,
       app_id = envelope["app_id"],
       is_remote = True,
       trace_id = ...
     )
     ```

   * B calls GraphManager.apply_message for each envelope.

   * GraphManager calls ACLManager.check_remote_write with:

     * sync_domain = "messages"
     * mode = "append_only"

   * ACLManager enforces:

     * remote cannot edit local messages
     * only append new messages or new conversations
     * cannot overwrite local owned objects

So initial messages are synced without scanning everything, only change_seq > 0 and with domain mask and participant filter.

---

## 3. Local write and change_seq

Now a user on A sends a new message to a user on B.

1. Frontend app on A calls `/api/messages/send` on A with:

   * sender_identity_oid = `identity_A`
   * recipient_identity_oid = `identity_B`
   * body = `"Hi"`

2. MessagesService on A creates:

   * Parent `messages.message` plus its Attributes
   * Through GraphManager, each write:

     * increments `GLOBAL_CHANGE_SEQ`, say from 1432 to 1433
     * computes `sync_flags` for this message Parent and Attributes:

       * `sync_flags |= messages_domain_mask`
     * sets `change_seq = 1433`

3. ACLManager assigns default ACL:

   * participants have read
   * sender has write (maybe status updates)

So a single message creates a handful of rows, all tagged with:

* `change_seq = 1433`
* `sync_flags` indicating the `messages` domain

No external log, no extra table write.

---

## 4. Next pull from Node B

Time passes. B pulls again.

1. B calls `/sync/pull` with:

   ```json
   {
     "peer_id": "pubkey_B",
     "domain": "messages",
     "last_seq": 1432
   }
   ```

2. A reads `last_seq = 1432`.

3. A queries messages only where:

   * `change_seq > 1432`
   * `sync_flags` includes messages domain
   * B is a participant

This is only the newly created message.
No rescan of the entire messages table.

4. A builds a package from `1433` to `1433`, sends it, updates `last_seq`.

5. B applies it as before with ACLManager enforcing domain rules.

---

## 5. Optional push

If you want A to push instead of B pulling:

* A can keep a timer and for each peer and domain do the same “build package since last_seq” and send it out, instead of waiting for B to ask.

Or, if you want immediate push:

* Add a tiny `sync_outbox` with `(peer_id, domain, change_seq)` per new change for that domain.
* When a new message with change_seq 1433 is created:

  * insert `('pubkey_B', 'messages', 1433)`
* A push worker for B then:

  * looks up outbox entries for B and domain `messages`
  * fetches those objects
  * sends the package
  * deletes the outbox entries

Still no full payload log. Only keys per changed object.

But for now, regular short interval pull with `change_seq` is simple and good enough.

---

## 6. How ACLs play a role in sync

ACLs appear in three places.

### 6.1 At write time, local

When a user or app writes data locally:

* GraphManager calls ACLManager.check_access(op_ctx, subject_oid, "write")
* ACLManager decides based on:

  * owner identity
  * group membership
  * ACL objects on the parent or app defaults
* If allowed:

  * object is written and gets `change_seq` and `sync_flags`

So only valid objects even enter the domain.

### 6.2 At package build time, outbound

When StateEngine builds an outbound package for peer B and domain D:

* It selects rows based on:

  * `change_seq > last_seq`
  * `sync_flags` for domain D
* It must also ensure that sending to B is allowed.

Two options.

1. Enforce privacy by schema:

   * For example, `identities` domain only includes public identity attributes.
   * `messages` domain includes messages but selection also filters by participant.
   * Domain level rules ensure we never include objects that should not leave.

2. Enforce ACL per row:

   * Optionally call:

     * `ACLManager.check_access_for_remote(remote_server_identity, object_oid, "sync_read")`
   * This can be expensive per row, so you only use it for domains where schema rules are not enough.

In practice you combine both:

* schema defines which types are syncable and with what mode
* domain specific selection queries filter by participants or groups
* ACL is there to catch any odd cases

### 6.3 At package apply time, inbound

On the receiver, B:

* For each incoming object, GraphManager.apply_message is called with `is_remote = True` and `sync_domain = D`.
* ACLManager.check_remote_write enforces domain modes:

  * `append_only`: remote cannot update or delete
  * `allow_update`: remote can update own objects, but not ours
  * `no_update`: probably only used for some domains

So remote cannot destroy or corrupt local objects because even if the package contains an update, ACLManager will reject it.

---

## 7. How we limit syncing to apps that both sides care about

You asked:

> How efficient is syncing all the different things from the different apps a remote user might have access to? And how do we make sure that if a remote user requests to sync data that only the apps they or the other party have installed are synced in our system?

We control that at two levels.

### 7.1 Install and domain intersection

At handshake time:

* Each server sends:

  * list of app slugs
  * list of sync domains it supports

StateEngine then computes for this peer:

* Allowed domains = intersection of:

  * local supported domains
  * remote supported domains

For example:

* A supports: `["identities", "contacts", "messages", "rides.offers", "market.public_offers"]`
* B supports: `["identities", "contacts", "messages", "rides.offers"]`

Intersection:

* `["identities", "contacts", "messages", "rides.offers"]`

So A will never sync `market.public_offers` with B.
Even if B tried to request it, A sees that `domain` is not in `peer_sync_domains` and returns nothing.

### 7.2 Schema and ACL for per object decisions

Even inside a domain, not all objects are shared.

Examples:

* messages:

  * only share messages where B is participant, even though the domain is `messages`
  * this uses participants list and maybe ACL templates
* rides.offers:

  * maybe only share offers with radius or region that both nodes care about
  * that is app specific, but typically done by the frontend or a backend extension, not by the kernel

If a frontend app on B asks for sync for a domain that no local app uses:

* Node A will not send it, because the domain intersection is empty or disabled.
* Even if some objects exist in that domain locally, there is no remote consumer, so you can choose to avoid sending them.

---

## 8. How efficient is this in practice

Summary of work per sync domain and peer:

* No full rescan.
* Query cost is proportional to:

  * number of changed objects since last_seq
  * not total number of objects

Storage overhead:

* Two integers per row: `change_seq`, `sync_flags`
* One small `sync_state` row per `(peer, domain)`
* Optional `sync_outbox` rows per changed object if you use push scheduling

CPU:

* O(1) overhead per write to update `change_seq` and flags
* O(delta) per sync, where delta is number of changed objects since last sync

Network:

* You only ship changes, not whole domains.

This lines up with your design philosophy:

* no heavy global logs
* use the graph and schema to express everything
* add the minimum metadata needed for efficient incremental sync

If you want, next step we can write concrete table definitions and a little pseudo code or Python skeleton for:

* `GraphManager.save_with_sync`
* `StateEngine.build_package`
* `StateEngine.apply_package`

so you can see exactly what happens in code.
