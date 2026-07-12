import ctypes
import multiprocessing
import time
from collections.abc import Generator
from typing import Any

import numpy as np

from python.calibration import BoardCalibrator
from python.domain import BoundingBox, Detection, DetectionLabel, McuConnection, VisionSource
from python.domain.config import CameraType, settings
from python.domain.motion import MotionPolicy
from python.domain.value_objects import BoardXY


def _vision_worker(
    camera_type: CameraType,
    model_path: str,
    conf: float,
    iou: float,
    shared_lock: Any,
    shared_ball_u: Any,
    shared_ball_v: Any,
    shared_striker_u: Any,
    shared_striker_v: Any,
    shared_frame_w: Any,
    shared_frame_h: Any,
    shared_calibrated: Any,
    shared_src_pts: Any,
    gui_queue: Any,
) -> None:
    from python.calibration import BoardCalibrator
    from python.domain import DetectionLabel
    from python.infrastructure.vision_sources import get_vision_source

    source = get_vision_source(camera_type, model_path, conf, iou)
    calibrator = BoardCalibrator()
    source.start()

    calibrated = False

    try:
        while True:
            result = source.read()
            if result is None:
                time.sleep(0.001)
                continue

            frame, detections = result
            h, w = frame.shape[:2]

            # Try automatic calibration if not completed yet
            if not calibrated:
                if calibrator.calibrate_automatic(frame):
                    calibrated = True
                    with shared_lock:
                        shared_calibrated.value = True
                        if calibrator.src_pts is not None:
                            flat_pts = calibrator.src_pts.flatten().tolist()
                            for i in range(8):
                                shared_src_pts[i] = flat_pts[i]

            # Extract coordinates for ball and striker
            ball_pos = None
            striker_pos = None
            for d in detections:
                u, v = d.box.to_pixel_center(w, h)
                if d.label == DetectionLabel.BALL:
                    ball_pos = (u, v)
                elif d.label == DetectionLabel.STRIKER:
                    striker_pos = (u, v)

            # Write to shared memory
            with shared_lock:
                shared_frame_w.value = w
                shared_frame_h.value = h
                if ball_pos:
                    shared_ball_u.value = float(ball_pos[0])
                    shared_ball_v.value = float(ball_pos[1])
                else:
                    shared_ball_u.value = float("nan")
                    shared_ball_v.value = float("nan")

                if striker_pos:
                    shared_striker_u.value = float(striker_pos[0])
                    shared_striker_v.value = float(striker_pos[1])
                else:
                    shared_striker_u.value = float("nan")
                    shared_striker_v.value = float("nan")

            # Push to GUI queue
            if gui_queue is not None:
                if gui_queue.full():
                    try:
                        gui_queue.get_nowait()
                    except Exception:
                        pass
                try:
                    gui_queue.put_nowait((frame, detections))
                except Exception:
                    pass
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error in vision worker: {e}")
    finally:
        source.stop()


class TrackBallUseCase:
    def __init__(
        self,
        vision_source: VisionSource,
        calibrator: BoardCalibrator,
        mcu_connection: McuConnection,
        motion_policy: MotionPolicy,
        camera_type: CameraType = settings.camera,
        model_path: str | None = None,
        conf: float = settings.confidence_threshold,
        iou: float = settings.iou_threshold,
    ) -> None:
        self.vision_source = vision_source
        self.calibrator = calibrator
        self.mcu_connection = mcu_connection
        self.motion_policy = motion_policy

        self.camera_type = camera_type
        if model_path is None:
            from python.infrastructure.vision_sources.realsense.vision_source import RealsenseVisionSource

            if isinstance(vision_source, RealsenseVisionSource):
                model_path = str(settings.onnx_path)
            else:
                model_path = str(settings.blob_path)
        self.model_path = model_path
        self.confidence_threshold = conf
        self.iou_threshold = iou

    def execute(self) -> Generator[tuple[np.ndarray, list[Detection]] | None]:
        """Orchestrate the tracking loop: read frame, run detections, map coords, and send MCU target commands.

        Yields (frame, detections) or None for the UI presentation layer.
        """
        shared_lock = multiprocessing.Lock()
        shared_ball_u = multiprocessing.Value(ctypes.c_double, float("nan"))
        shared_ball_v = multiprocessing.Value(ctypes.c_double, float("nan"))
        shared_striker_u = multiprocessing.Value(ctypes.c_double, float("nan"))
        shared_striker_v = multiprocessing.Value(ctypes.c_double, float("nan"))
        shared_frame_w = multiprocessing.Value(ctypes.c_int, 0)
        shared_frame_h = multiprocessing.Value(ctypes.c_int, 0)
        shared_calibrated = multiprocessing.Value(ctypes.c_bool, False)
        shared_src_pts = multiprocessing.Array(ctypes.c_double, [0.0] * 8)

        gui_queue: multiprocessing.Queue[Any] = multiprocessing.Queue(maxsize=2)

        # Spawn vision worker process
        p = multiprocessing.Process(
            target=_vision_worker,
            args=(
                self.camera_type,
                self.model_path,
                self.confidence_threshold,
                self.iou_threshold,
                shared_lock,
                shared_ball_u,
                shared_ball_v,
                shared_striker_u,
                shared_striker_v,
                shared_frame_w,
                shared_frame_h,
                shared_calibrated,
                shared_src_pts,
                gui_queue,
            ),
        )
        p.start()

        self.mcu_connection.start()

        calibrated = False

        try:
            while True:
                loop_start = time.perf_counter()

                # Sync calibration matrices if newly calculated
                if not calibrated:
                    with shared_lock:
                        if shared_calibrated.value:
                            pts = np.array(shared_src_pts[:], dtype=np.float32).reshape(4, 2)
                            self.calibrator.src_pts = pts
                            self.calibrator.update_matrices()
                            calibrated = True
                            print("Synchronized auto calibration from vision process.")

                # Read from shared memory
                with shared_lock:
                    w = shared_frame_w.value
                    h = shared_frame_h.value
                    ball_u = shared_ball_u.value
                    ball_v = shared_ball_v.value
                    v_striker_u = shared_striker_u.value
                    v_striker_v = shared_striker_v.value

                # 1. Read encoder/stepper feedback from the MCU
                mcu_striker_xy = self.mcu_connection.read_feedback()

                detections = []

                # Process ball detection
                if w > 0 and h > 0 and not (np.isnan(ball_u) or np.isnan(ball_v)):
                    xmin = (ball_u - 5) / w
                    ymin = (ball_v - 5) / h
                    xmax = (ball_u + 5) / w
                    ymax = (ball_v + 5) / h
                    ball_det = Detection(
                        label=DetectionLabel.BALL,
                        confidence=1.0,
                        box=BoundingBox(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax),
                    )
                    x_board, y_board = self.calibrator.transform_point(ball_u, ball_v)
                    if x_board is not None and y_board is not None:
                        bx = float(max(0.0, min(float(self.calibrator.board_width - 1), x_board)))
                        by = float(max(0.0, min(float(self.calibrator.board_height - 1), y_board)))
                        ball_det.board_xy = BoardXY(board_x=bx, board_y=by)
                        ball_det.robot_xy = ball_det.board_xy.to_robot_xy(
                            float(self.calibrator.board_width), float(self.calibrator.board_height)
                        )
                    detections.append(ball_det)

                # Process striker position (prefer MCU feedback)
                if mcu_striker_xy is not None:
                    striker_det = Detection(
                        label=DetectionLabel.STRIKER,
                        confidence=1.0,
                        box=BoundingBox(xmin=0.0, ymin=0.0, xmax=0.0, ymax=0.0),
                        robot_xy=mcu_striker_xy,
                    )
                    bx = float(self.calibrator.board_width) * (1.0 - mcu_striker_xy.y) / 2.0
                    by = float(self.calibrator.board_height) * (1.0 - mcu_striker_xy.x) / 2.0
                    striker_det.board_xy = BoardXY(board_x=bx, board_y=by)
                    detections.append(striker_det)
                elif w > 0 and h > 0 and not (np.isnan(v_striker_u) or np.isnan(v_striker_v)):
                    xmin = (v_striker_u - 15) / w
                    ymin = (v_striker_v - 15) / h
                    xmax = (v_striker_u + 15) / w
                    ymax = (v_striker_v + 15) / h
                    striker_det = Detection(
                        label=DetectionLabel.STRIKER,
                        confidence=1.0,
                        box=BoundingBox(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax),
                    )
                    x_board, y_board = self.calibrator.transform_point(v_striker_u, v_striker_v)
                    if x_board is not None and y_board is not None:
                        bx = float(max(0.0, min(float(self.calibrator.board_width - 1), x_board)))
                        by = float(max(0.0, min(float(self.calibrator.board_height - 1), y_board)))
                        striker_det.board_xy = BoardXY(board_x=bx, board_y=by)
                        striker_det.robot_xy = striker_det.board_xy.to_robot_xy(
                            float(self.calibrator.board_width), float(self.calibrator.board_height)
                        )
                    detections.append(striker_det)

                # 2. Plan motion target coordinates using the policy
                target = self.motion_policy.plan_motion(detections)

                # 3. Transmit computed command target to the MCU
                self.mcu_connection.send_target(target)

                gui_data = None
                try:
                    frame, _ = gui_queue.get_nowait()
                    # Use our synced/updated detections instead of stale vision-only ones
                    gui_data = (frame, detections)
                except Exception:
                    pass

                yield gui_data

                # Maintain 20ms control loop interval (50Hz)
                elapsed = time.perf_counter() - loop_start
                sleep_time = 0.02 - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)
        finally:
            self.mcu_connection.stop()
            p.terminate()
            p.join()
