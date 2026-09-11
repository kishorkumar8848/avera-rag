import os
import io
import time
import threading
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from app.core.config import settings
from app.core.logging import logger

try:
    import torch
    import scipy.io.wavfile
    from transformers import VitsModel, AutoTokenizer
    HAS_VITS = True
except ImportError:
    HAS_VITS = False


MMS_MODEL_MAP = {
    "ta": "facebook/mms-tts-tam",
    "hi": "facebook/mms-tts-hin",
    "gu": "facebook/mms-tts-guj",
    "en": "facebook/mms-tts-eng",
    "te": "facebook/mms-tts-tel",
    "kn": "facebook/mms-tts-kan",
    "ml": "facebook/mms-tts-mal",
    "bn": "facebook/mms-tts-ben",
    "mr": "facebook/mms-tts-mar"
}


class MMSTTSService:
    """
    Offline Meta MMS-TTS (VITS Neural Architecture) Engine.
    Delivers studio-quality, lifelike human speech across Indic languages
    (Tamil, Hindi, Gujarati, English, etc.) without robotic metallic artifacts.
    Runs 100% offline on NVIDIA Jetson edge hardware.
    """

    def __init__(self):
        self.models_dir = settings.resolve_path("models/mms_tts")
        os.makedirs(self.models_dir, exist_ok=True)
        self.active_lang: Optional[str] = None
        self.active_model = None
        self.active_tokenizer = None
        self._lock = threading.Lock()
        self.device = "cuda" if (HAS_VITS and torch.cuda.is_available() and os.environ.get("FORCE_CPU", "0") != "1") else "cpu"

    @property
    def is_available(self) -> bool:
        return HAS_VITS

    def _load_language_model(self, lang: str) -> bool:
        """Loads or switches the active VITS model on demand, maintaining low memory usage."""
        if not HAS_VITS:
            return False

        if self.active_lang == lang and self.active_model is not None:
            return True

        model_id = MMS_MODEL_MAP.get(lang)
        if not model_id:
            logger.debug(f"No MMS-TTS model mapped for language: '{lang}'")
            return False

        lang_cache_dir = self.models_dir / lang
        os.makedirs(lang_cache_dir, exist_ok=True)

        try:
            logger.info(f"Loading Neural MMS-TTS model for '{lang}' ({model_id}) on {self.device}...")
            # Release previous model from GPU memory
            if self.active_model is not None:
                del self.active_model
                del self.active_tokenizer
                self.active_model = None
                self.active_tokenizer = None
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

            # Attempt loading from local offline cache or model identifier
            tokenizer = AutoTokenizer.from_pretrained(str(lang_cache_dir) if (lang_cache_dir / "tokenizer_config.json").exists() else model_id, cache_dir=str(lang_cache_dir))
            model = VitsModel.from_pretrained(str(lang_cache_dir) if (lang_cache_dir / "config.json").exists() else model_id, cache_dir=str(lang_cache_dir))

            model = model.to(self.device)
            model.eval()

            self.active_model = model
            self.active_tokenizer = tokenizer
            self.active_lang = lang
            logger.info(f"Neural MMS-TTS model for '{lang}' loaded successfully on {self.device}.")
            return True
        except Exception as e:
            logger.warning(f"Failed to load Neural MMS-TTS for '{lang}': {e}")
            self.active_model = None
            self.active_tokenizer = None
            self.active_lang = None
            return False

    def synthesize(self, text: str, language: str = "en") -> Tuple[Optional[bytes], float]:
        """
        Synthesizes text into 16-bit PCM WAV bytes using offline VITS neural network.
        Returns: (wav_bytes: Optional[bytes], latency_ms: float)
        """
        if not HAS_VITS or not text.strip():
            return None, 0.0

        lang = language.lower().strip()
        start_time = time.time()

        with self._lock:
            if not self._load_language_model(lang):
                return None, 0.0

            try:
                inputs = self.active_tokenizer(text, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                with torch.no_grad():
                    output = self.active_model(**inputs).waveform

                audio_data = output.cpu().float().numpy().squeeze()
                sample_rate = self.active_model.config.sampling_rate

                # Convert float32 [-1, 1] to int16 PCM
                import numpy as np
                audio_int16 = np.clip(audio_data * 32767.0, -32768, 32767).astype(np.int16)

                wav_buf = io.BytesIO()
                scipy.io.wavfile.write(wav_buf, rate=sample_rate, data=audio_int16)
                wav_bytes = wav_buf.getvalue()

                latency_ms = (time.time() - start_time) * 1000.0
                logger.info(f"Neural MMS-TTS synthesized {len(wav_bytes)} bytes for '{lang}' ({latency_ms:.1f}ms).")
                return wav_bytes, latency_ms
            except Exception as e:
                logger.error(f"Neural MMS-TTS synthesis failed for '{lang}': {e}")
                return None, 0.0


mms_tts_service = MMSTTSService()
