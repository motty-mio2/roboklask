import json
import os
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from python.domain import config


class BoardCalibrator:
    def __init__(
        self,
    ) -> None:
        self.config_path: Path = config.CalibrationSettings().config_path
        self.board_width: int = config.BoardSettings().board_width_mm
        self.board_height: int = config.BoardSettings().board_height_mm
        self.src_pts: np.ndarray | None = None
        self.M: np.ndarray | None = None
        self.M_inv: np.ndarray | None = None
        self.load()

    def load(self) -> None:
        # NOTE: Used by the future `calibrate` subcommand.
        # When interactive calibration is implemented as a separate CLI command,
        # the main loop will call load() on startup to restore the saved result
        # instead of running auto calibration every time.
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path) as f:
                    data = json.load(f)
                    self.src_pts = np.array(data["src_pts"], dtype=np.float32)
                    self.update_matrices()
                    print(f"Loaded calibration from {self.config_path}")
            except Exception as e:
                print(f"Failed to load calibration: {e}")

    def save(self) -> None:
        # NOTE: Used by the future `calibrate` subcommand.
        # Called after interactive calibration to persist the manually selected
        # corner points so they can be reloaded on subsequent runs.
        if self.src_pts is not None:
            try:
                data = {"src_pts": self.src_pts.tolist()}
                with open(self.config_path, "w") as f:
                    json.dump(data, f, indent=4)
                print(f"Saved calibration to {self.config_path}")
            except Exception as e:
                print(f"Failed to save calibration: {e}")

    def update_matrices(self) -> None:
        if self.src_pts is None:
            return
        dst_pts = np.array(
            [
                [0, 0],
                [self.board_width, 0],
                [self.board_width, self.board_height],
                [0, self.board_height],
            ],
            dtype=np.float32,
        )
        self.M = cv2.getPerspectiveTransform(self.src_pts, dst_pts)
        self.M_inv = cv2.getPerspectiveTransform(dst_pts, self.src_pts)

    def calibrate_interactive(self, frame: Any) -> bool:
        # NOTE: Intentionally not called from the main loop.
        # Reserved for the future `calibrate` subcommand (e.g. `python -m viewer calibrate`),
        # which will open a GUI window, let the user click the 4 board corners,
        # and persist the result via save() for subsequent headless runs.
        print("\n=== Interactive Calibration ===")
        print("Click the 4 corners of the blue playing field in order:")
        print("1. Top-Left, 2. Top-Right, 3. Bottom-Right, 4. Bottom-Left")
        print("Press 'r' to reset clicks, 'q' to cancel.")

        clicks: list[list[int]] = []
        window_name = "Interactive Calibration"
        display_frame = frame.copy()

        def mouse_callback(event: int, x: int, y: int, flags: int, param: Any) -> None:
            if event == cv2.EVENT_LBUTTONDOWN:
                if len(clicks) < 4:
                    clicks.append([x, y])
                    # Draw visual marker
                    cv2.circle(display_frame, (x, y), 5, (0, 255, 255), -1)
                    cv2.putText(
                        display_frame,
                        str(len(clicks)),
                        (x + 8, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 255),
                        2,
                    )
                    if len(clicks) > 1:
                        cv2.line(display_frame, (clicks[-2][0], clicks[-2][1]), (x, y), (0, 255, 255), 2)
                    if len(clicks) == 4:
                        cv2.line(display_frame, (x, y), (clicks[0][0], clicks[0][1]), (0, 255, 255), 2)
                    cv2.imshow(window_name, display_frame)

        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(window_name, mouse_callback)
        cv2.imshow(window_name, display_frame)

        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("r"):
                clicks.clear()
                display_frame = frame.copy()
                cv2.imshow(window_name, display_frame)
            elif len(clicks) == 4:
                cv2.waitKey(500)  # brief pause to let user see final square
                self.src_pts = np.array(clicks, dtype=np.float32)
                self.update_matrices()
                self.save()
                break

        cv2.destroyWindow(window_name)
        return self.src_pts is not None

    def calibrate_automatic(self, frame: Any) -> bool:
        print("\n=== Automatic Calibration (Blue Detection) ===")
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Segment blue color of the Klask field using bounds from settings
        lower_blue = np.array(config.settings.calibration.lower_blue)
        upper_blue = np.array(config.settings.calibration.upper_blue)
        mask = cv2.inRange(hsv, lower_blue, upper_blue)  # type: ignore

        # Morphological operations to merge components and filter noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # type: ignore
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)  # type: ignore

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            print("Auto calibration failed: No blue region detected.")
            return False

        # Extract largest contour
        largest_contour = max(contours, key=cv2.contourArea)

        # Compute the convex hull to fill in dents caused by corner white arcs and shadows
        hull = cv2.convexHull(largest_contour)

        # Try to approximate to a 4-sided polygon by sweeping the epsilon coefficient
        peri = cv2.arcLength(hull, True)
        approx = None
        for eps_coeff in [0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.05, 0.06, 0.07, 0.08]:
            cand = cv2.approxPolyDP(hull, eps_coeff * peri, True)
            if len(cand) == 4:
                approx = cand
                break

        if approx is not None:
            pts = approx.reshape(4, 2)
            # Reorder corners: Top-Left, Top-Right, Bottom-Right, Bottom-Left
            ordered_pts = self._order_points(pts)
            self.src_pts = np.array(ordered_pts, dtype=np.float32)
            self.update_matrices()
            print("Auto calibration succeeded: Detected board corners.")
            return True
        else:
            print("Warning: Could not approximate to exactly 4 corners. Falling back to extreme points.")
            pts_hull = hull.reshape(-1, 2)
            ordered_pts = self._order_points(pts_hull)
            self.src_pts = np.array(ordered_pts, dtype=np.float32)
            self.update_matrices()
            print("Auto calibration succeeded (using extreme points fallback).")
            return True

    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        # Sort pts based on their x-coordinates
        # Sum of coords gives TL and BR: TL has smallest sum, BR has largest sum
        # Diff of coords gives TR and BL: TR has smallest diff (x - y), BL has largest diff
        rect = np.zeros((4, 2), dtype=np.float32)
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]  # Top-Left
        rect[2] = pts[np.argmax(s)]  # Bottom-Right

        diff = np.diff(pts, axis=1).flatten()
        rect[1] = pts[np.argmin(diff)]  # Top-Right
        rect[3] = pts[np.argmax(diff)]  # Bottom-Left
        return rect

    def warp_frame(self, frame: Any) -> Any:
        if self.M is not None:
            return cv2.warpPerspective(frame, self.M, (self.board_width, self.board_height))
        return None

    def transform_point(self, u: float, v: float) -> tuple[float | None, float | None]:
        if self.M is not None:
            pt = np.array([[[u, v]]], dtype=np.float32)
            trans = cv2.perspectiveTransform(pt, self.M)  # type: ignore
            return float(trans[0][0][0]), float(trans[0][0][1])
        return None, None

    def to_scale_coordinates(self, x_mm: float | None, y_mm: float | None) -> tuple[float | None, float | None]:
        if x_mm is None or y_mm is None:
            return None, None
        # X: Left is 1.0, Right is 0.0. Center is 0.5.
        x_norm = 1.0 - (x_mm / self.board_width)
        # Y: Bottom is 0.0, Top is 1.0.
        y_norm = 1.0 - (y_mm / self.board_height)
        return float(x_norm), float(y_norm)
