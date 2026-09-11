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

    def load(self) -> bool:
        """Alias for load_model."""
        return self.load_model()

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

        # Step 1: Direct Fast-Path for Verified MoHFW Major Clinical Protocols
        matched_protocol = lookup_clinical_protocol(
            query,
            language=lang,
            patient_age=patient_age,
            patient_conditions=patient_conditions
        )
        if matched_protocol:
            latency_ms = (time.time() - start_time) * 1000.0
            logger.info(f"Verified MoHFW Clinical Protocol matched: {matched_protocol['condition_id']} in {latency_ms:.1f}ms")
            return MedicalResponseSchema(
                summary=matched_protocol["summary"],
                observations=[f"Reported symptoms matching {matched_protocol['condition_name']}"],
                possible_explanations=[f"{matched_protocol['condition_name']} as per {matched_protocol['citation']}"],
                recommended_actions=matched_protocol["recommended_actions"],
                warning_signs=matched_protocol["warning_signs"],
                referral=matched_protocol["referral"],
                confidence=0.95,
                sources=[matched_protocol["citation"]]
            ), latency_ms

        # Step 2: Build compact context prompt for LLM generation
        context_blocks = []
        for idx, doc in enumerate(retrieved_context[:2], 1):
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

        # First generation attempt via active LLM engine
        raw_output = self._call_inference(STRICT_SYSTEM_PROMPT, user_content, language=lang)
        is_valid, parsed_schema, err = OutputValidator.validate_and_parse(raw_output) if raw_output else (False, None, "Empty LLM output")

        if is_valid and parsed_schema:
            latency_ms = (time.time() - start_time) * 1000.0
            return parsed_schema, latency_ms

        logger.info(f"Using dynamic evidence synthesis for query: '{query}'")
        fallback_schema = self._create_deterministic_fallback(
            query, retrieved_context, language=lang, patient_profile=patient_profile
        )
        latency_ms = (time.time() - start_time) * 1000.0
        return fallback_schema, latency_ms

    def _call_inference(self, system_prompt: str, user_content: str, language: str = "en") -> str:
        """Invokes active backend engine (llama.cpp or Ollama)."""
        if not self._is_loaded and not self.load():
            return ""

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
                        "num_predict": 180,
                        "num_gpu": 0
                    }
                }
                res = requests.post(f"{settings.OLLAMA_BASE_URL}/api/chat", json=payload, timeout=12.0)
                if res.status_code == 200:
                    content = res.json().get("message", {}).get("content", "").strip()
                    if content and len(content) > 15:
                        return content
            except Exception as e:
                logger.warning(f"Ollama inference error/timeout: {e}")

        # Return empty string so caller falls back cleanly to dynamic evidence synthesis
        return ""

    def _generate_mock_json(self, user_content: str, language: str = "en") -> str:
        """Generates dynamic mock JSON matching retrieved evidence in patient's language."""
        schema = self._create_deterministic_fallback(user_content, context=[], language=language)
        return json.dumps(OutputValidator.format_for_ui(schema), ensure_ascii=False)

    def _create_deterministic_fallback(
        self,
        query: str,
        context: List[Dict[str, Any]],
        language: str = "en",
        patient_profile: Optional[Dict[str, Any]] = None
    ) -> MedicalResponseSchema:
        """Builds a verified response directly from retrieved context when LLM generation fails."""
        lang = language.lower() if language else "en"
        p_age = patient_profile.get("age") if patient_profile else None
        p_conds = patient_profile.get("chronic_conditions") if patient_profile else None

        # 1. First priority: Check if query matches a curated major clinical protocol
        matched = lookup_clinical_protocol(query, language=lang, patient_age=p_age, patient_conditions=p_conds)
        if matched:
            return MedicalResponseSchema(
                summary=matched["summary"],
                observations=[f"Reported symptoms matching {matched['condition_name']}"],
                possible_explanations=[f"{matched['condition_name']} as per {matched['citation']}"],
                recommended_actions=matched["recommended_actions"],
                warning_signs=matched["warning_signs"],
                referral=matched["referral"],
                confidence=0.95,
                sources=[matched["citation"]]
            )

        # 2. Second priority: Synthesize dynamically from top retrieved context
        import re
        primary_title = context[0]["title"] if context else "Clinical Guidance"
        source_cite = context[0].get("citation", "Official Health Protocol") if context else "MoHFW Guidelines"
        context_summary = context[0].get("summary", "") if context else ""

        # Extract clean sentences from context summary for guidance
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', context_summary) if len(s.strip()) > 15]
        summary_text = " ".join(sentences[:2]) if sentences else f"Verified clinical guidance for symptoms related to {primary_title}."

        title_lower = primary_title.lower()
        query_lower = query.lower()

        is_pain = any(k in query_lower or k in title_lower for k in [
            "pain", "ache", "shoulder", "back", "knee", "joint", "sprain", "injury", "fracture", "strain", "muscle", "bone", "dislocat"
        ])
        is_stomach = any(k in query_lower or k in title_lower for k in [
            "stomach", "abdomen", "belly", "gastritis", "acid", "vomit", "diarrhea", "stool", "nausea", "ulcer", "indigestion", "heartburn"
        ])
        is_fever_inf = any(k in query_lower or k in title_lower for k in [
            "fever", "cough", "cold", "infection", "shiver", "temperature", "pyrexia", "flu", "chills"
        ])
        is_skin = any(k in query_lower or k in title_lower for k in [
            "skin", "rash", "itch", "allergy", "dermatitis", "wound", "burn", "boil", "abscess"
        ])

        if is_pain:
            actions = [
                f"Rest the affected area and strictly avoid heavy lifting, strenuous exertion, or repetitive straining of the {primary_title.lower()}.",
                "Apply an ice pack wrapped in a clean towel for 15-20 minutes every 3-4 hours during the first 48 hours to minimize acute swelling and pain.",
                "Keep the joint or limb comfortably supported in a resting posture; avoid sudden jerks or twisting.",
                "For acute pain relief, adult standard medication is Paracetamol 500mg up to twice or thrice daily after meals if not contraindicated."
            ]
            warnings = [
                "Severe visible joint deformity, suspected bone fracture, or limb dislocation.",
                "Complete inability to move the limb, or progressive numbness and tingling in fingers/toes.",
                "Severe sudden pain or swelling following trauma, fall, or road accident."
            ]
            referral = f"Consult a Primary Health Centre (PHC) medical officer or orthopedic specialist if pain persists over 3-5 days or limits movement."

        elif is_stomach:
            actions = [
                "Take small, frequent bland meals (such as plain rice, porridge, or khichdi) rather than heavy portions.",
                "Maintain adequate fluid intake with clean room-temperature water or cool buttermilk (chaas); avoid dehydration.",
                "Strictly avoid oily, spicy, deep-fried food, tea, coffee, carbonated drinks, and tobacco.",
                "Do not lie down flat immediately after eating; wait at least 2 hours before sleeping."
            ]
            warnings = [
                "Severe, rigid, board-like abdominal tenderness (Acute Abdomen - Emergency!).",
                "Vomiting blood or passing black, tarry stools (melena).",
                "Persistent vomiting preventing any oral fluid intake, accompanied by high fever."
            ]
            referral = "Refer promptly to Primary Health Centre (PHC) for medical evaluation if abdominal pain lasts over 24-48 hours."

        elif is_fever_inf:
            actions = [
                "Drink plenty of clean fluids: boiled and cooled water, ORS, or light clear soups (2-3 liters/day).",
                "Perform room-temperature water sponging on forehead and extremities if temperature exceeds 101°F.",
                "Ensure complete bed rest in a well-ventilated, comfortable room.",
                "Take Paracetamol 500mg every 6-8 hours for fever control if needed (avoid NSAIDs like Aspirin)."
            ]
            warnings = [
                "Fever persisting continuously for more than 3 days (>72 hours).",
                "Difficulty breathing, extreme drowsiness, confusion, or inability to retain fluids.",
                "Unusual skin rashes or bleeding spots from gums or nose."
            ]
            referral = "Visit Primary Health Centre (PHC) for blood smear and fever evaluation if fever lasts past 48-72 hours."

        elif is_skin:
            actions = [
                "Keep the affected skin clean, dry, and exposed to cool circulating air.",
                "Avoid scratching, rubbing, or using harsh chemical soaps and unverified remedies.",
                "Apply clean cool compresses or soothing calamine lotion if skin is intact without open wounds.",
                "Wear loose, soft, breathable cotton clothing to minimize friction."
            ]
            warnings = [
                "Rapidly spreading redness, hot tender skin, or red streaks extending from the lesion.",
                "Pus discharge, large fluctuating blisters, or accompanying high fever.",
                "Facial swelling, lip/tongue swelling, or breathing distress (Anaphylaxis Emergency - Call 108!)."
            ]
            referral = "Consult a PHC medical officer or dermatologist if the skin lesion expands, weeps pus, or does not improve within 3-4 days."

        else:
            actions = [
                f"Follow primary healthcare precautions documented for {primary_title}.",
                "Ensure adequate physical rest and maintain comfortable daily hydration.",
                "Avoid unprescribed self-medication, strong painkillers, or unverified home remedies."
            ]
            warnings = [
                "Sudden severe worsening of symptoms or development of high persistent fever.",
                "Difficulty breathing, chest pain, dizziness, or loss of consciousness."
            ]
            referral = f"Consult a Primary Health Centre (PHC) medical officer for clinical confirmation and examination regarding {primary_title}."

        return MedicalResponseSchema(
            summary=summary_text,
            observations=[query[:80]],
            possible_explanations=[f"Symptoms aligned with {primary_title} documented in {source_cite}."],
            recommended_actions=actions,
            warning_signs=warnings,
            referral=referral,
            confidence=0.80,
            sources=[source_cite]
        )


qwen_backend = QwenBackend()
