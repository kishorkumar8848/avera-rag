import re
from typing import Dict, List, Optional, Tuple


# Red flag emergency detection definitions
# Matches English and transliterated Indic keywords/phrases
EMERGENCY_PATTERNS = {
    "chest_pain_cardiac": [
        r"\b(chest pain|crushing pain|tightness in chest|heart attack|angina|pain radiating to (arm|jaw|back))\b",
        r"\b(nenju vali|seene me dard|chhati me dard)\b"
    ],
    "severe_respiratory_distress": [
        r"\b(difficulty breathing|cannot breathe|severe shortness of breath|gasping|choking|cyanosis|blue lips|stridor)\b",
        r"\b(moochu thinaral|saans lene me takleef|saans phoolna)\b"
    ],
    "unconsciousness_altered_mental": [
        r"\b(unconscious|passed out|fainted|unresponsive|coma|loss of consciousness|altered mental state|severe confusion)\b",
        r"\b(mayakkam|behosh|hosh ud gaya)\b"
    ],
    "severe_hemorrhage": [
        r"\b(severe bleeding|uncontrolled bleeding|coughing blood|vomiting blood|hemoptysis|hematemesis|profuse bleeding)\b",
        r"\b(ratha kayam|khoon ki ulti|khoon behna)\b"
    ],
    "stroke_neurological": [
        r"\b(stroke|facial droop|slurred speech|sudden weakness|one sided paralysis|hemiplegia|sudden numbness)\b",
        r"\b(pakshavatham|lakwa|paralysis)\b"
    ],
    "seizures_convulsions": [
        r"\b(seizure|convulsions|epileptic fit|fits|jerking violently|continuous shaking)\b",
        r"\b(valippu|mirgi|daura)\b"
    ],
    "severe_anaphylaxis": [
        r"\b(anaphylaxis|swollen tongue|swollen throat|severe allergic reaction|face swelling and breathing trouble)\b"
    ],
    "poisoning_overdose": [
        r"\b(poisoning|swallowed poison|consumed pesticide|insecticide ingestion|snake\s*bite|bitten.*snake|venomous snake|scorpion sting|drug overdose)\b",
        r"\b(visham|zeher|paambu kadi|saanp kaatna)\b"
    ]
}


class RedFlagDetector:
    """
    Deterministic safety evaluator that identifies life-threatening red flags
    independent of LLM inference.
    """

    def __init__(self, patterns: Optional[Dict[str, List[str]]] = None):
        self.patterns = patterns or EMERGENCY_PATTERNS
        self._compiled_patterns = {
            category: [re.compile(p, re.IGNORECASE) for p in pattern_list]
            for category, pattern_list in self.patterns.items()
        }

    def detect_red_flags(self, text: str) -> Tuple[bool, List[str], Optional[str]]:
        """
        Analyzes query text for clinical red flags.
        Returns:
            (is_emergency: bool, detected_categories: List[str], urgent_message: Optional[str])
        """
        if not text:
            return False, [], None

        detected = []
        for category, regex_list in self._compiled_patterns.items():
            for regex in regex_list:
                if regex.search(text):
                    detected.append(category)
                    break

        if detected:
            escalation_message = self._build_escalation_message(detected)
            return True, detected, escalation_message

        return False, [], None

    def _build_escalation_message(self, categories: List[str]) -> str:
        """Constructs an urgent escalation advisory advising immediate medical attention."""
        category_labels = {
            "chest_pain_cardiac": "Possible Cardiac Event / Chest Pain",
            "severe_respiratory_distress": "Critical Breathing Difficulty",
            "unconsciousness_altered_mental": "Altered Consciousness / Unresponsiveness",
            "severe_hemorrhage": "Severe Hemorrhage / Acute Bleeding",
            "stroke_neurological": "Suspected Stroke / Acute Neurological Deficit",
            "seizures_convulsions": "Active Seizure / Convulsions",
            "severe_anaphylaxis": "Suspected Anaphylaxis / Severe Allergy",
            "poisoning_overdose": "Acute Poisoning / Envenomation / Toxic Ingestion"
        }
        detected_names = [category_labels.get(cat, cat.replace("_", " ").title()) for cat in categories]

        return (
            f"URGENT MEDICAL ALERT: Critical emergency warning sign detected: {', '.join(detected_names)}. "
            "Do NOT attempt home remedies or wait for medication. "
            "Immediately transport the patient to the nearest emergency department, Community Health Centre (CHC), "
            "or tertiary hospital. Call local emergency services (108 / 112) without delay."
        )


red_flag_detector = RedFlagDetector()
