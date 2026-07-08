from enum import StrEnum, auto
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_root_path() -> Path:
    """Get the root path of the project."""
    return Path(__file__).parents[3]


class CameraType(StrEnum):
    OAKD = "oakd"
    REALSENSE = "realsense"


class OutputType(StrEnum):
    NONE = auto()
    UART = auto()
    PPO = auto()  # Legacy output type, auto-mapped to UART + PolicyType.PPO
    BRIDGE = auto()


class PolicyType(StrEnum):
    BALL_TRACKING = auto()
    PPO = auto()


class KlaskBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KLASK_",
        env_file=get_root_path() / ".env",
        extra="ignore",
    )


class BoardSettings(KlaskBaseSettings):
    board_width_mm: int = Field(ge=0, lt=1000, default=445, description="Actual physical width of the board in mm")
    board_height_mm: int = Field(ge=0, lt=1000, default=345, description="Actual physical height of the board in mm")


class CalibrationSettings(KlaskBaseSettings):
    config_path: Path = Field(
        default=get_root_path() / "calibration.json", description="Path to save the 4-corner coordinates"
    )

    # HSV boundaries for blue color detection (tolerates dark shadows and highlights)
    lower_blue: list[int] = Field(default=[90, 30, 10], description="Lower HSV bounds for blue mask [H, S, V]")
    upper_blue: list[int] = Field(default=[130, 255, 255], description="Upper HSV bounds for blue mask [H, S, V]")


class UartSettings(KlaskBaseSettings):
    port: Path = Field(default=Path("/dev/ttyUSB0"), description="Serial port for UART output")
    baudrate: int = Field(ge=0, lt=1_000_000, default=115200, description="Baud rate for UART output")


class VisionSettings(KlaskBaseSettings):
    camera: CameraType = Field(
        default=CameraType.OAKD,
        description="Camera device type ('oakd' or 'realsense')",
    )
    blob_path: Path = Field(
        default=get_root_path() / "best.blob",
        description="Path to Myriad X blob model for OAK-D/DepthAI",
    )
    onnx_path: Path = Field(
        default=get_root_path() / "best.onnx",
        description="Path to ONNX model for RealSense host-side inference",
    )
    ppo_model_path: Path = Field(
        default=get_root_path() / "klask_ppo_model.onnx",
        description="Path to PPO ONNX model for target position inference",
    )
    confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for object detection",
    )
    iou_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="NMS IoU threshold for object detection",
    )

    calibration: CalibrationSettings = Field(
        default_factory=CalibrationSettings,
        description="Board calibration and color segmentation settings",
    )

    output_type: OutputType = Field(
        default=OutputType.NONE, description="Type of output sender ('none', 'uart', or 'bridge')"
    )
    policy_type: PolicyType = Field(
        default=PolicyType.BALL_TRACKING, description="Motion planning policy ('ball_tracking' or 'ppo')"
    )

    uart: UartSettings = Field(default_factory=UartSettings, description="UART serial output settings")

    @model_validator(mode="after")
    def adjust_legacy_settings(self) -> "VisionSettings":
        # If legacy output_type is PPO, map it to UART connection + PPO policy
        if self.output_type == OutputType.PPO:
            self.output_type = OutputType.UART
            self.policy_type = PolicyType.PPO
        return self


settings = VisionSettings()
