from typing import Self

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    xmin: float = Field(description="Normalized left bounding coordinate")
    ymin: float = Field(description="Normalized top bounding coordinate")
    xmax: float = Field(description="Normalized right bounding coordinate")
    ymax: float = Field(description="Normalized bottom bounding coordinate")

    def to_pixel_box(self, width: int, height: int) -> tuple[int, int, int, int]:
        """Convert normalized bounding box to pixel integer coordinates (x1, y1, x2, y2)."""
        return int(self.xmin * width), int(self.ymin * height), int(self.xmax * width), int(self.ymax * height)

    def to_pixel_center(self, width: int, height: int) -> tuple[int, int]:
        """Calculate center pixel coordinate (u, v) clamped within frame bounds."""
        u = int((self.xmin + self.xmax) / 2 * width)
        v = int((self.ymin + self.ymax) / 2 * height)
        return max(0, min(width - 1, u)), max(0, min(height - 1, v))


class SpatialXYZ(BaseModel):
    x: float = Field(description="Spatial X coordinate in meters")
    y: float = Field(description="Spatial Y coordinate in meters")
    z: float = Field(description="Spatial Z coordinate in meters")

    def __str__(self) -> str:
        return f"X:{self.x:.2f}m Y:{self.y:.2f}m Z:{self.z:.2f}m"


class RobotXY(BaseModel):
    x: float = Field(ge=-1.0, le=1.0, description="Normalized X coordinate (-1.0 ~ 1.0)")
    y: float = Field(ge=-1.0, le=1.0, description="Normalized Y coordinate (-1.0 ~ 1.0)")

    def as_opponent_side(self) -> Self:
        """Return a new RobotXY instance with the Y coordinate clamped to the opponent's side."""
        return self.__class__(x=self.x, y=abs(max(0.0, self.y)))

    def as_our_side(self) -> Self:
        """Return a new RobotXY instance with the Y coordinate clamped to our side."""
        return self.__class__(x=self.x, y=abs(min(0.0, self.y)))


class BoardXY(BaseModel):
    board_x: float = Field(description="X coordinate on the board in mm")
    board_y: float = Field(description="Y coordinate on the board in mm")

    def to_robot_xy(self, board_width: float, board_height: float) -> RobotXY:
        """Convert board coordinates (in mm) to normalized robot coordinates.

        Handles the physical 90-degree swap:
        - Robot's X corresponds to Camera's Y.
        - Robot's Y corresponds to Camera's X.
        """
        # Camera Y [0, board_height] maps to Robot X [-1.0, 1.0] (center at 0.0)
        robot_x = 1.0 - (2.0 * self.board_y / board_height)

        # Camera X [0, board_width] maps to Robot Y [-1.0, 1.0] (center at 0.0)
        robot_y = 1.0 - (2.0 * self.board_x / board_width)

        # Apply safety bounding box clamps
        robot_x = max(-1.0, min(1.0, robot_x))
        robot_y = max(-1.0, min(1.0, robot_y))

        return RobotXY(x=robot_x, y=robot_y)
