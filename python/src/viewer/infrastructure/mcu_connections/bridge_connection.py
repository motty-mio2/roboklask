import threading

from viewer.domain import RobotXY
from viewer.domain.mcu_connection import McuConnection


class BridgeMcuConnection(McuConnection):
    """McuConnection implementation using the Arduino App Bridge (RPC/notify)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._latest_feedback: RobotXY | None = None

    def start(self) -> None:
        try:
            from arduino.app_utils import Bridge

            Bridge.provide("report_xy", self._on_feedback)
            print("Arduino Bridge Mcu Connection started and report_xy handler registered.")
        except Exception as e:
            print(f"Error registering report_xy handler via Arduino Bridge: {e}")

    def _on_feedback(self, x: float, y: float) -> None:
        clamped_x = max(0.0, min(1.0, x))
        clamped_y = max(-1.0, min(1.0, y))
        feedback = RobotXY(x=clamped_x, y=clamped_y)
        with self._lock:
            self._latest_feedback = feedback

    def send_target(self, target: RobotXY | None) -> None:
        if target is None:
            return

        try:
            from arduino.app_utils import Bridge

            # Use notify for asynchronous, fire-and-forget sending to avoid blocking the main vision loop
            Bridge.notify("xy", target.x, target.y)
        except Exception as e:
            print(f"Error sending target coordinates via Arduino Bridge: {e}")

    def read_feedback(self) -> RobotXY | None:
        with self._lock:
            feedback = self._latest_feedback
            self._latest_feedback = None
        return feedback

    def stop(self) -> None:
        try:
            from arduino.app_utils import Bridge

            Bridge.unprovide("report_xy")
            print("Arduino Bridge Mcu Connection stopped and report_xy handler unregistered.")
        except Exception as e:
            print(f"Error unregistering report_xy handler via Arduino Bridge: {e}")
