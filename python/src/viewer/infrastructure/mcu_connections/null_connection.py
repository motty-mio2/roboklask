from viewer.domain.mcu_connection import McuConnection
from viewer.domain.value_objects import RobotXY


class NullMcuConnection(McuConnection):
    """No-op connection implementation for offline/headless simulation."""

    def start(self) -> None:
        pass

    def send_target(self, target: RobotXY | None) -> None:
        pass

    def read_feedback(self) -> RobotXY | None:
        return None

    def stop(self) -> None:
        pass
