#!/usr/bin/env python3
"""
Vyoma Offline Medical AI Assistant - Main Application Entrypoint.
Run directly on Laptop or Jetson Orin Nano:
    python main.py
"""

import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Strict Offline Mode - Prevent external HuggingFace Hub network queries
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# Default development settings for laptop testing if not already set
os.environ.setdefault("FULLSCREEN", "false")
os.environ.setdefault("UI_WIDTH", "1024")
os.environ.setdefault("UI_HEIGHT", "600")

# On Linux / Jetson, clean OpenCV plugin poisoning and auto-connect to local display if available
if sys.platform.startswith("linux"):
    if "QT_QPA_PLATFORM_PLUGIN_PATH" in os.environ and "cv2" in os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"]:
        del os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"]
    # If launched from SSH terminal without DISPLAY set, target local X11 display :0 if running
    if not os.environ.get("DISPLAY"):
        if os.path.exists("/tmp/.X11-unix/X0") or os.path.exists("/tmp/.X11-unix/X1"):
            target_disp = ":0" if os.path.exists("/tmp/.X11-unix/X0") else ":1"
            os.environ["DISPLAY"] = target_disp
            if not os.environ.get("XAUTHORITY"):
                cand = Path.home() / ".Xauthority"
                if cand.exists():
                    os.environ["XAUTHORITY"] = str(cand)
        else:
            os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


from app.core.logging import logger
from app.hardware.jetson_detector import log_system_summary
from app.ui.app import run_ui

if __name__ == "__main__":
    print("========================================================================")
    print("      AVERA - Offline Medical AI Assistant - Starting Kiosk            ")
    print("========================================================================")
    try:
        log_system_summary()
    except Exception as e:
        logger.debug(f"Hardware detection note: {e}")

    run_ui()
