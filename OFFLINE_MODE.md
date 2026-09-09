# Complete Offline Mode Guarantee & Verification

**Vyoma** is architected to operate with **zero internet connectivity** during runtime.

---

## 1. Zero Cloud Runtime Guarantee

After initial model installation and RAG index building, the application enforces:
- **NO CLOUD LLM** (Qwen runs on-device via `llama.cpp` CUDA / Ollama).
- **NO CLOUD VLM** (Moondream runs on-device).
- **NO CLOUD ASR** (Bhashini IndicConformer runs on-device).
- **NO CLOUD NMT** (Bhashini CTranslate2 INT8 runs on-device).
- **NO CLOUD TTS** (Bhashini VITS runs on-device).
- **NO CLOUD RAG** (SQLite FTS5 + FAISS are local embedded files).
- **NO EXTERNAL TELEMETRY** (Telemetry is written locally to `logs/vyoma_telemetry.jsonl` without PII).

Internet is strictly permitted only during an explicit update command executed by an administrator:
```bash
./scripts/download_models.sh
```

---

## 2. Verification Procedure

Run the automated offline validation suite:

```bash
# Option A: Run inside isolated Linux network namespace (if root)
sudo unshare -n python3 scripts/offline_test.py

# Option B: Run standard offline test with Python socket interceptor
./scripts/offline_test.sh
```

### What `offline_test.py` Does:
1. **Network Interceptor**: Monkeypatches Python's `socket.socket.connect` to throw an immediate `OfflineSecurityViolation` if any process attempts an outbound connection to any IP other than `127.0.0.1` / `localhost`.
2. **End-to-End Pipeline Execution**:
   - Triggers Red Flag Emergency Detector.
   - Queries Hybrid RAG (SQLite FTS5 + FAISS).
   - Generates Qwen2.5-1.5B clinical guidance.
   - Runs ASR audio transcription.
   - Captures 640x480 camera frame.
   - Synthesizes TTS audio bytes.
3. **Audit**: Confirms that zero unauthorized network calls were made and all components functioned in pure offline isolation.

---

## 3. Physical Air-Gap Testing on Jetson Orin Nano

To verify physical air-gap performance on the hardware kiosk:

1. Disconnect Ethernet cable.
2. Turn off Wi-Fi on Jetson:
   ```bash
   sudo nmcli radio wifi off
   ```
3. Verify no IP routing:
   ```bash
   ping -c 1 8.8.8.8
   # Expected output: Network is unreachable
   ```
4. Launch the application:
   ```bash
   ./run.sh
   ```
5. Perform voice and camera tests. The system operates with full functionality.
