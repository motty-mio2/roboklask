# Instructions

**Reply in Japanese（日本語で回答すること）**

## Architecture

This is a monorepo for an Arduino robotics project (Klask-playing robot) with two components:

- **`sketch/`** — Arduino C++ firmware targeting `arduino:zephyr:unoq` (Arduino UNO R4) or `arduino:samd:minima` (Arduino UNO R4 Minima).
  - For **UNO R4 (UNO Q / Zephyr RTOS)**: Uses the Zephyr RTOS kernel, LED matrix display, and `RouterBridge`. It receives target coordinates via `Bridge.provide("xy", ...)` and reports encoder feedback coordinates to the Python app via `Bridge.call("report_xy", ...)` at 20ms intervals.
  - For **Minima**: Uses raw UART serial connection at 115200 baud (`serial_bridge.hpp`) to read `0xAA` header target packets and write `0xAA` feedback position packets.
- **`python/`** — Python 3.13+ companion app using `arduino-app-bricks` framework and ONNX Runtime for inference. Communicates with the sketch via either Arduino App Bridge RPCs or raw UART serial. Managed with `uv`.

### Python Package Structure

The python app contains two main systems:
1. **Web UI & Stepper Bridge Control (`main.py`)**: Exposes API endpoints for manual control over the robot via `arduino-app-bricks`.
2. **Vision Tracking & Motion Inference (`src/viewer/`, started via `run_vision.py`)**:
   - Captures frames from OAK-D (`depthai`) or RealSense (`pyrealsense2`).
   - Automatically calibrates the board using HSV-based blue color detection (under-the-hood optimization for dark lighting conditions).
   - Maps coordinate spaces from pixel frame, to board (mm), to normalized robot coordinate space (`RobotXY`).
   - Replaces noisy camera striker coordinates with high-confidence MCU encoder coordinates when feedback is available.
   - Runs a linear pipeline: **VisionSource** -> **MotionPolicy** -> **McuConnection**.

### McuConnection Implementations
- **`SerialMcuConnection`**: Sends target commands and reads feedback positions over raw binary serial packets (`0xAA` header). Used for `output_type = OutputType.UART`.
- **`BridgeMcuConnection`**: Sends target commands via `Bridge.notify("xy", ...)` (asynchronous notification to avoid blocking the vision loop) and registers `Bridge.provide("report_xy", ...)` to consume microcontroller encoder position feedback. Used for `output_type = OutputType.BRIDGE`.
- **`NullMcuConnection`**: No-op interface for headless/offline simulations. Used for `output_type = OutputType.NONE`.

### MotionPolicy Implementations
- **`BallTrackingPolicy`**: Standard tracking policy that directly targets the ball, clamped to our side of the board. Used for `policy_type = PolicyType.BALL_TRACKING`.
- **`ModelBasedPolicy`**: Reinforcement learning agent strategy that evaluates the PPO policy model (`klask_ppo_model.onnx`) via ONNX Runtime using raw coordinate inputs and clamps the resulting target outputs to our side. Used for `policy_type = PolicyType.PPO`.

### Configuration Settings
All parameters are defined in `python/src/viewer/config.py` and can be customized via `.env` variables prefixed with `KLASK_`:
- **`KLASK_OUTPUT_TYPE`**: The communication channel (`none`, `uart`, `bridge`). Note: `ppo` is supported as a legacy value and automatically maps to `uart` with `ppo` policy.
- **`KLASK_POLICY_TYPE`**: The motion strategy (`ball_tracking`, `ppo`).
- **`KLASK_CAMERA`**: The camera hardware (`oakd`, `realsense`).
- **`KLASK_CONFIDENCE_THRESHOLD`**: The object detection confidence threshold (defaults to `0.5`).

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
uv run pyrefly check           # Type check only (ignores src/ folder to avoid binary binding stub errors)
uv run poe check               # Runs strict pyright type checking on src/viewer/
uv run python run_vision.py    # Starts the vision viewer tracking pipeline
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
- Linter: **ruff** with rules `E, F, W, I, B, RUF, UP, TID252` targeting Python 3.13.
- Type checkers:
  - **pyrefly** with `strict` preset for root python scripts. Note: `src/` is excluded via `.ignore` to avoid false-positives with binary wheels.
  - **pyright** with `strict` mode config for all core package code in `src/`.
- The `arduino-app-bricks` dependency is sourced from a Git tag (not PyPI).
- After changing dependencies, run `mise run export` in `python/` to regenerate `requirements.txt`.

## Sketch Conventions

- Formatter: **clang-format** (managed via mise).
- The sketch uses Zephyr kernel primitives (`K_MUTEX_DEFINE`) for thread safety between `loop()` and Bridge provider callbacks.
- Board target: `arduino:zephyr:unoq` (configured in `sketch.yaml`).
- Libraries used: `AccelStepper`, `Arduino_LED_Matrix`, `Arduino_RouterBridge`, Zephyr kernel headers.

## CI

GitHub Actions runs on pushes/PRs to `main` with path-scoped triggers:

- **Python** (`python/`): pyrefly check → ruff check → ruff format --check → pyright check → verify `requirements.txt` is in sync on `ubuntu-arm64`.
- **Sketch** (`sketch/`): clang-format lint → arduino-cli compile.
