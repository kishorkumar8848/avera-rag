#!/usr/bin/env bash
# ==============================================================================
# Vyoma Offline Medical AI Assistant - Cache & Temporary Artifact Cleanup
# Cleans temporary audio, video, and bytecode without deleting required models or indexes.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "=== Cleaning temporary cache artifacts ==="

# 1. Clean Python bytecode and pytest cache
echo "[*] Removing Python __pycache__ and test caches..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# 2. Clean temporary audio files from logs
echo "[*] Cleaning temporary audio WAV buffers..."
rm -f logs/*.wav 2>/dev/null || true
rm -f logs/tts_temp.wav 2>/dev/null || true

# 3. Clean temporary camera snapshots
echo "[*] Cleaning temporary camera frames..."
rm -f logs/*.jpg logs/*.png 2>/dev/null || true

echo "=== Cache cleanup complete. Models and indexes preserved! ==="
