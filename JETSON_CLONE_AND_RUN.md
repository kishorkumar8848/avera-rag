# Jetson Orin Nano — Complete Clone & Run Guide

Follow these exact steps to run the **Vyoma Offline Medical AI Assistant** on your **NVIDIA Jetson Orin Nano 8GB** without errors.

---

## Step 1: Clone Repository on Jetson

Open a terminal on your Jetson Orin Nano and run:

```bash
cd ~
git clone https://github.com/kishorkumar8848/avera-rag.git
cd avera-rag
cp .env.example .env
```

> [!NOTE]
> The pre-computed 1,042-topic medical vector knowledge base (`indexes/medical_kb.db` and `indexes/faiss/index.faiss`) is **already included in the repo**. You do **not** need to wait for RAG embedding indexing on the Jetson!

---

## Step 2: Run Automated Environment Installer

Make scripts executable and run the setup script:

```bash
chmod +x scripts/*.sh
./scripts/install.sh
```

This script will:
- Install essential system libraries (`ffmpeg`, `portaudio19-dev`, `libasound2-dev`, `v4l-utils`).
- Create and configure Python virtual environment (`venv`).
- Install all Python dependencies from `requirements.txt`.
- Pre-cache NLTK tokenizers (`punkt`, `punkt_tab`) for offline Bhashini translation.

---

## Step 3: Transfer Model Weights

GitHub strictly enforces a 100MB file limit, so heavy model checkpoint binaries (`.bin`, `.onnx.data`, `.gguf`) are transferred directly to your Jetson:

### 3.1 Bhashini Speech & Translation Models
You need the local weights for `bhashini_models/`. Choose either method:

* **Method A — USB Flash Drive (Easiest)**:
  1. On your Windows laptop, copy the `bhashini_models` folder from `D:\avera-rag\bhashini_models` onto a USB drive.
  2. Plug the USB drive into your Jetson.
  3. Copy and merge the folder into your cloned repository:
     ```bash
     cp -r /media/$USER/<USB_NAME>/bhashini_models/* ~/avera-rag/bhashini_models/
     ```

* **Method B — Network Transfer via SCP**:
  From your Windows laptop (in PowerShell):
  ```powershell
  scp -r D:\avera-rag\bhashini_models orion@<jetson-ip>:~/avera-rag/
  ```

### 3.2 Download LLM & Embedding Models
On your Jetson, run the model setup script:

```bash
./scripts/download_models.sh
```

This will automatically:
- Download `qwen2.5-1.5b-instruct-q4_k_m.gguf` (1.1 GB) from Hugging Face into `models/`.
- Pre-cache `BAAI/bge-small-en-v1.5` embeddings locally.

---

## Step 4: Verify System & Run Tests

Activate the virtual environment and run the offline test suite:

```bash
source venv/bin/activate

# Inspect Jetson hardware, CUDA, audio, and camera
./scripts/check_jetson.sh

# Run the 18 automated unit tests
pytest
```

---

## Step 5: Start the Vyoma Kiosk Application

### Development / Windowed Mode (Testing)
```bash
source venv/bin/activate
python3 main.py
```

### Production Fullscreen Kiosk Mode (1024x600 Waveshare Touchscreen)
```bash
./run.sh
```

---

## Step 6: (Optional) Enable Automatic Boot on Startup

To make the Jetson automatically launch Vyoma when powered on:

```bash
sudo cp systemd/vyoma.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vyoma.service
sudo systemctl start vyoma.service
```

To view live logs:
```bash
journalctl -u vyoma.service -f
```
