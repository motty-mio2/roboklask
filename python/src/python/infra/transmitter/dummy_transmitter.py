import random
import time

from python.domain.model.robot_xy import RobotXY
from python.domain.model.shared import Shared


class DummyTransmitter:
    """Dummy transmitter that simulates robot states completely offline without Zenoh."""

    def __init__(self, shared: Shared) -> None:
        self.shared = shared

    def publish(self, striker_position: RobotXY) -> None:
        """No-op for offline dummy simulation."""
        pass

    def close(self) -> None:
        """No-op for offline dummy simulation."""
        pass

    def spin(self) -> None:
        """Simulate ball coordinate updates at 30Hz."""
        last_update_time = time.time()
        try:
            while True:
                now = time.time()
                # 30Hz dummy update
                if now - last_update_time >= 1.0 / 30.0:
                    last_update_time = now
                    with self.shared.lock:
                        self.shared.ball = RobotXY(
                            x=random.uniform(-1.0, 1.0),
                            y=random.uniform(-1.0, 1.0)
                        )
                time.sleep(0.01)
        except KeyboardInterrupt:
            pass
