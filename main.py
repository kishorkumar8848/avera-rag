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

# Headless Linux fallback if running via SSH without X11 DISPLAY
if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


from app.core.logging import logger
from app.hardware.jetson_detector import log_system_summary
from app.ui.app import run_ui

if __name__ == "__main__":
    print("========================================================================")
    print("      Vyoma Offline Medical AI Assistant - Starting Kiosk               ")
    print("========================================================================")
    try:
        log_system_summary()
    except Exception as e:
        logger.debug(f"Hardware detection note: {e}")

    run_ui()
