import os
from typing import Any

import cv2
import numpy as np
import onnxruntime as ort

from viewer.domain import BoundingBox, Detection, DetectionLabel


class OnnxRuntimeYoloDetector:
    def __init__(
        self,
        model_path: str = "best.onnx",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.3,
    ) -> None:
        self.model_path: str = model_path
        self.confidence_threshold: float = confidence_threshold
        self.iou_threshold: float = iou_threshold
        # self.label_map: list[str] = ["ball", "striker"]
        self.session: Any | None = None
        self.input_name: str = ""
        self.output_name: str = ""
        self.has_model: bool = False

        if os.path.exists(self.model_path):
            try:
                # Load ONNX model using ONNX Runtime
                # Default to CPU execution provider
                self.session = ort.InferenceSession(self.model_path, providers=["CPUExecutionProvider"])
                self.input_name = self.session.get_inputs()[0].name
                self.output_name = self.session.get_outputs()[0].name
                self.has_model = True
                print(f"Loaded YOLOv8 ONNX model using ONNX Runtime from {self.model_path}")
            except Exception as e:
                print(f"Failed to load ONNX model {self.model_path} via ONNX Runtime: {e}")
                print("Falling back to dummy detector.")
        else:
            print(f"ONNX model not found at {self.model_path}. Running in DUMMY mode (no actual detection).")
            print("To enable detection, please place your 'best.onnx' in the working directory.")

    def detect(self, frame: np.ndarray) -> list[Detection]:
        if not self.has_model or self.session is None:
            # DUMMY MODE: Return dummy detections (e.g. static/moving boxes)
            # This helps test the pipeline even without a real model file.
            return self._generate_dummy_detections(frame)

        h, w = frame.shape[:2]

        # YOLOv8 preprocessing: Resize, BGR to RGB, normalize, HWC to CHW, add batch dim
        img = cv2.resize(frame, (640, 640))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32) / 255.0
        img = img.transpose(2, 0, 1)  # HWC -> CHW
        input_tensor = np.expand_dims(img, axis=0)

        # Run inference
        import time

        start_time = time.perf_counter()
        outputs = self.session.run([self.output_name], {self.input_name: input_tensor})
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        print(f"[RealSense YOLO] Inference time: {elapsed_ms:.2f} ms")

        output = np.squeeze(outputs[0])  # Shape: (6, 8400) or similar

        # Parse outputs
        detections: list[Detection] = []

        # Transpose if output shape is (6, 8400) -> (8400, 6)
        if output.shape[0] < output.shape[1]:
            output = output.T

        boxes = []
        confidences = []
        class_ids = []

        for row in output:
            classes_scores = row[4:]
            class_id = np.argmax(classes_scores)
            confidence = classes_scores[class_id]

            if confidence >= self.confidence_threshold:
                cx, cy, box_w, box_h = row[0:4]

                # Scale back to original image dimensions
                x_scale = w / 640.0
                y_scale = h / 640.0

                pixel_cx = cx * x_scale
                pixel_cy = cy * y_scale
                pixel_w = box_w * x_scale
                pixel_h = box_h * y_scale

                left = int(pixel_cx - pixel_w / 2)
                top = int(pixel_cy - pixel_h / 2)
                width = int(pixel_w)
                height = int(pixel_h)

                boxes.append([left, top, width, height])
                confidences.append(float(confidence))
                class_ids.append(int(class_id))

        # Non-Maximum Suppression (NMS) using OpenCV NMS (still lightweight)
        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.confidence_threshold, self.iou_threshold)  # type: ignore

        if len(indices) > 0:
            flat_indices = np.array(indices).flatten()
            for idx in flat_indices:
                left, top, width, height = boxes[idx]
                conf = confidences[idx]
                class_id = class_ids[idx]

                # Normalize coordinates (0.0 ~ 1.0)
                xmin = max(0.0, left / w)
                ymin = max(0.0, top / h)
                xmax = min(1.0, (left + width) / w)
                ymax = min(1.0, (top + height) / h)

                # label_name = self.label_map[class_id] if class_id < len(self.label_map) else f"Class {class_id}"

                try:
                    label_name = DetectionLabel(class_id)
                except ValueError:
                    continue

                detections.append(
                    Detection(
                        label=label_name,
                        confidence=conf,
                        box=BoundingBox(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax),
                    )
                )

        return detections

    def _generate_dummy_detections(self, frame: np.ndarray) -> list[Detection]:
        import time

        t = time.time()

        # Ball moving in a circle in the center of the frame
        cx = 0.5 + 0.15 * np.cos(t * 1.5)
        cy = 0.5 + 0.15 * np.sin(t * 1.5)
        ball = Detection(
            label=DetectionLabel.BALL,
            confidence=0.95,
            box=BoundingBox(xmin=cx - 0.02, ymin=cy - 0.02, xmax=cx + 0.02, ymax=cy + 0.02),
        )

        # Striker vibrating slightly near the bottom of the frame
        scx = 0.5 + 0.005 * np.cos(t * 8)
        scy = 0.85 + 0.005 * np.sin(t * 6)
        striker = Detection(
            label=DetectionLabel.STRIKER,
            confidence=0.89,
            box=BoundingBox(xmin=scx - 0.04, ymin=scy - 0.04, xmax=scx + 0.04, ymax=scy + 0.04),
        )
        return [ball, striker]
