import time
import uuid
from typing import Optional, Dict, Any, List
from PIL import Image

from app.ui.qt_compat import QRunnable, QObject, Signal, Slot, HAS_QT

from app.core.config import settings
from app.core.logging import logger, log_interaction_telemetry
from app.safety.red_flags import red_flag_detector
from app.safety.policies import ClinicalPolicyEngine
from app.safety.validator import OutputValidator, MedicalResponseSchema
from app.safety.query_validator import QueryValidator
from app.models.bhashini_asr import asr_service
from app.models.bhashini_nmt import nmt_service
from app.models.bhashini_tts import tts_service
from app.models.qwen_backend import qwen_backend
from app.models.moondream_backend import moondream_backend
from app.rag.hybrid_retriever import HybridRetriever


class WorkerSignals(QObject if HAS_QT else object):
    """Signals for communicating pipeline progress to the Qt UI thread."""
    if HAS_QT:
        status_changed = Signal(str)
        emergency_alert = Signal(str)
        finished = Signal(dict)
        error = Signal(str)


class SpeechPipelineWorker(QRunnable if HAS_QT else object):
    """
    Background worker executing the complete speech consultation pipeline:
    1. Audio recording processing
    2. Local Bhashini ASR (Speech-to-Text)
    3. Emergency Red Flag Triage (Safety check)
    4. Local Bhashini NMT (Indic to English)
    5. Dual-Corpus Hybrid Medical RAG (SQLite FTS5 + FAISS)
    6. Qwen2.5-1.5B Grounded Clinical Generation
    7. MedicalResponseSchema Validation & Self-Correction
    8. Local Bhashini NMT (English to User's language)
    9. Local Bhashini TTS Synthesis
    """

    def __init__(
        self,
        audio_data: bytes,
        language: str,
        retriever: HybridRetriever,
        patient_profile: Optional[Dict[str, Any]] = None
    ):
        if HAS_QT:
            super().__init__()
        self.audio_data = audio_data
        self.language = language
        self.retriever = retriever
        self.patient_profile = patient_profile
        self.signals = WorkerSignals() if HAS_QT else None


    @Slot()
    def run(self):
        start_total = time.time()
        req_id = f"req_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        latencies: Dict[str, float] = {}

        try:
            # 1. ASR (Speech to Text)
            self._emit_status("Understanding...")
            query_text, asr_conf, asr_ms = asr_service.transcribe(self.audio_data, language=self.language)
            latencies["asr_ms"] = asr_ms

            # 1b. Check for Empty Speech / Disconnected or Muted Microphone
            if not query_text.strip():
                logger.info(f"No speech detected in audio recording (ASR latency: {asr_ms:.1f}ms). Prompting user to check mic.")
                self._emit_status("⚠️ குரல் பதிவு செய்யப்படவில்லை / Mic silent")
                silence_payload = QueryValidator.build_silence_payload(language=self.language)

                # Speak friendly guidance in patient's language
                tts_service.speak_async(
                    text=silence_payload["spoken_text"],
                    language=self.language,
                    on_finished=lambda: self._emit_status("Ready")
                )

                total_ms = (time.time() - start_total) * 1000.0
                silence_payload["patient_profile"] = self.patient_profile
                silence_payload["latencies"] = latencies
                silence_payload["total_ms"] = round(total_ms, 1)

                if self.signals:
                    try:
                        self.signals.finished.emit(silence_payload)
                    except RuntimeError:
                        pass
                return

            # 2. Deterministic Medical Safety Guard (Red Flags)
            is_emergency, categories, escalation_msg = red_flag_detector.detect_red_flags(query_text)
            if is_emergency and escalation_msg:
                logger.warning(f"Red flag emergency detected: {categories}")
                if self.language != "en":
                    escalation_msg, _ = nmt_service.translate_from_english(escalation_msg, tgt_lang=self.language)
                if self.signals:
                    self.signals.emergency_alert.emit(escalation_msg)
                
                # Speak emergency warning immediately in patient's language
                tts_service.speak_async(escalation_msg, language=self.language)
                
                total_ms = (time.time() - start_total) * 1000.0
                log_interaction_telemetry(req_id, self.language, "speech", latencies, total_ms, status="emergency")
                if self.signals:
                    self.signals.finished.emit({
                        "is_emergency": True,
                        "query": query_text,
                        "summary": escalation_msg,
                        "observations": categories,
                        "recommended_actions": ["Call 108 / 112 emergency services immediately.", "Keep patient calm and still."],
                        "warning_signs": ["Immediate danger to life or vital organs."],
                        "referral": "Nearest Emergency Department or Community Health Centre.",
                        "sources": ["National Emergency Triage Protocol"],
                        "patient_profile": self.patient_profile
                    })

                return

            # 3. NMT (Indic speech query -> English medical query)
            self._emit_status("Translating query...")
            english_query, nmt_in_ms = nmt_service.translate_to_english(query_text, src_lang=self.language)
            latencies["nmt_in_ms"] = nmt_in_ms

            # 3b. Clinical Intent & Symptom Validation
            # Prevents RAG hallucinations and NMT loops on casual greetings or unclear speech
            is_valid, retake_payload = QueryValidator.validate_clinical_query(
                raw_query=query_text,
                english_query=english_query,
                language=self.language
            )
            if not is_valid and retake_payload:
                logger.info(f"Query '{query_text}' failed clinical validation: {retake_payload.get('reason')}")
                self._emit_status("⚠️ குரல் தெளிவாக இல்லை / Voice unclear")

                # Speak short friendly retry prompt in patient's language
                tts_service.speak_async(
                    text=retake_payload["spoken_text"],
                    language=self.language,
                    on_finished=lambda: self._emit_status("Ready")
                )

                total_ms = (time.time() - start_total) * 1000.0
                retake_payload["patient_profile"] = self.patient_profile
                retake_payload["latencies"] = latencies
                retake_payload["total_ms"] = round(total_ms, 1)

                if self.signals:
                    try:
                        self.signals.finished.emit(retake_payload)
                    except RuntimeError:
                        pass
                return

            # 4. Medical RAG (Hybrid SQLite FTS5 + FAISS)
            self._emit_status("Searching medical guidance...")
            rag_start = time.time()
            retrieved_docs = self.retriever.retrieve(english_query, top_k=settings.TOP_K_RETRIEVAL)
            latencies["rag_ms"] = (time.time() - rag_start) * 1000.0

            # Precedence rule: prioritize Indian protocols
            retrieved_docs = ClinicalPolicyEngine.enforce_protocol_precedence(retrieved_docs)

            # 5. Qwen2.5-1.5B Clinical Reasoning
            self._emit_status("Preparing guidance...")
            response_schema, qwen_ms = qwen_backend.generate_clinical_guidance(
                query=english_query,
                retrieved_context=retrieved_docs[:settings.TOP_K_CONTEXT],
                patient_profile=self.patient_profile,
                language=self.language
            )
            latencies["qwen_ms"] = qwen_ms


            # 6. NMT back to target language (if non-English and response is still in English)
            final_summary = response_schema.summary
            if self.language != "en":
                # Check if guidance is already localized into patient's Indic language
                is_already_localized = any(ord(c) > 127 for c in final_summary)
                if not is_already_localized:
                    self._emit_status(f"Translating guidance to {self.language.upper()}...")
                    translated_summary, nmt_out_ms = nmt_service.translate_from_english(final_summary, tgt_lang=self.language)
                    latencies["nmt_out_ms"] = nmt_out_ms
                    final_summary = translated_summary

                    # Translate action items, warning signs, and referral
                    if response_schema.recommended_actions:
                        combined_actions = "\n".join(response_schema.recommended_actions)
                        t_act, _ = nmt_service.translate_from_english(combined_actions, tgt_lang=self.language)
                        response_schema.recommended_actions = [line.strip("- •0123456789. ") for line in t_act.split("\n") if line.strip()]

                    if response_schema.warning_signs:
                        combined_warn = "\n".join(response_schema.warning_signs)
                        t_warn, _ = nmt_service.translate_from_english(combined_warn, tgt_lang=self.language)
                        response_schema.warning_signs = [line.strip("- •0123456789. ") for line in t_warn.split("\n") if line.strip()]

                    if response_schema.referral:
                        t_ref, _ = nmt_service.translate_from_english(response_schema.referral, tgt_lang=self.language)
                        response_schema.referral = t_ref
                else:
                    logger.info(f"Clinical guidance already natively localized in {self.language.upper()}; bypassing NMT translation.")

            # Construct complete spoken narration across all clinical sections
            full_spoken_text = self._build_full_narration(final_summary, response_schema)

            # 7. Asynchronous TTS synthesis & playback
            self._emit_status("Speaking...")
            tts_start = time.time()
            tts_service.speak_async(
                text=full_spoken_text,
                language=self.language,
                on_finished=lambda: self._emit_status("Ready")
            )
            latencies["tts_ms"] = (time.time() - tts_start) * 1000.0

            total_ms = (time.time() - start_total) * 1000.0
            log_interaction_telemetry(req_id, self.language, "speech", latencies, total_ms)

            # Emit final structured result to UI
            ui_result = OutputValidator.format_for_ui(response_schema)
            ui_result["summary"] = final_summary
            ui_result["spoken_text"] = full_spoken_text
            ui_result["query"] = query_text
            ui_result["is_emergency"] = False
            ui_result["latencies"] = latencies
            ui_result["total_ms"] = round(total_ms, 1)
            ui_result["patient_profile"] = self.patient_profile

            if self.signals:

                try:
                    self.signals.finished.emit(ui_result)
                except RuntimeError:
                    pass

        except Exception as e:
            logger.error(f"Error in speech pipeline worker: {e}", exc_info=True)
            if self.signals:
                try:
                    self.signals.error.emit(str(e))
                except RuntimeError:
                    pass

    def _build_full_narration(self, summary: str, schema: MedicalResponseSchema) -> str:
        """Assembles a comprehensive voice narration covering summary, actions, danger signs, and referral."""
        parts = [summary.strip()]
        if schema.recommended_actions:
            header = {
                "ta": "பரிந்துரைக்கப்பட்ட அடுத்த படிகள். ",
                "hi": "सुझाए गए अगले कदम. ",
                "te": "సూచించిన తదుపరి చర్యలు. ",
                "kn": "ಶಿಫಾರಸು ಮಾಡಿದ ಮುಂದಿನ ಹಂತಗಳು. ",
                "ml": "ശുപാർശ ചെയ്യുന്ന അടുത്ത ഘട്ടങ്ങൾ. "
            }.get(self.language, "Recommended next steps. ")
            parts.append(header + ". ".join(schema.recommended_actions))

        if schema.warning_signs:
            header = {
                "ta": "கவனிக்க வேண்டிய ஆபத்து அறிகுறிகள். ",
                "hi": "खतरे के लक्षण जिन पर ध्यान दें. ",
                "te": "ప్రమాద సంకేతాలు. ",
                "kn": "ಅಪಾಯದ ಲಕ್ಷಣಗಳು. ",
                "ml": "ശ്രദ്ധിക്കേണ്ട അപകട ലക്ഷണങ്ങൾ. "
            }.get(self.language, "Watch for danger signs. ")
            parts.append(header + ". ".join(schema.warning_signs))

        if schema.referral:
            header = {
                "ta": "மருத்துவ பரிந்துரை ஆலோசனை. ",
                "hi": "रेफरल मार्गदर्शन. ",
                "te": "సిఫార్సు మార్గదర్శకత్వం. ",
                "kn": "ರೆಫರಲ್ ಮಾರ್ಗದರ್ಶನ. ",
                "ml": "റഫറൽ മാർഗ്ഗനിർദ്ദേശം. "
            }.get(self.language, "Referral guidance. ")
            parts.append(header + schema.referral)

        return " ".join(parts)

    def _emit_status(self, text: str):
        if self.signals:
            try:
                self.signals.status_changed.emit(text)
            except RuntimeError:
                pass


class MultimodalPipelineWorker(QRunnable if HAS_QT else object):
    """
    Asynchronous worker executing the Multimodal Flow:
    Captured Frame -> Moondream (Structured Observations) -> Speech/Query -> Red Flag Guard -> RAG -> Qwen -> TTS.
    """

    def __init__(
        self,
        image: Image.Image,
        speech_audio: Optional[Any],
        text_query: Optional[str],
        language: str,
        retriever: HybridRetriever,
        patient_profile: Optional[Dict[str, Any]] = None
    ):
        if HAS_QT:
            super().__init__()
        self.image = image
        self.speech_audio = speech_audio
        self.text_query = text_query
        self.language = language
        self.retriever = retriever
        self.patient_profile = patient_profile
        self.signals = WorkerSignals() if HAS_QT else None


    @Slot()
    def run(self):
        start_total = time.time()
        req_id = f"req_mm_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        latencies: Dict[str, float] = {}

        try:
            # 1. Moondream Vision Inference (Visual feature extraction only, strictly non-diagnostic)
            self._emit_status("Analyzing image...")
            vision_result = moondream_backend.analyze_image(self.image)
            observations = vision_result.get("observations", [])
            latencies["vision_ms"] = vision_result.get("latency_ms", 1500.0)

            # 2. ASR or User Text
            user_symptoms = self.text_query or ""
            if self.speech_audio is not None:
                self._emit_status("Understanding speech...")
                transcribed, _, asr_ms = asr_service.transcribe(self.speech_audio, language=self.language)
                latencies["asr_ms"] = asr_ms
                user_symptoms = f"{user_symptoms} {transcribed}".strip()

            combined_query = f"{user_symptoms} (Visual findings: {', '.join(observations)})"

            # 3. Red Flag Guard
            is_emergency, categories, escalation_msg = red_flag_detector.detect_red_flags(combined_query)
            if is_emergency and escalation_msg:
                if self.language != "en":
                    escalation_msg, _ = nmt_service.translate_from_english(escalation_msg, tgt_lang=self.language)
                if self.signals:
                    self.signals.emergency_alert.emit(escalation_msg)
                tts_service.speak_async(escalation_msg, language=self.language)
                total_ms = (time.time() - start_total) * 1000.0
                log_interaction_telemetry(req_id, self.language, "speech_camera", latencies, total_ms, status="emergency")
                if self.signals:
                    self.signals.finished.emit({
                        "is_emergency": True,
                        "query": combined_query,
                        "summary": escalation_msg,
                        "observations": observations + categories,
                        "recommended_actions": ["Immediate emergency transfer required."],
                        "warning_signs": ["Critical warning sign detected."],
                        "referral": "Immediate tertiary or CHC hospital referral.",
                        "sources": ["Emergency Medical Safety Protocol"]
                    })
                return

            # 4. NMT to English
            english_query, nmt_in_ms = nmt_service.translate_to_english(combined_query, src_lang=self.language)
            latencies["nmt_in_ms"] = nmt_in_ms

            # 5. Hybrid RAG
            self._emit_status("Searching medical guidance...")
            rag_start = time.time()
            retrieved_docs = self.retriever.retrieve(english_query, top_k=settings.TOP_K_RETRIEVAL)
            latencies["rag_ms"] = (time.time() - rag_start) * 1000.0

            # 6. Qwen Reasoning
            self._emit_status("Preparing guidance...")
            response_schema, qwen_ms = qwen_backend.generate_clinical_guidance(
                query=english_query,
                retrieved_context=retrieved_docs[:settings.TOP_K_CONTEXT],
                visual_observations=observations,
                patient_profile=self.patient_profile,
                language=self.language
            )
            latencies["qwen_ms"] = qwen_ms


            # 7. Translation & TTS
            final_summary = response_schema.summary
            if self.language != "en":
                is_already_localized = any(ord(c) > 127 for c in final_summary)
                if not is_already_localized:
                    self._emit_status(f"Translating guidance to {self.language.upper()}...")
                    translated_summary, nmt_out_ms = nmt_service.translate_from_english(final_summary, tgt_lang=self.language)
                    latencies["nmt_out_ms"] = nmt_out_ms
                    final_summary = translated_summary

                    # Translate action items, warning signs, and referral
                    if response_schema.recommended_actions:
                        combined_actions = "\n".join(response_schema.recommended_actions)
                        t_act, _ = nmt_service.translate_from_english(combined_actions, tgt_lang=self.language)
                        response_schema.recommended_actions = [line.strip("- •0123456789. ") for line in t_act.split("\n") if line.strip()]

                    if response_schema.warning_signs:
                        combined_warn = "\n".join(response_schema.warning_signs)
                        t_warn, _ = nmt_service.translate_from_english(combined_warn, tgt_lang=self.language)
                        response_schema.warning_signs = [line.strip("- •0123456789. ") for line in t_warn.split("\n") if line.strip()]

                    if response_schema.referral:
                        t_ref, _ = nmt_service.translate_from_english(response_schema.referral, tgt_lang=self.language)
                        response_schema.referral = t_ref
                else:
                    logger.info(f"Clinical guidance already natively localized in {self.language.upper()}; bypassing NMT translation.")

            full_spoken_text = self._build_full_narration(final_summary, response_schema)

            self._emit_status("Speaking...")
            tts_start = time.time()
            tts_service.speak_async(
                text=full_spoken_text,
                language=self.language,
                on_finished=lambda: self._emit_status("Ready")
            )
            latencies["tts_ms"] = (time.time() - tts_start) * 1000.0

            total_ms = (time.time() - start_total) * 1000.0
            log_interaction_telemetry(req_id, self.language, "speech_camera", latencies, total_ms)

            ui_result = OutputValidator.format_for_ui(response_schema)
            ui_result["summary"] = final_summary
            ui_result["spoken_text"] = full_spoken_text
            ui_result["observations"] = observations
            ui_result["query"] = combined_query
            ui_result["is_emergency"] = False
            ui_result["latencies"] = latencies
            ui_result["total_ms"] = round(total_ms, 1)
            ui_result["patient_profile"] = self.patient_profile

            if self.signals:

                try:
                    self.signals.finished.emit(ui_result)
                except RuntimeError:
                    pass

        except Exception as e:
            logger.error(f"Error in multimodal worker: {e}", exc_info=True)
            if self.signals:
                try:
                    self.signals.error.emit(str(e))
                except RuntimeError:
                    pass

    def _build_full_narration(self, summary: str, schema: MedicalResponseSchema) -> str:
        """Assembles a comprehensive voice narration covering summary, actions, danger signs, and referral."""
        parts = [summary.strip()]
        if schema.recommended_actions:
            header = {
                "ta": "பரிந்துரைக்கப்பட்ட அடுத்த படிகள். ",
                "hi": "सुझाए गए अगले कदम. ",
                "te": "సూచించిన తదుపరి చర్యలు. ",
                "kn": "ಶಿಫಾರಸು ಮಾಡಿದ ಮುಂದಿನ ಹಂತಗಳು. ",
                "ml": "ശുപാർശ ചെയ്യുന്ന അടുത്ത ഘട്ടങ്ങൾ. "
            }.get(self.language, "Recommended next steps. ")
            parts.append(header + ". ".join(schema.recommended_actions))

        if schema.warning_signs:
            header = {
                "ta": "கவனிக்க வேண்டிய ஆபத்து அறிகுறிகள். ",
                "hi": "खतरे के लक्षण जिन पर ध्यान दें. ",
                "te": "ప్రమాద సంకేతాలు. ",
                "kn": "ಅಪಾಯದ ಲಕ್ಷಣಗಳು. ",
                "ml": "ശ്രദ്ധിക്കേണ്ട അപകട ലക്ഷണങ്ങൾ. "
            }.get(self.language, "Watch for danger signs. ")
            parts.append(header + ". ".join(schema.warning_signs))

        if schema.referral:
            header = {
                "ta": "மருத்துவ பரிந்துரை ஆலோசனை. ",
                "hi": "रेफरल मार्गदर्शन. ",
                "te": "సిఫార్సు మార్గదర్శకత్వం. ",
                "kn": "ರೆಫರಲ್ ಮಾರ್ಗದರ್ಶನ. ",
                "ml": "റഫറൽ മാർഗ്ഗനിർദ്ദേശം. "
            }.get(self.language, "Referral guidance. ")
            parts.append(header + schema.referral)

        return " ".join(parts)

    def _emit_status(self, text: str):
        if self.signals:
            try:
                self.signals.status_changed.emit(text)
            except RuntimeError:
                pass
