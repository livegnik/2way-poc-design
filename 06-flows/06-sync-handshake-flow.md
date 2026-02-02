



# 06 Sync handshake flow

This flow defines the handshake between two peers before sync exchange begins.

For the meta specifications, see [06-sync-handshake-flow-meta.md](../09-appendix/meta/06-flows/06-sync-handshake-flow-meta.md).

## 1. Inputs

* Incoming peer connection admitted by Network Manager.
* Authenticated peer identity and advertised app/domain capabilities.

## 2. Flow

1) Network Manager accepts a connection subject to DoS Guard admission.
2) Peer presents handshake payload with:
   * node identity
   * supported apps and sync domains
   * protocol version
3) Key Manager verifies the peer signature and identity.
4) State Manager compares protocol version and sync domains.
5) State Manager responds with accepted domains and sequence ranges.
6) If accepted, sync ingress/egress flows are enabled for the peer.

## 3. Allowed behavior

* Negotiation of domain subsets based on local policy.
* Rejection of unknown or unsupported protocol versions.

## 4. Forbidden behavior

* Accepting sync data before handshake completes.
* Accepting domains that are not locally registered.

## 5. Failure behavior

* Any validation failure rejects the handshake.
* Rejections do not alter local sync state.
