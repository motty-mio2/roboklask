import sys
from typing import Any

import numpy as np
import pyrealsense2 as rs

from viewer.config import settings
from viewer.domain import Detection, SpatialXYZ, VisionSource

from .detector import OnnxRuntimeYoloDetector


class RealsenseVisionSource(VisionSource):
    def __init__(
        self,
        model_path: str | None = None,
        confidence_threshold: float | None = None,
        iou_threshold: float | None = None,
    ) -> None:
        self.model_path = str(model_path or settings.onnx_path)
        self.confidence_threshold = (
            confidence_threshold if confidence_threshold is not None else settings.confidence_threshold
        )
        self.iou_threshold = iou_threshold if iou_threshold is not None else settings.iou_threshold
        self.detector: OnnxRuntimeYoloDetector | None = None
        self.pipeline: Any | None = None
        self.config: Any | None = None
        self.align: Any | None = None
        self.color_intrinsics: Any | None = None

    def start(self) -> None:
        print("Initializing RealSense camera...")
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        # Enable both color and depth streams
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

        try:
            profile = self.pipeline.start(self.config)
            print("RealSense camera stream started.")

            # Retrieve color stream intrinsics for 3D coordinates calculation
            color_stream = profile.get_stream(rs.stream.color).as_video_stream_profile()
            self.color_intrinsics = color_stream.get_intrinsics()

            # Create align object to align depth frame to color frame
            self.align = rs.align(rs.stream.color)
        except Exception as e:
            print(f"Error starting RealSense stream: {e}", file=sys.stderr)
            print(
                "Please ensure the RealSense camera is connected properly.",
                file=sys.stderr,
            )
            raise e

        # Initialize the PC-side detector
        self.detector = OnnxRuntimeYoloDetector(
            model_path=self.model_path,
            confidence_threshold=self.confidence_threshold,
            iou_threshold=self.iou_threshold,
        )

    def read(self) -> tuple[np.ndarray, list[Detection]] | None:
        if self.pipeline is None or self.detector is None or self.align is None:
            raise RuntimeError("Vision source is not started. Call start() first.")

        try:
            # Wait for frames with a timeout to avoid blocking indefinitely
            frames = self.pipeline.wait_for_frames(timeout_ms=1000)

            # Align depth frame to color frame
            aligned_frames = self.align.process(frames)
            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()

            if not color_frame or not depth_frame:
                return None

            frame = np.asanyarray(color_frame.get_data())
            h, w = frame.shape[:2]

            # Perform inference on PC side using OpenCV DNN
            detections = self.detector.detect(frame)

            # Calculate spatial coordinates for each detection on the host PC
            for d in detections:
                u, v = d.box.to_pixel_center(w, h)

                # Query depth value (distance in meters)
                depth = depth_frame.get_distance(u, v)

                # Simple 3x3 pixel fallback if center pixel depth is invalid (0)
                if depth == 0:
                    found = False
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            nu, nv = u + dx, v + dy
                            if 0 <= nu < w and 0 <= nv < h:
                                d_val = depth_frame.get_distance(nu, nv)
                                if d_val > 0:
                                    depth = d_val
                                    found = True
                                    break
                        if found:
                            break

                # Deproject pixel to 3D point using camera intrinsics
                if depth > 0 and self.color_intrinsics is not None:
                    point = rs.rs2_deproject_pixel_to_point(self.color_intrinsics, [u, v], depth)
                    d.spatial = SpatialXYZ(x=point[0], y=point[1], z=point[2])

            return frame, detections
        except Exception as e:
            print(f"Error reading from RealSense: {e}")
            return None

    def stop(self) -> None:
        if self.pipeline is not None:
            print("Stopping RealSense camera stream...")
            try:
                self.pipeline.stop()
            except Exception as e:
                print(f"Error during pipeline stop: {e}")
            self.pipeline = None
            self.config = None
            self.align = None
            self.color_intrinsics = None
        self.detector = None
