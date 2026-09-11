import io
import time
import threading
from typing import Optional, Tuple, Callable
import numpy as np

try:
    import sounddevice as sd
    import soundfile as sf
    HAS_SOUNDDEVICE = True
except (ImportError, OSError):
    HAS_SOUNDDEVICE = False

from app.core.config import settings
from app.core.logging import logger


class VADDetector:
    """
    Voice Activity Detection using adaptive root-mean-square (RMS) energy calculations.
    """
    def __init__(self, energy_threshold: float = 0.015, silence_duration_sec: float = 1.2):
        self.energy_threshold = energy_threshold
        self.silence_duration_sec = silence_duration_sec

    def is_speech(self, chunk: np.ndarray) -> bool:
        """Determines if the audio frame contains vocal energy."""
        if len(chunk) == 0:
            return False
        rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
        return bool(rms > self.energy_threshold)


class AudioRecorder:
    """
    Records mono 16kHz audio from local microphone directly into memory buffers.
    Avoids redundant disk I/O.
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.vad = VADDetector(
            energy_threshold=settings.VAD_ENERGY_THRESHOLD,
            silence_duration_sec=settings.VAD_SILENCE_DURATION
        )
        self._is_recording = False
        self._frames = []
        self._stream: Optional[object] = None
        self._lock = threading.Lock()

    def start_recording(self):
        """Starts streaming microphone audio into an in-memory frame buffer."""
        with self._lock:
            if self._is_recording:
                return
            self._frames = []
            self._is_recording = True

            if not HAS_SOUNDDEVICE:
                logger.warning("sounddevice not available. Using mock audio recorder.")
                return

            try:
                self._stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype="float32",
                    callback=self._audio_callback
                )
                self._stream.start()
                logger.info(f"Audio recording started at {self.sample_rate}Hz mono.")
            except Exception as e:
                logger.error(f"Failed to start sounddevice recording: {e}. Falling back to mock recorder.")
                self._stream = None

    def _audio_callback(self, indata, frames, time_info, status):
        """Streaming callback appending PCM frames in memory."""
        if status:
            logger.debug(f"sounddevice stream status: {status}")
        if self._is_recording:
            self._frames.append(indata.copy())

    def stop_recording(self) -> Tuple[np.ndarray, io.BytesIO]:
        """
        Stops recording and returns:
        1. Raw float32 numpy waveform array.
        2. In-memory BytesIO containing a standard 16-bit PCM WAV.
        """
        with self._lock:
            if not self._is_recording:
                return np.zeros(0, dtype=np.float32), io.BytesIO()

            self._is_recording = False
            if self._stream:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception as e:
                    logger.debug(f"Error closing audio stream: {e}")
                self._stream = None

            if not self._frames:
                # Return empty buffer if no frames collected
                empty_wav = io.BytesIO()
                return np.zeros(0, dtype=np.float32), empty_wav

            audio_data = np.concatenate(self._frames, axis=0).flatten()
            self._frames = []

            # Encode into in-memory WAV buffer
            wav_buffer = io.BytesIO()
            if HAS_SOUNDDEVICE:
                sf.write(wav_buffer, audio_data, self.sample_rate, format="WAV", subtype="PCM_16")
                wav_buffer.seek(0)
            
            logger.info(f"Audio recording completed: {len(audio_data) / self.sample_rate:.2f} seconds.")
            return audio_data, wav_buffer

    def is_recording(self) -> bool:
        return self._is_recording


class AudioPlayer:
    """
    Plays audio asynchronously from memory buffers without blocking the main UI thread.
    Uses native OS audio servers (winsound on Windows, paplay/aplay on Linux/Jetson,
    with sounddevice as universal fallback) to prevent buffer underrun crackling.
    """

    def __init__(self):
        self._current_stream = None
        self._proc = None
        self._lock = threading.Lock()

    def play_wav_bytes(self, wav_bytes: bytes, on_finished: Optional[Callable[[], None]] = None):
        """Plays WAV bytes asynchronously from memory."""
        threading.Thread(target=self._play_worker, args=(wav_bytes, on_finished), daemon=True).start()

    def _play_worker(self, wav_bytes: bytes, on_finished: Optional[Callable[[], None]] = None):
        import os
        import subprocess
        import shutil

        # 1. On Windows, use winsound to guarantee output to Windows default system speakers
        if os.name == "nt":
            try:
                import winsound
                temp_path = str(settings.resolve_path("logs/tts_playback.wav"))
                os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                with open(temp_path, "wb") as f:
                    f.write(wav_bytes)
                winsound.PlaySound(temp_path, winsound.SND_FILENAME)
                if on_finished:
                    on_finished()
                return
            except Exception as ex:
                logger.debug(f"winsound playback fallback: {ex}")

        # 2. On Linux (Ubuntu / Jetson Orin Nano), use native PulseAudio (paplay) or ALSA (aplay)
        # This completely avoids PortAudio callback underrun cracking / breaking on Jetson hardware!
        if os.name == "posix":
            temp_path = "/tmp/tts_playback.wav"
            try:
                with open(temp_path, "wb") as f:
                    f.write(wav_bytes)

                paplay_bin = shutil.which("paplay")
                aplay_bin = shutil.which("aplay")
                play_cmd = None

                if paplay_bin:
                    play_cmd = [paplay_bin, temp_path]
                elif aplay_bin:
                    play_cmd = [aplay_bin, "-q", temp_path]

                if play_cmd:
                    with self._lock:
                        self._proc = subprocess.Popen(play_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self._proc.wait()
                    with self._lock:
                        self._proc = None
                    if on_finished:
                        on_finished()
                    return
            except Exception as ex:
                logger.debug(f"Linux native audio player fallback: {ex}")

        # 3. Sounddevice fallback
        if not HAS_SOUNDDEVICE:
            logger.info("sounddevice not available. Audio playback simulated.")
            time.sleep(1.0)
            if on_finished:
                on_finished()
            return

        try:
            with io.BytesIO(wav_bytes) as buf:
                data, fs = sf.read(buf, dtype="float32")
                sd.play(data, fs)
                sd.wait()
        except Exception as e:
            logger.error(f"Audio playback error: {e}")
        finally:
            if on_finished:
                on_finished()

    def stop(self):
        """Immediately stops audio playback."""
        with self._lock:
            if self._proc is not None:
                try:
                    self._proc.terminate()
                except Exception:
                    pass
                self._proc = None

        if HAS_SOUNDDEVICE:
            try:
                sd.stop()
            except Exception as e:
                logger.debug(f"Error stopping sounddevice: {e}")

