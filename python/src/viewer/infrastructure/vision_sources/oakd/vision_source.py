import os
from typing import Any

import depthai as dai

from viewer.config import settings
from viewer.domain import BoundingBox, Detection, DetectionLabel, SpatialXYZ, VisionSource


class OakdVisionSource(VisionSource):
    def __init__(
        self,
        blob_path: str | None = None,
        confidence_threshold: float | None = None,
        iou_threshold: float | None = None,
    ) -> None:
        self.blob_path = str(blob_path or settings.blob_path)
        self.confidence_threshold = (
            confidence_threshold if confidence_threshold is not None else settings.confidence_threshold
        )
        self.iou_threshold = iou_threshold if iou_threshold is not None else settings.iou_threshold
        self.label_map = [DetectionLabel.BALL, DetectionLabel.STRIKER]
        self.device: Any | None = None
        self.q_rgb: Any | None = None
        self.q_det: Any | None = None
        self.last_frame_time: float | None = None

    def start(self) -> None:
        if not os.path.exists(self.blob_path):
            raise FileNotFoundError(
                f"Blob model not found at {self.blob_path}. "
                "Please ensure the model is compiled and placed in the working directory."
            )

        pipeline = dai.Pipeline()

        # Nodes definition
        cam_rgb = pipeline.create(dai.node.ColorCamera)
        mono_left = pipeline.create(dai.node.MonoCamera)
        mono_right = pipeline.create(dai.node.MonoCamera)
        stereo = pipeline.create(dai.node.StereoDepth)
        detection_network = pipeline.create(dai.node.YoloSpatialDetectionNetwork)  # type: ignore
        xout_rgb = pipeline.create(dai.node.XLinkOut)  # type: ignore
        nn_out = pipeline.create(dai.node.XLinkOut)  # type: ignore

        xout_rgb.setStreamName("rgb")
        nn_out.setStreamName("nn")

        # Camera properties
        cam_rgb.setPreviewSize(640, 640)
        cam_rgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        cam_rgb.setInterleaved(False)
        cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
        cam_rgb.setFps(30)

        # Mono cameras configuration
        mono_left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        mono_left.setBoardSocket(dai.CameraBoardSocket.LEFT)
        mono_right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        mono_right.setBoardSocket(dai.CameraBoardSocket.RIGHT)

        # Stereo depth properties
        stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)  # type: ignore
        stereo.setDepthAlign(dai.CameraBoardSocket.RGB)

        # YOLO spatial detection network properties
        detection_network.setConfidenceThreshold(self.confidence_threshold)
        detection_network.setNumClasses(len(self.label_map))
        detection_network.setCoordinateSize(4)
        detection_network.setIouThreshold(self.iou_threshold)
        detection_network.setBlobPath(self.blob_path)
        detection_network.setNumInferenceThreads(2)
        detection_network.input.setBlocking(False)

        # YOLO anchorless configuration
        detection_network.setAnchorMasks({})
        detection_network.setAnchors([])

        # Spatial YOLO settings
        detection_network.setBoundingBoxScaleFactor(0.5)
        detection_network.setDepthLowerThreshold(100)
        detection_network.setDepthUpperThreshold(5000)

        # Connect nodes
        mono_left.out.link(stereo.left)
        mono_right.out.link(stereo.right)
        stereo.depth.link(detection_network.inputDepth)

        cam_rgb.preview.link(detection_network.input)
        detection_network.passthrough.link(xout_rgb.input)
        detection_network.out.link(nn_out.input)

        print("Initializing OAK-D camera...")
        try:
            self.device = dai.Device(pipeline)  # type: ignore
            self.q_rgb = self.device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
            self.q_det = self.device.getOutputQueue(name="nn", maxSize=4, blocking=False)
            print("OAK-D camera stream started.")
        except Exception as e:
            print(f"Error starting OAK-D stream: {e}")
            self.stop()
            raise

    def read(self) -> tuple[Any, list[Detection]] | None:
        if self.device is None or self.q_rgb is None or self.q_det is None:
            return None

        in_rgb = self.q_rgb.tryGet()
        in_det = self.q_det.tryGet()

        if in_rgb is None or in_det is None:
            return None

        import time

        now = time.perf_counter()
        if self.last_frame_time is not None:
            diff_ms = (now - self.last_frame_time) * 1000.0
            fps = 1000.0 / diff_ms if diff_ms > 0 else 0.0
            print(f"[OAK-D] Frame interval: {diff_ms:.2f} ms ({fps:.1f} FPS)")
        self.last_frame_time = now

        frame = in_rgb.getCvFrame()
        detections: list[Detection] = []

        if in_det is not None:
            for d in in_det.detections:
                label_idx = int(d.label)

                try:
                    label_name = DetectionLabel(label_idx)
                except ValueError:
                    continue

                detections.append(
                    Detection(
                        label=label_name,
                        confidence=d.confidence,
                        box=BoundingBox(xmin=d.xmin, ymin=d.ymin, xmax=d.xmax, ymax=d.ymax),
                        spatial=SpatialXYZ(
                            x=d.spatialCoordinates.x / 1000.0,
                            y=d.spatialCoordinates.y / 1000.0,
                            z=d.spatialCoordinates.z / 1000.0,
                        ),
                    )
                )

        return frame, detections

    def stop(self) -> None:
        if self.device is not None:
            print("Closing OAK-D device...")
            self.device.close()
            self.device = None
            self.q_rgb = None
            self.q_det = None
