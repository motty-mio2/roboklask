from typing import Self

from pydantic import BaseModel, Field


class RobotXY(BaseModel):
    x: float = Field(ge=-1.0, le=1.0, default=0.0, description="Normalized X coordinate (-1.0 ~ 1.0)")
    y: float = Field(ge=-1.0, le=1.0, default=0.0, description="Normalized Y coordinate (-1.0 ~ 1.0)")

    def as_opponent_side(self) -> Self:
        """Return a new RobotXY instance with the Y coordinate clamped to the opponent's side."""
        return self.__class__(x=self.x, y=abs(max(0.0, self.y)))

    def as_our_side(self) -> Self:
        """Return a new RobotXY instance with the Y coordinate clamped to our side."""
        return self.__class__(x=self.x, y=abs(min(0.0, self.y)))
