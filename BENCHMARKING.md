# Benchmarking & Latency Budget Guide

This document defines the strict latency budgets, resource constraints, and benchmarking methodology for the **Vyoma Offline Medical AI Assistant** on NVIDIA Jetson Orin Nano 8GB.

---

## 1. Latency Budgets (10–15 Second Hard Requirement)

The kiosk must complete normal speech and camera interactions in **$\le 10–15$ seconds** end-to-end:

| Pipeline Stage | Target Latency Budget | Maximum Permissible | Optimization Lever |
| :--- | :--- | :--- | :--- |
| **VAD + ASR** | $\le 1.5$ sec | $3.0$ sec | Conformer ONNX / Faster-Whisper tiny FP16 |
| **NMT (Indic $\rightarrow$ En)** | $\le 0.4$ sec | $1.0$ sec | CTranslate2 INT8 (skipped if English) |
| **Hybrid RAG** | $\le 0.15$ sec | $0.5$ sec | SQLite FTS5 index + FAISS FlatIP (CPU) |
| **Moondream Vision** | $\le 1.8$ sec | $3.0$ sec | Resized to 640x480, INT4 quantization |
| **Qwen2.5-1.5B LLM** | $\le 2.2$ sec | $4.0$ sec | CUDA offloaded, max tokens $\le 250$, temp 0.15 |
| **NMT (En $\rightarrow$ Indic)** | $\le 0.4$ sec | $1.0$ sec | CTranslate2 INT8 (skipped if English) |
| **Bhashini TTS** | $\le 0.8$ sec | $2.0$ sec | Early sentence playback streaming |
| **Overall Speech Interaction** | **$\le 5.5$ sec** | **$\le 15.0$ sec** | Asynchronous worker pipelines |
| **Overall Camera Interaction** | **$\le 7.5$ sec** | **$\le 15.0$ sec** | 640x480 resolution downsampling |

---

## 2. Running the Full Benchmark Suite

```bash
# Run comprehensive 9-stage benchmark
python3 benchmark/benchmark_all.py
```

### Measured Stages:
1. `Embeddings`: Vector encoding time (BGE-small-en-v1.5).
2. `Hybrid RAG`: Combined FTS5 + FAISS + RRF query latency.
3. `Qwen2.5-1.5B`: Token generation latency and RAM footprint.
4. `Moondream 0.5B`: Structured observation extraction latency.
5. `Bhashini ASR`: Audio transcription WER and latency.
6. `Bhashini NMT`: Translation throughput.
7. `Bhashini TTS`: Audio synthesis duration.
8. `End-to-End Speech`: Complete audio-in to audio-out latency.
9. `End-to-End Multimodal`: Camera frame + speech to answer latency.

---

## 3. Telemetry Output & Logging

The benchmark records hardware metrics during every stage and exports:
- `benchmark/benchmark_results.json`
- `benchmark/benchmark_results.csv`

Fields captured:
```json
{
  "component": "Qwen2.5-1.5B LLM",
  "latency_ms": 2180.5,
  "budget_ms": 4000.0,
  "within_budget": true,
  "ram_used_mb": 4210.0,
  "ram_percent": 53.2,
  "cpu_percent": 24.5,
  "gpu_percent": 72.0,
  "temperature_c": 46.5,
  "power_mode": "15W"
}
```

---

## 4. Troubleshooting Latency Regressions

If total latency exceeds 15 seconds:
1. **Check Jetson Power Mode**:
   ```bash
   sudo nvpmodel -m 0
   sudo jetson_clocks
   ```
2. **Verify Camera Resolution**:
   Ensure images sent to Moondream are resized to 640x480. Never feed 1080p or 4K frames to the VLM.
3. **Verify LLM Token Budget**:
   Check `LLM_MAX_NEW_TOKENS=250` in `.env`. Higher token limits increase generation time linearly.
4. **Check CUDA Offload**:
   Verify `llama-cpp-python` was compiled with `CUBLAS=on` so layers execute on GPU rather than CPU.
