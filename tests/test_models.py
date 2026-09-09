import pytest
from PIL import Image
from app.models.manager import ModelManager
from app.models.qwen_backend import QwenBackend
from app.models.moondream_backend import MoondreamBackend
from app.models.bhashini_asr import ASRService
from app.models.bhashini_nmt import NMTService
from app.models.bhashini_tts import TTSService


def test_model_manager_memory_check():
    mgr = ModelManager()
    mem = mgr.memory_usage()
    assert "ram_total_gb" in mem
    assert "ram_available_gb" in mem
    assert mem["ram_total_gb"] > 0
    assert mgr.check_memory_headroom(required_mb=100.0) is True


def test_qwen_backend_generation():
    qwen = QwenBackend()
    context = [{
        "title": "Fever Management",
        "summary": "Keep patient hydrated with ORS. Administer Paracetamol 500mg. Rest.",
        "citation": "MoHFW Standard Treatment Guidelines"
    }]
    schema, latency = qwen.generate_clinical_guidance(
        query="High fever for two days",
        retrieved_context=context
    )
    assert schema is not None
    assert len(schema.summary) > 10
    assert len(schema.recommended_actions) > 0
    assert latency > 0.0


def test_moondream_vision_non_diagnostic():
    vlm = MoondreamBackend()
    img = Image.new("RGB", (640, 480), color=(200, 80, 80))
    result = vlm.analyze_image(img)
    assert "observations" in result
    assert "image_quality" in result
    assert "confidence" in result
    # Crucial safety rule: never outputs direct diagnostic assertions
    obs_text = " ".join(result["observations"]).lower()
    assert "you have" not in obs_text


def test_nmt_english_bypass():
    nmt = NMTService()
    # English queries must bypass NMT with 0ms latency
    text, lat = nmt.translate_to_english("Patient has mild headache", src_lang="en")
    assert text == "Patient has mild headache"
    assert lat == 0.0

    out, lat2 = nmt.translate_from_english("Rest in a quiet room", tgt_lang="en")
    assert out == "Rest in a quiet room"
    assert lat2 == 0.0


def test_tts_sentence_splitting():
    tts = TTSService()
    text = "Fever is elevated. Please drink fluids immediately! Watch for high temperature."
    sentences = tts.split_into_sentences(text)
    assert len(sentences) == 3
    assert sentences[0] == "Fever is elevated."
    assert sentences[1] == "Please drink fluids immediately!"
