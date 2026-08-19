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

    def py2mcu(self, command: str, target: RobotXY, ball: RobotXY) -> Any:
        """Call a command on the Arduino Bridge."""
        logger.debug(f"TX target & ball -> MCU: tx={target.x:.4f}, ty={target.y:.4f}, bx={ball.x:.4f}, by={ball.y:.4f}")
        self.bridge.notify(command, target.x, target.y, ball.x, ball.y)

    def mcu2py(self, st_x: float, st_y: float) -> Any:
        logger.debug(f"RX feedback <- MCU: x={st_x:.4f}, y={st_y:.4f}")
        # 物理的な遊びやキャリブレーションのズレによる範囲外の値をクリップ
        clamped_x = max(-1.0, min(1.0, st_x))
        clamped_y = max(-1.0, min(1.0, st_y))
        with self.shared.lock:
            self.shared.striker = RobotXY(x=clamped_x, y=clamped_y)

    def loop(self) -> None:
        time.sleep(0.1)  # 10Hz
        with self.shared.lock:
            st = self.shared.striker
            ba = self.shared.ball

        resp = self.predict.predict(ba, st)
        self.py2mcu("py2mcu", resp, ba)

    def run(self) -> None:
        """Run the BridgeDriver."""
        print("Starting BridgeDriver...")
        App.run(user_loop=self.loop)
