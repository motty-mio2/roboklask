from typing import Protocol

from viewer.domain.value_objects import RobotXY


class McuConnection(Protocol):
    """Domain interface for bidirectional communication with the MCU (robot)."""

    def start(self) -> None:
        """Initialize and start the connection to the MCU."""
        ...

    def send_target(self, target: RobotXY | None) -> None:
        """Send target coordinates (RobotXY) to the MCU."""
        ...

    def read_feedback(self) -> RobotXY | None:
        """Read the latest striker position feedback (RobotXY) from the MCU."""
        ...

    def stop(self) -> None:
        """Stop the connection and release resources."""
        ...
