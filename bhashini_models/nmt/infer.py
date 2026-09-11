import os
import time
import logging
import sys
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)
from inference.engine import Model, iso_to_flores


# =========================================================
# LOGGING
# =========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("nmt_inference")


# =========================================================
# CONSTANTS
# =========================================================
INDIC_LANGUAGES = set(iso_to_flores.keys())
REQUIRED_MODELS = {"en-indic", "indic-en", "indic-indic"}


# =========================================================
# INFERENCE CLASS
# =========================================================
class NMTInference:

    # -----------------------------------------------------
    # Init → Lazy loading setup
    # -----------------------------------------------------
    def __init__(self, checkpoint_root="./checkpoints"):
        self.models = {}
        self.checkpoint_root = checkpoint_root

        if not os.path.exists(checkpoint_root):
            raise RuntimeError(
                f"Checkpoint folder not found: {checkpoint_root}"
            )

        logger.info(f"NMTInference initialized with root: {checkpoint_root}. Lazy model loading active.")

    def _get_model(self, name: str) -> Model:
        """Lazily loads requested model on demand, managing GPU VRAM efficiently."""
        if name in self.models:
            return self.models[name]

        model_path = os.path.join(
            self.checkpoint_root,
            name,
            "ct2_int8_model"
        )
        if not os.path.exists(model_path):
            raise RuntimeError(f"Missing model path: {model_path}")

        logger.info(f"Loading NMT model on demand: {name}...")
        import torch
        device = "cuda" if (torch.cuda.is_available() and os.environ.get("FORCE_CPU", "0") != "1") else "cpu"

        # On Jetson edge GPUs (8GB), maintain at most 1 active model in VRAM to prevent OOM
        if device == "cuda" and len(self.models) >= 1:
            for old_name in list(self.models.keys()):
                logger.info(f"Unloading previous NMT model '{old_name}' from VRAM...")
                del self.models[old_name]
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass

        self.models[name] = Model(
            model_path,
            device=device,
            input_lang_code_format="iso",
            model_type="ctranslate2"
        )
        logger.info(f"NMT model '{name}' loaded successfully on {device}.")
        return self.models[name]

    # -----------------------------------------------------
    # Translation Routing
    # -----------------------------------------------------
    def _route_translate(self, text: str, src: str, tgt: str) -> str:
        s = src.lower()
        t = tgt.lower()

        if s == t:
            return text

        if s != "en" and t == "en":
            model = self._get_model("indic-en")
            return model.paragraphs_batch_translate__multilingual(
                [[text, s, "en"]]
            )[0]

        elif s == "en" and t != "en":
            model = self._get_model("en-indic")
            return model.paragraphs_batch_translate__multilingual(
                [[text, "en", t]]
            )[0]

        elif s != "en" and t != "en":
            model = self._get_model("indic-indic")
            return model.paragraphs_batch_translate__multilingual(
                [[text, s, t]]
            )[0]

        else:
            return text

    # -----------------------------------------------------
    # Public Inference Method
    # -----------------------------------------------------
    def infer(self, text: str, src_lang: str, tgt_lang: str):

        start_time = time.time()

        # -------------------------
        # Validation
        # -------------------------
        if not text.strip():
            raise ValueError("Input text cannot be empty")

        if len(text) > 5000:
            raise ValueError("Text too long")

        # -------------------------
        # Translation
        # -------------------------
        translated = self._route_translate(
            text,
            src_lang,
            tgt_lang
        )

        logger.info(
            f"NMT {src_lang}→{tgt_lang} | "
            f"Time: {time.time() - start_time:.3f}s"
        )

        return {
            "translated_text": translated,
            "src_lang": src_lang,
            "tgt_lang": tgt_lang,
            "processing_time_sec": round(
                time.time() - start_time, 3
            )
        }
