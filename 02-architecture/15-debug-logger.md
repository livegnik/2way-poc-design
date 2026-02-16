



# 15 Debug logger utility

Defines a lightweight debug logger used by backend modules that need opt-in diagnostic output without relying on [Log Manager](managers/12-log-manager.md). This utility is for developer diagnostics only and is not a structured logging system.

For the meta specifications, see [15-debug-logger meta](../10-appendix/meta/02-architecture/15-debug-logger-meta.md).

## 1. Purpose and scope

The debug logger provides:

* A minimal, opt-in logging helper for development and diagnostics.
* A config-backed enable/disable mechanism with per-component overrides.
* An environment fallback for modules that cannot access [Config Manager](managers/01-config-manager.md) during early startup or isolated utilities.

## 2. Configuration keys

Debug logger configuration lives under the `debug.*` namespace and is owned by the debug logger utility.

Keys:

| Key | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `debug.enabled` | bool | No | `false` | Global debug enable flag. |
| `debug.<component>` | bool | No | unset | Per-component override. When set, it overrides `debug.enabled` for that component. |

Rules:

* `debug.<component>` MUST override `debug.enabled` when present.
* If neither key is present, debug logging is disabled.
* `debug.*` keys are not boot-critical and live in the SQLite `settings` table.
* `debug.*` keys MAY be reloadable; owners determine reloadability at registration.

## 3. Environment fallback

When a component cannot access [Config Manager](managers/01-config-manager.md), the debug logger MAY fall back to environment variables.

Accepted environment variables (first match wins):

* `DEBUG_<COMPONENT>` (component name uppercased, non-alphanumeric replaced by `_`)
* `DEBUG`
* `TWOWAY_DEBUG`

Accepted truthy values (case-insensitive): `1`, `true`, `yes`, `on`. Any other value is treated as false.

Environment fallback MUST NOT be used when a config snapshot is available.

## 4. API surface

The debug logger utility provides:

* `DebugLogger(component: str, enabled: bool)` with method `log(message: str, *args: Any) -> None`.
* `resolve_debug(component: str, snapshot: Mapping[str, Any] | None) -> bool`.
* `env_debug_enabled(component: str) -> bool` for environment-only contexts.
* `env_logger(component: str) -> DebugLogger` convenience constructor.
* `log_calls(cls)` decorator that wraps instance methods to emit begin/error/done messages via a `_log` callable when present.

Rules:

* `DebugLogger.log` MUST be a no-op when `enabled` is false.
* `DebugLogger.log` MUST emit a single line using the standard Python logging facility at `INFO` level and prefix messages with `[<component>]`.
* `resolve_debug` MUST implement the precedence: `debug.<component>` (if present) else `debug.enabled` (if present) else `false`.
* `log_calls` MUST skip dunder methods and MUST NOT wrap `@staticmethod` or `@classmethod` entries.
* `log_calls` MUST re-raise exceptions after logging the error line.
* The decorator MUST NOT mutate method signatures or return values.

## 5. Validation and failure behavior

* Unknown `debug.*` keys are rejected by [Config Manager](managers/01-config-manager.md) unless registered by the owning component.
* Debug logging must never be required for correctness; failures to emit debug output MUST NOT change functional behavior.

## 6. Forbidden behaviors

* Emitting structured audit/security/operational logs through the debug logger.
* Using debug logger output as a source of truth for persistence or state transitions.
* Enabling debug logging by default in production configurations.
