



# 05 Demo scenarios

These scenarios demonstrate that the PoC meets its core goals. They are intended for manual walkthroughs or scripted demos.

For the meta specifications, see [05-demo-scenarios-meta.md](../10-appendix/meta/07-poc/05-demo-scenarios-meta.md).

## 1. Bootstrap + first admin

* Run the bootstrap flow to create node, admin identity, and first device.
* Verify health readiness and initial graph objects.

## 2. Messaging flow

* Create a conversation with two participants.
* Send a message as a participant.
* Verify inbox listing and ACL enforcement for non-participants.

## 3. Social flow

* Create a post as a user.
* Reply to the post.
* Verify feed listing and author-only edits.

## 4. Marketplace flow

* Open the app marketplace UI.
* Install the market app (or another available app) via the app lifecycle route.
* Verify the app appears in the installed list and can be enabled or disabled.

## 5. Sync convergence

* Run a two-node handshake and exchange envelopes.
* Verify both nodes converge to identical graph state.

## 6. Error posture

* Submit a malformed envelope and verify fail-closed rejection.
* Attempt cross-app access and verify denial.
