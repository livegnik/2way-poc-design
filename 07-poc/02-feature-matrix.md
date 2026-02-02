



# 02 Feature matrix

This matrix summarizes the features delivered by the PoC.

For the meta specifications, see [02-feature-matrix-meta.md](../09-appendix/meta/07-poc/02-feature-matrix-meta.md).

| Area | PoC feature | Notes |
| --- | --- | --- |
| Protocol envelopes | Structural validation + ordering | See [01-protocol/03-serialization-and-envelopes.md](../01-protocol/03-serialization-and-envelopes.md) |
| Storage | SQLite, migrations, global_seq | See [03-data/**](../03-data/) |
| Managers | Config, Storage, Schema, ACL, Graph, State, Network, DoS, Auth, Log, Event, Health, App, Key | See [02-architecture/managers/**](../02-architecture/managers/) |
| System services | Graph, Sync, Identity, Network, Bootstrap | See [02-architecture/services-and-apps/02-system-services.md](../02-architecture/services-and-apps/02-system-services.md) |
| App services | Messaging and social | See [POC-APPS.md](../../POC-APPS.md) |
| Interfaces | Local HTTP + WebSocket | See [04-interfaces/**](../04-interfaces/) |
| Frontend | Flask scaffold and test smoke | See [BUILD-PLAN.md](../../BUILD-PLAN.md) |
| Tests | Unit, integration, and e2e placeholders | See [TEST-CONVENTIONS.md](../../TEST-CONVENTIONS.md) and [TRACEABILITY.md](../../TRACEABILITY.md) |
