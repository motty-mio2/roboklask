from collections.abc import Generator

import numpy as np

from viewer.calibration import BoardCalibrator
from viewer.domain import BoundingBox, Detection, DetectionLabel, McuConnection, VisionSource
from viewer.domain.motion import MotionPolicy
from viewer.domain.value_objects import BoardXY


class TrackBallUseCase:
    def __init__(
        self,
        vision_source: VisionSource,
        calibrator: BoardCalibrator,
        mcu_connection: McuConnection,
        motion_policy: MotionPolicy,
    ) -> None:
        self.vision_source = vision_source
        self.calibrator = calibrator
        self.mcu_connection = mcu_connection
        self.motion_policy = motion_policy

    def execute(self) -> Generator[tuple[np.ndarray, list[Detection]] | None]:
        """Orchestrate the tracking loop: read frame, run detections, map coords, and send MCU target commands.

        Yields (frame, detections) or None for the UI presentation layer.
        """
        self.vision_source.start()
        self.mcu_connection.start()
        try:
            while True:
                result = self.vision_source.read()
                if result is None:
                    # No frame available yet, yield None to allow UI loop to process events
                    yield None
                    continue

                frame, detections = result

                # 1. Read encoder/stepper feedback from the MCU
                mcu_striker_xy = self.mcu_connection.read_feedback()

                # Prioritize MCU striker coordinates over camera-based detection
                if mcu_striker_xy is not None:
                    # Discard any weak camera-based striker detections
                    detections = [d for d in detections if d.label != DetectionLabel.STRIKER]

                    # Inject the highly accurate MCU-reported striker position
                    striker_det = Detection(
                        label=DetectionLabel.STRIKER,
                        confidence=1.0,
                        box=BoundingBox(xmin=0.0, ymin=0.0, xmax=0.0, ymax=0.0),
                        robot_xy=mcu_striker_xy,
                    )
                    detections.append(striker_det)

                # 2. Process raw detections (like the ball) and perform coordinate transformations
                for d in detections:
                    # Only calculate coordinate mappings if they haven't been set (e.g. for camera-based detections)
                    if d.robot_xy is None:
                        h, w = frame.shape[:2]
                        u, v = d.box.to_pixel_center(w, h)

                        # Transform pixel coordinates to physical board coordinates (in mm)
                        x_board, y_board = self.calibrator.transform_point(u, v)
                        if x_board is not None and y_board is not None:
                            bx = float(max(0.0, min(float(self.calibrator.board_width - 1), x_board)))
                            by = float(max(0.0, min(float(self.calibrator.board_height - 1), y_board)))

                            # Create rich Value Objects
                            d.board_xy = BoardXY(board_x=bx, board_y=by)
                            d.robot_xy = d.board_xy.to_robot_xy(
                                float(self.calibrator.board_width), float(self.calibrator.board_height)
                            )

                # 3. Plan motion target coordinates using the policy (ball tracking or PPO model inference)
                target = self.motion_policy.plan_motion(detections)

                # 4. Transmit computed command target to the MCU connection
                self.mcu_connection.send_target(target)

                yield frame, detections
        finally:
            self.mcu_connection.stop()
            self.vision_source.stop()
