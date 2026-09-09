# Jetson Orin Nano Hardware & Software Installation Guide

This document details the exact installation, environment configuration, display calibration, and audio routing required to run the **Vyoma Offline Medical AI Assistant** on the **NVIDIA Jetson Orin Nano 8GB**.

---

## 1. System Assumptions & Prerequisites

| Parameter | Specification | Verification Command |
| :--- | :--- | :--- |
| **Board** | NVIDIA Jetson Orin Nano Developer Kit (8GB) | `cat /proc/device-tree/model` |
| **Operating System** | JetPack 5.1.2 / 5.1.3 (Ubuntu 20.04) or JetPack 6.0 (Ubuntu 22.04) | `cat /etc/nv_tegra_release` |
| **CUDA Version** | CUDA 11.4 (JetPack 5.x) or CUDA 12.2 (JetPack 6.x) | `nvcc --version` |
| **Python Version** | Python 3.8 / 3.10 (Linux standard) | `python3 --version` |
| **Storage** | 128GB M.2 NVMe SSD (minimum 25GB free) | `df -h /` |
| **Power Mode** | 15W 6-core (Mode 0: Maximum Performance) | `sudo nvpmodel -q` |

---

## 2. Power Mode Configuration

The Jetson Orin Nano should be configured to run in maximum performance 15W mode to ensure predictable inference latencies:

```bash
# Set 15W 6-core power mode
sudo nvpmodel -m 0

# Enable jetson_clocks to lock clock frequencies for maximum throughput
sudo jetson_clocks
```

---

## 3. Waveshare 7-inch HDMI Touchscreen (1024x600) Setup

1. **Connect Cables**:
   - Connect HDMI from Jetson to Waveshare HDMI port.
   - Connect Micro-USB from Waveshare Touch port to Jetson USB 3.0 port.
2. **Resolution Configuration**:
   If the display boots into a default 720p/1080p mode and appears squished or offset, configure `xrandr`:
   ```bash
   # Identify connected display name (e.g. HDMI-0)
   xrandr

   # Add 1024x600 mode if missing
   cvt 1024 600 60
   xrandr --newmode "1024x600_60.00" 49.00 1024 1072 1168 1312 600 603 613 624 -hsync +vsync
   xrandr --addmode HDMI-0 "1024x600_60.00"
   xrandr --output HDMI-0 --mode "1024x600_60.00"
   ```
3. **Touch Input Calibration**:
   The touch interface presents as a standard USB HID digitizer. Test touch input:
   ```bash
   sudo apt-get install -y xinput-calibrator
   xinput list
   ```

---

## 4. Audio Input & Output Configuration

The kiosk requires mono 16kHz microphone capture and clean audio playback without GUI blocking.

1. **Identify Audio Cards**:
   ```bash
   # List record devices
   arecord -l

   # List playback devices
   aplay -l
   ```
   Typical hardware layout:
   - USB Microphone / Arducam array: `hw:1,0` (or `plughw:1,0`)
   - 3.5mm Headphone Jack / USB DAC Speaker: `hw:0,0` (or `plughw:0,0`)

2. **Test Capture & Playback**:
   ```bash
   # Record 3-second test clip
   arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -d 3 test_mic.wav

   # Play back test clip
   aplay -D plughw:0,0 test_mic.wav
   ```

3. **Update `.env`**:
   Verify `AUDIO_INPUT_DEVICE` and `AUDIO_OUTPUT_DEVICE` in `.env` match your device IDs.

---

## 5. Camera Device Setup

1. **USB UVC Webcams**:
   ```bash
   v4l2-ctl --list-devices
   # Output will show /dev/video0 or /dev/video1
   ```
2. **CSI Camera (IMX219 / IMX477)**:
   Tested via Jetson GStreamer pipeline:
   ```bash
   gst-launch-1.0 nvarguscamerasrc sensor-id=0 ! 'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1' ! nvvidconv ! xvimagesink
   ```

---

## 6. Software & Python Environment Setup

```bash
# 1. Inspect hardware environment
./scripts/check_jetson.sh

# 2. Run automated installer
./scripts/install.sh

# 3. Activate Python venv
source venv/bin/activate

# 4. Install llama-cpp-python with CUDA support
# Pre-built wheel or compiled with CUDA flag
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --no-cache-dir

# 5. Download model weights
./scripts/download_models.sh

# 6. Ingest data & precompute embeddings
python scripts/build_rag.py

# 7. Execute complete offline test suite
./scripts/offline_test.sh
```

---

## 7. Systemd Automatic Kiosk Boot Setup

To make the Jetson boot directly into the Vyoma touchscreen interface without opening a terminal:

```bash
# 1. Copy service file
sudo cp systemd/vyoma.service /etc/systemd/system/

# 2. Reload daemon and enable autostart
sudo systemctl daemon-reload
sudo systemctl enable vyoma.service

# 3. Test starting the service immediately
sudo systemctl start vyoma.service

# 4. View kiosk logs
journalctl -u vyoma.service -f
```
