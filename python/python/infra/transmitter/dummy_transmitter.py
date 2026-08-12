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
        import math

        start_time = time.time()
        last_update_time = start_time
        try:
            while True:
                now = time.time()
                # 30Hz dummy update
                if now - last_update_time >= 1.0 / 30.0:
                    last_update_time = now
                    # 経過時間(秒)に適度な速度係数(1.5)を掛けて角度にする
                    t = (now - start_time) * 1.5
                    # 8の字の軌跡を描く(X: -1.0〜1.0, Y: 0.0〜1.0)
                    x = math.sin(t)
                    y = (math.sin(2 * t) + 1.0) / 2.0
                    with self.shared.lock:
                        self.shared.ball = RobotXY(x=x, y=y)
                time.sleep(0.01)
        except KeyboardInterrupt:
            pass
