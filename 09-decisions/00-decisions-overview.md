



# **Architecture Decision Records**

This directory contains all long-term architectural decisions that define the 2WAY protocol, its system architecture, and its PoC implementation. Each ADR captures a single stable decision, why it was chosen, and the constraints it introduces. Together they form the canonical reference for how the protocol operates, how backend managers and services interact, how frontend apps integrate with the backend, and how nodes synchronize and enforce authority.

The ADRs are grouped into categories that match the conceptual layers of the system:
- Foundational ADRs describe the theoretical basis of the protocol.
- Protocol-level ADRs describe the rules every implementation must honor.
- System architecture ADRs describe how the protocol maps onto managers, services, and apps.
- Backend and frontend ADRs define implementation-level guarantees.
- Sync and networking ADRs describe how nodes communicate and maintain distributed consistency.
- Operational ADRs cover configuration, initialization, debugging, and long-term maintainability.

These decisions create the stable backbone for the PoC and all future evolution.

# **0. Foundations and Theory**

## **0.1. Core Protocol Philosophy**

```
adr-000-01-01-protocol-purpose-and-scope.md
adr-000-01-02-graph-as-universal-data-layer.md
adr-000-01-03-object-model-parent-attr-rating-edge.md
adr-000-01-04-identity-as-cryptographic-authority.md
adr-000-01-05-local-first-design-principle.md
adr-000-01-06-user-owned-state-and-decentralized-control.md
adr-000-01-07-local-authority-vs-remote-authority.md
adr-000-01-08-object-ownership-as-a-global-invariant.md
adr-000-01-09-append-only-graph-growth-as-default-behavior.md
adr-000-01-10-frontier-expansion-rule-for-new-data.md
adr-000-01-11-domain-isolation-as-a-boundary-of-meaning.md
adr-000-01-12-the-protocol-as-a-minimal-kernel-not-a-platform.md
adr-000-01-13-interoperability-through-shared-semantics.md
adr-000-01-14-the-separation-of-intent-vs-representation.md
adr-000-01-15-the-holistic-role-of-edges-in-knowledge-shape.md
```

## **0.2. Trust, Reputation, and Social Structure**

```
adr-000-02-01-trust-graph-model.md
adr-000-02-02-ratings-as-evaluative-objects.md
adr-000-02-03-sybil-resistance-and-identity-constraints.md
adr-000-02-04-degrees-of-separation-and-trust-propagation.md
adr-000-02-05-group-forming-dynamics-and-social-topology.md
adr-000-02-06-context-dependent-trust-evaluation.md
adr-000-02-07-local-vs-propagated-reputation.md
adr-000-02-08-trust-dampening-and-decay-rules.md
adr-000-02-09-multidimensional-reputation-spaces.md
adr-000-02-10-reputation-anchoring-in-object-ownership.md
adr-000-02-11-identity-strength-and-key-longevity.md
adr-000-02-12-emergent-hierarchies-without-central-authority.md
adr-000-02-13-reliability-of-information-flows-in-social-graphs.md
```

## **0.3. Economic and Network-Theoretic Principles**

```
adr-000-03-01-network-effects-and-metcalfes-law.md
adr-000-03-02-group-networks-and-reeds-law.md
adr-000-03-03-scale-constraints-and-moores-law.md
adr-000-03-04-marginal-cost-of-coordination-in-distributed-systems.md
adr-000-03-05-incentive-structures-and-participation-dynamics.md
adr-000-03-06-data-network-theory-and-value-creation.md
adr-000-03-07-economic-friction-in-centralized-vs-distributed-systems.md
adr-000-03-08-distribution-of-agency-among-nodes.md
adr-000-03-09-self-amplifying-value-of-local-first-architectures.md
adr-000-03-10-negative-network-effects-and-failure-propagation.md
adr-000-03-11-limits-of-scaling-without-global-consensus.md
adr-000-03-12-cost-of-abstraction-vs-cost-of-coordination.md
```

## **0.4. Privacy, Autonomy, and Safety**

```
adr-000-04-01-privacy-model-and-threat-surfaces.md
adr-000-04-02-consent-driven-data-sharing.md
adr-000-04-03-local-storage-vs-synced-storage-boundaries.md
adr-000-04-04-contextual-access-and-least-privilege.md
adr-000-04-05-adversarial-assumptions-and-resilience.md
adr-000-04-06-anonymity-vs-authenticity-tradeoffs.md
adr-000-04-07-attribute-level-encryption-philosophy.md
adr-000-04-08-data-minimization-through-object-decomposition.md
adr-000-04-09-observability-vs-privacy-in-distributed-graphs.md
adr-000-04-10-revocation-limits-in-a-distributed-world.md
adr-000-04-11-ownership-loss-and-identity-recovery-theory.md
adr-000-04-12-social-harm-mitigation-in-open-networks.md
```

## **0.5. Consistency, Causality, and Synchronization Theory**

```
adr-000-05-01-eventual-consistency-in-distributed-graphs.md
adr-000-05-02-causal-ordering-and-object-versioning.md
adr-000-05-03-ownership-as-a-consistency-anchor.md
adr-000-05-04-conflict-handling-and-deterministic-resolution.md
adr-000-05-05-sync-as-state-convergence-not-replication.md
adr-000-05-06-local-vs-global-knowledge-paradox.md
adr-000-05-07-causality-boundaries-between-sync-domains.md
adr-000-05-08-interpretation-vs-ordering-consistency.md
adr-000-05-09-latency-tolerance-in-eventual-systems.md
adr-000-05-10-meaning-preservation-in-concurrent-writes.md
```

## **0.6. Threat Models and System Integrity**

```
adr-000-06-01-adversarial-network-assumptions.md
adr-000-06-02-data-integrity-and-forgery-prevention.md
adr-000-06-03-failure-modes-in-distributed-identity-systems.md
adr-000-06-04-social-attacks-vs-technical-attacks.md
adr-000-06-05-trust-boundaries-between-nodes.md
adr-000-06-06-resilience-under-partial-compromise.md
adr-000-06-07-limits-of-defense-against-metadata-analysis.md
adr-000-06-08-decentralized-detectability-of-abuse-behavior.md
adr-000-06-09-zero-assumption-policy-on-peer-honesty.md
```

# **1. Protocol-Level Decisions**

## **1.1. Object Semantics and Structure**

```
adr-001-01-01-parent-object-semantics.md
adr-001-01-02-attribute-object-semantics.md
adr-001-01-03-rating-object-semantics.md
adr-001-01-04-edge-object-semantics.md
adr-001-01-05-object-oid-rules.md
adr-001-01-06-object-ownership-rules.md
adr-001-01-07-object-mutation-rules.md
adr-001-01-08-object-lifecycle.md
adr-001-01-09-object-normalization.md
adr-001-01-10-object-type-keys-and-schema-mapping.md
```

## **1.2. Envelopes, Operations, and Commands**

```
adr-001-02-01-envelope-format.md
adr-001-02-02-operation-types.md
adr-001-02-03-operationcontext-requirements.md
adr-001-02-04-operation-validation.md
adr-001-02-05-operation-causality-rules.md
adr-001-02-06-operation-deduplication.md
adr-001-02-07-forbidden-operations.md
adr-001-02-08-envelope-signature-rules.md
adr-001-02-09-envelope-ordering-rules.md
```

## **1.3. Identity, Keys, and Authorization**

```
adr-001-03-01-identity-representation.md
adr-001-03-02-pubkey-as-identity-anchor.md
adr-001-03-03-device-identities.md
adr-001-03-04-signature-verification.md
adr-001-03-05-owner-write-authority.md
adr-001-03-06-foreign-write-restrictions.md
adr-001-03-07-identity-proofs.md
adr-001-03-08-key-rotation.md
adr-001-03-09-identity-recovery.md
```

## **1.4. ACL Model and Permission Semantics**

```
adr-001-04-01-acl-object-structure.md
adr-001-04-02-acl-evaluation-rules.md
adr-001-04-03-acl-inheritance.md
adr-001-04-04-acl-local-operations.md
adr-001-04-05-acl-remote-operations.md
adr-001-04-06-acl-sync-interactions.md
adr-001-04-07-acl-consistency.md
```

## **1.5. Schema, Typing, and Validation**

```
adr-001-05-01-schema-as-graph.md
adr-001-05-02-schema-validation.md
adr-001-05-03-schema-versioning.md
adr-001-05-04-schema-migration.md
adr-001-05-05-app-owned-schema.md
adr-001-05-06-cross-schema-linking.md
```

## **1.6. Sync Domains and State Semantics**

```
adr-001-06-01-sync-domain-definition.md
adr-001-06-02-domain-modes.md
adr-001-06-03-cross-domain-causality.md
adr-001-06-04-domain-visibility.md
adr-001-06-05-domain-filtering.md
adr-001-06-06-sync-state-format.md
adr-001-06-07-sync-state-advancement.md
```

## **1.7. Change Sequence, Ordering, and Causality**

```
adr-001-07-01-change-seq-format.md
adr-001-07-02-change-seq-monotonicity.md
adr-001-07-03-causality-vs-ordering.md
adr-001-07-04-conflict-detection.md
adr-001-07-05-conflict-resolution.md
```

## **1.8. Packages, Verification, and Sync Behavior**

```
adr-001-08-01-package-format.md
adr-001-08-02-package-signing.md
adr-001-08-03-package-verification.md
adr-001-08-04-apply-package-semantics.md
adr-001-08-05-build-package-semantics.md
adr-001-08-06-package-deduplication.md
adr-001-08-07-package-error-handling.md
adr-001-08-08-package-visibility-rules.md
adr-001-08-09-package-batching-guidelines.md
```

## **1.9. Distributed Interpretation and Semantic Convergence**

```
adr-001-09-01-interpretation-vs-representation.md
adr-001-09-02-semantic-equivalence.md
adr-001-09-03-conflicting-interpretations.md
adr-001-09-04-semantic-crossapp-linking.md
adr-001-09-05-meaning-preservation-in-sync.md
```

# **2. System Architecture**

## **2.1. Global System Architecture**

```
adr-002-01-01-system-overview.md
adr-002-01-02-node-architecture.md
adr-002-01-03-backend-frontend-boundary.md
adr-002-01-04-managers-vs-services-vs-apps.md
adr-002-01-05-system-app-vs-user-app-definition.md
adr-002-01-06-app-id-allocation-and-namespace.md
adr-002-01-07-system-invariants-and-safety-properties.md
adr-002-01-08-process-level-authority-model.md
adr-002-01-09-graph-indexing-in-memory-and-on-disk.md
```

## **2.2. Backend Layering and Responsibilities**

```
adr-002-02-01-backend-layering-rules.md
adr-002-02-02-manager-responsibility-boundaries.md
adr-002-02-03-service-responsibility-boundaries.md
adr-002-02-04-no-backend-apps-policy.md
adr-002-02-05-helpers-inside-managers-and-services-only.md
adr-002-02-06-operationcontext-mandatory-path.md
adr-002-02-07-backend-error-handling-principles.md
```

## **2.3. Frontend Architecture and App Model**

```
adr-002-03-01-frontend-app-structure.md
adr-002-03-02-frontend-routing-and-app-loading.md
adr-002-03-03-frontend-services-vs-backend-services.md
adr-002-03-04-frontend-app-initialization-sequence.md
adr-002-03-05-frontend-side-schema-awareness.md
adr-002-03-06-frontend-session-state-design.md
adr-002-03-07-isolated-app-sandboxes-with-shared-graph.md
```

## **2.4. System Services (Core Mandatory Services)**

```
adr-002-04-01-contacts-service-role.md
adr-002-04-02-messages-service-role.md
adr-002-04-03-groups-service-role.md
adr-002-04-04-schema-service-role.md
adr-002-04-05-service-interop-contracts.md
adr-002-04-06-service-lifecycle-and-upgrade.md
adr-002-04-07-service-interface-consistency.md
```

## **2.5. App Services Installed by Apps**

```
adr-002-05-01-app-service-model.md
adr-002-05-02-app-service-registration.md
adr-002-05-03-app-service-permissions.md
adr-002-05-04-app-service-interoperability.md
adr-002-05-05-app-service-performance-constraints.md
adr-002-05-06-app-service-upgrade-compatibility.md
```

## **2.6. Application Boundaries and Cross-App Interaction**

```
adr-002-06-01-app-boundary-definition.md
adr-002-06-02-cross-app-links-via-edges.md
adr-002-06-03-cross-app-schema-interpretation.md
adr-002-06-04-cross-app-permissions-and-visibility.md
adr-002-06-05-cross-app-rating-and-evaluation-rules.md
adr-002-06-06-app-removal-and-data-persistence.md
adr-002-06-07-shared-message-transport-between-apps.md
```

## **2.7. Performance, Scaling, and Resource Strategy**

```
adr-002-07-01-sqlite-performance-assumptions.md
adr-002-07-02-ram-indexing-strategy.md
adr-002-07-03-query-efficiency-in-distributed-graphs.md
adr-002-07-04-database-write-amplification-management.md
adr-002-07-05-app-id-scaling-limits.md
adr-002-07-06-multi-app-graph-load-behavior.md
adr-002-07-07-future-distributed-storage-options.md
```

## **2.8. Initialization, Bootstrapping, and Lifecycle**

```
adr-002-08-01-first-run-initialization.md
adr-002-08-02-system-app-bootstrap.md
adr-002-08-03-schema-bootstrap.md
adr-002-08-04-default-services-bootstrap.md
adr-002-08-05-app-registration-bootstrap.md
adr-002-08-06-peer-handshake-bootstrap.md
adr-002-08-07-upgrade-paths-and-migration-policy.md
```

## **2.9. Observability, Debugging, and System Introspection**

```
adr-002-09-01-system-health-model.md
adr-002-09-02-diagnostics-and-introspection.md
adr-002-09-03-event-stream-observability.md
adr-002-09-04-log-visibility-and-retention.md
adr-002-09-05-debugging-through-graph-state.md
```

# **3. Backend Manager & Service Decisions**

## **3.1. Storage Manager**

```
adr-003-01-01-storage-manager-purpose.md
adr-003-01-02-sqlite-schema-layout.md
adr-003-01-03-per-app-table-generation.md
adr-003-01-04-attribute-parent-edge-rating-storage-rules.md
adr-003-01-05-log-table-and-event-storage.md
adr-003-01-06-indexing-strategy-and-performance.md
adr-003-01-07-row-level-consistency-guarantees.md
adr-003-01-08-transaction-boundaries-and-durability.md
adr-003-01-09-storage-migration-rules.md
adr-003-01-10-storage-error-handling-model.md
```

## **3.2. Graph Manager**

```
adr-003-02-01-graph-manager-purpose.md
adr-003-02-02-envelope-processing-pipeline.md
adr-003-02-03-object-validation-rules.md
adr-003-02-04-cross-object-consistency-rules.md
adr-003-02-05-sync-flag-computation.md
adr-003-02-06-domain-detection-and-routing.md
adr-003-02-07-object-deduplication-and-upsert-rules.md
adr-003-02-08-graph-query-semantics.md
adr-003-02-09-graph-index-interaction.md
adr-003-02-10-graph-error-handling.md
```

## **3.3. ACL Manager**

```
adr-003-03-01-acl-manager-purpose.md
adr-003-03-02-acl-object-resolution.md
adr-003-03-03-owner-write-authorization.md
adr-003-03-04-local-operation-acl-rules.md
adr-003-03-05-remote-operation-acl-rules.md
adr-003-03-06-group-resolution.md
adr-003-03-07-acl-inheritance-and-fallbacks.md
adr-003-03-08-acl-cache-and-indexing-strategy.md
adr-003-03-09-acl-consistency-and-reconciliation.md
adr-003-03-10-acl-evaluation-failure-modes.md
```

## **3.4. Key Manager**

```
adr-003-04-01-key-manager-purpose.md
adr-003-04-02-keypair-generation-rules.md
adr-003-04-03-key-storage-layout.md
adr-003-04-04-signature-verification-interface.md
adr-003-04-05-key-rotation-procedures.md
adr-003-04-06-multi-device-identity-handling.md
adr-003-04-07-private-key-security-requirements.md
adr-003-04-08-deterministic-key-behavior-considerations.md
adr-003-04-09-key-loading-lifecycle.md
```

## **3.5. App Manager**

```
adr-003-05-01-app-manager-purpose.md
adr-003-05-02-app-registration-process.md
adr-003-05-03-app-id-assignment.md
adr-003-05-04-schema-registration.md
adr-003-05-05-app-service-registration.md
adr-003-05-06-app-upgrade-rules.md
adr-003-05-07-app-removal-safety-rules.md
adr-003-05-08-app-metadata-storage.md
adr-003-05-09-app-error-handling.md
```

## **3.6. Log Manager & Event Bus**

```
adr-003-06-01-log-manager-purpose.md
adr-003-06-02-log-record-format.md
adr-003-06-03-log-routing-rules.md
adr-003-06-04-event-bus-contract.md
adr-003-06-05-subscriber-model-and-delivery.md
adr-003-06-06-notification-emission-rules.md
adr-003-06-07-log-retention-policy.md
adr-003-06-08-log-query-capabilities.md
adr-003-06-09-log-integrity-and-auditability.md
```

## **3.7. Health Manager**

```
adr-003-07-01-health-manager-purpose.md
adr-003-07-02-health-check-categories.md
adr-003-07-03-self-test-design.md
adr-003-07-04-component-checks.md
adr-003-07-05-dependency-checks.md
adr-003-07-06-health-diagnostics-format.md
adr-003-07-07-health-dashboard-integration.md
adr-003-07-08-health-event-triggers.md
adr-003-07-09-health-result-persistence.md
```

## **3.8. Schema Service**

```
adr-003-08-01-schema-service-purpose.md
adr-003-08-02-schema-loading-rules.md
adr-003-08-03-schema-caching-strategy.md
adr-003-08-04-schema-validation-contract.md
adr-003-08-05-schema-version-resolution.md
adr-003-08-06-schema-cross-app-visibility.md
adr-003-08-07-schema-metadata-storage.md
```

## **3.9. Contacts Service**

```
adr-003-09-01-contacts-service-purpose.md
adr-003-09-02-contact-object-schema.md
adr-003-09-03-contact-graph-indices.md
adr-003-09-04-contact-linking-rules.md
adr-003-09-05-contact-rating-integration.md
adr-003-09-06-contact-permissions-model.md
adr-003-09-07-contact-sync-domain.md
```

## **3.10. Groups Service**

```
adr-003-10-01-groups-service-purpose.md
adr-003-10-02-group-object-schema.md
adr-003-10-03-membership-edge-rules.md
adr-003-10-04-group-acl-propagation.md
adr-003-10-05-group-role-model.md
adr-003-10-06-group-sync-domain.md
adr-003-10-07-group-visibility-rules.md
```

## **3.11. Messages Service**

```
adr-003-11-01-messages-service-purpose.md
adr-003-11-02-conversation-object-schema.md
adr-003-11-03-message-object-schema.md
adr-003-11-04-participant-resolution.md
adr-003-11-05-message-delivery-semantics.md
adr-003-11-06-message-sync-domain.md
adr-003-11-07-cross-app-message-embedding.md
adr-003-11-08-message-search-indexing.md
```

## **3.12. App Services Installed by Apps**

```
adr-003-12-01-app-service-definition.md
adr-003-12-02-app-service-registration-path.md
adr-003-12-03-app-service-permission-scope.md
adr-003-12-04-app-service-consistency-rules.md
adr-003-12-05-app-service-interoperability.md
adr-003-12-06-app-service-performance-requirements.md
adr-003-12-07-app-service-error-handling.md
```

# **4. Sync, Networking, and Tor**

## **4.1. State Engine and Sync Semantics**

```
adr-004-01-01-state-engine-purpose.md
adr-004-01-02-state-tracking-per-peer-per-domain.md
adr-004-01-03-build-package-rules.md
adr-004-01-04-apply-package-rules.md
adr-004-01-05-sync-state-advancement-model.md
adr-004-01-06-incremental-sync-vs-full-sync.md
adr-004-01-07-sync-window-and-batching.md
adr-004-01-08-deduplication-across-sync-cycles.md
adr-004-01-09-convergence-criteria.md
adr-004-01-10-sync-liveness-guarantees.md
```

## **4.2. Sync Domains and Isolation Rules**

```
adr-004-02-01-domain-definition-rules.md
adr-004-02-02-domain-boundary-enforcement.md
adr-004-02-03-domain-filtering-and-visibility.md
adr-004-02-04-cross-domain-causality-constraints.md
adr-004-02-05-domain-level-security-rules.md
adr-004-02-06-domain-growth-and-pruning.md
adr-004-02-07-app-defined-domains-vs-system-domains.md
```

## **4.3. Network Manager and Transport Layer**

```
adr-004-03-01-network-manager-purpose.md
adr-004-03-02-peer-handshake-protocol.md
adr-004-03-03-peer-capability-negotiation.md
adr-004-03-04-app-compatibility-negotiation.md
adr-004-03-05-sync-domain-negotiation.md
adr-004-03-06-peer-rate-limiting-and-dos-controls.md
adr-004-03-07-transport-abstraction-layer.md
adr-004-03-08-message-framing-rules.md
adr-004-03-09-peer-identity-and-fingerprinting.md
```

## **4.4. Tor Transport and Anonymity Layer**

```
adr-004-04-01-tor-as-default-transport.md
adr-004-04-02-hidden-service-hosting-model.md
adr-004-04-03-address-discovery-and-distribution.md
adr-004-04-04-metadata-minimization-principles.md
adr-004-04-05-anonymity-vs-authenticity-boundaries.md
adr-004-04-06-tor-performance-assumptions.md
adr-004-04-07-tor-failure-modes-and-recovery.md
```

## **4.5. Sync Error Handling and Recovery**

```
adr-004-05-01-package-verification-failures.md
adr-004-05-02-invalid-object-handling.md
adr-004-05-03-partial-sync-failures.md
adr-004-05-04-peer-blacklisting-rules.md
adr-004-05-05-sync-retry-strategy.md
adr-004-05-06-domain-reset-and-resync.md
adr-004-05-07-conflict-surface-detection.md
```

## **4.6. Sync Scheduling and Prioritization**

```
adr-004-06-01-sync-tick-schedule.md
adr-004-06-02-priority-queues.md
adr-004-06-03-peer-fairness-policy.md
adr-004-06-04-batching-thresholds.md
adr-004-06-05-idle-vs-active-sync-modes.md
adr-004-06-06-backpressure-handling.md
adr-004-06-07-sync-pausing-and-throttling.md
```

# **5. Frontend Decisions**

## **5.1. Frontend Architecture and App Framework**

```
adr-005-01-01-frontend-architecture-overview.md
adr-005-01-02-frontend-app-model.md
adr-005-01-03-app-sandboxing-and-isolation.md
adr-005-01-04-shared-graph-access-layer.md
adr-005-01-05-frontend-routing-structure.md
adr-005-01-06-frontend-initialization-pipeline.md
adr-005-01-07-frontend-performance-baseline.md
adr-005-01-08-frontend-error-boundaries.md
```

## **5.2. Identity, Authentication, and Session Model**

```
adr-005-02-01-frontend-identity-mapping.md
adr-005-02-02-authentication-flow.md
adr-005-02-03-session-storage-model.md
adr-005-02-04-session-expiration-and-refresh.md
adr-005-02-05-user-switching-model.md
adr-005-02-06-session-security-constraints.md
adr-005-02-07-frontend-identity-loss-behavior.md
```

## **5.3. Frontend–Backend Interaction**

```
adr-005-03-01-backend-api-consumption.md
adr-005-03-02-rest-request-formatting.md
adr-005-03-03-error-handling-and-status-codes.md
adr-005-03-04-envelope-submission-rules.md
adr-005-03-05-sync-triggering-from-frontend.md
adr-005-03-06-rate-limiting-and-throttling-client-side.md
adr-005-03-07-frontend-cache-and-state-sync.md
```

## **5.4. WebSocket Notifications and Realtime Behavior**

```
adr-005-04-01-notification-stream-design.md
adr-005-04-02-subscription-model.md
adr-005-04-03-event-types-and-routing.md
adr-005-04-04-realtime-state-updates.md
adr-005-04-05-offline-and-reconnect-behavior.md
adr-005-04-06-notification-security-model.md
adr-005-04-07-notification-error-handling.md
```

## **5.5. UI Architecture, Templates, and Components**

```
adr-005-05-01-template-hierarchy.md
adr-005-05-02-app-specific-template-rules.md
adr-005-05-03-shared-components-and-ui-patterns.md
adr-005-05-04-static-assets-organization.md
adr-005-05-05-css-and-js-loading-strategy.md
adr-005-05-06-accessibility-baseline.md
adr-005-05-07-internationalization-approach.md
```

## **5.6. Frontend Apps and Their Life Cycle**

```
adr-005-06-01-app-registration.md
adr-005-06-02-app-loading-and-initialization.md
adr-005-06-03-app-permission-model.md
adr-005-06-04-app-interop-and-shared-data.md
adr-005-06-05-app-upgrade-process.md
adr-005-06-06-app-removal-safety-rules.md
adr-005-06-07-app-error-recovery.md
```

## **5.7. Frontend Developer Apps and Local Logic**

```
adr-005-07-01-frontend-apps.md
adr-005-07-02-local-logic-and-data-transformations.md
adr-005-07-03-cross-app-ui-integration.md
adr-005-07-04-app-like-behavior-model.md
adr-005-07-05-frontend-performance-optimizations.md
adr-005-07-06-frontend-linting-and-static-validation.md
adr-005-07-07-frontend-security-guidelines.md
```

# **6. Operations and Deployment**

## **6.1. Configuration, Environment, and Settings**

```
adr-006-01-01-config-model-overview.md
adr-006-01-02-env-file-authority-and-loading.md
adr-006-01-03-settings-table-design.md
adr-006-01-04-sensitive-config-handling.md
adr-006-01-05-config-caching-and-invalidation.md
adr-006-01-06-instance-identification-rules.md
adr-006-01-07-multi-environment-behavior.md
```

## **6.2. Database Schema, Migrations, and Storage Management**

```
adr-006-02-01-database-schema-overview.md
adr-006-02-02-migration-policy-and-versioning.md
adr-006-02-03-storage-consistency-requirements.md
adr-006-02-04-backup-and-restore-strategy.md
adr-006-02-05-compaction-and-vacuum-policy.md
adr-006-02-06-corruption-detection-and-recovery.md
adr-006-02-07-database-growth-limits-and-guidelines.md
```

## **6.3. Key Handling, Identity Lifecycle, and Crypto Rotation**

```
adr-006-03-01-key-storage-layout.md
adr-006-03-02-private-key-protection.md
adr-006-03-03-key-load-lifecycle.md
adr-006-03-04-key-rotation-policy.md
adr-006-03-05-device-key-management.md
adr-006-03-06-identity-recovery-procedures.md
adr-006-03-07-crypto-upgrade-paths.md
```

## **6.4. Health, Diagnostics, and Monitoring**

```
adr-006-04-01-health-check-framework.md
adr-006-04-02-core-component-tests.md
adr-006-04-03-service-health-checks.md
adr-006-04-04-sync-health-evaluation.md
adr-006-04-05-network-health-evaluation.md
adr-006-04-06-diagnostics-dump-format.md
adr-006-04-07-health-dashboard-behavior.md
adr-006-04-08-health-alerts-and-notifications.md
```

## **6.5. Deployment Lifecycle, Bootstrapping, and Upgrades**

```
adr-006-05-01-first-run-initialization.md
adr-006-05-02-system-bootstrap-sequence.md
adr-006-05-03-app-bootstrap-and-registration.md
adr-006-05-04-service-bootstrap.md
adr-006-05-05-upgrade-safety-rules.md
adr-006-05-06-backward-compatibility-contracts.md
adr-006-05-07-rollbacks-and-recovery-procedures.md
```

## **6.6. Logging, Auditing, and Observability**

```
adr-006-06-01-log-structure-and-severity.md
adr-006-06-02-log-persistence-policy.md
adr-006-06-03-log-rotation-and-retention.md
adr-006-06-04-auditability-requirements.md
adr-006-06-05-event-bus-observability.md
adr-006-06-06-admin-diagnostics-tools.md
adr-006-06-07-anomaly-detection-baseline.md
```

## **6.7. Deployment Models, Networking, and Hosting Constraints**

```
adr-006-07-01-single-user-deployment-model.md
adr-006-07-02-multi-user-deployment-model.md
adr-006-07-03-headless-server-deployment.md
adr-006-07-04-tor-hosting-guidelines.md
adr-006-07-05-public-vs-private-node-behavior.md
adr-006-07-06-firewall-and-port-guidelines.md
adr-006-07-07-resource-limits-and-capacity-planning.md
```

# **7. Error Handling, Failure States, and Recovery Semantics**

## **7.1. Global Error Taxonomy**

```
adr-007-01-01-error-taxonomy.md
adr-007-01-02-error-severity-levels.md
adr-007-01-03-retryable-vs-nonretryable-errors.md
adr-007-01-04-fatal-vs-nonfatal-errors.md
adr-007-01-05-expected-vs-unexpected-errors.md
adr-007-01-06-user-error-vs-system-error-distinction.md
adr-007-01-07-intermittent-vs-persistent-failure-modes.md
adr-007-01-08-error-propagation-boundaries.md
```

## **7.2. Envelope and Object Validation Failures**

```
adr-007-02-01-envelope-validation-failure.md
adr-007-02-02-object-structure-validation-failure.md
adr-007-02-03-schema-violation-failure.md
adr-007-02-04-ownership-validation-failure.md
adr-007-02-05-edge-linking-validation-failure.md
adr-007-02-06-rating-target-validation-failure.md
adr-007-02-07-normalization-failure.md
adr-007-02-08-invalid-object-rejection.md
```

## **7.3. ACL and Authorization Failures**

```
adr-007-03-01-acl-authorization-failure.md
adr-007-03-02-owner-check-failure.md
adr-007-03-03-group-resolution-failure.md
adr-007-03-04-acl-inheritance-failure.md
adr-007-03-05-forbidden-operation-due-to-acl.md
adr-007-03-06-remote-write-authorization-failure.md
adr-007-03-07-acl-cache-inconsistency.md
```

## **7.4. Sync & State Engine Failure Modes**

```
adr-007-04-01-sync-state-corruption.md
adr-007-04-02-sync-state-divergence.md
adr-007-04-03-sync-loop-prevention.md
adr-007-04-04-unapplied-object-due-to-prerequisite-missing.md
adr-007-04-05-invalid-delta-detection.md
adr-007-04-06-sync-deadlock-detection.md
adr-007-04-07-sync-resume-after-interruption.md
adr-007-04-08-domain-reset-procedure.md
```

## **7.5. Package and Verification Failures**

```
adr-007-05-01-invalid-package-structure.md
adr-007-05-02-package-signature-failure.md
adr-007-05-03-package-integrity-failure.md
adr-007-05-04-replay-detection-failure.md
adr-007-05-05-out-of-bound-domain-objects.md
adr-007-05-06-package-object-conflict-detection.md
adr-007-05-07-package-deduplication-failure.md
adr-007-05-08-partial-package-application.md
```

## **7.6. Network and Transport Failures**

```
adr-007-06-01-network-disconnect.md
adr-007-06-02-peer-timeout.md
adr-007-06-03-peer-refusal.md
adr-007-06-04-malformed-network-message.md
adr-007-06-05-peer-identity-mismatch.md
adr-007-06-06-transport-level-corruption.md
adr-007-06-07-handshake-failure.md
adr-007-06-08-network-retry-policy.md
```

## **7.7. System-Level Recovery Strategies**

```
adr-007-07-01-local-recovery-from-object-errors.md
adr-007-07-02-local-recovery-from-acl-errors.md
adr-007-07-03-local-recovery-from-schema-errors.md
adr-007-07-04-peer-blacklisting-policy.md
adr-007-07-05-sync-retry-and-backoff.md
adr-007-07-06-circuit-breaker-strategy.md
adr-007-07-07-state-cleanup-and-compaction.md
adr-007-07-08-admin-triggered-recovery-tools.md
```

## **7.8. Failure Isolation and Containment Rules**

```
adr-007-08-01-local-vs-remote-failure-isolation.md
adr-007-08-02-object-level-failure-containment.md
adr-007-08-03-domain-level-failure-containment.md
adr-007-08-04-peer-level-failure-containment.md
adr-007-08-05-service-level-failure-containment.md
adr-007-08-06-manager-level-failure-containment.md
adr-007-08-07-failure-visibility-policy.md
```

# **8. Security Model & Cryptographic Guarantees**

## **8.1. Cryptographic Foundations**

```
adr-008-01-01-cryptographic-primitives.md
adr-008-01-02-hash-function-selection.md
adr-008-01-03-signature-algorithm-selection.md
adr-008-01-04-secure-randomness-requirements.md
adr-008-01-05-entropy-sourcing-guidelines.md
adr-008-01-06-public-key-format-and-representation.md
adr-008-01-07-cryptographic-strength-lifetime.md
```

## **8.2. Identity, Ownership, and Authenticity Guarantees**

```
adr-008-02-01-identity-binding-to-public-key.md
adr-008-02-02-object-ownership-cryptographic-proof.md
adr-008-02-03-owner-write-verification.md
adr-008-02-04-device-subkey-authentication.md
adr-008-02-05-key-compromise-impact-model.md
adr-008-02-06-key-loss-and-recovery-security.md
adr-008-02-07-identity-metadata-protection.md
```

## **8.3. Signing, Verification, and Anti-Forgery Measures**

```
adr-008-03-01-envelope-signing-rules.md
adr-008-03-02-package-signing-rules.md
adr-008-03-03-signature-verification-failure-semantics.md
adr-008-03-04-signature-replay-prevention.md
adr-008-03-05-nonce-and-sequence-protection.md
adr-008-03-06-forgery-detection-model.md
```

## **8.4. Confidentiality and Encryption Strategy**

```
adr-008-04-01-encrypted-attribute-policy.md
adr-008-04-02-end-to-end-message-encryption.md
adr-008-04-03-symmetric-key-derivation.md
adr-008-04-04-ephemeral-keys-and-forward-secrecy.md
adr-008-04-05-storage-encryption-guidelines.md
adr-008-04-06-visibility-rules-for-encrypted-data.md
adr-008-04-07-cross-device-key-sharing.md
```

## **8.5. Network Security and Transport Protection**

```
adr-008-05-01-peer-authentication-handshake.md
adr-008-05-02-peer-fingerprinting-protection.md
adr-008-05-03-metadata-minimization.md
adr-008-05-04-transport-layer-integrity-checks.md
adr-008-05-05-peer-impersonation-prevention.md
adr-008-05-06-network-downgrade-defense.md
adr-008-05-07-session-key-rotation.md
```

## **8.6. Anti-Abuse, Spam Limits, and Graph Safety**

```
adr-008-06-01-rate-limiting-principles.md
adr-008-06-02-spam-object-detection-model.md
adr-008-06-03-graph-poisoning-prevention.md
adr-008-06-04-rating-abuse-and-sybil-pattern-detection.md
adr-008-06-05-malicious-edge-structure-detection.md
adr-008-06-06-protection-from-resource-exhaustion.md
```

## **8.7. Integrity Guarantees and Auditability**

```
adr-008-07-01-object-integrity-guarantees.md
adr-008-07-02-cross-object-consistency-security.md
adr-008-07-03-audit-log-integrity.md
adr-008-07-04-tamper-detection.md
adr-008-07-05-security-invariants-and-failure-proofs.md
adr-008-07-06-protocol-invariant-checklist.md
```

# **9. Compatibility and Evolution Rules**

## **9.1. Protocol Versioning and Stability Guarantees**

```
adr-009-01-01-protocol-versioning-model.md
adr-009-01-02-stable-vs-experimental-features.md
adr-009-01-03-version-capabilities-negotiation.md
adr-009-01-04-breaking-change-policy.md
adr-009-01-05-protocol-enhancement-mechanisms.md
adr-009-01-06-version-mismatch-behavior.md
adr-009-01-07-protocol-deprecation-guidelines.md
```

## **9.2. Schema Evolution and App Compatibility**

```
adr-009-02-01-schema-versioning-rules.md
adr-009-02-02-schema-backward-compatibility.md
adr-009-02-03-schema-forward-compatibility.md
adr-009-02-04-schema-negotiation-between-peers.md
adr-009-02-05-schema-deprecation-policy.md
adr-009-02-06-cross-schema-linking-evolution.md
adr-009-02-07-app-schema-stability-contract.md
```

## **9.3. Sync Domain Evolution and State Migration**

```
adr-009-03-01-sync-domain-versioning.md
adr-009-03-02-domain-expansion-rules.md
adr-009-03-03-domain-contraction-and-retirement.md
adr-009-03-04-domain-remapping-between-versions.md
adr-009-03-05-domain-evolution-handshake.md
adr-009-03-06-state-forward-migration-process.md
adr-009-03-07-state-backward-compatibility-rules.md
```

## **9.4. Node Compatibility and Cross-Version Operation**

```
adr-009-04-01-supported-version-window.md
adr-009-04-02-peer-compatibility-checks.md
adr-009-04-03-feature-gating-based-on-version.md
adr-009-04-04-minimum-client-requirements.md
adr-009-04-05-behavior-under-partial-compatibility.md
adr-009-04-06-mixed-version-network-stability.md
adr-009-04-07-fallback-behavior-when-negotiation-fails.md
```

## **9.5. Security and Crypto Evolution**

```
adr-009-05-01-crypto-agility-policy.md
adr-009-05-02-hash-algorithm-migration.md
adr-009-05-03-signature-algorithm-migration.md
adr-009-05-04-key-size-evolution.md
adr-009-05-05-post-quantum-preparedness.md
adr-009-05-06-crypto-version-negotiation.md
adr-009-05-07-security-deprecation-policy.md
```

## **9.6. App and Service Lifecycle Compatibility**

```
adr-009-06-01-app-upgrade-compatibility.md
adr-009-06-02-service-upgrade-compatibility.md
adr-009-06-03-app-service-compatibility.md
adr-009-06-04-app-uninstallation-state-rules.md
adr-009-06-05-deprecated-api-surface.md
adr-009-06-06-ui-compatibility-contract.md
adr-009-06-07-app-metadata-versioning.md
```

## **9.7. Long-Term Evolution and Governance Constraints**

```
adr-009-07-01-protocol-governance-baseline.md
adr-009-07-02-evolution-principles.md
adr-009-07-03-change-adoption-process.md
adr-009-07-04-community-driven-app-service-model.md
adr-009-07-05-backward-compatible-protocol-expansion.md
adr-009-07-06-future-removal-of-legacy-behavior.md
adr-009-07-07-permanent-invariants.md
```
