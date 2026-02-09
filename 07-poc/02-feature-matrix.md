



# 02 Feature matrix

This matrix summarizes the features delivered by the PoC.

For the meta specifications, see [02-feature-matrix-meta.md](../10-appendix/meta/07-poc/02-feature-matrix-meta.md).

| Area | PoC feature | Notes |
| --- | --- | --- |
| Protocol envelopes | Structural validation + ordering | See [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md) |
| Storage | SQLite, migrations, global_seq | See [03-data/**](../03-data/) |
| Managers | Config, Storage, Schema, ACL, Graph, State, Network, DoS, Auth, Log, Event, Health, App, Key | See [02-architecture/managers/**](../02-architecture/managers/) |
| System services | Graph, Sync, Identity, Network, Bootstrap | See [02-architecture/services-and-apps/02-system-services.md](../02-architecture/services-and-apps/02-system-services.md) |
| App services | Contact list, messaging, social, and market (domain app) | See [POC-APPS.md](../../docs-build/POC-APPS.md) |
| Interfaces | Local HTTP + WebSocket | See [04-interfaces/**](../04-interfaces/) |
| Frontend | Flask scaffold, auth flow, and marketplace UI (app discovery/install) | See [BUILD-PLAN.md](../../docs-build/BUILD-PLAN.md) |
| Tests | Unit, integration, and e2e placeholders | See [TEST-CONVENTIONS.md](../../docs-build/TEST-CONVENTIONS.md) and [TRACEABILITY.md](../../docs-build/TRACEABILITY.md) |

## 3. PoC app schemas (authoritative for app payloads)

Unknown fields are rejected for all schemas below. All PoC app writes use `POST /graph/envelope`; list/read flows use the Graph Manager read surface.

### 3.1 Contacts app (`app.contacts`)

Type: `contact.profile` (Parent)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `handle` | Yes | string | 1-64 chars, lowercase `[a-z0-9_]+`. |
| `display_name` | No | string | 1-128 chars. |
| `email` | No | string | 3-254 chars. |
| `phone` | No | string | 3-32 chars. |
| `avatar_url` | No | string | 1-2048 chars. |
| `status` | No | string | `active`, `blocked`, or `archived`. |
| `tags` | No | array[string] | 0-16 items, each 1-24 chars. |
| `identity_id` | No | string | Identity id bound to this profile (used for degree-of-separation reads). |
| `created_at` | Yes | string | RFC3339 timestamp. |
| `updated_at` | No | string | RFC3339 timestamp. |

Type: `contact.link` (Edge)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `relation` | Yes | string | `friend`, `coworker`, `family`, or `other`. |
| `created_at` | Yes | string | RFC3339 timestamp. |

Type: `contact.trust` (Rating)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `value` | Yes | int | -1, 0, or 1. |
| `reason` | No | string | 0-256 chars. |
| `created_at` | Yes | string | RFC3339 timestamp. |

### 3.2 Messaging app (`app.messaging`)

Type: `message.thread` (Parent)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `title` | Yes | string | 1-120 chars. |
| `created_at` | Yes | string | RFC3339 timestamp. |
| `created_by` | Yes | string | Identity id of creator. |
| `visibility` | No | string | `private` or `shared`. |
| `archived` | No | bool | Default false. |

Type: `message.item` (Parent)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `thread_id` | Yes | string | Parent id of `message.thread`. |
| `body` | Yes | string | 1-2000 chars. |
| `sent_at` | Yes | string | RFC3339 timestamp. |
| `author_id` | Yes | string | Identity id of author. |
| `edited_at` | No | string | RFC3339 timestamp. |
| `reply_to_id` | No | string | Parent id of `message.item`. |
| `kind` | No | string | `text` or `system`. |

Type: `message.participant` (Edge)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `role` | Yes | string | `member` or `admin`. |
| `joined_at` | Yes | string | RFC3339 timestamp. |

Type: `message.reaction` (Rating)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `value` | Yes | int | 0-5. |
| `reaction` | No | string | 1-24 chars. |
| `created_at` | Yes | string | RFC3339 timestamp. |

### 3.3 Social app (`app.social`)

Type: `social.post` (Parent)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `title` | No | string | 1-120 chars. |
| `body` | Yes | string | 1-2000 chars. |
| `created_at` | Yes | string | RFC3339 timestamp. |
| `author_id` | Yes | string | Identity id of author. |
| `visibility` | No | string | `public`, `followers`, or `private`. |
| `edited_at` | No | string | RFC3339 timestamp. |

Type: `social.comment` (Parent)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `post_id` | Yes | string | Parent id of `social.post`. |
| `body` | Yes | string | 1-2000 chars. |
| `created_at` | Yes | string | RFC3339 timestamp. |
| `author_id` | Yes | string | Identity id of author. |
| `reply_to_id` | No | string | Parent id of `social.comment`. |

Type: `social.mention` (Edge)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `context` | Yes | string | `post` or `comment`. |
| `created_at` | Yes | string | RFC3339 timestamp. |

Type: `social.reaction` (Rating)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `value` | Yes | int | 0-5. |
| `reaction` | No | string | 1-24 chars. |
| `created_at` | Yes | string | RFC3339 timestamp. |

### 3.4 Market app (`app.market`)

Type: `market.listing` (Parent)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `title` | Yes | string | 1-120 chars. |
| `description` | No | string | 0-2000 chars. |
| `category` | No | string | 1-64 chars. |
| `price_cents` | Yes | int | 0-100000000. |
| `currency` | Yes | string | 3 chars (ISO 4217). |
| `status` | Yes | string | `active`, `sold`, or `archived`. |
| `quantity` | No | int | 1-100000. |
| `unit` | No | string | 1-16 chars. |
| `seller_id` | Yes | string | Identity id of seller. |
| `location` | No | string | 0-128 chars. |
| `created_at` | Yes | string | RFC3339 timestamp. |
| `updated_at` | No | string | RFC3339 timestamp. |

Type: `market.offer` (Parent)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `listing_id` | Yes | string | Parent id of `market.listing`. |
| `price_cents` | Yes | int | 0-100000000. |
| `message` | No | string | 1-256 chars. |
| `buyer_id` | Yes | string | Identity id of buyer. |
| `status` | Yes | string | `pending`, `accepted`, or `rejected`. |
| `created_at` | Yes | string | RFC3339 timestamp. |

Type: `market.contract` (Parent)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `offer_id` | Yes | string | Parent id of `market.offer`. |
| `status` | Yes | string | `open`, `fulfilled`, or `cancelled`. |
| `created_at` | Yes | string | RFC3339 timestamp. |

Type: `market.participant` (Edge)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `role` | Yes | string | `seller` or `buyer`. |
| `created_at` | Yes | string | RFC3339 timestamp. |

Type: `market.feedback` (Rating)

| Field | Required | Type | Constraints |
| --- | --- | --- | --- |
| `value` | Yes | int | 1-5. |
| `comment` | No | string | 0-512 chars. |
| `created_at` | Yes | string | RFC3339 timestamp. |

## 4. PoC app list/read request shapes

PoC list/read flows use `GraphReadRequest` via `/apps/{slug}/list` and `/apps/{slug}/read`. The shapes below are canonical and must be used by frontend flows.

### 4.1 Contacts app (`app.contacts`)

List contacts (default):

```
{
  "read_request": {
    "app_id": <app.contacts>,
    "target": "parent",
    "parent_type": "contact.profile",
    "order_by": "updated_at",
    "order_dir": "desc",
    "limit": 50
  }
}
```

Read contact by id:

```
{
  "read_request": {
    "app_id": <app.contacts>,
    "target": "parent",
    "parent_type": "contact.profile",
    "filters": [
      {"op": "parent_id_equals", "parent_id": "<contact_parent_id>"}
    ],
    "limit": 1
  }
}
```

### 4.2 Messaging app (`app.messaging`)

List threads:

```
{
  "read_request": {
    "app_id": <app.messaging>,
    "target": "parent",
    "parent_type": "message.thread",
    "order_by": "updated_at",
    "order_dir": "desc",
    "limit": 50
  }
}
```

List messages for a thread:

```
{
  "read_request": {
    "app_id": <app.messaging>,
    "target": "parent",
    "parent_type": "message.item",
    "filters": [
      {"op": "parent_field_equals", "parent_field": "thread_id", "value": "<thread_parent_id>"}
    ],
    "order_by": "created_at",
    "order_dir": "asc",
    "limit": 200
  }
}
```

### 4.3 Social app (`app.social`)

List posts:

```
{
  "read_request": {
    "app_id": <app.social>,
    "target": "parent",
    "parent_type": "social.post",
    "order_by": "created_at",
    "order_dir": "desc",
    "limit": 50
  }
}
```

List comments for a post:

```
{
  "read_request": {
    "app_id": <app.social>,
    "target": "parent",
    "parent_type": "social.comment",
    "filters": [
      {"op": "parent_field_equals", "parent_field": "post_id", "value": "<post_parent_id>"}
    ],
    "order_by": "created_at",
    "order_dir": "asc",
    "limit": 200
  }
}
```

### 4.4 Market app (`app.market`)

List listings:

```
{
  "read_request": {
    "app_id": <app.market>,
    "target": "parent",
    "parent_type": "market.listing",
    "filters": [
      {"op": "parent_field_equals", "parent_field": "status", "value": "active"}
    ],
    "order_by": "created_at",
    "order_dir": "desc",
    "limit": 50
  }
}
```

List offers for a listing:

```
{
  "read_request": {
    "app_id": <app.market>,
    "target": "parent",
    "parent_type": "market.offer",
    "filters": [
      {"op": "parent_field_equals", "parent_field": "listing_id", "value": "<listing_parent_id>"}
    ],
    "order_by": "created_at",
    "order_dir": "desc",
    "limit": 50
  }
}
```

