#!/usr/bin/env python3
"""
Vyoma Offline Medical AI Assistant - Comprehensive Edge AI Benchmark Suite.
Measures latency, RAM usage, CPU utilization, GPU load, and temperature across:
1. Qwen2.5-1.5B LLM
2. Moondream 0.5B VLM
3. Bhashini ASR
4. Bhashini NMT
5. Bhashini TTS
6. BGE-small-en-v1.5 Embeddings
7. Hybrid RAG (SQLite FTS5 + FAISS)
8. Complete Speech Pipeline (End-to-End)
9. Complete Camera + Speech Multimodal Pipeline (End-to-End)
Outputs results in both JSON and CSV formats.
"""

from __future__ import annotations
import sys
import os
import time
import json
import csv
from pathlib import Path
from typing import Dict, Any, List
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.core.logging import logger
from app.hardware.monitor import monitor
from app.hardware.jetson_detector import JetsonDetector
from app.models.qwen_backend import qwen_backend
from app.models.moondream_backend import moondream_backend
from app.models.bhashini_asr import asr_service
from app.models.bhashini_nmt import nmt_service
from app.models.bhashini_tts import tts_service
from app.rag.embeddings import EmbeddingEngine
from app.rag.hybrid_retriever import HybridRetriever


class VyomaBenchmarker:
    def __init__(self):
        self.retriever = HybridRetriever()
        self.embedding_engine = EmbeddingEngine()
        monitor.start()

    def _measure_resource_delta(self, fn, *args, **kwargs) -> Tuple_Res:
        """Executes function and measures elapsed time, memory delta, and hardware telemetry."""
        stats_before = monitor.get_stats()
        t0 = time.time()

        res = fn(*args, **kwargs)

        elapsed_ms = (time.time() - t0) * 1000.0
        stats_after = monitor.get_stats()

        metrics = {
            "latency_ms": round(elapsed_ms, 2),
            "ram_used_mb": stats_after.get("ram_used_mb", 0.0),
            "ram_percent": stats_after.get("ram_percent", 0.0),
            "cpu_percent": stats_after.get("cpu_percent", 0.0),
            "gpu_percent": stats_after.get("gpu_percent", 0.0),
            "temperature_c": stats_after.get("temperature_c", None),
            "power_mode": stats_after.get("power_mode", "Standard")
        }
        return res, metrics

    def benchmark_all(self) -> List[Dict[str, Any]]:
        print("========================================================================")
        print("      Vyoma Offline Medical AI Assistant - Benchmark Suite              ")
        print("========================================================================")

        results = []

        # 1. Benchmark Embeddings
        print("\n[1/9] Benchmarking English Embeddings (BGE-small-en-v1.5)...")
        sample_query = "What are the common symptoms and treatment guidelines for dengue fever?"
        _, m_emb = self._measure_resource_delta(self.embedding_engine.encode_text, sample_query)
        m_emb["component"] = "Embeddings (Query Encode)"
        m_emb["budget_ms"] = 100.0
        m_emb["within_budget"] = m_emb["latency_ms"] <= 100.0
        results.append(m_emb)
        print(f"  Latency: {m_emb['latency_ms']}ms | RAM: {m_emb['ram_used_mb']}MB")

        # 2. Benchmark Hybrid RAG
        print("\n[2/9] Benchmarking Hybrid RAG (SQLite FTS5 + FAISS)...")
        _, m_rag = self._measure_resource_delta(self.retriever.retrieve, sample_query, top_k=5)
        m_rag["component"] = "Hybrid RAG Retrieval"
        m_rag["budget_ms"] = settings.BUDGET_RAG_SEC * 1000.0
        m_rag["within_budget"] = m_rag["latency_ms"] <= m_rag["budget_ms"]
        results.append(m_rag)
        print(f"  Latency: {m_rag['latency_ms']}ms | Budget: {m_rag['budget_ms']}ms")

        # 3. Benchmark Qwen2.5-1.5B LLM
        print("\n[3/9] Benchmarking Qwen2.5-1.5B-Instruct Generation...")
        mock_ctx = [{
            "title": "Malaria Treatment Guideline",
            "summary": "Administer Paracetamol 500mg for fever. Maintain oral hydration. Conduct blood smear or RDT.",
            "citation": "MoHFW Clinical Protocol"
        }]
        _, m_qwen = self._measure_resource_delta(
            qwen_backend.generate_clinical_guidance,
            query="High fever and shivering after forest travel",
            retrieved_context=mock_ctx
        )
        m_qwen["component"] = "Qwen2.5-1.5B LLM"
        m_qwen["budget_ms"] = settings.BUDGET_LLM_SEC * 1000.0
        m_qwen["within_budget"] = m_qwen["latency_ms"] <= m_qwen["budget_ms"]
        results.append(m_qwen)
        print(f"  Latency: {m_qwen['latency_ms']}ms | Budget: {m_qwen['budget_ms']}ms")

        # 4. Benchmark Moondream Vision
        print("\n[4/9] Benchmarking Moondream 0.5B INT4 Structured Vision...")
        dummy_img = Image.new("RGB", (640, 480), color=(180, 50, 50))
        _, m_vlm = self._measure_resource_delta(moondream_backend.analyze_image, dummy_img)
        m_vlm["component"] = "Moondream 0.5B Vision"
        m_vlm["budget_ms"] = settings.BUDGET_VISION_SEC * 1000.0
        m_vlm["within_budget"] = m_vlm["latency_ms"] <= m_vlm["budget_ms"]
        results.append(m_vlm)
        print(f"  Latency: {m_vlm['latency_ms']}ms | Budget: {m_vlm['budget_ms']}ms")

        # 5. Benchmark Bhashini ASR
        print("\n[5/9] Benchmarking Bhashini ASR...")
        mock_audio = b"\x00" * 32000
        _, m_asr = self._measure_resource_delta(asr_service.transcribe, mock_audio, language="ta")
        m_asr["component"] = "Bhashini ASR"
        m_asr["budget_ms"] = settings.BUDGET_ASR_SEC * 1000.0
        m_asr["within_budget"] = m_asr["latency_ms"] <= m_asr["budget_ms"]
        results.append(m_asr)
        print(f"  Latency: {m_asr['latency_ms']}ms | Budget: {m_asr['budget_ms']}ms")

        # 6. Benchmark Bhashini NMT
        print("\n[6/9] Benchmarking Bhashini NMT (CTranslate2 INT8)...")
        _, m_nmt = self._measure_resource_delta(nmt_service.translate_to_english, "எனக்கு இரண்டு நாட்களாக கடுமையான காய்ச்சல் உள்ளது", "ta")
        m_nmt["component"] = "Bhashini NMT"
        m_nmt["budget_ms"] = settings.BUDGET_NMT_SEC * 1000.0
        m_nmt["within_budget"] = m_nmt["latency_ms"] <= m_nmt["budget_ms"]
        results.append(m_nmt)
        print(f"  Latency: {m_nmt['latency_ms']}ms | Budget: {m_nmt['budget_ms']}ms")

        # 7. Benchmark Bhashini TTS
        print("\n[7/9] Benchmarking Bhashini TTS Synthesis...")
        _, m_tts = self._measure_resource_delta(tts_service.synthesize, "Please drink clean fluids and rest.", "en")
        m_tts["component"] = "Bhashini TTS"
        m_tts["budget_ms"] = settings.BUDGET_TTS_SEC * 1000.0
        m_tts["within_budget"] = m_tts["latency_ms"] <= m_tts["budget_ms"]
        results.append(m_tts)
        print(f"  Latency: {m_tts['latency_ms']}ms | Budget: {m_tts['budget_ms']}ms")

        # 8. Benchmark End-to-End Speech Pipeline
        print("\n[8/9] Benchmarking Full Speech Pipeline (E2E)...")
        def run_speech_e2e():
            txt, _, _ = asr_service.transcribe(mock_audio, language="en")
            eng, _ = nmt_service.translate_to_english(txt, "en")
            docs = self.retriever.retrieve(eng, top_k=3)
            schema, _ = qwen_backend.generate_clinical_guidance(eng, docs)
            out_txt, _ = nmt_service.translate_from_english(schema.summary, "en")
            tts_service.synthesize(out_txt, "en")
        _, m_sp_e2e = self._measure_resource_delta(run_speech_e2e)
        m_sp_e2e["component"] = "Full Speech Pipeline (E2E)"
        m_sp_e2e["budget_ms"] = settings.BUDGET_TOTAL_SEC * 1000.0
        m_sp_e2e["within_budget"] = m_sp_e2e["latency_ms"] <= m_sp_e2e["budget_ms"]
        results.append(m_sp_e2e)
        print(f"  Total Speech E2E Latency: {m_sp_e2e['latency_ms']}ms (Target <= 15,000ms)")

        # 9. Benchmark End-to-End Multimodal Pipeline (Camera + Speech)
        print("\n[9/9] Benchmarking Full Multimodal Pipeline (E2E Camera + Speech)...")
        def run_camera_e2e():
            vis = moondream_backend.analyze_image(dummy_img)
            obs = vis.get("observations", [])
            txt, _, _ = asr_service.transcribe(mock_audio, language="en")
            combined = f"{txt} (Visuals: {', '.join(obs)})"
            docs = self.retriever.retrieve(combined, top_k=3)
            schema, _ = qwen_backend.generate_clinical_guidance(combined, docs, visual_observations=obs)
            tts_service.synthesize(schema.summary, "en")
        _, m_cam_e2e = self._measure_resource_delta(run_camera_e2e)
        m_cam_e2e["component"] = "Full Multimodal Pipeline (E2E)"
        m_cam_e2e["budget_ms"] = settings.BUDGET_TOTAL_SEC * 1000.0
        m_cam_e2e["within_budget"] = m_cam_e2e["latency_ms"] <= m_cam_e2e["budget_ms"]
        results.append(m_cam_e2e)
        print(f"  Total Multimodal E2E Latency: {m_cam_e2e['latency_ms']}ms (Target <= 15,000ms)")

        # Export Reports
        self._export_reports(results)
        return results

    def _export_reports(self, results: List[Dict[str, Any]]):
        benchmarks_dir = settings.resolve_path("benchmark")
        benchmarks_dir.mkdir(parents=True, exist_ok=True)

        json_path = benchmarks_dir / "benchmark_results.json"
        csv_path = benchmarks_dir / "benchmark_results.csv"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        fieldnames = ["component", "latency_ms", "budget_ms", "within_budget", "ram_used_mb", "ram_percent", "cpu_percent", "gpu_percent", "temperature_c", "power_mode"]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                row = {k: r.get(k, "") for k in fieldnames}
                writer.writerow(row)

        print("\n========================================================================")
        print(f"[SUCCESS] Benchmark report written to {json_path}")
        print(f"[SUCCESS] Benchmark CSV written to {csv_path}")
        print("========================================================================")


Tuple_Res = tuple[Any, Dict[str, Any]]


if __name__ == "__main__":
    benchmarker = VyomaBenchmarker()
    benchmarker.benchmark_all()
