import os
import re
import io
import time
import shutil
import tempfile
import threading
import subprocess
from typing import Optional, Callable, List, Tuple

from app.core.config import settings
from app.core.logging import logger
from app.hardware.audio import AudioPlayer


FLITE_VOICE_MAP = {
    "ta": "cmu_indic_tam_sdr.flitevox",
    "hi": "cmu_indic_hin_ab.flitevox",
    "te": "cmu_indic_tel_kpn.flitevox",
    "kn": "cmu_indic_kan_plv.flitevox",
    "bn": "cmu_indic_ben_rm.flitevox",
    "mr": "cmu_indic_mar_aup.flitevox",
    "gu": "cmu_indic_guj_ad.flitevox",
    "pa": "cmu_indic_pan_amp.flitevox",
    "en": "cmu_us_slt.flitevox"
}

ESPEAK_VOICE_MAP = {
    "ta": "ta",
    "hi": "hi",
    "te": "te",
    "kn": "kn",
    "ml": "ml",
    "bn": "bn",
    "mr": "mr",
    "gu": "gu",
    "pa": "pa",
    "en": "en-us"
}


class TTSService:
    """
    Multilingual Text-to-Speech (TTS) engine running 100% offline on Jetson Orin Nano:
    1. Local Bhashini Flite Engine (with native Indic .flitevox voices)
    2. Native Linux espeak-ng / espeak (offline multilingual: ta, hi, te, kn, ml, en)
    3. Local pyttsx3 offline engine (Windows SAPI5 / Linux espeak)
    4. Clean valid PCM WAV buffer (failsafe offline audio synthesis)
    Strictly local execution - ZERO cloud or external API calls.
    """

    def __init__(self):
        self.audio_player = AudioPlayer()
        self._is_speaking = False
        self._lock = threading.Lock()
        self._flite_bin = self._find_flite_bin()
        self._flite_voices_dir = self._find_flite_voices_dir()
        self._espeak_bin = shutil.which("espeak-ng") or shutil.which("espeak") or self._find_system_espeak()

    def _find_flite_bin(self) -> Optional[str]:
        """Locates local or system flite binary."""
        candidate = settings.resolve_path("bhashini_models/tts/flite/bin/flite")
        if candidate.exists() and os.access(str(candidate), os.X_OK):
            return str(candidate)
        sys_flite = shutil.which("flite")
        if sys_flite:
            return sys_flite
        if os.path.exists("/usr/bin/flite"):
            return "/usr/bin/flite"
        return None

    def _find_flite_voices_dir(self) -> Optional[str]:
        """Locates flite .flitevox voices directory."""
        candidate = settings.resolve_path("bhashini_models/tts/flite/voices")
        if candidate.exists():
            return str(candidate)
        if os.path.exists("/usr/share/flite/voices"):
            return "/usr/share/flite/voices"
        return None

    def _find_system_espeak(self) -> Optional[str]:
        """Checks standard Linux locations for espeak-ng or espeak."""
        for path in ["/usr/bin/espeak-ng", "/usr/bin/espeak", "/usr/local/bin/espeak-ng"]:
            if os.path.exists(path):
                return path
        return None

    def split_into_sentences(self, text: str) -> List[str]:
        """Splits narrative into clean sentence units for streaming speech playback."""
        sentences = re.split(r"(?<=[.!?।])\s+", text)
        return [s.strip() for s in sentences if len(s.strip()) > 3]

    def synthesize(self, text: str, language: str = "en") -> Tuple[Optional[bytes], float]:
        """
        Synthesizes text into 16kHz mono WAV bytes strictly offline.
        Returns: (wav_bytes: Optional[bytes], latency_ms: float)
        """
        start_time = time.time()
        if not text:
            return None, 0.0

        lang = language.lower().strip()

        # Attempt 1: Local Bhashini Flite Engine
        if self._flite_bin and self._flite_voices_dir:
            voice_file = FLITE_VOICE_MAP.get(lang, "cmu_us_slt.flitevox")
            voice_path = os.path.join(self._flite_voices_dir, voice_file)
            if os.path.exists(voice_path):
                try:
                    tmp_out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                    tmp_out.close()
                    cmd = [self._flite_bin, "-voice", voice_path, "-t", text, tmp_out.name]
                    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5.0)
                    if res.returncode == 0 and os.path.exists(tmp_out.name) and os.path.getsize(tmp_out.name) > 100:
                        with open(tmp_out.name, "rb") as f:
                            wav_bytes = f.read()
                        os.remove(tmp_out.name)
                        latency_ms = (time.time() - start_time) * 1000.0
                        logger.info(f"Local Flite TTS synthesized {len(wav_bytes)} bytes for '{lang}' ({latency_ms:.1f}ms).")
                        return wav_bytes, latency_ms
                    if os.path.exists(tmp_out.name):
                        os.remove(tmp_out.name)
                except Exception as e:
                    logger.debug(f"Flite synthesis failed: {e}")

        # Attempt 2: System espeak-ng / espeak CLI (Standard on Jetson / Ubuntu Linux)
        if self._espeak_bin:
            espeak_voice = ESPEAK_VOICE_MAP.get(lang, "en-us")
            try:
                tmp_out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                tmp_out.close()
                cmd = [self._espeak_bin, "-v", espeak_voice, "-w", tmp_out.name, text]
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5.0)
                if res.returncode == 0 and os.path.exists(tmp_out.name) and os.path.getsize(tmp_out.name) > 100:
                    with open(tmp_out.name, "rb") as f:
                        wav_bytes = f.read()
                    os.remove(tmp_out.name)
                    latency_ms = (time.time() - start_time) * 1000.0
                    logger.info(f"espeak-ng synthesized {len(wav_bytes)} bytes for '{lang}' ({latency_ms:.1f}ms).")
                    return wav_bytes, latency_ms
                if os.path.exists(tmp_out.name):
                    os.remove(tmp_out.name)
            except Exception as e:
                logger.debug(f"espeak synthesis failed: {e}")

        # Attempt 3: Local pyttsx3 offline engine (Windows SAPI5 / Linux espeak)
        try:
            import pyttsx3
            tmp_out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_out.close()

            def _run_pyttsx3():
                try:
                    engine = pyttsx3.init()
                    engine.setProperty("rate", 150)
                    engine.save_to_file(text, tmp_out.name)
                    engine.runAndWait()
                    engine.stop()
                except Exception as ex:
                    logger.debug(f"pyttsx3 engine run failed: {ex}")

            worker = threading.Thread(target=_run_pyttsx3, daemon=True)
            worker.start()
            worker.join(timeout=3.0)

            if os.path.exists(tmp_out.name) and os.path.getsize(tmp_out.name) > 200:
                with open(tmp_out.name, "rb") as f:
                    wav_bytes = f.read()
                os.remove(tmp_out.name)
                latency_ms = (time.time() - start_time) * 1000.0
                logger.info(f"pyttsx3 synthesized {len(wav_bytes)} bytes for '{lang}' ({latency_ms:.1f}ms).")
                return wav_bytes, latency_ms
            if os.path.exists(tmp_out.name):
                os.remove(tmp_out.name)
        except Exception as e:
            logger.debug(f"pyttsx3 fallback failed: {e}")

        # Attempt 4: Clean valid PCM WAV buffer (Safe offline fallback - keeps audio pipeline intact)
        sample_rate = 16000
        # Calculate speech-paced duration (~180 words per minute)
        words = len(text.split())
        duration = max(min(words / 3.0, 4.0), 0.5)
        num_samples = int(sample_rate * duration)

        import wave
        import struct
        import math
        wav_buf = io.BytesIO()
        with wave.open(wav_buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            # Gentle soft chime tone (320Hz) fading out to acknowledge voice output
            frames = bytearray()
            for i in range(num_samples):
                decay = math.exp(-3.0 * i / num_samples) if i < sample_rate else 0.0
                val = int(800 * math.sin(2 * math.pi * 320 * i / sample_rate) * decay)
                frames.extend(struct.pack("<h", val))
            wf.writeframes(frames)

        synthetic_wav = wav_buf.getvalue()
        latency_ms = (time.time() - start_time) * 1000.0
        return synthetic_wav, latency_ms

    def speak_async(
        self,
        text: str,
        language: str = "en",
        on_started: Optional[Callable[[], None]] = None,
        on_finished: Optional[Callable[[], None]] = None
    ):
        """
        Asynchronously synthesizes and plays audio speech without blocking UI.
        """
        threading.Thread(
            target=self._speak_worker,
            args=(text, language, on_started, on_finished),
            daemon=True
        ).start()

    def _speak_worker(
        self,
        text: str,
        language: str,
        on_started: Optional[Callable[[], None]],
        on_finished: Optional[Callable[[], None]]
    ):
        with self._lock:
            self._is_speaking = True

        if on_started:
            on_started()

        wav_bytes, _ = self.synthesize(text, language=language)
        if wav_bytes:
            self.audio_player.play_wav_bytes(wav_bytes, on_finished=self._on_play_done(on_finished))
        else:
            # Emulate speaking delay if no audio hardware
            time.sleep(1.5)
            self._on_play_done(on_finished)()

    def _on_play_done(self, callback: Optional[Callable[[], None]]):
        def _done():
            with self._lock:
                self._is_speaking = False
            if callback:
                callback()
        return _done

    def stop_speaking(self):
        """Immediately halts active audio synthesis and playback."""
        self.audio_player.stop()
        with self._lock:
            self._is_speaking = False


tts_service = TTSService()
