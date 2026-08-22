from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from python.domain.model.robot_xy import RobotXY


class BaseDriver(ABC):
    def logger(self, msg: str) -> None:
        """Write a message to the console."""
        with open(Path.home() / "bridge_driver.log", "a") as log_file:
            log_file.write(msg + "\n")

    @abstractmethod
    def py2mcu(self, command: str, target: RobotXY, ball: RobotXY) -> Any:
        """Call a command on the Arduino Bridge."""
        self.logger(f"Calling command: {command} with target: {target} and ball: {ball}")

        raise NotImplementedError("Subclasses must implement the py2mcu method.")

    @abstractmethod
    def mcu2py(self, st_x: float, st_y: float) -> Any:
        raise NotImplementedError("Subclasses must implement the mcu2py method.")

    @abstractmethod
    def run(self) -> None:
        """Run the driver."""
        raise NotImplementedError("Subclasses must implement the run method.")
