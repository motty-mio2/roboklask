import time
from typing import Any

from arduino.app_utils import App, Bridge

from python.domain.driver.base import BaseDriver
from python.domain.model.robot_xy import RobotXY
from python.domain.model.shared import Shared
from python.domain.runtime import Runtime


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
        self.bridge.notify(command, data.x, data.y)

    def mcu2py(self, st_x: float, st_y: float) -> Any:
        with self.shared.lock:
            self.shared.striker = RobotXY(x=st_x, y=st_y)

    def loop(self) -> None:
        time.sleep(0.03)  # 30Hz
        with self.shared.lock:
            st = self.shared.striker
            ba = self.shared.ball

        resp = self.predict.predict(ba, st)
        self.py2mcu("py2mcu", resp)
        self.bridge.notify("ball", ba.x, ba.y)

    def run(self) -> None:
        """Run the BridgeDriver."""
        print("Starting BridgeDriver...")
        App.run(user_loop=self.loop)
