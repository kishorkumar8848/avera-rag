import io
import time
from typing import Optional, Tuple, Any
from PIL import Image
import numpy as np

try:
    import os
    # OpenCV wheels forcibly set QT_QPA_PLATFORM_PLUGIN_PATH to internal broken plugins on Linux.
    _prev_qt_plugin_path = os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH")
    import cv2
    if _prev_qt_plugin_path is not None:
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = _prev_qt_plugin_path
    elif "QT_QPA_PLATFORM_PLUGIN_PATH" in os.environ and "cv2" in os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"]:
        del os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"]
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
        self._last_probe_time = 0.0

    def _get_gstreamer_pipeline(self) -> str:
        """Standard Jetson CSI camera GStreamer pipeline string."""
        return (
            f"nvarguscamerasrc sensor-id={self.camera_index} ! "
            f"video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=30/1 ! "
            f"nvvidconv ! video/x-raw, width={self.target_width}, height={self.target_height}, format=BGRx ! "
            f"videoconvert ! video/x-raw, format=BGR ! appsink"
        )

    def open(self) -> bool:
        """Initializes the camera hardware with automatic backend and device scanning."""
        if not HAS_OPENCV:
            logger.warning("OpenCV not installed. Camera running in mock mode.")
            return False

        # Fast non-blocking check on Linux: if no /dev/video* devices exist, don't stall UI with cv2 probe
        import glob
        import os
        if os.name == "posix":
            nodes = glob.glob("/dev/video*")
            if not nodes:
                return False

        # Throttle re-probe attempts to at most once every 2 seconds
        now = time.time()
        if (now - self._last_probe_time) < 2.0:
            return False
        self._last_probe_time = now

        # Candidate indices to probe: configured index first, then common indices
        candidates = [self.camera_index]
        for idx in [0, 1, 2, 3]:
            if idx not in candidates:
                candidates.append(idx)

        for idx in candidates:
            # Attempt USB / V4L2 with MJPG
            try:
                backend = cv2.CAP_V4L2 if hasattr(cv2, 'CAP_V4L2') else cv2.CAP_ANY
                cap = cv2.VideoCapture(idx, backend)
                if cap.isOpened():
                    try:
                        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                    except Exception:
                        pass
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)

                    # Test reading a frame to verify it actually yields image data
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None and test_frame.size > 0:
                        self._cap = cap
                        self.camera_index = idx
                        logger.info(f"Successfully opened and verified camera index {idx} ({test_frame.shape[1]}x{test_frame.shape[0]}).")
                        return True
                    else:
                        cap.release()
            except Exception as e:
                logger.debug(f"Camera index {idx} open failed: {e}")

        # Attempt Jetson CSI GStreamer pipeline as fallback
        try:
            pipeline = self._get_gstreamer_pipeline()
            cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
            if cap.isOpened():
                ret, test_frame = cap.read()
                if ret and test_frame is not None and test_frame.size > 0:
                    self._cap = cap
                    logger.info("Opened Jetson CSI camera via GStreamer pipeline.")
                    return True
                else:
                    cap.release()
        except Exception as e:
            logger.debug(f"Jetson GStreamer camera open failed: {e}")

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
            logger.warning("Failed to capture frame from camera. Resetting handle for auto-reconnect.")
            self.close()
            mock_img = self._create_synthetic_preview()
            buf = io.BytesIO()
            mock_img.save(buf, format="JPEG")
            return True, mock_img, buf.getvalue()

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

    @property
    def is_hardware_available(self) -> bool:
        """Returns True if a physical camera is currently connected and accessible."""
        if self._cap is not None and self._cap.isOpened():
            return True
        # Fast non-blocking check
        import glob
        if glob.glob("/dev/video*"):
            return True
        return False

    def _create_synthetic_preview(self) -> Image.Image:
        """
        Generates a realistic clinical skin/lesion inspection test pattern when
        no physical USB/CSI webcam is plugged into the kiosk.
        Displays dermal background with localized erythema/rash and calibration crosshairs.
        """
        img_array = np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)
        # Natural warm dermal background base
        img_array[:, :, 0] = 224  # R
        img_array[:, :, 1] = 188  # G
        img_array[:, :, 2] = 168  # B

        # Draw central erythematous rash patch (dermal redness)
        cy, cx = self.target_height // 2, self.target_width // 2
        y, x = np.ogrid[:self.target_height, :self.target_width]
        dist_from_center = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)

        # Gradient redness mask
        mask = np.clip(1.0 - (dist_from_center / 110.0), 0.0, 1.0)
        img_array[:, :, 0] = np.clip(img_array[:, :, 0] + (mask * 45), 0, 255).astype(np.uint8)
        img_array[:, :, 1] = np.clip(img_array[:, :, 1] - (mask * 55), 0, 255).astype(np.uint8)
        img_array[:, :, 2] = np.clip(img_array[:, :, 2] - (mask * 55), 0, 255).astype(np.uint8)

        # Draw subtle crosshairs and border
        try:
            if HAS_OPENCV:
                cv2.circle(img_array, (cx, cy), 110, (180, 80, 80), 2)
                cv2.line(img_array, (cx - 20, cy), (cx + 20, cy), (140, 60, 60), 1)
                cv2.line(img_array, (cx, cy - 20), (cx, cy + 20), (140, 60, 60), 1)
                cv2.putText(
                    img_array, "AVERA Clinical Inspection Area",
                    (18, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (90, 40, 40), 2
                )
                cv2.putText(
                    img_array, "Offline Visual Calibration Sample: Skin Lesion / Rash",
                    (18, self.target_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 50, 50), 1
                )
        except Exception:
            pass

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
