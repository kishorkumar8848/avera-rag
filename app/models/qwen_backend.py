import json
import time
import requests
from typing import Dict, Any, List, Optional, Tuple

from app.core.config import settings
from app.core.logging import logger
from app.safety.validator import OutputValidator, MedicalResponseSchema
from app.models.manager import model_manager

from app.safety.clinical_protocols import lookup_clinical_protocol

# Strict 19-Rule Medical Grounded System Prompt with Few-Shot Exemplar
STRICT_SYSTEM_PROMPT = """You are Vyoma, an offline medical clinical decision support assistant for frontline health workers in community health centers.
You must adhere strictly to these 19 rules:
1. You are an offline medical information and frontline-support assistant.
2. You are not a doctor and do not claim to make definitive diagnoses.
3. Formulate clear, authoritative clinical guidance based strictly on the retrieved medical evidence.
4. Keep the summary clinically precise, objective, and directly relevant to the patient's symptoms.
5. Prioritize non-pharmacological home care, hydration, rest, and safe fever management.
6. Emphasize explicit warning signs and danger flags requiring urgent hospital transfer.
7. Prefer official Indian clinical protocols (MoHFW/NHM) over general educational sources.
8. If evidence is insufficient, state: "I do not have enough reliable information to provide safe guidance."
9. Never invent drug doses or prescribe prescription-only antibiotics/steroids.
10. Output MUST strictly be a single valid raw JSON object matching this schema:
{
  "summary": "Clear, clinically sound 1-2 sentence overview suitable for audio synthesis",
  "observations": ["Observed symptom 1", "Observed symptom 2"],
  "possible_explanations": ["Possible health explanation based on context"],
  "recommended_actions": ["Immediate non-invasive home care step"],
  "warning_signs": ["Emergency warning sign requiring immediate referral"],
  "referral": "Guidance on when and where to see a healthcare professional",
  "confidence": 0.90,
  "sources": ["Source name and topic from context"]
}

FEW-SHOT CLINICAL EXAMPLE:
Query: "I have high fever and severe shivering for two days"
Output:
{
  "summary": "The patient presents with acute febrile illness accompanied by rigors, characteristic of an acute viral or systemic infection. Immediate focus must be on adequate hydration, rest, temperature monitoring, and ruling out red flag complications.",
  "observations": ["High body temperature (>100°F)", "Severe shivering/rigors for 2 days"],
  "possible_explanations": ["Acute viral fever", "Early vector-borne illness (Dengue/Malaria)"],
  "recommended_actions": [
    "Drink plenty of fluids (ORS, boiled water, tender coconut water) at least 2-3 liters/day",
    "Perform tepid sponging with room-temperature water if temperature exceeds 101°F",
    "Ensure complete bed rest in a well-ventilated room",
    "Take paracetamol 500mg every 6-8 hours for fever control (avoid Aspirin/Ibuprofen)"
  ],
  "warning_signs": [
    "Fever persisting continuously for more than 3 days (>72 hours)",
    "Inability to retain liquids or persistent vomiting",
    "Bleeding from gums or unusual skin rashes/red spots",
    "Severe breathlessness or extreme lethargy"
  ],
  "referral": "Visit the nearest Primary Health Centre (PHC) for blood smear and complete blood count testing if fever persists past 48-72 hours, or immediately if any warning sign occurs.",
  "confidence": 0.95,
  "sources": ["MoHFW Standard Treatment Guidelines: Acute Viral Fever"]
}
DO NOT write any markdown ticks or conversational text before or after the JSON. Output ONLY raw JSON."""


class QwenBackend:
    """
    Manages Qwen2.5-1.5B-Instruct inference supporting:
    1. Direct llama.cpp with CUDA acceleration (preferred edge runtime).
    2. Local Ollama REST API compatibility (fallback).
    3. Mock reasoning fallback for testing environments.
    """

    def __init__(self):
        self.backend_type = settings.LLM_BACKEND
        self.model_path = settings.resolve_path(settings.LLM_MODEL_PATH)
        self.llama_engine = None
        self._is_loaded = False

    def load_model(self) -> bool:
        """Loads model into memory if not already active."""
        if self._is_loaded:
            return True

        # Check memory headroom (~1.2GB required for Qwen2.5-1.5B Q4_K_M)
        if not model_manager.check_memory_headroom(required_mb=1200.0):
            logger.error("Insufficient memory to load Qwen2.5-1.5B.")
            return False

        if self.backend_type == "llama_cpp":
            try:
                import importlib
                llama_module = importlib.import_module("llama_cpp")
                Llama = getattr(llama_module, "Llama")
                logger.info(f"Loading Qwen2.5-1.5B-Instruct via llama.cpp from {self.model_path}...")
                self.llama_engine = Llama(
                    model_path=str(self.model_path),
                    n_ctx=settings.LLM_N_CTX,
                    n_gpu_layers=settings.LLM_N_GPU_LAYERS,
                    verbose=settings.DEBUG
                )
                self._is_loaded = True
                model_manager.register_model("qwen_llm", self)
                logger.info("Qwen2.5-1.5B loaded successfully via llama.cpp.")
                return True
            except Exception as e:
                logger.warning(f"Failed to load via llama.cpp: {e}. Switching to Ollama fallback...")
                self.backend_type = "ollama"

        if self.backend_type == "ollama":
            if self._check_ollama():
                self._is_loaded = True
                model_manager.register_model("qwen_llm", self)
                logger.info("Qwen backend connected via Ollama.")
                return True
            else:
                logger.warning("Ollama service not reachable. Running in protocol-grounded mock mode.")
                return False

        return False

    def _resolve_ollama_model(self) -> str:
        """Finds matching installed Ollama model name (e.g. qwen2.5:1.5b-instruct-q4_K_M)."""
        try:
            res = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2.0)
            if res.status_code == 200:
                available = [m.get("name", "") for m in res.json().get("models", [])]
                if settings.OLLAMA_MODEL in available:
                    return settings.OLLAMA_MODEL
                for name in available:
                    if "qwen2.5" in name or "qwen" in name:
                        logger.info(f"Resolved Ollama model '{settings.OLLAMA_MODEL}' to installed '{name}'")
                        return name
                if available:
                    return available[0]
        except Exception:
            pass
        return settings.OLLAMA_MODEL

    def _check_ollama(self) -> bool:
        """Verifies if local Ollama daemon is running."""
        try:
            res = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2.0)
            return res.status_code == 200
        except Exception:
            return False

    def unload(self):
        """Releases model from memory."""
        if self.llama_engine is not None:
            del self.llama_engine
            self.llama_engine = None
        self._is_loaded = False

    load = load_model

    def generate_clinical_guidance(
        self,
        query: str,
        retrieved_context: List[Dict[str, Any]],
        visual_observations: Optional[List[str]] = None,
        patient_profile: Optional[Dict[str, Any]] = None,
        language: str = "en"
    ) -> Tuple[Optional[MedicalResponseSchema], float]:
        """
        Generates grounded, non-diagnostic clinical advice with few-shot guidance,
        JSON schema enforcement, and 1x retry on validation error.
        Returns:
            (validated_schema: MedicalResponseSchema, latency_ms: float)
        """
        start_time = time.time()
        lang = language.lower() if language else "en"

        patient_age = patient_profile.get("age") if patient_profile else None
        patient_conditions = patient_profile.get("chronic_conditions") if patient_profile else None

        # Check for direct match against verified MoHFW Major Clinical Protocols in patient's language
        matched_protocol = lookup_clinical_protocol(
            query,
            language=lang,
            patient_age=patient_age,
            patient_conditions=patient_conditions
        )
        if matched_protocol:
            protocol_block = {
                "title": matched_protocol["condition_name"],
                "citation": matched_protocol["citation"],
                "summary": (
                    f"Official Guidance: {matched_protocol['summary']} "
                    f"Recommended Actions: {'; '.join(matched_protocol['recommended_actions'][:3])}. "
                    f"Danger Flags: {'; '.join(matched_protocol['warning_signs'][:3])}. "
                    f"Referral: {matched_protocol['referral']}"
                )
            }
            retrieved_context = [protocol_block] + [d for d in retrieved_context if d.get("title") != protocol_block["title"]]

        # Build context prompt
        context_blocks = []
        for idx, doc in enumerate(retrieved_context, 1):
            source_citation = doc.get("citation", doc.get("title", "Clinical Protocol"))
            summary = doc.get("summary", "")
            context_blocks.append(f"--- Evidence Chunk {idx} ---\nSource: {source_citation}\n{summary}")
        full_context_text = "\n\n".join(context_blocks)

        user_content = ""
        if patient_profile:
            p_name = patient_profile.get("name", "Citizen")
            p_age = patient_profile.get("age", "Unknown")
            p_gender = patient_profile.get("gender", "")
            p_conds = ", ".join(patient_profile.get("chronic_conditions", [])) or "None reported"
            p_allergies = ", ".join(patient_profile.get("allergies", [])) or "None"
            user_content += (
                f"PATIENT PROFILE:\n"
                f"- Name: {p_name} | Age: {p_age} years | Gender: {p_gender}\n"
                f"- Known Comorbidities: {p_conds}\n"
                f"- Known Allergies: {p_allergies}\n\n"
            )

        user_content += f"Patient Query: {query}\n\n"
        if visual_observations:
            user_content += f"Visual Observations: {', '.join(visual_observations)}\n\n"
        user_content += f"Retrieved Medical Evidence:\n{full_context_text}\n\nProvide structured clinical guidance:"

        # First generation attempt
        raw_output = self._call_inference(STRICT_SYSTEM_PROMPT, user_content, language=lang)
        is_valid, parsed_schema, err = OutputValidator.validate_and_parse(raw_output)

        if is_valid and parsed_schema:
            latency_ms = (time.time() - start_time) * 1000.0
            return parsed_schema, latency_ms

        logger.warning(f"Initial schema validation failed: {err}. Triggering 1x self-correction retry...")

        # 1x Retry self-correction prompt
        retry_prompt = (
            f"PREVIOUS INVALID OUTPUT:\n{raw_output}\n\n"
            f"VALIDATION ERROR:\n{err}\n\n"
            "Correct the JSON so it strictly matches the required medical schema without markdown fences. Provide the valid JSON now:"
        )
        retry_raw_output = self._call_inference(STRICT_SYSTEM_PROMPT, retry_prompt, language=lang)
        is_valid_retry, parsed_schema_retry, err_retry = OutputValidator.validate_and_parse(retry_raw_output)

        if is_valid_retry and parsed_schema_retry:
            latency_ms = (time.time() - start_time) * 1000.0
            logger.info("Self-correction retry succeeded!")
            return parsed_schema_retry, latency_ms

        logger.error(f"Retry validation also failed ({err_retry}). Using deterministic clinical protocol fallback.")
        fallback_schema = self._create_deterministic_fallback(query, retrieved_context, language=lang)
        latency_ms = (time.time() - start_time) * 1000.0
        return fallback_schema, latency_ms

    def _call_inference(self, system_prompt: str, user_content: str, language: str = "en") -> str:
        """Invokes active backend engine (llama.cpp or Ollama)."""
        if not self._is_loaded and not self.load():
            return self._generate_mock_json(user_content, language=language)

        if self.backend_type == "llama_cpp" and self.llama_engine is not None:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            try:
                response = self.llama_engine.create_chat_completion(
                    messages=messages,
                    temperature=settings.LLM_TEMPERATURE,
                    top_p=settings.LLM_TOP_P,
                    max_tokens=settings.LLM_MAX_NEW_TOKENS
                )
                return response["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.error(f"llama.cpp inference error: {e}")

        if self.backend_type == "ollama" and self._check_ollama():
            try:
                resolved_name = self._resolve_ollama_model()
                payload = {
                    "model": resolved_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": settings.LLM_TEMPERATURE,
                        "top_p": settings.LLM_TOP_P,
                        "num_predict": settings.LLM_MAX_NEW_TOKENS
                    }
                }
                res = requests.post(f"{settings.OLLAMA_BASE_URL}/api/chat", json=payload, timeout=20.0)
                if res.status_code == 200:
                    return res.json().get("message", {}).get("content", "").strip()
            except Exception as e:
                logger.error(f"Ollama inference error: {e}")

        # Fallback protocol-grounded mock response
        return self._generate_mock_json(user_content, language=language)

    def _generate_mock_json(self, user_content: str, language: str = "en") -> str:
        """Generates deterministic mock JSON matching retrieved evidence in patient's language."""
        lang = language.lower() if language else "en"

        if lang == "ta":
            return json.dumps({
                "summary": "சரிபார்க்கப்பட்ட வழிகாட்டுதலின்படி மருத்துவ முதலுதவி ஆலோசனை வழங்கப்பட்டுள்ளது.",
                "observations": ["அறிவிக்கப்பட்ட மருத்துவ அறிகுறிகள் வழிகாட்டுதலுடன் பொருந்துகின்றன"],
                "possible_explanations": ["ஆரம்ப சுகாதார வழிகாட்டுதல்களில் பதிவு செய்யப்பட்டுள்ள பொதுவான உடல்நிலை"],
                "recommended_actions": [
                    "நோயாளிக்கு வாய்வழி திரவங்கள் (ORS / சுத்தமான தண்ணீர்) மூலம் நீர்ச்சத்து குறையாமல் பார்த்துக் கொள்ளவும்",
                    "குளிர்ந்த, நல்ல காற்றோட்டமான அறையில் ஓய்வெடுக்கவும்",
                    "அதிக காய்ச்சல் இருந்தால் வழிகாட்டுதலின்படி பாராசிட்டமால் கொடுக்கவும்"
                ],
                "warning_signs": [
                    "மூச்சுத்திணறல், அதீத சோர்வு, தொடர் வாந்தி அல்லது 3 நாட்களுக்கு மேல் நீடிக்கும் காய்ச்சல்"
                ],
                "referral": "உறுதியான மருத்துவ பரிசோதனைக்கு அருகில் உள்ள ஆரம்ப சுகாதார நிலையத்திற்கு (PHC) செல்லவும்.",
                "confidence": 0.88,
                "sources": ["தேசிய சுகாதார இயக்கம் (NHM) வழிகாட்டுதல்"]
            }, ensure_ascii=False)

        elif lang == "hi":
            return json.dumps({
                "summary": "सत्यापित प्राथमिक स्वास्थ्य दिशानिर्देशों के अनुसार नैदानिक मार्गदर्शन प्रदान किया गया है।",
                "observations": ["बताए गए लक्षण प्राथमिक स्वास्थ्य मार्गदर्शिका से मेल खाते हैं"],
                "possible_explanations": ["प्राथमिक उपचार दिशानिर्देशों के अंतर्गत स्थिति"],
                "recommended_actions": [
                    "मरीज को ओआरएस (ORS) अथवा साफ पानी देकर निर्जलीकरण से बचाएं",
                    "हवादार और शांत कमरे में पर्याप्त आराम करने दें",
                    "तेज बुखार होने पर प्रोटोकॉल के अनुसार पेरासिटामोल दें"
                ],
                "warning_signs": [
                    "सांस लेने में कठिनाई, अत्यधिक सुस्ती, लगातार उल्टी या 3 दिन से अधिक तेज बुखार"
                ],
                "referral": "पुष्टि और उपचार के लिए तुरंत नजदीकी प्राथमिक स्वास्थ्य केंद्र (PHC) जाएं।",
                "confidence": 0.88,
                "sources": ["राष्ट्रीय स्वास्थ्य मिशन (NHM) दिशानिर्देश"]
            }, ensure_ascii=False)

        elif lang == "gu":
            return json.dumps({
                "summary": "ચકાસાયેલ માર્ગદર્શિકા મુજબ પ્રાથમિક આરોગ્ય સંભાળ સલાહ આપવામાં આવી છે.",
                "observations": ["જણાવેલ લક્ષણો માર્ગદર્શિકા સાથે સુસંગત છે"],
                "possible_explanations": ["પ્રાથમિક આરોગ્ય માર્ગદર્શિકા હેઠળ સામાન્ય સ્થિતિ"],
                "recommended_actions": [
                    "દર્દીને ORS અથવા સ્વચ્છ પાણી આપીને ડિહાઇડ્રેશન ટાળો",
                    "હવાઉજાસ વાળા ઓરડામાં પૂરતો આરામ કરવા દો",
                    "તીવ્ર તાવ હોય તો માર્ગદર્શિકા મુજબ પેરાસિટામોલ આપો"
                ],
                "warning_signs": [
                    "શ્વાસ લેવામાં તકલીફ, વધુ પડતી સુસ્તી અથવા 3 દિવસથી વધુ સમય રહેતો તાવ"
                ],
                "referral": "ચોક્કસ તપાસ માટે નજીકના પ્રાથમિક આરોગ્ય કેન્દ્ર (PHC) નો સંપર્ક કરો.",
                "confidence": 0.88,
                "sources": ["રાષ્ટ્રીય આરોગ્ય મિશન (NHM) માર્ગદર્શિકા"]
            }, ensure_ascii=False)

        return json.dumps({
            "summary": "Clinical guidance retrieved from verified offline protocols.",
            "observations": ["Reported medical symptoms matching retrieved guidance"],
            "possible_explanations": ["Condition documented in primary healthcare guidelines"],
            "recommended_actions": [
                "Keep patient hydrated with oral fluids (ORS / clean water)",
                "Rest in a cool, well-ventilated area",
                "Administer Paracetamol for high fever if indicated in protocol"
            ],
            "warning_signs": [
                "Breathing difficulty, confusion, uncontrollable vomiting, or fever lasting > 3 days"
            ],
            "referral": "Refer promptly to a Primary Health Centre (PHC) medical officer for clinical confirmation.",
            "confidence": 0.78,
            "sources": ["MoHFW Standard Treatment Guidelines", "MedlinePlus Health Education"]
        })

    def _create_deterministic_fallback(self, query: str, context: List[Dict[str, Any]], language: str = "en") -> MedicalResponseSchema:
        """Builds a verified response directly from retrieved context when LLM generation fails."""
        lang = language.lower() if language else "en"
        # 1. First priority: Check if query matches a curated major clinical protocol
        matched = lookup_clinical_protocol(query, language=lang)
        if matched:
            return MedicalResponseSchema(
                summary=matched["summary"],
                observations=[f"Patient reported symptoms matching {matched['condition_name']}"],
                possible_explanations=[f"{matched['condition_name']} as per {matched['citation']}"],
                recommended_actions=matched["recommended_actions"],
                warning_signs=matched["warning_signs"],
                referral=matched["referral"],
                confidence=0.95,
                sources=[matched["citation"]]
            )

        # 2. Second priority: Synthesize from top retrieved context
        import re
        primary_title = context[0]["title"] if context else "Clinical Guidance"
        source_cite = context[0].get("citation", "Official Health Protocol") if context else "MoHFW Guidelines"
        context_summary = context[0].get("summary", "") if context else ""

        # Extract clean sentences from context summary for guidance
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', context_summary) if len(s.strip()) > 15]
        summary_text = " ".join(sentences[:2]) if sentences else f"Verified clinical guidance for symptoms related to {primary_title}."

        return MedicalResponseSchema(
            summary=summary_text,
            observations=[query[:80]],
            possible_explanations=[f"Symptom complex aligned with {primary_title} documented in {source_cite}."],
            recommended_actions=[
                "Rest and maintain adequate oral fluid intake (ORS, clean water, or warm soups)",
                "Monitor temperature and symptom progression closely",
                "Apply gentle joint support or cold compress for joint discomfort",
                "Avoid unprescribed antibiotics or self-medication without professional advice"
            ],
            warning_signs=[
                "High persistent fever lasting more than 3 days",
                "Severe disabling joint swelling or inability to bear weight",
                "Signs of bleeding, severe persistent vomiting, confusion, or breathing difficulty"
            ],
            referral="Consult a Primary Health Centre (PHC) medical officer or physician promptly if symptoms persist or red flags appear.",
            confidence=0.75,
            sources=[source_cite]
        )


qwen_backend = QwenBackend()
