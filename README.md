# 😀 roboklask

English | [日本語](./README_ja.md)

Autonomous Klask-playing robot with Arduino UNO R4 firmware and Python computer vision pipeline.

## Repository Structure

- **[`sketch/`](./sketch/)** — Arduino C++ firmware targeting Arduino UNO R4 (UNO Q / Minima) for dual stepper motor control and sensor integration.
- **[`python/`](./python/)** — Python companion app for vision tracking (OAK-D / RealSense), motion policy inference, and web UI.
- **[`hardware/`](./hardware/)** — 3D printable mechanical parts and mount designs.
  - **[Hardware & 3D Printing Guide](./hardware/HardWare.md)** ([日本語版](./hardware/HardWare_ja.md))

## Documentation

- **[Hardware & 3D Printing Guide](./hardware/HardWare.md)**: STL files, recommended BambuLab P1S print settings, and parts list.
- **[Python Package Documentation](./python/README.md)**: Setup and usage for the vision tracking and motion control application.
