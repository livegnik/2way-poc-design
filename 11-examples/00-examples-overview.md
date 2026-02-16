



# 00 Examples Overview

Non-normative examples for implementers and test authors. In conflicts, `/specs/**` are authoritative.

## 1. Purpose

This folder provides machine-readable example payloads that correspond to normative contracts in the specs. Examples are intended for:

* Fixture seeds in contract tests
* Schema/shape validation checks
* Implementation onboarding

## 2. Current examples

* `app-package-notes-v1/manifest.json`
* `app-package-notes-v1/schema.json`
* `app-package-notes-v1/acl.json`
* `app-package-notes-v1/app-service/main.py`
* `app-package-notes-v1/package_sig.json`

These files model a canonical app install package for the app lifecycle register flow defined in [04-interfaces/06-app-lifecycle.md](../04-interfaces/06-app-lifecycle.md).

## 3. Constraints

* Example artifacts are slug-first and do not include node-local `app_id`.
* Signature examples use `publisher_public_key` plus detached ZIP signature; signature bytes are placeholders.
* Example objects are illustrative and may be simplified for readability.
