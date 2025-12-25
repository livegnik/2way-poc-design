



# 09 State Manager

## 1. Purpose and scope

This document specifies the State Manager component within the 2WAY architecture. The State Manager is responsible for controlling local mutable system state derived from accepted, authorized graph operations and synchronization results. It defines how state transitions are ordered, committed, persisted, exposed, and recovered.

This document specifies only state handling semantics and boundaries. It does not define storage schemas, graph semantics, authorization rules, cryptographic verification, or network behavior, except where required to define inputs, outputs, and trust boundaries.

## 2. Responsibilities and boundaries

This specification is responsible for the following:

- Owning all mutable local system state.
- Applying authorized and validated state mutations in a single total order.
- Enforcing atomic state transitions.
- Ensuring deterministic state evolution for identical ordered inputs.
- Coordinating durable persistence of committed state.
- Providing consistent, read-only state access to internal components.
- Managing rollback boundaries on failed or rejected mutations.
- Reconstructing state after restart from persisted data only.
- Refusing state mutation when safety, ordering, or durability guarantees cannot be met.

This specification does not cover the following:

- Cryptographic verification of envelopes or signatures.
- Authorization, ACL evaluation, or policy decisions.
- Graph object schema definition or semantic validation.
- Conflict resolution semantics beyond ordering and rejection.
- Network transport, peer communication, or synchronization logic.
- Application-specific logic or derived business rules.
- Storage engine internals or physical database layout.

## 3. State definition and ownership

### 3.1 State definition

State is defined as the locally materialized result of applying an ordered sequence of accepted graph mutations. State includes:

- Materialized views required for core system operation.
- Derived indices or caches necessary for correctness or performance.
- Metadata required to track state version and commit progress.

State explicitly excludes:

- Raw envelopes or network messages.
- Unauthorized, rejected, or unverifiable inputs.
- Transient in-flight mutations.

### 3.2 Exclusive ownership

The State Manager is the sole authority permitted to mutate persisted state. No other component may write to stateful storage except through the State Manager. All state mutations must be serialized through this component.

## 4. Mutation ordering and determinism

### 4.1 Ordering model

All state mutations are applied in a single total order defined by the State Manager. Concurrent mutation requests must be serialized. Partial ordering or parallel application is forbidden.

### 4.2 Deterministic execution

State transition logic must be deterministic. Given the same initial state and the same ordered sequence of accepted mutations, the resulting state must be identical. Sources of non-determinism are forbidden.

## 5. Invariants and guarantees

### 5.1 Invariants and guarantees

Across all relevant components, boundaries, or contexts defined in this file, the following invariants and guarantees hold:

- State transitions are atomic. A mutation is either fully applied or not applied.
- Intermediate or partially applied state is never externally visible.
- State versions advance monotonically.
- Persisted state reflects only fully committed transitions.
- Concurrent mutation requests do not interleave state changes.
- Rejected mutations have no observable effect.
- State exposed to consumers is internally consistent at all times.

These guarantees must hold regardless of caller, execution context, input source, or peer behavior, unless explicitly stated otherwise.

## 6. Allowed and forbidden behaviors

### 6.1 Explicitly allowed behaviors

The following behaviors are explicitly allowed:

- Rejecting mutations that violate ordering, consistency, or safety constraints.
- Buffering authorized mutations pending ordered application.
- Rebuilding state entirely from persisted data during recovery.
- Exposing read-only state snapshots to trusted internal components.
- Halting acceptance of new mutations when durability cannot be guaranteed.

### 6.2 Explicitly forbidden behaviors

The following behaviors are explicitly forbidden:

- Applying mutations that have not been authorized and validated upstream.
- Allowing multiple writers to mutate state concurrently.
- Exposing intermediate, speculative, or partially applied state.
- Mutating state based on unverifiable or rejected inputs.
- Bypassing the State Manager for any stateful write operation.

## 7. Component interactions

### 7.1 Inputs

The State Manager accepts the following inputs:

- Authorized and validated mutation requests from the Graph Manager.
- Recovery directives during startup or restore flows.
- Explicit rollback or reinitialization signals from trusted system control paths.

All inputs are assumed to originate from trusted internal components and to have passed required validation stages.

### 7.2 Outputs

The State Manager produces the following outputs:

- Committed state writes issued to the Storage Manager.
- Read-only state views provided to internal consumers.
- Explicit rejection or failure signals for unsuccessful mutations.

### 7.3 Trust boundaries

The State Manager relies on upstream components to ensure that:

- Cryptographic verification is complete.
- Authorization decisions are final.
- Schema and structural validation has succeeded.

The State Manager does not re-evaluate these properties.

## 8. Failure handling and recovery

### 8.1 Invalid mutations

If a mutation violates ordering rules, determinism constraints, or state consistency requirements, it must be rejected. Rejected mutations must not alter state or persistence.

### 8.2 Partial failure

If a failure occurs during mutation application or persistence:

- The mutation is treated as not applied.
- State must be rolled back to the last committed version.
- No partial effects may be observable.

### 8.3 Restart and recovery

On restart, the State Manager must reconstruct state exclusively from persisted data. In-memory state and in-flight mutations must be discarded. Recovery must not assume completion of interrupted operations.

### 8.4 Degraded operation

If persistence or other required dependencies are unavailable, the State Manager must refuse new state mutations. Previously committed state may continue to be served in read-only form where safe.

## 9. Security considerations

The State Manager is a core integrity boundary. Violations of ordering, atomicity, or determinism can result in state divergence or data corruption. Implementations must strictly enforce all invariants and forbidden behaviors defined in this document.

The State Manager must not weaken, override, or reinterpret security decisions made by upstream components.

## 10. Compliance criteria

An implementation complies with this specification if it:

- Enforces exclusive state ownership.
- Applies mutations in a single total order.
- Preserves atomicity, consistency, and durability guarantees.
- Rejects all forbidden behaviors.
- Correctly handles failure and recovery scenarios without state corruption.
