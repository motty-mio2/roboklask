# Instructions

** Reply in Japanese（日本語で回答すること）**

## Architecture

This is a monorepo for an Arduino robotics project (Klask-playing robot) with two components:

- **`sketch/`** — Arduino C++ firmware targeting `arduino:zephyr:unoq` (Arduino UNO R4). Uses the Zephyr RTOS kernel, LED matrix display, and a `RouterBridge` for receiving commands from the Python side. Pin mappings are in `pinout.h`.
- **`python/`** — Python 3.13+ companion app using `arduino-app-bricks` framework and ONNX Runtime for inference. Communicates with the sketch via `Bridge.call()`. Managed with `uv`.

The two components communicate over the Arduino App Bridge: Python calls `Bridge.call("xy", x, y)` and the sketch provides the `"xy"` handler via `Bridge.provide()`.

## Task Runner (mise)

The project uses [mise](https://mise.jdx.dev/) as a polyglot task runner. The root `mise.toml` defines a monorepo with config roots in `sketch/` and `python/`.

### Common commands (run from repo root)

```sh
mise run format        # Format all (Python + C++ + TOML)
mise run lint          # Lint all (ruff + pyrefly + TOML)
```

### Python commands (run from `python/`)

```sh
mise run lint          # ruff check + pyrefly check
mise run format        # ruff format + ruff check --fix
mise run export        # Regenerate requirements.txt from uv.lock
```

### Sketch commands (run from `sketch/`)

```sh
mise run format        # clang-format on .ino and .h files
```

## Python Conventions

- Package manager: **uv** (not pip). Use `uv add` to add dependencies, `uv run` to execute tools.
- Linter: **ruff** with rules `E, F, W, I, B` targeting Python 3.13.
- Type checker: **pyrefly** with `strict` preset.
- The `arduino-app-bricks` dependency is sourced from a Git tag (not PyPI).
- After changing dependencies, run `mise run export` in `python/` to regenerate `requirements.txt`.

## Sketch Conventions

- Formatter: **clang-format** (managed via mise).
- The sketch uses Zephyr kernel primitives (`K_MUTEX_DEFINE`) for thread safety between `loop()` and Bridge provider callbacks.
- Board target: `arduino:zephyr:unoq` (configured in `sketch.yaml`).
