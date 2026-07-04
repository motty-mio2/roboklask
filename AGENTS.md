# Instructions

**Reply in Japanese（日本語で回答すること）**

## Architecture

This is a monorepo for an Arduino robotics project (Klask-playing robot) with two components:

- **`sketch/`** — Arduino C++ firmware targeting `arduino:zephyr:unoq` (Arduino UNO R4). Uses the Zephyr RTOS kernel, LED matrix display, and a `RouterBridge` for receiving commands from the Python side. Pin mappings are in `pinout.h`.
- **`python/`** — Python 3.13+ companion app using `arduino-app-bricks` framework and ONNX Runtime for inference. Communicates with the sketch via `Bridge.call()`. Managed with `uv`.

The two components communicate over the Arduino App Bridge: Python calls `Bridge.call("xy", x, y)` and the sketch provides the `"xy"` handler via `Bridge.provide()`. The app is configured via `app.yaml` (uses the `arduino:web_ui` brick).

## Task Runner (mise)

The project uses [mise](https://mise.jdx.dev/) as a polyglot task runner. The root `mise.toml` defines a monorepo with config roots in `sketch/` and `python/`.

### Common commands (run from repo root)

```sh
mise run format        # Format all (Python + C++ + TOML)
mise run lint          # Lint all (ruff + pyrefly + TOML)
mise run build         # Build sketch (delegates to sketch:build)
```

### Python commands (run from `python/`)

```sh
mise run lint          # ruff check + pyrefly check
mise run format        # ruff format + ruff check --fix
mise run export        # Regenerate requirements.txt from uv.lock
```

Individual Python tools can be run directly:

```sh
cd python
uv run ruff check              # Lint only
uv run ruff format --check     # Check formatting without modifying
uv run pyrefly check           # Type check only
```

### Sketch commands (run from `sketch/`)

```sh
mise run format        # clang-format on .ino and .h files
mise run lint          # clang-format --dry-run --Werror (check only)
mise run build         # arduino-cli compile --fqbn arduino:zephyr:unoq .
```

## Python Conventions

- Package manager: **uv** (not pip). Use `uv add` to add dependencies, `uv run` to execute tools.
- Task runner within Python: **poethepoet** (via `uv run poe <task>`).
- Linter: **ruff** with rules `E, F, W, I, B` targeting Python 3.13.
- Type checker: **pyrefly** with `strict` preset.
- The `arduino-app-bricks` dependency is sourced from a Git tag (not PyPI).
- After changing dependencies, run `mise run export` in `python/` to regenerate `requirements.txt`.

## Sketch Conventions

- Formatter: **clang-format** (managed via mise).
- The sketch uses Zephyr kernel primitives (`K_MUTEX_DEFINE`) for thread safety between `loop()` and Bridge provider callbacks.
- Board target: `arduino:zephyr:unoq` (configured in `sketch.yaml`).
- Libraries used: `AccelStepper`, `Arduino_LED_Matrix`, `Arduino_RouterBridge`, Zephyr kernel headers.

## CI

GitHub Actions runs on pushes/PRs to `main` with path-scoped triggers:

- **Python** (`python/`): pyrefly check → ruff check → ruff format --check → verify `requirements.txt` is in sync.
- **Sketch** (`sketch/`): clang-format lint → arduino-cli compile.
