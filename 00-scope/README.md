



# 00 Scope

This folder defines the system boundary for the 2WAY proof of concept. It establishes repository-wide
invariants, trust boundaries, and rejection behavior, along with canonical terminology used across
all other documents.

If a requirement appears to conflict with anything outside this folder, treat this folder as the
authoritative source and record exceptions in an ADR.

## What lives here

- [`00-scope-overview.md`](00-scope-overview.md) - Global invariants, trust boundaries, and invalid input handling.
- [`01-scope-and-goals.md`](01-scope-and-goals.md) - System scope, goals, allowed/forbidden behavior, and guarantees.
- [`02-non-goals-and-out-of-scope.md`](02-non-goals-and-out-of-scope.md) - Explicit exclusions and non-goals with rejection expectations.
- [`03-definitions-and-terminology.md`](03-definitions-and-terminology.md) - Canonical terms and object names used throughout the repo.
- [`04-assumptions-and-constraints.md`](04-assumptions-and-constraints.md) - PoC assumptions, constraints, and hard exclusions.

Each document has a corresponding meta specification in [`09-appendix/meta/00-scope/`](../09-appendix/meta/00-scope/).

## How to read

1. Start with [`00-scope-overview.md`](00-scope-overview.md) for the top-level invariants and trust boundaries.
2. Read [`01-scope-and-goals.md`](01-scope-and-goals.md) and [`02-non-goals-and-out-of-scope.md`](02-non-goals-and-out-of-scope.md) to understand the boundary.
3. Use [`04-assumptions-and-constraints.md`](04-assumptions-and-constraints.md) to confirm what the PoC must and must not rely on.
4. Keep [`03-definitions-and-terminology.md`](03-definitions-and-terminology.md) open as a reference for canonical terms.

## Key guarantees this folder enforces

- Trust boundaries are explicit: network, frontend, and app inputs are untrusted until validated.
- Graph writes are only permitted via Graph Manager.
- Raw database access is restricted to Storage Manager.
- All request-scoped work is bound to a complete [`OperationContext`](../02-architecture/services-and-apps/05-operation-context.md).
- Authentication and requester resolution are mediated by Auth Manager.
- Schema validation and ACL authorization are required for all persisted mutations.
- Sync state transitions are applied by State Manager.
- Event emission and audit logging are mediated by Event Manager and Log Manager.
- Private keys are owned and accessed only by Key Manager.
- `global_seq` is strictly monotonic for accepted writes.
- Rejections produce no persistent state changes and do not advance sequence.
- Rejections do not emit state-changing events.
- PoC process and persistence constraints assume a single long-running backend process
  with a single serialized writer path using SQLite.

## Using this folder in reviews

- Treat undefined behavior as unsupported.
- If a design depends on a non-goal or an excluded assumption, treat it as a correctness defect.
- Use the canonical terms from `03-definitions-and-terminology.md` in all normative text.
