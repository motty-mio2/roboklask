import collections
import os
from pathlib import Path

import numpy as np
import onnxruntime as ort

from python.domain.model.robot_xy import RobotXY


class Runtime:
    MAX_LEN = 3

    def __init__(self) -> None:
        self.model_path = (
            Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "roboklask" / "klask_ppo_model.onnx"
        )
        self.session = ort.InferenceSession(self.model_path)

        self.past_striker: collections.deque[RobotXY] = collections.deque(
            [RobotXY() for _ in range(self.MAX_LEN)],
            maxlen=self.MAX_LEN,
        )

        self.past_ball: collections.deque[RobotXY] = collections.deque(
            [RobotXY() for _ in range(self.MAX_LEN)],
            maxlen=self.MAX_LEN,
        )

    def predict(self, ball: RobotXY, striker: RobotXY) -> RobotXY:
        self.past_ball.append(ball)
        self.past_striker.append(striker)

        input_ = self.session.get_inputs()[0]
        output_ = self.session.get_outputs()[0]

        f_input = []
        f_input.extend([coord for b in self.past_ball for coord in (b.x, b.y)])
        f_input.extend([coord for s in self.past_striker for coord in (s.x, s.y)])

        result = self.session.run([output_.name], {input_.name: np.array([f_input], dtype=np.float32)})
        resp = RobotXY(x=result[0][0][0], y=result[0][0][1])

        return resp


if __name__ == "__main__":
    rx = Runtime()
    resp = rx.predict(RobotXY(), RobotXY())
    print(f"Predicted: x={resp.x}, y={resp.y}")
