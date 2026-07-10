import argparse
import time

import cv2

from python.calibration import BoardCalibrator
from python.domain.config import CameraType, PolicyType, settings
from python.infrastructure.mcu_connections import get_mcu_connection
from python.infrastructure.vision_sources import get_vision_source
from python.presentation import DebuggerUI, RawVisionDebugger, RobotOrientDebugger
from python.usecase.track_ball import TrackBallUseCase


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Klask Vision Viewer - Switch between OAK-D/DepthAI and RealSense")
    parser.add_argument(
        "--camera",
        type=CameraType,
        choices=list(CameraType),
        default=settings.camera,
        help=f"Camera device to use (default: {settings.camera})",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Path to model file (blob for oakd, onnx for realsense). Uses default path if not specified.",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=settings.confidence_threshold,
        help=f"Confidence threshold (default: {settings.confidence_threshold})",
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=settings.iou_threshold,
        help=f"NMS IoU threshold (default: {settings.iou_threshold})",
    )
    parser.add_argument(
        "--gui",
        choices=["none", "raw", "warped", "all"],
        default="none",
        help="UI debug presentation mode (default: none). Use 'none' for CLI-only headless production mode.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    camera_type = args.camera

    # Determine default model path based on camera type
    model_path = args.model
    if not model_path:
        model_path = settings.blob_path if camera_type == CameraType.OAKD else settings.onnx_path
    model_path = str(model_path)

    # Initialize domain components
    calibrator = BoardCalibrator()
    mcu_connection = get_mcu_connection()
    source = get_vision_source(camera_type, model_path, args.conf, args.iou)

    # Determine motion planning policy (PPO model inference vs standard ball tracking)
    from python.domain.motion import BallTrackingPolicy, ModelBasedPolicy, MotionPolicy

    motion_policy: MotionPolicy
    if settings.policy_type == PolicyType.PPO:
        from python.infrastructure.onnx import OnnxInferenceEngine

        engine = OnnxInferenceEngine(str(settings.ppo_model_path))
        motion_policy = ModelBasedPolicy(engine)
    else:
        motion_policy = BallTrackingPolicy()

    # Instantiate tracking UseCase
    usecase = TrackBallUseCase(
        vision_source=source,
        calibrator=calibrator,
        mcu_connection=mcu_connection,
        motion_policy=motion_policy,
        camera_type=camera_type,
        model_path=model_path,
        conf=args.conf,
        iou=args.iou,
    )

    print(f"\nVision stream started using {camera_type.value.upper()}.")
    if args.gui != "none":
        print("Press:")
        print("  'q' on any image window to exit")
        print("  'c' to run interactive (manual click) calibration")
        print("  'a' to run automatic (color-based) calibration")
    else:
        print("Running in headless CLI mode (no UI windows). Press Ctrl+C to exit.")

    # Initialize modular UI presentation debuggers based on --gui option
    debuggers: list[DebuggerUI] = []
    if args.gui in ("raw", "all"):
        debuggers.append(RawVisionDebugger(camera_type))
    if args.gui in ("warped", "all"):
        debuggers.append(RobotOrientDebugger(calibrator))

    calibrated = False

    try:
        # Get the execution generator from UseCase
        stream = usecase.execute()

        for data in stream:
            if data is None:
                if debuggers:
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        break
                else:
                    time.sleep(0.005)
                continue

            frame, detections = data

            # Auto calibration runs on every startup using blue-field color detection.
            # No JSON persistence is used: if auto calibration is reliable enough, this
            # is sufficient. If manual precision is needed in the future, use the
            # `calibrate` subcommand (calibrate_interactive + save) and restore via
            # load() here instead.
            if not calibrated:
                if calibrator.calibrate_automatic(frame):
                    calibrated = True

            # Dispatch to all registered presentation UI modules
            for debugger in debuggers:
                debugger.update(frame, detections)

            if debuggers:
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                elif key == ord("c"):
                    calibrator.calibrate_interactive(frame)
                elif key == ord("a"):
                    calibrator.calibrate_automatic(frame)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        for debugger in debuggers:
            debugger.close()
        stream.close()
        if debuggers:
            cv2.destroyAllWindows()
        print("Application cleanup finished.")


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.set_start_method("spawn", force=True)
    main()
