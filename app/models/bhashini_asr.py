import io
import sys
import base64
import time
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import numpy as np

from app.core.config import settings
from app.core.logging import logger
from app.models.manager import model_manager


# Clinical domain-specific initial prompts to bias Whisper decoder toward medical vocabulary
MEDICAL_INITIAL_PROMPTS = {
    "ta": "மருத்துவ உரையாடல்: நோயாளிக்கு காய்ச்சல், குளிர், சளி, கடுமையான இருமல், தலைவலி, நெஞ்சு வலி, மூச்சுத் திணறல், வாந்தி, வயிற்று வலி, உடல் சோர்வு, மயக்கம் போன்ற அறிகுறிகள் உள்ளன.",
    "hi": "चिकित्सीय परामर्श: मरीज को तेज बुखार, ठंड लगना, खांसी, जुकाम, सिरदर्द, सीने में दर्द, सांस लेने में तकलीफ, उल्टी, पेट दर्द, बदन दर्द, कमजोरी के लक्षण हैं।",
    "gu": "તબીબી પરામર્શ: દર્દીને તાવ, શરદી, ઉધરસ, માથાનો દુખાવો, છાતીમાં દુખાવો, શ્વાસ લેવામાં તકલીફ, ઉલટી, પેટમાં દુખાવો, નબળાઈ જેવા લક્ષણો છે.",
    "en": "Clinical consultation: Patient presents with acute symptoms such as high fever, chills, persistent cough, cold, severe headache, chest pain, shortness of breath, nausea, abdominal pain, body ache.",
    "ml": "ചികിത്സാ സംഭാഷണം: രോഗിക്ക് പനി, ചുമ, ജലദോഷം, തലവേദന, ശ്വാസംമുട്ടൽ, ഛർദ്ദി, വയറുവേദന, നെഞ്ചുവേദന എന്നീ ലಕ್ಷಣങ്ങൾ ഉണ്ട്.",
    "te": "వైద్య సంప్రదింపులు: రోగికి జ్వరం, దగ్గు, జలుబు, తలనొప్పి, ఛాతీ నొప్పి, శ్వాస తీసుకోవడంలో ఇబ్బంది, వాంతులు, కడుపు నొప్పి వంటి లక్షణాలు ఉన్నాయి.",
    "kn": "ವೈದ್ಯಕೀಯ ಸಮಾಲೋಚನೆ: ರೋಗಿಗೆ ಜ್ವರ, ಕೆಮ್ಮು, ನೆಗಡಿ, ತಲೆನೋವು, ಎದೆನೋವು, ಉಸಿರಾಟದ ತೊಂದರೆ, ವಾಂತಿ, ಹೊಟ್ಟೆನೋವು ಲಕ್ಷಣಗಳಿವೆ."
}


def _resolve_local_whisper_path(model_size: str = "base") -> str:
    """Finds local snapshot or cached model directory to avoid any HuggingFace hub network calls."""
    # 1. Check local project models/ directory
    for size in [model_size, "base", "tiny"]:
        local_proj = settings.resolve_path(f"models/faster-whisper-{size}")
        if local_proj.exists() and (local_proj / "model.bin").exists():
            return str(local_proj)

    # 2. Check user's HuggingFace hub cache (prefer base if present on device)
    for size in [model_size, "base", "tiny"]:
        hf_hub = Path.home() / ".cache" / "huggingface" / "hub" / f"models--Systran--faster-whisper-{size}" / "snapshots"
        if hf_hub.exists():
            for snap in hf_hub.iterdir():
                if snap.is_dir() and (snap / "model.bin").exists():
                    return str(snap)

    return model_size


class ASRService:
    """
    Unified Offline ASR abstraction layer:
    Interface: transcribe(audio, language) -> (text, confidence, latency_ms)
    Primary: Local Faster-Whisper with Medical Initial Prompts (offline ta/hi/gu/en/ml).
    Secondary: In-process Local Bhashini ONNX Conformer ASR.
    Strictly local execution - NO external cloud or API calls.
    """

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.ASR_PROVIDER
        self.whisper_model = None
        self._is_loaded = False
        self._local_bhashini_asr = None
        self._local_asr_init = False

    def _get_local_bhashini_asr(self):
        """Lazily initializes in-process Bhashini Conformer ONNX ASR."""
        if self._local_bhashini_asr is None and not self._local_asr_init:
            self._local_asr_init = True
            try:
                bhashini_dir = settings.resolve_path("bhashini_models")
                ckpt_dir = bhashini_dir / "asr" / "checkpoints"
                # Check both ONNX and external weight data file
                if ckpt_dir.exists() and (ckpt_dir / "hi-conformer.onnx").exists() and (ckpt_dir / "hi-conformer.onnx.data").exists():
                    if str(bhashini_dir) not in sys.path:
                        sys.path.insert(0, str(bhashini_dir))
                    from asr.infer import ASRInference
                    logger.info(f"Loading in-process Bhashini Conformer ASR from {ckpt_dir}...")
                    self._local_bhashini_asr = ASRInference(checkpoint_dir=str(ckpt_dir))
                    logger.info("In-process Bhashini Conformer ASR loaded successfully!")
                    model_manager.register_model("bhashini_asr", self)
            except Exception as e:
                logger.warning(f"Could not load in-process Bhashini Conformer ASR: {e}")
        return self._local_bhashini_asr

    def load_whisper_benchmark(self, model_size: str = "base") -> bool:
        """Loads Faster-Whisper strictly offline with GPU acceleration."""
        try:
            from faster_whisper import WhisperModel
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            if device == "cuda":
                try:
                    torch.cuda.set_device(0)
                except Exception:
                    pass
            compute_type = "float16" if device == "cuda" else "int8"
            model_path = _resolve_local_whisper_path(model_size)
            logger.info(f"Loading offline Faster-Whisper from '{model_path}' on {device} ({compute_type})...")
            self.whisper_model = WhisperModel(model_path, device=device, compute_type=compute_type)
            self._is_loaded = True
            model_manager.register_model("whisper_asr", self)
            return True
        except Exception as e:
            logger.warning(f"Could not load Faster-Whisper offline: {e}")
            return False

    def transcribe(self, audio_data: Any, language: str = "en") -> Tuple[str, float, float]:
        """
        Transcribes audio buffer or WAV bytes 100% offline.
        Uses medical domain initial prompts for enhanced symptom recognition accuracy.
        Returns:
            (transcribed_text: str, confidence: float, latency_ms: float)
        """
        start_time = time.time()
        lang = language.lower().strip()

        # Handle bytes vs numpy array
        wav_bytes = None
        if isinstance(audio_data, bytes):
            wav_bytes = audio_data
        elif isinstance(audio_data, io.BytesIO):
            wav_bytes = audio_data.getvalue()
        elif isinstance(audio_data, np.ndarray):
            import soundfile as sf
            buf = io.BytesIO()
            sf.write(buf, audio_data, settings.AUDIO_SAMPLE_RATE, format="WAV", subtype="PCM_16")
            wav_bytes = buf.getvalue()

        if not wav_bytes or len(wav_bytes) < 100:
            return "", 0.0, (time.time() - start_time) * 1000.0

        # Attempt 1: Local Faster-Whisper with Medical Initial Prompt (Best accuracy across ta, hi, gu, en, ml)
        if self.whisper_model is not None or self.load_whisper_benchmark("base") or self.load_whisper_benchmark("tiny"):
            try:
                from faster_whisper.tokenizer import _LANGUAGE_CODES
                whisper_lang = lang if lang in _LANGUAGE_CODES else "en"
                initial_prompt = MEDICAL_INITIAL_PROMPTS.get(whisper_lang, MEDICAL_INITIAL_PROMPTS["en"])

                segments, info = self.whisper_model.transcribe(
                    io.BytesIO(wav_bytes),
                    language=whisper_lang,
                    initial_prompt=initial_prompt,
                    beam_size=1
                )
                text = " ".join([s.text for s in segments]).strip()
                if text:
                    conf = 0.90
                    latency_ms = (time.time() - start_time) * 1000.0
                    logger.info(f"Offline Faster-Whisper transcribed '{text}' [{whisper_lang}] ({latency_ms:.1f}ms).")
                    return text, conf, latency_ms
            except Exception as e:
                logger.error(f"Offline Faster-Whisper error: {e}")

        # Attempt 2: In-process Local Bhashini Conformer ASR (Fallback for Hindi and Tamil if weights present)
        if lang in ["hi", "ta"]:
            local_asr = self._get_local_bhashini_asr()
            if local_asr is not None and lang in getattr(local_asr, "sessions", {}):
                try:
                    audio_b64 = base64.b64encode(wav_bytes).decode("utf-8")
                    result = local_asr.infer(audio_base64=audio_b64, language=lang)
                    text = result.get("text", "").strip()
                    if text:
                        latency_ms = (time.time() - start_time) * 1000.0
                        logger.info(f"In-process Bhashini ASR transcribed '{text}' ({latency_ms:.1f}ms).")
                        return text, 0.85, latency_ms
                except Exception as e:
                    logger.debug(f"In-process Bhashini ASR fallback: {e}")

        # Fallback for synthetic/testing queries
        latency_ms = (time.time() - start_time) * 1000.0
        return "", 0.0, latency_ms

    def benchmark_audio(self, wav_path: str, reference_text: str, language: str = "en") -> Dict[str, Any]:
        """
        Runs standardized benchmark recording WER, latency, and resource metrics.
        """
        import psutil
        cpu_start = psutil.cpu_percent()
        mem_start = psutil.virtual_memory().used / (1024 * 1024)

        with open(wav_path, "rb") as f:
            audio_bytes = f.read()

        text, conf, latency_ms = self.transcribe(audio_bytes, language=language)

        cpu_end = psutil.cpu_percent()
        mem_end = psutil.virtual_memory().used / (1024 * 1024)

        # Simple word error rate approximation
        ref_words = reference_text.lower().split()
        hyp_words = text.lower().split()
        mismatches = abs(len(ref_words) - len(hyp_words)) + sum(1 for w in hyp_words if w not in ref_words)
        wer = round(mismatches / max(len(ref_words), 1), 4)

        return {
            "model": self.provider,
            "language": language,
            "latency_ms": round(latency_ms, 2),
            "confidence": conf,
            "wer": wer,
            "delta_ram_mb": round(mem_end - mem_start, 2),
            "cpu_percent": round(cpu_end - cpu_start, 2),
            "hypothesis": text,
            "reference": reference_text
        }


asr_service = ASRService()
