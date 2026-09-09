#!/usr/bin/env bash
# ==============================================================================
# Vyoma Offline Medical AI Assistant - Developer Launcher
# Launches kiosk window with verbose debug telemetry, model health checks, and stats.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../bhashini_models/venv" ]; then
    source ../bhashini_models/venv/bin/activate
fi

export FULLSCREEN=false
export DEBUG=true
export LOG_LEVEL=DEBUG

echo "========================================================================"
echo "    Vyoma Offline Medical AI Assistant - Developer Diagnostics Mode     "
echo "========================================================================"

# Run system profiler check
python3 -c "
from app.hardware.jetson_detector import log_system_summary
from app.models.manager import model_manager
log_system_summary()
print('Initial Model Manager Health:', model_manager.health_check())
" || true

echo "Starting PySide6 Kiosk Application in Windowed Mode (1024x600)..."
exec python3 -m app.ui.app
