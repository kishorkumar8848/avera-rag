#!/usr/bin/env bash
# ==============================================================================
# Vyoma Offline Medical AI Assistant - Environment Installation Script
# Prepares Python virtual environment and native Jetson dependencies.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "=== Installing Vyoma Offline Medical AI Assistant on Jetson Orin Nano ==="

# 1. System packages check
echo "[1/5] Checking essential system packages..."
sudo apt-get update -y
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    portaudio19-dev \
    libasound2-dev \
    libsqlite3-dev \
    v4l-utils \
    ffmpeg

# 2. Add user to audio and video hardware groups
echo "[2/5] Configuring hardware device permissions..."
sudo usermod -a -G audio,video "$USER" || true

# 3. Create & Activate Virtual Environment
echo "[3/5] Initializing Python virtual environment (venv)..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# 4. Install Python Dependencies
echo "[4/5] Installing Python requirements..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 5. Pre-download NLTK tokenization assets for offline Bhashini NMT
echo "[5/5] Pre-caching NLTK sentence tokenizers..."
python3 -c "
import nltk
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
print('NLTK tokenizers ready.')
" || true

# Create required directory structure
mkdir -p models/bhashini data/medlineplus data/indian_protocols indexes/faiss logs

echo "=== Vyoma Installation Completed Successfully! ==="
echo "Next step: Transfer or download models using ./scripts/download_models.sh"
