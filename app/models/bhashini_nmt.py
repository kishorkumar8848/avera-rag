import os
import sys
import time
import requests
from pathlib import Path
from typing import Tuple, Optional

from app.core.config import settings
from app.core.logging import logger

LANGUAGE_NAMES = {
    "ta": "Tamil",
    "hi": "Hindi",
    "te": "Telugu",
    "kn": "Kannada",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "or": "Odia",
    "as": "Assamese",
    "ur": "Urdu",
    "en": "English"
}


class NMTService:
    """
    Local Bhashini Neural Machine Translation (NMT) Service (CTranslate2 INT8).
    Directly loads and executes the official Bhashini NMT models from bhashini_models/
    for sub-100ms bidirectional translation between Indic languages (Tamil, Hindi, etc.) and English.
    Includes REST microservice fallback and edge LLM fallback.
    """

    def __init__(self):
        self.nmt_url = settings.BHASHINI_NMT_URL
        self._local_nmt = None
        self._init_attempted = False

    def _get_local_nmt(self):
        """Lazily initializes the embedded Bhashini CTranslate2 engine."""
        if self._local_nmt is None and not self._init_attempted:
            self._init_attempted = True
            try:
                bhashini_dir = settings.resolve_path("bhashini_models")
                ckpt_dir = bhashini_dir / "nmt" / "checkpoints"
                if ckpt_dir.exists():
                    if str(bhashini_dir) not in sys.path:
                        sys.path.insert(0, str(bhashini_dir))
                    from nmt.infer import NMTInference
                    logger.info(f"Loading local Bhashini NMT models from {ckpt_dir}...")
                    self._local_nmt = NMTInference(checkpoint_root=str(ckpt_dir))
                    logger.info("Local Bhashini NMT models (en-indic, indic-en, indic-indic) loaded successfully!")
            except Exception as e:
                logger.warning(f"Could not load local Bhashini NMT engine: {e}. Will use service or LLM fallback.")
        return self._local_nmt

    @staticmethod
    def _normalize_query(text: str, lang: str) -> str:
        """Corrects common ASR phonetic variations in Indic medical queries."""
        if not text:
            return text
        import re

        if lang == "ta":
            # 1. Spoken Tamil ASR transcribes 'சலி' (boredom) instead of 'சளி' (cold / phlegm)
            text = re.sub(r'(\s|^)சலி(\s|$|[\?\.\,\!])', r'\1சளி\2', text)
            text = re.sub(r'(\s|^)சலிப்பு(\s|$|[\?\.\,\!])', r'\1சளி\2', text)

            # 2. Spoken Tamil typos for fever: காயச்சல் / காச்சல் -> காய்ச்சல்
            text = text.replace("காயச்சல்", "காய்ச்சல்")
            text = text.replace("காச்சல்", "காய்ச்சல்")
            text = text.replace("காய்ச்சல் அடிக்குது", "காய்ச்சல்")

            # 3. 'மட்டும்' between symptoms heard instead of 'மற்றும்' (and)
            text = re.sub(
                r'(சளி|காய்ச்சல்|இருமல்|தலைவலி|வலி|வாந்தி|தலை)\s+மட்டும்\s+(சளி|காய்ச்சல்|இருமல்|தலைவலி|வலி|வாந்தி|தலை)',
                r'\1 மற்றும் \2',
                text
            )

            # 4. Spoken Tamil ASR commonly transcribes 'வளி' (wind) instead of 'வலி' (pain)
            text = re.sub(r'(\s|^)வளி([\s\?\.\,\!]|$)', r'\1வலி\2', text)
            for body_part in ["முட்டி", "மூட்டு", "தலை", "வயிறு", "வயிற்று", "நெஞ்சு", "முதுகு", "இடுப்பு", "பல்", "உடம்பு", "கால்", "கை", "கழுத்து", "தொண்டை", "பாதம்"]:
                text = text.replace(f"{body_part} வளி", f"{body_part} வலி")
                text = text.replace(f"{body_part}வளி", f"{body_part} வலி")

            # 5. Cough variations: இருமள் -> இருமல்
            text = text.replace("இருமள்", "இருமல்")
            text = text.replace("இருமல் வருது", "இருமல்")

            # 6. Breathlessness variations: மூச்சடைப்பு / மூச்சு தினறல் -> மூச்சுத் திணறல்
            text = text.replace("மூச்சடைப்பு", "மூச்சுத் திணறல்")
            text = text.replace("மூச்சு தினறல்", "மூச்சுத் திணறல்")
            text = text.replace("மூச்சு தனறல்", "மூச்சுத் திணறல்")

            # 7. Fast conversational / ASR phonetic variations:
            text = text.replace("ஏனக்கு", "எனக்கு")
            text = text.replace("காய், சலி", "காய்ச்சல், சளி")
            text = text.replace("காய் சலி", "காய்ச்சல் சளி")
            text = text.replace("காய்,", "காய்ச்சல்,")
            text = text.replace("மாட்ருமிருமல்", "மற்றும் இருமல்")
            text = text.replace("மாட்று", "மற்றும்")
            text = text.replace("மிரமலிருக்கு", "இருமல் இருக்கு")
            text = text.replace("மிருமல்", "இருமல்")


        elif lang == "hi":
            # Common Hindi ASR variations
            text = text.replace("खासी", "खांसी")
            text = text.replace("जुखाम", "जुकाम")
            text = text.replace("सरदर्द", "सिरदर्द")
            text = text.replace("सर दर्द", "सिरदर्द")
            text = text.replace("पेट का दर्द", "पेट दर्द")
            text = text.replace("छाती में दर्द", "सीने में दर्द")
            text = text.replace("उलटी", "उल्टी")
            text = text.replace("पतले दस्त", "दस्त")

        elif lang == "gu":
            # Common Gujarati ASR variations
            text = text.replace("સિરદર્દ", "માથાનો દુખાવો")
            text = text.replace("માથુ દુખે", "માથાનો દુખાવો")
            text = text.replace("છાતી નો દુખાવો", "છાતીમાં દુખાવો")
            text = text.replace("ઝાડા ઉલટી", "ઝાડા અને ઉલટી")

        return text.strip()

    def translate_to_english(self, text: str, src_lang: str) -> Tuple[str, float]:
        """
        Translates Indic query into clinical English for RAG retrieval.
        Returns: (translated_english_text, latency_ms)
        """
        if not text or src_lang.lower() == "en":
            return text, 0.0

        start_time = time.time()
        text = self._normalize_query(text, src_lang.lower())

        # Step 1: Direct Local Bhashini CTranslate2 Inference (< 100ms)
        local_nmt = self._get_local_nmt()
        if local_nmt is not None:
            try:
                res = local_nmt.infer(text, src_lang=src_lang.lower(), tgt_lang="en")
                translated = res.get("translated_text", "").strip()
                if translated:
                    latency_ms = (time.time() - start_time) * 1000.0
                    logger.info(f"Bhashini NMT ({src_lang}->en): '{text}' -> '{translated}' ({latency_ms:.1f}ms)")
                    return translated, latency_ms
            except Exception as ex:
                logger.debug(f"Direct Bhashini NMT failed: {ex}")

        # Step 2: External/Local Bhashini REST Microservice
        try:
            payload = {"text": text, "source_language": src_lang, "target_language": "en"}
            res = requests.post(self.nmt_url, json=payload, timeout=settings.BUDGET_NMT_SEC + 1.0)
            if res.status_code == 200:
                translated = res.json().get("translated_text", text).strip()
                latency_ms = (time.time() - start_time) * 1000.0
                logger.info(f"Bhashini REST NMT ({src_lang}->en): '{text}' -> '{translated}' ({latency_ms:.1f}ms)")
                return translated, latency_ms
        except Exception as e:
            logger.debug(f"Bhashini REST NMT service ({src_lang}->en) unavailable: {e}")

        # Step 3: Qwen Multilingual LLM Fallback
        try:
            from app.models.qwen_backend import qwen_backend
            lang_name = LANGUAGE_NAMES.get(src_lang.lower(), src_lang)
            sys_prompt = (
                f"You are a medical interpreter. Translate this patient's query from {lang_name} into clear clinical English. "
                "Output ONLY the English translation without preamble or conversational notes."
            )
            translated = qwen_backend._call_inference(sys_prompt, text).strip()
            if translated and len(translated) > 3 and not translated.startswith("{"):
                latency_ms = (time.time() - start_time) * 1000.0
                logger.info(f"Qwen LLM translation ({src_lang}->en): '{text}' -> '{translated}' ({latency_ms:.1f}ms)")
                return translated, latency_ms
        except Exception as ex:
            logger.debug(f"LLM translation to English failed: {ex}")

        latency_ms = (time.time() - start_time) * 1000.0
        return text, latency_ms

    def translate_from_english(self, english_text: str, tgt_lang: str) -> Tuple[str, float]:
        """
        Translates English clinical guidance into target Indic language (e.g. Tamil, Hindi).
        Returns: (translated_target_text, latency_ms)
        """
        if not english_text or tgt_lang.lower() == "en":
            return english_text, 0.0

        start_time = time.time()

        # Step 1: Direct Local Bhashini CTranslate2 Inference (~200ms)
        local_nmt = self._get_local_nmt()
        if local_nmt is not None:
            try:
                res = local_nmt.infer(english_text, src_lang="en", tgt_lang=tgt_lang.lower())
                translated = res.get("translated_text", "").strip()
                if translated:
                    latency_ms = (time.time() - start_time) * 1000.0
                    logger.info(f"Bhashini NMT (en->{tgt_lang}): '{english_text[:40]}...' -> '{translated[:40]}...' ({latency_ms:.1f}ms)")
                    return translated, latency_ms
            except Exception as ex:
                logger.debug(f"Direct Bhashini NMT (en->{tgt_lang}) failed: {ex}")

        # Step 2: External/Local Bhashini REST Microservice
        try:
            payload = {"text": english_text, "source_language": "en", "target_language": tgt_lang}
            res = requests.post(self.nmt_url, json=payload, timeout=settings.BUDGET_NMT_SEC + 1.0)
            if res.status_code == 200:
                translated = res.json().get("translated_text", english_text).strip()
                latency_ms = (time.time() - start_time) * 1000.0
                logger.info(f"Bhashini REST NMT (en->{tgt_lang}): '{english_text[:40]}...' -> '{translated[:40]}...' ({latency_ms:.1f}ms)")
                return translated, latency_ms
        except Exception as e:
            logger.debug(f"Bhashini REST NMT service (en->{tgt_lang}) unavailable: {e}")

        # Step 3: Qwen Multilingual LLM Fallback
        try:
            from app.models.qwen_backend import qwen_backend
            lang_name = LANGUAGE_NAMES.get(tgt_lang.lower(), tgt_lang)
            sys_prompt = (
                f"You are a medical translator for frontline healthcare. "
                f"Translate the following clinical guidance directly into natural, accurate {lang_name} ({tgt_lang}) using native {lang_name} script. "
                f"Ensure the medical advice is clear and reassuring. "
                f"Output ONLY the {lang_name} translation without English words, preamble, or markdown formatting."
            )
            translated = qwen_backend._call_inference(sys_prompt, english_text).strip()
            if translated and len(translated) > 5 and not translated.startswith("{"):
                latency_ms = (time.time() - start_time) * 1000.0
                logger.info(f"Qwen LLM translation (en->{tgt_lang}): '{english_text[:40]}...' -> '{translated[:40]}...' ({latency_ms:.1f}ms)")
                return translated, latency_ms
        except Exception as ex:
            logger.debug(f"LLM translation from English failed: {ex}")

        latency_ms = (time.time() - start_time) * 1000.0
        return english_text, latency_ms


nmt_service = NMTService()
