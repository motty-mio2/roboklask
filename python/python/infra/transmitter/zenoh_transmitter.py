import time

import zenoh

from python.domain.config import get_config_dir
from python.domain.model.robot_xy import RobotXY
from python.domain.model.shared import Shared


def create_zenoh_session() -> zenoh.Session:
    config_file = get_config_dir() / "zenoh.json5"
    if config_file.exists():
        return zenoh.open(zenoh.Config.from_file(config_file))
    else:
        return zenoh.open(zenoh.Config())


class ZenohTransmitter:
    """Transmits data using Zenoh protocol."""

    def __init__(self, shared: Shared) -> None:
        super().__init__()
        self.shared = shared
        self.publishers: dict[str, zenoh.Publisher] = {}

    def publish(
        self,
        striker_position: RobotXY,
    ) -> None:
        """Transmit data to the specified topic."""
        self.publishers["striker"].put(striker_position.model_dump_json())

    def ball_subscriber(self, sample: zenoh.Sample) -> None:
        with self.shared.lock:
            self.shared.ball = RobotXY.model_validate_json(sample.payload.to_string())

    def close(self) -> None:
        """Close the Zenoh session."""
        if hasattr(self, "zenoh_session"):
            self.zenoh_session.close()  # type: ignore

    def spin(self) -> None:
        self.zenoh_session = create_zenoh_session()

        self.publishers["striker"] = self.zenoh_session.declare_publisher("striker")

        self.zenoh_session.declare_subscriber(
            "ball",
            self.ball_subscriber,
        )

        last_send_time = time.time()

        try:
            while True:
                if time.time() - last_send_time >= 1.0 / 30.0:  # 30Hz
                    with self.shared.lock:
                        state = self.shared.ball
                    last_send_time = time.time()
                    # 送信
                    self.publish(state)

                time.sleep(0.01)
        except KeyboardInterrupt:
            pass
        finally:
            self.close()
