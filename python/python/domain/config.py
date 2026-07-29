import os
from pathlib import Path

from pydantic_settings import BaseSettings


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    return Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "roboklask"


def get_data_dir() -> Path:
    """Get the data directory path."""
    return Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "roboklask"


class Config(BaseSettings):
    """Configuration settings for the application."""

    model_path: Path = get_data_dir() / "model" / "model.onnx"


class SerialConfig(Config):
    """Configuration settings specific to the SerialDriver."""

    serial_port: str = "/dev/ttyUSB0"
    baudrate: int = 115200


class ZenohConfig(Config):
    zenoh_peers: str = "tcp/"
