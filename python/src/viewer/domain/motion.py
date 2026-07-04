from typing import Protocol

from viewer.domain.models import Detection, DetectionLabel
from viewer.domain.value_objects import RobotXY


class MotionPolicy(Protocol):
    """Domain interface for deciding the next target coordinates (RobotXY) for the striker."""

    def plan_motion(self, detections: list[Detection]) -> RobotXY | None:
        """Plan the next striker movement target from the list of detections."""
        ...


class InferenceEngine(Protocol):
    """Domain port interface for executing machine learning policy inference."""

    def infer(self, ball: RobotXY, striker: RobotXY) -> RobotXY | None:
        """Infer target coordinates given current ball and striker coordinates."""
        ...


class BallTrackingPolicy(MotionPolicy):
    """Standard tracking policy that targets the ball directly, clamped to our side."""

    def plan_motion(self, detections: list[Detection]) -> RobotXY | None:
        for d in detections:
            if d.label == DetectionLabel.BALL and d.robot_xy is not None:
                # Restrict tracking to our half of the board
                return d.robot_xy.as_our_side()
        return None


class ModelBasedPolicy(MotionPolicy):
    """Strategy that uses an InferenceEngine to compute striker targets with fallback coordinates."""

    def __init__(self, engine: InferenceEngine) -> None:
        self.engine = engine

        # Keep track of last known coordinates for fallback if detections are missed
        self.last_ball_x = 0.5
        self.last_ball_y = 0.0
        self.last_striker_x = 0.5
        self.last_striker_y = -0.5

    def plan_motion(self, detections: list[Detection]) -> RobotXY | None:
        # Extract ball and striker positions
        ball_x = None
        ball_y = None
        striker_x = None
        striker_y = None

        for d in detections:
            if d.label == DetectionLabel.BALL and d.robot_xy is not None:
                ball_x = d.robot_xy.x
                ball_y = d.robot_xy.y
            elif d.label == DetectionLabel.STRIKER and d.robot_xy is not None:
                striker_x = d.robot_xy.x
                striker_y = d.robot_xy.y

        # Fallback to last known coordinates if not detected
        if ball_x is not None and ball_y is not None:
            self.last_ball_x = ball_x
            self.last_ball_y = ball_y
        else:
            ball_x = self.last_ball_x
            ball_y = self.last_ball_y

        if striker_x is not None and striker_y is not None:
            self.last_striker_x = striker_x
            self.last_striker_y = striker_y
        else:
            striker_x = self.last_striker_x
            striker_y = self.last_striker_y

        ball = RobotXY(x=ball_x, y=ball_y)
        striker = RobotXY(x=striker_x, y=striker_y)

        # Delegate ONNX/model execution to the inference engine port
        return self.engine.infer(ball, striker)
