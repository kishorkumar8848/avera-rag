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


def find_best_input_device() -> Optional[int]:
    """
    Intelligently discovers the best input capture device:
    1. Scans sounddevice devices for external USB/Type-C microphone or webcam capture.
    2. Prioritizes devices with keywords: 'usb', 'type-c', 'mic', 'audio', 'headset', 'webcam', 'camera', 'ab13x', 'jieli'.
    3. Sets PulseAudio default-source and ensures capture volume is unmuted and 100%.
    """
    if not HAS_SOUNDDEVICE:
        return None
    try:
        devices = sd.query_devices()
        usb_candidates = []

        for idx, dev in enumerate(devices):
            max_in = dev.get("max_input_channels", 0)
            if max_in <= 0:
                continue
            name = dev.get("name", "").lower()

            # Check if this is an external USB / Type-C / microphone hardware device
            is_usb = any(k in name for k in ["usb", "type-c", "typec", "mic", "headset", "ab13x", "uac", "jieli", "camera", "webcam"])
            if is_usb and "monitor" not in name:
                usb_candidates.append((idx, dev))

        # Unmute and set capture volume to 100% on Linux
        import subprocess, shutil
        if shutil.which("pactl"):
            try:
                subprocess.run(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=0.5)
                subprocess.run(["pactl", "set-source-volume", "@DEFAULT_SOURCE@", "100%"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=0.5)
            except Exception:
                pass

        if usb_candidates:
            best_idx, best_dev = usb_candidates[0]
            logger.info(f"Selected USB/Type-C audio input device: [{best_idx}] {best_dev['name']}")
            return best_idx

        return None
    except Exception as e:
        logger.debug(f"Device discovery fallback: {e}")
        return None


class AudioRecorder:
    """
    Records mono 16kHz audio from local microphone directly into memory buffers.
    Avoids redundant disk I/O. Automatically detects USB/Type-C microphone hardware.
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
        self.last_rms: float = 0.0
        self.last_peak: float = 0.0

    def start_recording(self):
        """Starts streaming microphone audio into an in-memory frame buffer."""
        with self._lock:
            if self._is_recording:
                return
            self._frames = []
            self._is_recording = True
            self.last_rms = 0.0
            self.last_peak = 0.0

            if not HAS_SOUNDDEVICE:
                logger.warning("sounddevice not available. Using mock audio recorder.")
                return

            try:
                device_idx = find_best_input_device()
                self._stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype="float32",
                    device=device_idx,
                    callback=self._audio_callback
                )
                self._stream.start()
                dev_info = f"device={device_idx}" if device_idx is not None else "default device"
                logger.info(f"Audio recording started at {self.sample_rate}Hz mono ({dev_info}).")
            except Exception as e:
                logger.error(f"Failed to start sounddevice recording: {e}. Retrying default input...")
                try:
                    self._stream = sd.InputStream(
                        samplerate=self.sample_rate,
                        channels=self.channels,
                        dtype="float32",
                        callback=self._audio_callback
                    )
                    self._stream.start()
                except Exception as ex2:
                    logger.error(f"Default input recording failed: {ex2}")
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
        Also calculates RMS energy and peak amplitude to detect silence/muted hardware.
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
                empty_wav = io.BytesIO()
                self.last_rms = 0.0
                self.last_peak = 0.0
                return np.zeros(0, dtype=np.float32), empty_wav

            audio_data = np.concatenate(self._frames, axis=0).flatten()
            self._frames = []

            # Compute RMS energy and peak amplitude
            self.last_rms = float(np.sqrt(np.mean(audio_data ** 2))) if len(audio_data) > 0 else 0.0
            self.last_peak = float(np.max(np.abs(audio_data))) if len(audio_data) > 0 else 0.0

            # Encode into in-memory WAV buffer
            wav_buffer = io.BytesIO()
            if HAS_SOUNDDEVICE:
                sf.write(wav_buffer, audio_data, self.sample_rate, format="WAV", subtype="PCM_16")
                wav_buffer.seek(0)
            
            dur = len(audio_data) / self.sample_rate
            logger.info(f"Audio recording completed: {dur:.2f}s, RMS={self.last_rms:.6f}, Peak={self.last_peak:.6f}")
            return audio_data, wav_buffer

    def is_silent(self, threshold: float = 0.003) -> bool:
        """Returns True if the recorded audio has near-zero energy (silence / muted mic)."""
        return self.last_rms < threshold and self.last_peak < (threshold * 2.5)

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
            import tempfile
            tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", prefix="tts_play_", delete=False)
            temp_path = tmp_wav.name
            try:
                tmp_wav.write(wav_bytes)
                tmp_wav.close()

                # Ensure system default sink volume is set to 100% (0 dB)
                try:
                    subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "100%"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.0)
                except Exception:
                    pass

                paplay_bin = shutil.which("paplay")
                aplay_bin = shutil.which("aplay")
                play_cmd = None

                if paplay_bin:
                    play_cmd = [paplay_bin, "--volume=65536", temp_path]
                elif aplay_bin:
                    play_cmd = [aplay_bin, "-q", temp_path]

                if play_cmd:
                    with self._lock:
                        self._proc = subprocess.Popen(play_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self._proc.wait()
                    with self._lock:
                        self._proc = None

                if os.path.exists(temp_path):
                    os.remove(temp_path)

                if on_finished:
                    on_finished()
                return
            except Exception as ex:
                logger.debug(f"Linux native audio player fallback: {ex}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

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

