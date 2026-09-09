#!/usr/bin/env bash
# ==============================================================================
# Vyoma Offline Medical AI Assistant - Jetson Environment Inspection Script
# Non-destructively inspects JetPack, CUDA, RAM, Audio, Camera, and Power Modes.
# ==============================================================================

echo "========================================================================"
echo "    Vyoma Offline Medical AI Assistant - Jetson Hardware Inspection     "
echo "========================================================================"

# 1. Tegra Release & JetPack
echo -e "\n[1] Checking Tegra / JetPack Version:"
if [ -f "/etc/nv_tegra_release" ]; then
    cat /etc/nv_tegra_release
else
    echo "  -> /etc/nv_tegra_release NOT found. Running on non-Tegra / development host."
fi

# 2. Kernel & Architecture
echo -e "\n[2] System Kernel & Architecture:"
uname -a

# 3. CUDA Toolkit
echo -e "\n[3] Checking CUDA Compiler (nvcc):"
if command -v nvcc &> /dev/null; then
    nvcc --version | grep "release"
else
    echo "  -> nvcc not found in PATH. Check /usr/local/cuda/bin/nvcc"
fi

# 4. Python Environment
echo -e "\n[4] Python Version:"
python3 --version 2>&1 || python --version 2>&1

# 5. Memory Status (8GB Unified RAM check)
echo -e "\n[5] Unified Memory & Swap Status:"
free -h

# 6. Tegrastats & NVPModel
echo -e "\n[6] Jetson Utilities:"
if command -v tegrastats &> /dev/null; then
    echo "  -> tegrastats: AVAILABLE"
else
    echo "  -> tegrastats: NOT FOUND"
fi

if command -v nvpmodel &> /dev/null; then
    echo "  -> Active Power Mode (nvpmodel -q):"
    sudo nvpmodel -q 2>/dev/null || nvpmodel -q 2>/dev/null || echo "     (run with sudo to view nvpmodel)"
fi

# 7. Audio Devices (Capture & Playback)
echo -e "\n[7] Audio Hardware Check:"
echo "--- Audio Recording Devices (arecord -l) ---"
arecord -l 2>/dev/null | head -n 10 || echo "  -> arecord not available"
echo "--- Audio Playback Devices (aplay -l) ---"
aplay -l 2>/dev/null | head -n 10 || echo "  -> aplay not available"

# 8. Camera Devices (V4L2 / CSI)
echo -e "\n[8] Camera Hardware Check (v4l2-ctl):"
if command -v v4l2-ctl &> /dev/null; then
    v4l2-ctl --list-devices 2>/dev/null || echo "  -> No V4L2 video devices detected"
else
    ls -l /dev/video* 2>/dev/null || echo "  -> /dev/video* devices not present"
fi

echo -e "\n========================================================================"
echo "Inspection Complete. Ready for Vyoma environment setup."
echo "========================================================================"
