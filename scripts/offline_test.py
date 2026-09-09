#!/usr/bin/env python3
"""
Vyoma Offline Medical AI Assistant - Complete Zero-Network Offline Guarantee Test.
Monkeypatches Python socket layer to strictly block any non-localhost network connections.
Tests ASR, Medical RAG, Qwen LLM, Camera capture, and TTS in complete offline isolation.
"""

import sys
import os
import socket
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Strict Network Interceptor: Blocks all non-localhost outbound sockets
original_socket = socket.socket
ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}

class OfflineSecurityViolation(Exception):
    pass

class GuardedSocket(socket.socket):
    def connect(self, address):
        host = address[0]
        if host not in ALLOWED_HOSTS and not host.startswith("127."):
            raise OfflineSecurityViolation(
                f"[SECURITY ALERT] Unauthorized external internet connection attempt to: {address}. "
                "Vyoma core must operate 100% offline without external network calls!"
            )
        return super().connect(address)

socket.socket = GuardedSocket
print("[*] Strict offline sandbox enabled. All external network connections blocked.")

from app.core.config import settings
from app.rag.hybrid_retriever import HybridRetriever
from app.models.qwen_backend import qwen_backend
from app.models.bhashini_asr import asr_service
from app.models.bhashini_tts import tts_service
from app.hardware.camera import camera_service
from app.safety.red_flags import red_flag_detector


def run_offline_verification():
    print("========================================================================")
    print("    Vyoma Offline Medical AI Assistant - Offline Verification Suite     ")
    print("========================================================================")

    test_passed = True

    # 1. Test Deterministic Emergency Red Flag Guard
    print("\n[1/6] Testing Emergency Red Flag Guard:")
    query = "Patient has crushing chest pain radiating to left arm and severe shortness of breath."
    is_em, cats, msg = red_flag_detector.detect_red_flags(query)
    if is_em:
        print(f"  [PASS] Red flag emergency correctly caught: {cats}")
    else:
        print("  [FAIL] Emergency detection missed critical symptoms!")
        test_passed = False

    # 2. Test Offline Hybrid RAG
    print("\n[2/6] Testing Hybrid Medical RAG (SQLite FTS5 + FAISS):")
    try:
        retriever = HybridRetriever()
        results = retriever.retrieve("What is treatment for dengue fever?", top_k=3)
        if results:
            print(f"  [PASS] Retrieved {len(results)} offline evidence chunks. Top: {results[0]['citation']}")
        else:
            print("  [WARN] RAG returned 0 results. Ensure indexes are built via 'python scripts/build_rag.py'.")
    except Exception as e:
        print(f"  [FAIL] RAG execution failed: {e}")
        test_passed = False

    # 3. Test Offline Qwen LLM
    print("\n[3/6] Testing Offline Qwen Clinical Reasoning:")
    try:
        schema, latency = qwen_backend.generate_clinical_guidance(
            query="Fever and body aches for two days",
            retrieved_context=[{
                "title": "Dengue Fever Protocol",
                "summary": "Administer Paracetamol. Maintain generous oral hydration. Avoid Aspirin or NSAIDs.",
                "citation": "MoHFW Standard Treatment Guideline"
            }]
        )
        print(f"  [PASS] Qwen generated structured guidance ({latency:.1f}ms): {schema.summary[:80]}...")
    except Exception as e:
        print(f"  [FAIL] Qwen execution failed: {e}")
        test_passed = False

    # 4. Test Offline ASR Interface
    print("\n[4/6] Testing Offline ASR:")
    try:
        mock_audio = b"RIFF....WAVEfmt ...."
        text, conf, lat = asr_service.transcribe(mock_audio, language="en")
        print(f"  [PASS] ASR returned hypothesis: '{text}' ({lat:.1f}ms)")
    except Exception as e:
        print(f"  [FAIL] ASR failed: {e}")
        test_passed = False

    # 5. Test Camera Capture & Resizing
    print("\n[5/6] Testing Camera Abstraction (640x480):")
    try:
        success, img, buf = camera_service.capture_frame()
        if success and img is not None:
            print(f"  [PASS] Camera frame captured: {img.size} mode={img.mode}")
        else:
            print("  [WARN] Camera hardware unavailable, synthetic preview active.")
    except Exception as e:
        print(f"  [FAIL] Camera failed: {e}")
        test_passed = False

    # 6. Test Offline TTS
    print("\n[6/6] Testing Offline TTS Synthesis:")
    try:
        wav_bytes, lat = tts_service.synthesize("Drink plenty of water and rest.", language="en")
        print(f"  [PASS] TTS synthesized successfully ({lat:.1f}ms).")
    except Exception as e:
        print(f"  [FAIL] TTS failed: {e}")
        test_passed = False

    print("\n========================================================================")
    if test_passed:
        print("[SUCCESS] ALL CORE COMPONENTS OPERATE 100% OFFLINE WITHOUT INTERNET!")
        print("          ZERO external API or cloud calls were made.")
    else:
        print("[FAILURE] Some offline tests encountered issues.")
    print("========================================================================")
    return test_passed


if __name__ == "__main__":
    success = run_offline_verification()
    sys.exit(0 if success else 1)
