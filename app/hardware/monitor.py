import os
import time
import threading
from typing import Dict, Any, Optional
from app.core.logging import logger
from app.hardware.jetson_detector import JetsonDetector


class PerformanceMonitor:
    """
    Non-blocking performance monitor that tracks CPU, GPU, RAM,
    temperature, and power mode periodically without interfering with AI inference.
    """

    def __init__(self, interval_sec: float = 2.0):
        self.interval_sec = interval_sec
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._latest_stats: Dict[str, Any] = {
            "cpu_percent": 0.0,
            "ram_used_mb": 0.0,
            "ram_free_mb": 0.0,
            "ram_percent": 0.0,
            "gpu_percent": 0.0,
            "temperature_c": None,
            "power_mode": "Standard",
            "timestamp": time.time()
        }

    def start(self):
        """Starts background monitoring thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info(f"Hardware PerformanceMonitor started (polling every {self.interval_sec}s).")

    def stop(self):
        """Stops background monitoring."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.info("PerformanceMonitor stopped.")

    def get_stats(self) -> Dict[str, Any]:
        """Returns a snapshot of the latest performance telemetry."""
        with self._lock:
            return dict(self._latest_stats)

    def _monitor_loop(self):
        while self._running:
            try:
                stats = self._collect_metrics()
                with self._lock:
                    self._latest_stats = stats
            except Exception as e:
                logger.debug(f"Performance monitoring poll failed: {e}")
            time.sleep(self.interval_sec)

    def _collect_metrics(self) -> Dict[str, Any]:
        stats: Dict[str, Any] = {
            "cpu_percent": 0.0,
            "ram_used_mb": 0.0,
            "ram_free_mb": 0.0,
            "ram_percent": 0.0,
            "gpu_percent": 0.0,
            "temperature_c": None,
            "power_mode": "Normal",
            "timestamp": time.time()
        }

        # 1. CPU & RAM (via psutil or /proc)
        try:
            import psutil
            stats["cpu_percent"] = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            stats["ram_used_mb"] = round((mem.total - mem.available) / (1024 * 1024), 1)
            stats["ram_free_mb"] = round(mem.available / (1024 * 1024), 1)
            stats["ram_percent"] = mem.percent
        except ImportError:
            pass

        # 2. Thermal readings on Linux / Jetson (/sys/class/thermal/thermal_zone0/temp)
        if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
            try:
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    temp_raw = int(f.read().strip())
                    stats["temperature_c"] = round(temp_raw / 1000.0, 1)
            except Exception:
                pass

        # 3. GPU utilization on Jetson (/sys/devices/gpu.0/load)
        if os.path.exists("/sys/devices/gpu.0/load"):
            try:
                with open("/sys/devices/gpu.0/load", "r") as f:
                    stats["gpu_percent"] = round(float(f.read().strip()) / 10.0, 1)
            except Exception:
                pass

        # 4. Fallback for NVIDIA GPU via Torch
        if stats["gpu_percent"] == 0.0:
            try:
                import torch
                if torch.cuda.is_available():
                    # Memory reserved as approximation if utilization counter unavailable
                    allocated = torch.cuda.memory_allocated(0) / (1024 * 1024)
                    stats["gpu_vram_used_mb"] = round(allocated, 1)
            except Exception:
                pass

        return stats


# Global instance
monitor = PerformanceMonitor(interval_sec=2.0)
