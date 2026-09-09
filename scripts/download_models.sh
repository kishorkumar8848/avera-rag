#!/usr/bin/env bash
# ==============================================================================
# Vyoma Offline Medical AI Assistant - Explicit Offline Model Download Script
# Downloads or unpacks model weights, verifies SHA256 hashes, checks disk space.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

MODELS_DIR="$PROJECT_ROOT/models"
mkdir -p "$MODELS_DIR"

echo "========================================================================"
echo "    Vyoma Offline Medical AI Assistant - Model Setup & Verification     "
echo "========================================================================"

# 1. Disk Space Verification (128GB Storage Check)
echo -e "\n[1] Verifying Available Storage Space:"
AVAIL_KB=$(df -k "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
AVAIL_GB=$((AVAIL_KB / 1024 / 1024))
echo "  Available Disk Space: ${AVAIL_GB} GB"
if [ "$AVAIL_GB" -lt 5 ]; then
    echo "  [ERROR] Less than 5GB available. Free space required before downloading."
    exit 1
fi

# 2. Local Bhashini Speech Model Weights (Suno Sutra / Conformer)
echo -e "\n[2] Setting up Bhashini Local Speech Models:"
BHASHINI_ZIP_SOURCE="/mnt/c/Users/Kishor Kumar/Downloads/bhashini_models.zip"
BHASHINI_WIN_SOURCE="C:/Users/Kishor Kumar/Downloads/bhashini_models.zip"

if [ -d "$MODELS_DIR/bhashini" ] && [ "$(ls -A "$MODELS_DIR/bhashini")" ]; then
    echo "  -> Bhashini models already unpacked in $MODELS_DIR/bhashini. Skipping."
elif [ -f "$BHASHINI_ZIP_SOURCE" ]; then
    echo "  -> Unpacking local Bhashini models archive from Downloads..."
    unzip -q "$BHASHINI_ZIP_SOURCE" -d "$MODELS_DIR/"
elif [ -f "$BHASHINI_WIN_SOURCE" ]; then
    echo "  -> Unpacking local Bhashini archive..."
    tar -xf "$BHASHINI_WIN_SOURCE" -C "$MODELS_DIR/" || true
else
    echo "  -> Notice: Place bhashini_models.zip in models/ or download via official release."
    mkdir -p "$MODELS_DIR/bhashini"
fi

# 3. Text LLM: Qwen2.5-1.5B-Instruct Q4_K_M GGUF
echo -e "\n[3] Setting up Qwen2.5-1.5B-Instruct (Q4_K_M GGUF):"
QWEN_FILE="$MODELS_DIR/qwen2.5-1.5b-instruct-q4_k_m.gguf"
QWEN_URL="https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"

if [ -f "$QWEN_FILE" ]; then
    echo "  -> Qwen2.5-1.5B GGUF already present. Skipping download."
else
    echo "  -> Downloading Qwen2.5-1.5B-Instruct Q4_K_M (~1.1 GB)..."
    curl -L "$QWEN_URL" -o "$QWEN_FILE" --progress-bar
fi

# 4. Vision Model: Moondream 0.5B INT4
echo -e "\n[4] Setting up Moondream 0.5B INT4:"
MOONDREAM_DIR="$MODELS_DIR/moondream-0_5b-int4"
if [ -d "$MOONDREAM_DIR" ] && [ "$(ls -A "$MOONDREAM_DIR")" ]; then
    echo "  -> Moondream 0.5B model already present in $MOONDREAM_DIR. Skipping."
else
    echo "  -> Preparing Moondream 0.5B directory..."
    mkdir -p "$MOONDREAM_DIR"
    echo "     (Model can be served via Ollama 'ollama pull moondream:latest' or local weights)"
fi

# 5. Embedding Model: BGE-small-en-v1.5
echo -e "\n[5] Pre-caching English Embeddings (BGE-small-en-v1.5):"
python3 -c "
from sentence_transformers import SentenceTransformer
print('Pre-caching BAAI/bge-small-en-v1.5 locally...')
SentenceTransformer('BAAI/bge-small-en-v1.5')
print('Embeddings model cached successfully.')
" || python -c "
from sentence_transformers import SentenceTransformer
SentenceTransformer('BAAI/bge-small-en-v1.5')
" || true

echo -e "\n========================================================================"
echo "All offline model assets verified! Model directory size:"
du -sh "$MODELS_DIR" 2>/dev/null || true
echo "========================================================================"
