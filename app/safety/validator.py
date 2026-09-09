import json
import re
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field, ValidationError


class MedicalResponseSchema(BaseModel):
    """Structured clinical response schema enforced on Qwen output."""
    summary: str = Field(description="Concise 1-2 sentence overview suitable for audio synthesis.")
    observations: List[str] = Field(default_factory=list, description="Key symptoms or visual findings reported.")
    possible_explanations: List[str] = Field(default_factory=list, description="General health explanations based on retrieved context.")
    recommended_actions: List[str] = Field(default_factory=list, description="Immediate non-invasive home care or hydration steps.")
    warning_signs: List[str] = Field(default_factory=list, description="Signs requiring emergency care.")
    referral: str = Field(description="Guidance on when and where to see a healthcare professional.")
    confidence: float = Field(ge=0.0, le=1.0, default=0.7, description="Estimated confidence score based on protocol coverage.")
    sources: List[str] = Field(default_factory=list, description="Explicit source citations (e.g. MedlinePlus or MoHFW STG).")


class OutputValidator:
    """
    Validates, repairs, and parses structured clinical responses from the LLM.
    """

    @classmethod
    def clean_json_string(cls, raw_text: str) -> str:
        """Extracts and auto-repairs JSON object substring even if LLM output was truncated or wrapped."""
        raw_text = raw_text.strip()
        # Remove ```json ... ``` wrapper if present
        json_match = re.search(r"```(?:json)?\s*(\{.*)", raw_text, re.DOTALL)
        if json_match:
            candidate = json_match.group(1).split("```")[0].strip()
        else:
            candidate = raw_text

        start_idx = candidate.find("{")
        if start_idx != -1:
            candidate = candidate[start_idx:].strip()

        # If it already parses cleanly, return it
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass

        # Auto-repair unclosed quotes and brackets for streaming/truncated LLM outputs
        repaired = candidate
        # If odd number of unescaped quotes, close the quote
        unescaped_quotes = len(re.findall(r'(?<!\\)"', repaired))
        if unescaped_quotes % 2 != 0:
            repaired += '"'

        # Remove trailing comma inside array/object or at end of text
        repaired = re.sub(r',\s*([\]\}])', r'\1', repaired)
        repaired = re.sub(r',\s*$', '', repaired)

        # Balance open brackets
        stack = []
        in_string = False
        i = 0
        while i < len(repaired):
            ch = repaired[i]
            if ch == '\\' and in_string:
                i += 2
                continue
            if ch == '"':
                in_string = not in_string
            elif not in_string:
                if ch in ('{', '['):
                    stack.append(ch)
                elif ch == '}' and stack and stack[-1] == '{':
                    stack.pop()
                elif ch == ']' and stack and stack[-1] == '[':
                    stack.pop()
            i += 1

        while stack:
            open_bracket = stack.pop()
            if open_bracket == '{':
                repaired += '}'
            elif open_bracket == '[':
                repaired += ']'

        return repaired

    @classmethod
    def validate_and_parse(cls, raw_text: str) -> Tuple[bool, Optional[MedicalResponseSchema], Optional[str]]:
        """
        Parses and validates raw LLM output against the schema.
        Returns:
            (is_valid: bool, parsed_schema: Optional[MedicalResponseSchema], error_message: Optional[str])
        """
        cleaned_json = cls.clean_json_string(raw_text)
        try:
            data = json.loads(cleaned_json)
            # Ensure required string fields exist with fallbacks
            if "summary" not in data or not data["summary"]:
                data["summary"] = "Clinical information retrieved for patient query."
            if "referral" not in data or not data["referral"]:
                data["referral"] = "Consult a primary health center (PHC) medical officer if symptoms persist."
            if "confidence" not in data:
                data["confidence"] = 0.65

            validated = MedicalResponseSchema(**data)
            return True, validated, None
        except (json.JSONDecodeError, ValidationError) as err:
            return False, None, str(err)

    @classmethod
    def format_for_ui(cls, schema: MedicalResponseSchema) -> Dict[str, Any]:
        """Converts structured schema into a clean, presentation-ready display object."""
        return {
            "summary": schema.summary,
            "observations": schema.observations,
            "possible_explanations": schema.possible_explanations,
            "recommended_actions": schema.recommended_actions,
            "warning_signs": schema.warning_signs,
            "referral": schema.referral,
            "confidence": schema.confidence,
            "sources": schema.sources,
            "tts_text": cls.generate_tts_summary(schema)
        }

    @classmethod
    def generate_tts_summary(cls, schema: MedicalResponseSchema) -> str:
        """
        Generates a concise, natural spoken script (<= 2 sentences) optimized for Bhashini TTS.
        """
        lines = [schema.summary]
        if schema.recommended_actions:
            lines.append(f"Recommended step: {schema.recommended_actions[0]}.")
        if schema.warning_signs:
            lines.append(f"Watch for warning signs: {schema.warning_signs[0]}.")
        lines.append(schema.referral)
        return " ".join(lines)
