# Model Specifications, Licenses & Checksums

This document catalogs every offline model used in the **Vyoma Offline Medical AI Assistant**, verifying its license, upstream source, SHA256 checksum, quantization format, and memory budget.

---

## 1. Complete Model Manifest

| Model | Task | Format / Quantization | Parameter Count | License | Upstream Source | Size on Disk | Active RAM Footprint |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen2.5-1.5B-Instruct** | Text LLM / Clinical Guidance | GGUF (`Q4_K_M`) | 1.54 Billion | Apache 2.0 | [Qwen / Alibaba](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF) | ~1.12 GB | ~1.20 GB |
| **Moondream 0.5B** | Vision Front-End (Non-diagnostic) | INT4 ONNX / PyTorch | 0.5 Billion | Apache 2.0 | [Vikhyat / Moondream](https://huggingface.co/vikhyat/moondream2) | ~490 MB | ~800 MB |
| **BGE-small-en-v1.5** | Dense RAG Embeddings | PyTorch / Safetensors | 33.5 Million | MIT | [BAAI](https://huggingface.co/BAAI/bge-small-en-v1.5) | ~133 MB | ~200 MB (CPU) |
| **Bhashini IndicConformer** | Offline ASR (Tamil / Hindi / Indic) | ONNX | ~110 Million | Open / AI4Bharat | [Bhashini / Suno Sutra](https://bhashini.gov.in) | ~420 MB | ~550 MB |
| **Bhashini IndicTrans2** | Offline NMT (Indic $\leftrightarrow$ English) | CTranslate2 INT8 | ~220 Million | CC-BY-4.0 | [AI4Bharat / Bhashini](https://github.com/AI4Bharat/IndicTrans2) | ~710 MB | ~650 MB |
| **Bhashini VITS TTS** | Offline Voice Synthesis | PyTorch / ONNX | ~80 Million | Open / AI4Bharat | [AI4Bharat / Bhashini](https://github.com/AI4Bharat) | ~260 MB | ~350 MB |

---

## 2. Cryptographic Checksums (SHA256)

Every binary model downloaded must match its verified cryptographic hash:

```
# Qwen2.5-1.5B-Instruct-Q4_K_M.gguf
SHA256: 7d6c7e3f890214a7e93433df7121287cba1b9d4f29a008892d19485e921d7b38

# BGE-small-en-v1.5 (model.safetensors)
SHA256: 8a7c29e71b2851cf27732adbf3122fa45e3f9a740449c2ba0f1c97a514d7a8e2

# bhashini_models.zip
SHA256: a14c330f81d11ebf7c9e09d13e904b772c803ff26390a19e2bb9705b766124cb
```

---

## 3. License Compliance & Redistribution Policy

- **Qwen2.5-1.5B-Instruct**: Distributed under the **Apache 2.0 License**. Permits commercial and non-commercial local execution, fine-tuning, and deployment.
- **Moondream 0.5B / 2B**: Distributed under the **Apache 2.0 License**.
- **BGE-small-en-v1.5**: Distributed under the **MIT License**.
- **Bhashini / AI4Bharat Speech Models**: Distributed under open academic and public-good licenses.
- **Strict Repository Rule**: No model weight binaries (`*.gguf`, `*.bin`, `*.safetensors`, `*.onnx`) are committed into the Git repository. All models are explicitly downloaded during `./scripts/download_models.sh` into `models/` (which is excluded in `.gitignore`).

---

## 4. Jetson 8GB Unified RAM Budget

```
+-------------------------------------------------------------+
|               JETSON ORIN NANO 8GB UNIFIED RAM              |
+-------------------------------------------------------------+
| Ubuntu OS + Display Server + Background daemons:   ~1.50 GB |
| Qwen2.5-1.5B Q4_K_M (CUDA offloaded):              ~1.20 GB |
| Moondream 0.5B INT4 (Active during camera mode):   ~0.80 GB |
| Bhashini Speech Stack (ASR / NMT / TTS):           ~1.50 GB |
| Embeddings (CPU) + SQLite FTS5 + FAISS:            ~0.35 GB |
| UI Framebuffer & Application Memory:               ~0.25 GB |
| Dynamic Headroom / Safety Buffer:                  ~2.40 GB |
+-------------------------------------------------------------+
| TOTAL RUNTIME PEAK: ~5.60 GB (Comfortably below 8GB ceiling)|
+-------------------------------------------------------------+
```

When switching from Camera mode to Speech mode, `ModelManager` can evict inactive Moondream tensors to keep total utilization below 5GB.
