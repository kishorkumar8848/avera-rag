from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from app.safety.validator import MedicalResponseSchema

Tuple_Check = Tuple[bool, Optional[str]]


FALLBACK_UNCERTAIN_MESSAGE = (
    "I do not have enough reliable medical information to provide safe guidance for this query. "
    "Please consult a qualified healthcare professional or visit your nearest Primary Health Centre (PHC)."
)

EMERGENCY_DISCLAIMER = (
    "IMPORTANT: Vyoma is an offline clinical guidance and frontline-support assistant, not a doctor. "
    "This guidance is grounded exclusively on verified health protocols and does not constitute a definitive medical diagnosis."
)


class ClinicalPolicyEngine:
    """
    Enforces conservative medical safety rules, fail-safe fallbacks,
    confidence cutoffs, and official Indian protocol precedence.
    """

    MIN_ASR_CONFIDENCE = 0.50
    MIN_RAG_SCORE = 0.25
    MIN_OVERALL_CONFIDENCE = 0.40

    @classmethod
    def check_safety_guards(
        cls,
        asr_confidence: float = 1.0,
        rag_score: float = 1.0,
        has_context: bool = True,
        image_quality_acceptable: bool = True
    ) -> Tuple_Check:
        """
        Validates pipeline parameters before permitting LLM reasoning.
        Returns:
            (is_safe_to_proceed: bool, reason: Optional[str])
        """
        if asr_confidence < cls.MIN_ASR_CONFIDENCE:
            return False, "Audio input was unclear or confidence too low. Please speak closer to the microphone."

        if not image_quality_acceptable:
            return False, "The captured image was blurry or too dark. Please capture a clear, well-lit photo."

        if not has_context or rag_score < cls.MIN_RAG_SCORE:
            return False, FALLBACK_UNCERTAIN_MESSAGE

        return True, None

    @classmethod
    def create_fail_safe_response(cls, reason: str) -> MedicalResponseSchema:
        """Constructs a deterministic, non-hallucinatory safe response when confidence is low."""
        return MedicalResponseSchema(
            summary=reason,
            observations=[],
            possible_explanations=[],
            recommended_actions=["Seek in-person evaluation from an Auxiliary Nurse Midwife (ANM), ASHA, or medical officer."],
            warning_signs=["Fever over 3 days, breathlessness, vomiting blood, or extreme weakness."],
            referral="Please visit the nearest Primary Health Centre (PHC) or Community Health Centre (CHC).",
            confidence=0.1,
            sources=["Safety Policy Guard: Conservative Medical Threshold"]
        )

    @classmethod
    def enforce_protocol_precedence(cls, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ensures official Indian clinical protocols (MoHFW, NHM, ASHA) take priority
        over general educational information (MedlinePlus) for actionable guidance.
        """
        indian_protocols = [s for s in sources if s.get("source") == "Indian_Protocol"]
        general_education = [s for s in sources if s.get("source") != "Indian_Protocol"]

        # Sort Indian protocols to top of retrieved context
        return indian_protocols + general_education
