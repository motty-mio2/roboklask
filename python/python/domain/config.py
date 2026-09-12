import os
from pathlib import Path

from pydantic_settings import BaseSettings


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    return Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "roboklask"


def get_data_dir() -> Path:
    """Get the data directory path."""
    return Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "roboklask"


def is_in_docker() -> bool:
    """Check if running inside a Docker container by checking /.dockerenv."""
    return Path("/.dockerenv").exists()


def get_default_model_path() -> Path:
    """Get the default model path depending on the execution environment.

    - Inside Docker: assets/model.onnx relative to working directory.
    - Native environment: ../assets/model.onnx relative to main.py.
    """
    if is_in_docker():
        return Path("assets/model.onnx")

    # In native environment, main.py is in python/ (parents[2] of this file)
    main_py_dir = Path(__file__).resolve().parents[2]
    return (main_py_dir / ".." / "assets" / "model.onnx").resolve()


class Config(BaseSettings):
    """Configuration settings for the application."""

    model_path: Path = get_default_model_path()


class SerialConfig(Config):
    """Configuration settings specific to the SerialDriver."""

    serial_port: str = "/dev/ttyUSB0"
    baudrate: int = 115200


class ZenohConfig(Config):
    zenoh_peers: str = "tcp/"
