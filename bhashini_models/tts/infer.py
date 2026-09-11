import base64
import subprocess
import os
import tempfile
import time


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FLITE_BIN = os.path.join(BASE_DIR, "flite", "bin", "flite")
VOICES_DIR = os.path.join(BASE_DIR, "flite", "voices")


class TTSInference:

    def __init__(self, flite_bin=None, voices_dir=None):
        import shutil
        self.flite_bin = flite_bin or FLITE_BIN
        if not os.path.exists(self.flite_bin):
            sys_flite = shutil.which("flite") or ("/usr/bin/flite" if os.path.exists("/usr/bin/flite") else None)
            if sys_flite:
                self.flite_bin = sys_flite

        self.voices_dir = voices_dir or VOICES_DIR
        if not os.path.exists(self.voices_dir):
            if os.path.exists("/usr/share/flite/voices"):
                self.voices_dir = "/usr/share/flite/voices"

        # -------------------------------------------------
        # LANGUAGE → VOICE MAP
        # -------------------------------------------------
        self.LANG_VOICE_MAP = {
            "bn": ["cmu_indic_ben_rm.flitevox"],
            "gu": [
                "cmu_indic_guj_ad.flitevox",
                "cmu_indic_guj_dp.flitevox",
                "cmu_indic_guj_kt.flitevox",
            ],
            "hi": ["cmu_indic_hin_ab.flitevox"],
            "ka": ["cmu_indic_kan_plv.flitevox"],
            "kn": ["cmu_indic_kan_plv.flitevox"],
            "mr": [
                "cmu_indic_mar_aup.flitevox",
                "cmu_indic_mar_slp.flitevox",
            ],
            "pa": ["cmu_indic_pan_amp.flitevox"],
            "ta": ["cmu_indic_tam_sdr.flitevox"],
            "te": [
                "cmu_indic_tel_kpn.flitevox",
                "cmu_indic_tel_sk.flitevox",
                "cmu_indic_tel_ss.flitevox",
            ],
            "en": [
                "cmu_us_slt.flitevox",
                "cmu_us_aew.flitevox",
                "cmu_us_ahw.flitevox",
                "cmu_us_awb.flitevox",
                "cmu_us_axb.flitevox",
                "cmu_us_bdl.flitevox",
                "cmu_us_clb.flitevox",
            ],
        }

        print("TTS Engine initialized successfully.")

    # -----------------------------------------------------
    # Core Synthesis
    # -----------------------------------------------------
    def synthesize_to_bytes(
        self,
        text: str,
        lang: str,
        voice_name: str | None = None,
        duration_stretch: float = 1.0,
        f0_mean: int = 110,
    ) -> bytes:

        if lang not in self.LANG_VOICE_MAP:
            raise ValueError(
                f"Language '{lang}' not supported"
            )

        voices = self.LANG_VOICE_MAP[lang]

        # Default voice
        if voice_name is None:
            voice_name = voices[0]

        if voice_name not in voices:
            raise ValueError(
                f"Voice '{voice_name}' not valid. "
                f"Available: {voices}"
            )

        voice_path = os.path.join(
            self.voices_dir,
            voice_name
        )

        if not os.path.exists(voice_path):
            raise RuntimeError(
                f"Voice file not found: {voice_path}"
            )

        # Temp wav file
        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as tmp_file:

            tmp_wav_path = tmp_file.name

        # Flite command
        cmd = [
            self.flite_bin,
            "-voice", voice_path,
            "--setf", f"duration_stretch={duration_stretch}",
            "--setf", f"int_f0_target_mean={f0_mean}",
            "-t", text,
            tmp_wav_path,
        ]

        subprocess.run(cmd, check=True)

        # Read audio
        with open(tmp_wav_path, "rb") as f:
            audio_bytes = f.read()

        os.remove(tmp_wav_path)

        return audio_bytes

    # -----------------------------------------------------
    # Public Inference
    # -----------------------------------------------------
    def infer(
        self,
        text: str,
        language: str,
        voice_name: str | None = None,
        duration_stretch: float = 1.0,
        f0_mean: int = 110,
        return_base64: bool = True,
    ):

        start_time = time.time()

        if not text.strip():
            raise ValueError("Text cannot be empty")

        audio_bytes = self.synthesize_to_bytes(
            text=text,
            lang=language,
            voice_name=voice_name,
            duration_stretch=duration_stretch,
            f0_mean=f0_mean,
        )

        result = {
            "language": language,
            "processing_time_sec": round(
                time.time() - start_time, 3
            )
        }

        if return_base64:
            result["audio_base64"] = (
                base64.b64encode(audio_bytes).decode()
            )
        else:
            result["audio_bytes"] = audio_bytes

        return result
