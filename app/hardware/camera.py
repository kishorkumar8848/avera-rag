import io
import time
from typing import Optional, Tuple, Any
from PIL import Image
import numpy as np

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

from app.core.config import settings
from app.core.logging import logger


class CameraService:
    """
    Hardware-agnostic camera abstraction supporting OpenCV, V4L2, and GStreamer (CSI/USB).
    Automatically resizes frames to 640x480 for efficient VLM inference.
    """

    def __init__(
        self,
        camera_index: int = 0,
        target_width: int = 640,
        target_height: int = 480,
        backend: str = "opencv"
    ):
        self.camera_index = camera_index
        self.target_width = target_width
        self.target_height = target_height
        self.backend = backend
        self._cap = None

    def _get_gstreamer_pipeline(self) -> str:
        """Standard Jetson CSI camera GStreamer pipeline string."""
        return (
            f"nvarguscamerasrc sensor-id={self.camera_index} ! "
            f"video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=30/1 ! "
            f"nvvidconv ! video/x-raw, width={self.target_width}, height={self.target_height}, format=BGRx ! "
            f"videoconvert ! video/x-raw, format=BGR ! appsink"
        )

    def open(self) -> bool:
        """Initializes the camera hardware with automatic backend fallback."""
        if not HAS_OPENCV:
            logger.warning("OpenCV not installed. Camera running in mock mode.")
            return False

        # Attempt 1: Standard V4L2 / USB camera
        try:
            self._cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2 if hasattr(cv2, 'CAP_V4L2') else cv2.CAP_ANY)
            if self._cap.isOpened():
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
                logger.info(f"Opened camera index {self.camera_index} via standard backend.")
                return True
        except Exception as e:
            logger.debug(f"Standard camera open failed: {e}")

        # Attempt 2: Jetson CSI GStreamer pipeline
        try:
            pipeline = self._get_gstreamer_pipeline()
            self._cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
            if self._cap.isOpened():
                logger.info("Opened Jetson CSI camera via GStreamer pipeline.")
                return True
        except Exception as e:
            logger.debug(f"Jetson GStreamer camera open failed: {e}")

        logger.warning(f"No active camera hardware found on index {self.camera_index}.")
        return False

    def capture_frame(self) -> Tuple[bool, Optional[Image.Image], Optional[bytes]]:
        """
        Captures a single frame, resizes it to 640x480, and returns:
        (success, PIL.Image in RGB, JPEG bytes in memory).
        """
        if self._cap is None or not self._cap.isOpened():
            if not self.open():
                # Provide a synthetic test image if no hardware camera is present
                mock_img = self._create_synthetic_preview()
                buf = io.BytesIO()
                mock_img.save(buf, format="JPEG")
                return True, mock_img, buf.getvalue()

        ret, frame = self._cap.read()
        if not ret or frame is None:
            logger.warning("Failed to capture frame from camera.")
            return False, None, None

        # Resize to 640x480 target for Moondream
        if frame.shape[1] != self.target_width or frame.shape[0] != self.target_height:
            frame = cv2.resize(frame, (self.target_width, self.target_height), interpolation=cv2.INTER_AREA)

        # Convert BGR (OpenCV) to RGB (PIL)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_frame)

        # Encode JPEG to in-memory bytes
        is_success, buffer = cv2.imencode(".jpg", frame)
        jpg_bytes = buffer.tobytes() if is_success else None

        return True, pil_img, jpg_bytes

    def _create_synthetic_preview(self) -> Image.Image:
        """Generates a synthetic medical preview pattern when camera is offline."""
        img_array = np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)
        # Gradient background
        for y in range(self.target_height):
            img_array[y, :, :] = [15, int(23 + y * 0.05), int(42 + y * 0.1)]
        return Image.fromarray(img_array)

    def close(self):
        """Releases the camera hardware cleanly."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.info("Camera released.")


camera_service = CameraService(
    camera_index=settings.CAMERA_INDEX,
    target_width=settings.CAMERA_WIDTH,
    target_height=settings.CAMERA_HEIGHT
)
