# Troubleshooting & Diagnostic Guide

Common issues, diagnostic procedures, and resolutions for the **Vyoma Offline Medical AI Assistant** on NVIDIA Jetson Orin Nano.

---

## 1. Memory & OOM (Out of Memory) Protection

### Issue: System sluggishness or process killed (OOM-killer)
- **Root Cause**: Jetson Orin Nano has unified memory (8GB total shared between CPU and GPU). Loading multiple unquantized models simultaneously exhausts memory.
- **Resolution**:
  1. Verify quantized models are used:
     - Qwen2.5-1.5B must be `Q4_K_M` GGUF (~1.1GB).
     - Moondream must be `0.5B INT4` (~0.8GB).
  2. Enable ZRAM swap on Jetson:
     ```bash
     sudo apt-get install -y zram-config
     sudo systemctl start zram-config
     free -h
     ```
  3. `ModelManager` automatically unloads inactive models when RAM utilization crosses `MAX_RAM_PERCENT=85.0%`. You can force eviction via developer mode.

---

## 2. Audio Capture & Playback Issues

### Issue: `sounddevice.PortAudioError: Invalid number of channels` or `Device unavailable`
- **Root Cause**: Default ALSA device index changed upon USB reboot.
- **Resolution**:
  1. Identify current card numbers:
     ```bash
     arecord -l
     aplay -l
     ```
  2. Update `.env` with exact card string:
     ```ini
     AUDIO_INPUT_DEVICE="plughw:1,0"
     AUDIO_OUTPUT_DEVICE="plughw:0,0"
     ```
  3. Ensure user has audio permissions:
     ```bash
     sudo usermod -a -G audio $USER
     ```

### Issue: Microphone recording is completely silent
- **Resolution**: Adjust ALSA mixer gain:
  ```bash
  alsamixer
  # Select USB soundcard (F6), navigate to Capture, raise gain to 80%
  ```

---

## 3. Waveshare 7-inch HDMI Touchscreen (1024x600) Issues

### Issue: Display shows black borders or resolution is stretched
- **Root Cause**: Linux kernel EDID read default fallback for non-standard 1024x600 timings.
- **Resolution**: Add explicit 1024x600 mode using `xrandr`:
  ```bash
  cvt 1024 600 60
  xrandr --newmode "1024x600_60.00" 49.00 1024 1072 1168 1312 600 603 613 624 -hsync +vsync
  xrandr --addmode HDMI-0 "1024x600_60.00"
  xrandr --output HDMI-0 --mode "1024x600_60.00"
  ```

### Issue: Touch inputs are inverted or offset
- **Resolution**: Calibrate touch matrix with `xinput-calibrator`:
  ```bash
  sudo apt-get install -y xinput-calibrator
  xinput_calibrator
  ```

---

## 4. Camera Detection & Preview Failures

### Issue: `Camera capture failed` or `Cannot open /dev/video0`
- **Resolution**:
  1. Check connected video nodes:
     ```bash
     v4l2-ctl --list-devices
     ls -l /dev/video*
     ```
  2. Grant user video permissions:
     ```bash
     sudo usermod -a -G video $USER
     ```
  3. If using Raspberry Pi Camera V2 / IMX219 on CSI port:
     ```bash
     sudo /opt/nvidia/jetson-io/jetson-io.py
     # Enable CSI camera overlay and reboot
     ```

---

## 5. Bhashini Speech Stack Diagnostics

### Issue: ASR or NMT returns connection refused on localhost
- **Resolution**: Verify local Bhashini background services are active:
  ```bash
  # Check service status
  curl -s http://localhost:8001/status || echo "ASR down"
  curl -s http://localhost:8002/status || echo "NMT down"
  curl -s http://localhost:8003/status || echo "TTS down"

  # Restart bhashini service if using systemd
  sudo systemctl restart bhashini.service
  ```
  Vyoma includes automatic graceful fallbacks (Whisper tiny and pyttsx3) if local services are warming up.

---

## 6. Systemd Kiosk Autostart Issues

### Issue: Kiosk does not start on reboot
- **Resolution**:
  1. Check systemd service log:
     ```bash
     journalctl -u vyoma.service -n 50 -e
     ```
  2. Verify X11 display environment:
     Ensure `/etc/systemd/system/vyoma.service` contains `Environment="DISPLAY=:0"`.
  3. Verify file permissions:
     ```bash
     chmod +x run.sh
     chmod +x scripts/*.sh
     ```
