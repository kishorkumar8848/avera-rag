import pytest
from app.safety.red_flags import red_flag_detector, RedFlagDetector
from app.safety.validator import OutputValidator, MedicalResponseSchema
from app.safety.policies import ClinicalPolicyEngine


def test_red_flag_detection_cardiac():
    query = "Crushing chest pain radiating to left jaw"
    is_em, cats, msg = red_flag_detector.detect_red_flags(query)
    assert is_em is True
    assert "chest_pain_cardiac" in cats
    assert "108" in msg or "emergency" in msg.lower()


def test_red_flag_detection_respiratory():
    query = "Patient has severe difficulty breathing and cannot breathe"
    is_em, cats, msg = red_flag_detector.detect_red_flags(query)
    assert is_em is True
    assert "severe_respiratory_distress" in cats


def test_red_flag_detection_snake_bite():
    query = "Bitten by a venomous snake 10 minutes ago"
    is_em, cats, msg = red_flag_detector.detect_red_flags(query)
    assert is_em is True
    assert "poisoning_overdose" in cats


def test_red_flag_detection_stroke():
    query = "Sudden facial droop and slurred speech"
    is_em, cats, msg = red_flag_detector.detect_red_flags(query)
    assert is_em is True
    assert "stroke_neurological" in cats


def test_non_emergency_query():
    query = "Mild dry cough and runny nose for one day"
    is_em, cats, msg = red_flag_detector.detect_red_flags(query)
    assert is_em is False
    assert len(cats) == 0
    assert msg is None


def test_output_validator_valid_json():
    raw_json = '''
    {
      "summary": "Hydration and rest recommended for mild fever.",
      "observations": ["mild fever", "fatigue"],
      "possible_explanations": ["Viral illness"],
      "recommended_actions": ["Drink ORS fluids"],
      "warning_signs": ["Fever over 3 days"],
      "referral": "Visit PHC if worsening",
      "confidence": 0.85,
      "sources": ["MoHFW Guideline"]
    }
    '''
    is_valid, schema, err = OutputValidator.validate_and_parse(raw_json)
    assert is_valid is True
    assert schema is not None
    assert schema.confidence == 0.85
    assert len(schema.recommended_actions) == 1
    assert "ORS" in schema.recommended_actions[0]


def test_output_validator_markdown_wrapped_json():
    raw_text = """```json
    {
      "summary": "Summary text",
      "observations": [],
      "possible_explanations": [],
      "recommended_actions": ["Rest"],
      "warning_signs": [],
      "referral": "PHC",
      "confidence": 0.9,
      "sources": ["MedlinePlus"]
    }
    ```"""
    is_valid, schema, err = OutputValidator.validate_and_parse(raw_text)
    assert is_valid is True
    assert schema.summary == "Summary text"


def test_output_validator_invalid_json():
    raw_text = "This is not valid JSON."
    is_valid, schema, err = OutputValidator.validate_and_parse(raw_text)
    assert is_valid is False
    assert schema is None
    assert err is not None


def test_clinical_policy_fail_safe():
    safe, reason = ClinicalPolicyEngine.check_safety_guards(asr_confidence=0.2)
    assert safe is False
    assert "unclear" in reason.lower()

    safe2, reason2 = ClinicalPolicyEngine.check_safety_guards(rag_score=0.1)
    assert safe2 is False
    assert "reliable" in reason2.lower()
