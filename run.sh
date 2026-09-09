#!/usr/bin/env bash
# ==============================================================================
# Vyoma Offline Medical AI Assistant - Production Kiosk Launcher
# Boots directly into Language Selection screen in 1024x600 Fullscreen.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv if present
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../bhashini_models/venv" ]; then
    source ../bhashini_models/venv/bin/activate
fi

export FULLSCREEN=true
export DEBUG=false
export LOG_LEVEL=INFO

# Launch native PySide6 touchscreen kiosk application
exec python3 -m app.ui.app
