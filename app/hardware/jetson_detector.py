import os
import sys
import platform
import subprocess
import shutil
from typing import Dict, Any, Optional
from app.core.logging import logger


class JetsonDetector:
    """
    Detects whether the application is running on an NVIDIA Jetson platform
    (specifically Orin Nano) and inspects system/hardware capabilities.
    """

    @staticmethod
    def is_jetson() -> bool:
        """Checks for Jetson hardware indicators."""
        return os.path.exists("/etc/nv_tegra_release")

    @classmethod
    def get_system_profile(cls) -> Dict[str, Any]:
        """Collects complete hardware and OS profile non-intrusively."""
        profile: Dict[str, Any] = {
            "is_jetson": cls.is_jetson(),
            "platform": platform.platform(),
            "python_version": sys.version.split()[0],
            "architecture": platform.machine(),
            "tegra_release": None,
            "cuda_version": None,
            "gpu_name": None,
            "ram_total_gb": None,
            "ram_available_gb": None,
            "ram_used_percent": None,
            "power_mode": None,
            "tegrastats_available": shutil.which("tegrastats") is not None,
            "nvpmodel_available": shutil.which("nvpmodel") is not None,
            "jtop_available": False
        }

        # 1. Tegra Release / JetPack
        if cls.is_jetson():
            try:
                with open("/etc/nv_tegra_release", "r", encoding="utf-8") as f:
                    profile["tegra_release"] = f.read().strip()
            except Exception as e:
                profile["tegra_release"] = f"Error reading: {e}"

        # 2. CUDA version (nvcc)
        try:
            res = subprocess.run(["nvcc", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if "release" in line:
                        profile["cuda_version"] = line.strip()
                        break
        except Exception:
            profile["cuda_version"] = "nvcc not in PATH"

        # 3. GPU Info via Torch or Tegra sysfs
        try:
            import torch
            if torch.cuda.is_available():
                profile["gpu_name"] = torch.cuda.get_device_name(0)
                profile["cuda_available"] = True
            else:
                profile["gpu_name"] = "CUDA available in PyTorch: False"
                profile["cuda_available"] = False
        except Exception:
            profile["cuda_available"] = False

        # 4. RAM details
        try:
            import psutil
            mem = psutil.virtual_memory()
            profile["ram_total_gb"] = round(mem.total / (1024 ** 3), 2)
            profile["ram_available_gb"] = round(mem.available / (1024 ** 3), 2)
            profile["ram_used_percent"] = mem.percent
        except ImportError:
            # Fallback to os/free on Linux
            if os.path.exists("/proc/meminfo"):
                try:
                    with open("/proc/meminfo", "r") as f:
                        lines = f.readlines()
                    meminfo = {}
                    for line in lines:
                        parts = line.split(":")
                        if len(parts) == 2:
                            meminfo[parts[0].strip()] = parts[1].strip()
                    total_kb = int(meminfo.get("MemTotal", "0 kB").split()[0])
                    avail_kb = int(meminfo.get("MemAvailable", "0 kB").split()[0])
                    profile["ram_total_gb"] = round(total_kb / (1024 ** 2), 2)
                    profile["ram_available_gb"] = round(avail_kb / (1024 ** 2), 2)
                    profile["ram_used_percent"] = round((1 - (avail_kb / total_kb)) * 100, 1) if total_kb > 0 else 0
                except Exception:
                    pass

        # 5. Jetson Power Mode (nvpmodel -q)
        if profile["nvpmodel_available"]:
            try:
                res = subprocess.run(["nvpmodel", "-q"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if res.returncode == 0:
                    profile["power_mode"] = res.stdout.strip().splitlines()[0]
            except Exception:
                pass

        # 6. Check for jtop / jetson-stats
        try:
            import jtop
            profile["jtop_available"] = True
        except ImportError:
            profile["jtop_available"] = False

        return profile


def log_system_summary():
    """Logs a clean summary of current execution hardware."""
    profile = JetsonDetector.get_system_profile()
    if profile["is_jetson"]:
        logger.info(f"NVIDIA Jetson detected: {profile.get('tegra_release')}")
        logger.info(f"RAM: Total={profile.get('ram_total_gb')}GB, Available={profile.get('ram_available_gb')}GB")
        logger.info(f"Power Mode: {profile.get('power_mode')}")
    else:
        logger.info(f"Running on standard development host ({profile['platform']}). Jetson emulation active.")
    return profile
