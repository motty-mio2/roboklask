from threading import Lock

from python.domain.model.robot_xy import RobotXY


class Shared:
    lock = Lock()
    ball = RobotXY()
    striker = RobotXY()
