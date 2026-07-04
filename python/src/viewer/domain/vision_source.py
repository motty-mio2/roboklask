from abc import ABC, abstractmethod

import numpy as np

from .models import Detection


class VisionSource(ABC):
    @abstractmethod
    def start(self) -> None:
        """Starts the vision system (initializes camera, loads models, etc.)"""
        raise NotImplementedError()

    @abstractmethod
    def read(self) -> tuple[np.ndarray, list[Detection]] | None:
        """Reads the latest frame and detections from the source.

        Returns Tuple[frame_bgr, detections] or None if no frame is available.
        """
        raise NotImplementedError()

    @abstractmethod
    def stop(self) -> None:
        """Stops the vision system and releases resources"""
        raise NotImplementedError()
