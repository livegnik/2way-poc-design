



# 16 Launcher

Defines the local developer launcher for starting the backend and frontend together. This launcher is a developer tool and does not define any production behavior.

For the meta specifications, see [16-launcher meta](../10-appendix/meta/02-architecture/16-launcher-meta.md).

## 1. Purpose and scope

The launcher provides:

* A local UI for starting backend and frontend processes together.
* Separate log panes for backend and frontend output.
* A simple restart/quit control surface.

It does not:

* Replace service managers or production process supervisors.
* Persist logs or emit structured audit/security records.
* Expose any network-facing API.

## 2. Environment handling

The launcher builds a process environment derived from the host environment and `.env`:

* Load `.env` from repo root if present.
* Resolve `BACKEND_HOST` and `BACKEND_PORT` (defaults: `127.0.0.1` and `8000`).
* Set `BACKEND_BASE_URL` to `http://{BACKEND_HOST}:{BACKEND_PORT}`.
* Preserve all existing environment variables unless explicitly overridden by `.env`.

Rules:

* `.env` parsing ignores blank lines and comments.
* Missing `.env` must not fail launch; defaults apply.
* Launcher must not mutate `.env` or write to disk.

## 3. Process orchestration

* Backend is started first using the project virtual environment interpreter.
* Frontend starts only after backend readiness is detected or a timeout elapses.
* On quit or restart, all child processes are terminated.

Readiness rules:

* Readiness is detected via a backend startup log marker defined by the backend server.
* If readiness is not detected within the timeout, frontend still starts and the launcher records a warning.

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
