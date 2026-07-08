from typing import Any

import numpy as np

from python.domain import RobotXY
from python.domain.motion import InferenceEngine


class OnnxInferenceEngine(InferenceEngine):
    """Infrastructure adapter that runs policy inference using ONNX Runtime."""

    def __init__(self, model_path: str) -> None:
        self.model_path = model_path
        self.session: Any = None

    def _ensure_session(self) -> None:
        if self.session is not None:
            return

        try:
            import onnxruntime as ort

            self.session = ort.InferenceSession(self.model_path)
            print(f"ONNX Inference Session loaded successfully from {self.model_path}")
        except Exception as e:
            print(f"Error loading ONNX model: {e}")
            self.session = None

    def infer(self, ball: RobotXY, striker: RobotXY) -> RobotXY | None:
        self._ensure_session()
        if self.session is None:
            return None

        # Prepare 4-dimensional observation vector: [ball_x, ball_y, striker_x, striker_y]
        obs = np.array([[ball.x, ball.y, striker.x, striker.y]], dtype=np.float32)

        try:
            # Run inference: Input name is 'observation', Output name is 'action'
            import time

            start_time = time.perf_counter()
            outputs = self.session.run(["action"], {"observation": obs})
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            action = outputs[0][0]  # shape [2] -> [target_x, target_y]

            target_x = float(action[0])
            target_y = float(action[1])

            # Ensure output is a valid coordinate pair clamped to our side
            target_robot_xy = RobotXY(x=max(0.0, min(1.0, target_x)), y=max(-1.0, min(1.0, target_y))).as_our_side()

            print(
                f"[PPO] Inference time: {elapsed_ms:.2f} ms | "
                f"Obs=[B:({ball.x:.2f},{ball.y:.2f}), S:({striker.x:.2f},{striker.y:.2f})] -> "
                f"Target=({target_robot_xy.x:.2f},{target_robot_xy.y:.2f})"
            )
            return target_robot_xy

        except Exception as e:
            print(f"Error during ONNX inference: {e}")
            return None
