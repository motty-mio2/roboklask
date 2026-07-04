from typing import Any, Protocol

import cv2

from viewer.calibration import BoardCalibrator
from viewer.config import CameraType
from viewer.domain import Detection, DetectionLabel


class DebuggerUI(Protocol):
    """Protocol for modular UI debug presentations."""

    def update(self, frame: Any, detections: list[Detection]) -> None:
        """Render and display the UI window with the latest frame and detections."""
        ...

    def close(self) -> None:
        """Close any open windows or release resources managed by this UI."""
        ...


class RawVisionDebugger:
    """UI presentation module for displaying the raw camera frame with 2D bounding boxes."""

    def __init__(self, camera_type: CameraType) -> None:
        self.window_name = f"Klask Vision ({camera_type.value.upper()})"
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

    def update(self, frame: Any, detections: list[Detection]) -> None:
        height, width = frame.shape[:2]
        for detection in detections:
            x1, y1, x2, y2 = detection.box.to_pixel_box(width, height)

            label_name = detection.label.name
            conf = detection.confidence

            if label_name == "BALL":
                color = (0, 255, 0)
            elif label_name == "STRIKER":
                color = (0, 0, 255)
            else:
                color = (255, 0, 0)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame,
                f"{label_name} ({conf:.2f})",
                (x1, y1 - 10 if y1 - 10 > 10 else y1 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
                cv2.LINE_AA,
            )
            if detection.spatial is not None:
                cv2.putText(
                    frame,
                    str(detection.spatial),
                    (x1, y2 + 15 if y2 + 15 < height else y2 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    color,
                    1,
                    cv2.LINE_AA,
                )
        cv2.imshow(self.window_name, frame)

    def close(self) -> None:
        try:
            cv2.destroyWindow(self.window_name)
        except Exception:
            pass


class RobotOrientDebugger:
    """UI presentation module for displaying the warped top-down board and robot coordinates."""

    def __init__(self, calibrator: BoardCalibrator) -> None:
        self.calibrator = calibrator
        self.window_name = "Klask Board View (Top-Down)"
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

    def update(self, frame: Any, detections: list[Detection]) -> None:
        if self.calibrator.M is None:
            return

        warped_frame = self.calibrator.warp_frame(frame)
        if warped_frame is None:
            return

        for d in detections:
            if d.board_xy is not None and d.robot_xy is not None:
                bx = int(d.board_xy.board_x)
                by = int(d.board_xy.board_y)

                if d.label == DetectionLabel.BALL:
                    color = (0, 255, 0)
                elif d.label == DetectionLabel.STRIKER:
                    color = (0, 0, 255)
                else:
                    color = (255, 0, 0)

                # Draw clean indicator dots and coordinates on the warped view
                cv2.circle(warped_frame, (bx, by), 8, color, -1)
                cv2.circle(warped_frame, (bx, by), 10, (255, 255, 255), 1)
                cv2.putText(
                    warped_frame,
                    f"{bx},{by}mm",
                    (bx + 12, by - 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.35,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                )
                # Render robot normalized coordinates
                rx = d.robot_xy.x
                ry = d.robot_xy.y
                cv2.putText(
                    warped_frame,
                    f"({rx:+.2f}, {ry:+.2f})",
                    (bx + 12, by + 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.35,
                    (200, 255, 200),
                    1,
                    cv2.LINE_AA,
                )
        cv2.imshow(self.window_name, warped_frame)

    def close(self) -> None:
        try:
            cv2.destroyWindow(self.window_name)
        except Exception:
            pass
