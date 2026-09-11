#!/usr/bin/env bash
# ==============================================================================
# AVERA Medical AI Kiosk - Desktop Launcher & Background Runner
# Starts the offline AI kiosk cleanly on DISPLAY=:0 with crash recovery.
# ==============================================================================

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-/home/orion/.Xauthority}"
export PYTHONUNBUFFERED=1

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# If already running, notify and bring forward or restart cleanly
EXISTING_PIDS=$(pgrep -f "python3 main.py" || true)
if [ -n "$EXISTING_PIDS" ]; then
    echo "[AVERA] App already running with PID(s): $EXISTING_PIDS. Restarting cleanly..."
    pkill -9 -f "python3 main.py" || true
    sleep 1
fi

echo "[AVERA] Starting AVERA Medical AI Kiosk on $DISPLAY..."
nohup python3 main.py > "$PROJECT_DIR/main_gui.log" 2>&1 &

NEW_PID=$!
echo "[AVERA] Kiosk launched successfully in background (PID: $NEW_PID)."
