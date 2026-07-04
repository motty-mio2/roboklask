from viewer.domain import RobotXY
from viewer.domain.mcu_connection import McuConnection


class BridgeMcuConnection(McuConnection):
    """McuConnection implementation using the Arduino App Bridge (RPC/notify)."""

    def start(self) -> None:
        # No explicit start action required, the App Bridge starts automatically in the background
        print("Arduino Bridge Mcu Connection started.")

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
        # Currently, the App Bridge firmware does not publish/provide encoder positions back to Python.
        # Return None to fallback to camera-based detection or last known position.
        return None

    def stop(self) -> None:
        print("Arduino Bridge Mcu Connection stopped.")
