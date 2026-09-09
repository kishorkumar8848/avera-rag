# Vyoma Offline Medical AI Assistant

**Vyoma** is an offline-first Edge AI clinical decision support and frontline health assistant engineered specifically for the **NVIDIA Jetson Orin Nano 8GB** paired with a **Waveshare 7-inch HDMI touchscreen (1024x600)**, USB touchscreen, camera, microphone, and speaker.

Designed for Primary Health Centres (PHCs), sub-centres, and frontline health workers (ASHAs/ANMs), the entire system operates **100% locally on-device without internet connectivity, cloud APIs, or external inference servers**.

---

## Key Capabilities

1. **100% Offline Edge Architecture**:
   - Zero runtime cloud calls.
   - Zero external API dependencies for ASR, NMT, LLM, VLM, or RAG.
2. **Text Clinical LLM**:
   - **Qwen2.5-1.5B-Instruct** quantized in `Q4_K_M` GGUF format executed with CUDA offloading via `llama.cpp` (Ollama fallback compatibility).
   - Constrained generation budget ($\le 250$ tokens, temp 0.15, top-p 0.85) for concise speech-friendly responses.
   - Grounded strictly on verified clinical protocols across 19 safety rules.
3. **Structured Vision Front-End (VLM)**:
   - **Moondream 0.5B INT4** vision model extracting structured visual observations (redness, lesions, swelling).
   - **Strict Medical Safety**: Never produces standalone disease diagnoses from images. Combines visual findings with patient speech before clinical retrieval.
4. **Offline Speech Stack (Bhashini)**:
   - **Bhashini ASR**: Offline Conformer ONNX models for Indian languages (Tamil, Hindi, English, etc.).
   - **Bhashini NMT**: CTranslate2 INT8 neural machine translation (Indic $\rightarrow$ English clinical query; English $\rightarrow$ Indic guidance). Skips NMT for English.
   - **Bhashini TTS**: Sentence-level streaming speech synthesis with asynchronous audio playback.
5. **Two-Layer Hybrid Medical RAG**:
   - **Layer 1 (National Health Protocols)**: Official Ministry of Health and Family Welfare (MoHFW) Standard Treatment Guidelines, NHM, NVBDCP, and ASHA job aids.
   - **Layer 2 (Health Education)**: National Library of Medicine (NLM) MedlinePlus XML dataset (1,017 English health topics).
   - **Hybrid Engine**: Embedded **SQLite FTS5 (BM25)** full-text search + **FAISS** inner-product dense vector search with **Reciprocal Rank Fusion (RRF)**.
   - Precomputed embeddings using **BGE-small-en-v1.5** on CPU.
6. **Deterministic Medical Safety**:
   - Hardcoded regex and keyword emergency triage (`red_flags.py`) detecting cardiac arrest, acute dyspnea, stroke, severe bleeding, anaphylaxis, seizures, and snakebite envenomation.
   - Immediate escalation to emergency services (108 / 112) without speculative drug or treatment recommendations.
   - Pydantic structured JSON schema validation (`validator.py`) with 1x prompt self-correction retry.
7. **Native 1024x600 Touchscreen Kiosk UI**:
   - Built on **PySide6 / Qt6** optimized for 60–80px touch targets, high contrast dark theme, and zero main-thread UI blocking (`QThreadPool` worker architecture).
   - Screen Flow: **Language Selection** $\rightarrow$ **Module Selection** $\rightarrow$ **Speech Assistant** OR **Speech + Camera**.

---

## Hardware Target Specifications

| Component | Specification |
| :--- | :--- |
| **Compute Board** | NVIDIA Jetson Orin Nano Developer Kit (8GB Unified LPDDR5) |
| **Storage** | 128GB NVMe M.2 SSD / High-Endurance microSD |
| **Display** | Waveshare 7-inch HDMI Touchscreen (1024x600 resolution) |
| **Touch Input** | USB Capacitive Touch Controller |
| **Camera** | USB UVC Camera or IMX219 / IMX477 CSI Camera |
| **Audio Input** | USB Microphone / Arducam array (16kHz mono) |
| **Audio Output** | 3.5mm Headphone Jack / USB DAC Speaker |
| **OS / Environment** | JetPack 5.1.x / 6.x (Ubuntu 20.04/22.04 LTS, CUDA 11.4/12.x) |

---

## Quick Start (Jetson Deployment Workflow)

```bash
# 1. Clone repository onto Jetson Orin Nano
git clone https://github.com/your-org/vyoma-medical-ai.git
cd vyoma-medical-ai

# 2. Inspect Jetson hardware, CUDA, and audio/video devices
./scripts/check_jetson.sh

# 3. Install Python environment and system dependencies
./scripts/install.sh

# 4. Download and verify offline model weights (explicit, verifiable)
./scripts/download_models.sh

# 5. Precompute embeddings and build hybrid RAG database
python3 scripts/build_rag.py

# 6. Verify 100% offline functionality (zero internet guarantee)
./scripts/offline_test.sh

# 7. Launch Kiosk Application
./run.sh
```

For diagnostic developer mode with live telemetry:
```bash
./run_dev.sh
```

---

## Project Architecture

```
avera-rag/
├── app/
│   ├── core/           # Config, settings, and structured JSON telemetry (PII-free)
│   ├── hardware/       # Jetson detection, CPU/GPU monitor, camera & in-memory audio
│   ├── models/         # ModelManager, Qwen2.5 llama.cpp, Moondream, Bhashini speech
│   ├── rag/            # Schemas, MedlinePlus XML ingest, Indian protocols, FAISS/FTS5
│   ├── safety/         # Deterministic red flags, JSON validation, clinical policy
│   └── ui/             # Native PySide6 kiosk UI (1024x600 touch screens & workers)
├── benchmark/          # Comprehensive 9-point benchmark suite (JSON & CSV reports)
├── data/
│   ├── medlineplus/    # MedlinePlus Health Topics XML dataset
│   ├── indian_protocols/# MoHFW Standard Treatment Guidelines & ASHA job aids
│   └── golden_qa.json  # Quantitative RAG evaluation dataset
├── indexes/            # Precomputed SQLite FTS5 database & FAISS vector store
├── models/             # Local model weight binaries (gitignored)
├── scripts/            # Check, install, download, build, and offline verification scripts
├── systemd/            # Auto-boot systemd kiosk service
└── tests/              # Pytest automated test suite
```

---

## Acceptance Test Checklist

- [x] Application boots into 1024x600 touchscreen UI.
- [x] Language selection across 10 Indian languages.
- [x] Speech module operates with push-to-talk (no keyboard).
- [x] Bhashini ASR, NMT, and TTS operate completely offline.
- [x] Qwen2.5-1.5B executes locally with short TTS generation budget.
- [x] Dual-layer RAG indexes MedlinePlus + official Indian protocols.
- [x] Multimodal camera captures 640x480 frames; Moondream extracts structured non-diagnostic observations.
- [x] Deterministic emergency red-flag triage overrides ungrounded speculative recommendations.
- [x] Verified zero internet connectivity during runtime.
- [x] Unified memory usage stays safely below the 8GB Jetson ceiling.
