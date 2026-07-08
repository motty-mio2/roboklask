from enum import Enum

from pydantic import BaseModel

from .value_objects import BoardXY, BoundingBox, RobotXY, SpatialXYZ


class DetectionLabel(Enum):
    BALL = 0
    STRIKER = 1


class Detection(BaseModel):
    label: DetectionLabel
    confidence: float
    box: BoundingBox
    spatial: SpatialXYZ | None = None
    board_xy: BoardXY | None = None
    robot_xy: RobotXY | None = None
