import sys

from viewer.config import CameraType
from viewer.domain import VisionSource


def get_vision_source(camera: CameraType, model_path: str, conf: float, iou: float) -> VisionSource:
    """Factory to instantiate the selected camera VisionSource using lazy imports."""
    if camera == CameraType.OAKD:
        try:
            from viewer.infrastructure.vision_sources.oakd.vision_source import OakdVisionSource
        except ImportError:
            print(
                "Error: Could not import OAK-D dependencies. Make sure 'depthai' is installed.",
                file=sys.stderr,
            )
            print(
                "Try running: uv run --group luxonis python main.py --camera oakd",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"Creating OAK-D Vision Source with model: {model_path}")
        return OakdVisionSource(blob_path=model_path, confidence_threshold=conf, iou_threshold=iou)

    elif camera == CameraType.REALSENSE:
        try:
            from viewer.infrastructure.vision_sources.realsense.vision_source import RealsenseVisionSource
        except ImportError:
            print(
                "Error: Could not import RealSense dependencies. Make sure 'pyrealsense2' is installed.",
                file=sys.stderr,
            )
            print(
                "Try running: uv run --group realsense python main.py --camera realsense",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"Creating RealSense Vision Source with model: {model_path}")
        return RealsenseVisionSource(model_path=model_path, confidence_threshold=conf, iou_threshold=iou)

    else:
        print(f"Unsupported camera type: {camera}", file=sys.stderr)
        sys.exit(1)
