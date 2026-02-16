



# 16 Launcher

Defines the local developer launcher for starting the backend and frontend together. This launcher is a developer tool for local workflows.

For the meta specifications, see [16-launcher meta](../10-appendix/meta/02-architecture/16-launcher-meta.md).

## 1. Purpose and scope

The launcher provides:

* A local UI for starting backend and frontend processes together.
* Separate log panes for backend and frontend output.
* A simple restart/quit control surface.

## 2. Environment handling

The launcher builds a process environment derived from the host environment and `.env`:

* Load `.env` from repo root if present.
* Resolve `BACKEND_HOST` and `BACKEND_PORT` (defaults: `127.0.0.1` and `8000`).
* Set `BACKEND_BASE_URL` to `http://{BACKEND_HOST}:{BACKEND_PORT}`.
* Resolve `LAUNCHER_READY_MARKER` (default: `BACKEND_READY`).
* Resolve `LAUNCHER_BACKEND_READY_TIMEOUT_MS` (default: `15000`).
* Preserve all existing environment variables unless explicitly overridden by `.env`.

Rules:

* `.env` parsing ignores blank lines and comments.
* Missing `.env` must not fail launch; defaults apply.
* Launcher must not mutate `.env` or write to disk.
* `LAUNCHER_READY_MARKER` must be a non-empty ASCII token (1-64 chars).
* `LAUNCHER_BACKEND_READY_TIMEOUT_MS` must be an integer in `[1000, 120000]`.
* Invalid launcher readiness configuration must fail launch before child processes are started.

## 3. Process orchestration

* Backend is started first using the project virtual environment interpreter.
* Frontend starts only after backend readiness is detected or a timeout elapses.
* On quit or restart, all child processes are terminated.

Readiness rules:

* Readiness is detected when backend stdout/stderr emits a line containing the exact marker token from `LAUNCHER_READY_MARKER`.
* Marker matching is case-sensitive and uses literal substring matching.
* If readiness is not detected within `LAUNCHER_BACKEND_READY_TIMEOUT_MS`, frontend still starts and the launcher records a warning that includes the timeout value.

## 4. UI behavior

* The UI has separate panes for backend and frontend logs.
* A status bar reports lifecycle events (starting, ready, restart, shutdown).
* Key bindings include quit and restart.

## 5. Validation and failure behavior

* Failure to start a child process must be surfaced in the status bar.
* Launcher failures must not affect backend correctness; this tool is optional.

## 6. Forbidden behaviors

* Starting backend or frontend with non-local bind hosts by default.
* Emitting structured audit/security logs through the launcher.
* Altering configuration or settings during launch.
