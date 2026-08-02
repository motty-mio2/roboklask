import logging
import time
from typing import Any

from arduino.app_utils import App, Bridge

from python.domain.driver.base import BaseDriver
from python.domain.model.robot_xy import RobotXY
from python.domain.model.shared import Shared
from python.domain.runtime import Runtime

logger = logging.getLogger(__name__)


class BridgeDriver(BaseDriver):
    """BridgeDriver class to handle communication with the Arduino Bridge."""

    def __init__(self, shared: Shared, use_onnx: bool = True) -> None:
        """Initialize the BridgeDriver."""
        self.shared = shared
        self.bridge = Bridge()
        self.predict = Runtime(use_onnx=use_onnx)
        Bridge.provide("mcu2py", self.mcu2py)

    def py2mcu(self, command: str, data: RobotXY) -> Any:
        """Call a command on the Arduino Bridge."""
        logger.debug(f"TX target -> MCU: x={data.x:.4f}, y={data.y:.4f}")
        self.bridge.notify(command, data.x, data.y)

    def mcu2py(self, st_x: float, st_y: float) -> Any:
        logger.debug(f"RX feedback <- MCU: x={st_x:.4f}, y={st_y:.4f}")
        with self.shared.lock:
            self.shared.striker = RobotXY(x=st_x, y=st_y)

    def loop(self) -> None:
        time.sleep(0.03)  # 30Hz
        with self.shared.lock:
            st = self.shared.striker
            ba = self.shared.ball

        resp = self.predict.predict(ba, st)
        self.py2mcu("py2mcu", resp)
        logger.debug(f"TX ball -> MCU: x={ba.x:.4f}, y={ba.y:.4f}")
        self.bridge.notify("ball", ba.x, ba.y)

    def run(self) -> None:
        """Run the BridgeDriver."""
        print("Starting BridgeDriver...")
        App.run(user_loop=self.loop)
