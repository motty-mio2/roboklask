import time
from typing import Any

import numpy as np
import onnxruntime as ort

from python.domain.config import Config
from python.domain.model.robot_xy import RobotXY


class OnnxInferenceEngine:
    """Infrastructure adapter that runs policy inference using ONNX Runtime."""

    def __init__(self) -> None:
        self.session: Any = None
        self.model_path = Config().model_path

    def _ensure_session(self) -> None:
        if self.session is not None:
            return

        self.session = ort.InferenceSession(self.model_path)
        print(f"ONNX Inference Session loaded successfully from {self.model_path}")

    def infer(self, ball: RobotXY, striker: RobotXY) -> RobotXY | None:
        self._ensure_session()
        if self.session is None:
            return None

        # Prepare 4-dimensional observation vector: [ball_x, ball_y, striker_x, striker_y]
        obs = np.array([[ball.x, ball.y, striker.x, striker.y]], dtype=np.float32)

        # Run inference: Input name is 'observation', Output name is 'action'

        start_time = time.perf_counter()
        outputs = self.session.run(["action"], {"observation": obs})
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        action = outputs[0][0]  # shape [2] -> [target_x, target_y]

        target_x = float(action[0])
        target_y = float(action[1])

        # Ensure output is a valid coordinate pair clamped to our side
        target_robot_xy = RobotXY(x=max(-1.0, min(1.0, target_x)), y=max(-1.0, min(1.0, target_y))).as_our_side()

        print(
            f"[PPO] Inference time: {elapsed_ms:.2f} ms | "
            f"Obs=[B:({ball.x:.2f},{ball.y:.2f}), S:({striker.x:.2f},{striker.y:.2f})] -> "
            f"Target=({target_robot_xy.x:.2f},{target_robot_xy.y:.2f})"
        )
        return target_robot_xy
