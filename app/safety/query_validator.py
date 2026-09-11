import re
from typing import Dict, Any, Tuple, Optional

# Core clinical symptom indicators (multilingual and English)
CLINICAL_SYMPTOM_KEYWORDS = {
    # English terms
    "fever", "temperature", "cold", "cough", "pain", "headache", "ache", "hurt",
    "vomit", "vomiting", "nausea", "loose stool", "diarrhea", "dysentery", "stomach",
    "belly", "abdomen", "chest", "breath", "breathing", "choking", "rash", "itch",
    "skin", "allergy", "burn", "wound", "cut", "bleeding", "blood", "injury", "fracture",
    "swelling", "swollen", "dizzy", "dizziness", "faint", "unconscious", "weakness",
    "tired", "infection", "throat", "eye", "ear", "discharge", "pus", "boil", "bite",
    "insect", "dog", "snake", "pregnant", "labor", "bp", "sugar", "diabetes", "pressure",

    # Tamil terms (தமிழ்)
    "காய்ச்சல்", "காச்சல்", "இருமல்", "சளி", "வலி", "தலைவலி", "நெஞ்சு", "வயிறு",
    "வயிற்று வலி", "வாந்தி", "பேதி", "வயிற்றுப்போக்கு", "மூச்சு", "மூச்சுத்திணறல்",
    "திணறல்", "தோல்", "அரிப்பு", "சிவத்தல்", "காயம்", "தீக்காயம்", "வெட்டு",
    "இரத்தம்", "வீக்கம்", "மயக்கம்", "சோர்வு", "தொண்டை", "கண்", "காது",
    "சீழ்", "கட்டி", "பூச்சி", "கடி", "நாய்", "பாம்பு", "பிரசவம்", "சர்க்கரை", "பிபி",

    # Hindi terms (हिन्दी)
    "बुखार", "खांसी", "जुकाम", "सर्दी", "दर्द", "सिरदर्द", "छाती", "पेट", "पेट दर्द",
    "उल्टी", "दस्त", "सांस", "सांस फूलना", "चमड़ी", "खुजली", "चकत्ते", "घाव", "चोट",
    "जलना", "खून", "सूजन", "चक्कर", "कमजोरी", "थकान", "गला", "आंख", "कान",
    "मवाद", "फोड़ा", "कीड़ा", "काटना", "कुत्ता", "सांप", "गर्भवती", "शुगर",

    # Gujarati terms (ગુજરાતી)
    "તાવ", "ઉધરસ", "શરદી", "દુખાવો", "માથાનો દુખાવો", "છાતી", "પેટ", "પેટમાં દુખાવો",
    "ઉલટી", "ઝાડા", "શ્વાસ", "દમ", "ચામડી", "ખંજવાળ", "ચકામા", "ઘા", "ઇજા",
    "દાઝવું", "લોહી", "સોજો", "ચક્કર", "નબળાઈ", "થાક", "ગળું", "આંખ", "કાન",
    "કીડાનો ડંખ", "કૂતરું", "સાપ", "ડાયાબિટીસ"
}

# Common conversational greetings, filler phrases, and non-clinical utterances
GREETING_OR_FILLER_PATTERNS = [
    # Tamil greetings and non-clinical fluff
    r'^(வணக்கம்|ஹலோ|டாக்டராக|டாக்டர்|வணக்கம்\s+டாக்டர்|டாக்டராக\s+இருக்கிறேன்|அம்மா|அப்பா|வணக்கம்\s+அம்மா|பேசுகிறேன்|கேட்கிறதா|ஆடியோ|டெஸ்ட்).*$',
    # Hindi greetings
    r'^(नमस्ते|हेलो|डॉक्टर|डॉक्टर\s+साहब|आवाज\s+आ\s+रही\s+है|माइक\s+चेक|टेस्ट).*$',
    # Gujarati greetings
    r'^(નમસ્તે|હેલો|ડોક્ટર|ડોક્ટર\s+સાહેબ|અવાજ\s+આવે\s+છે|ટેસ્ટ).*$',
    # English greetings
    r'^(hello|hi|hey|good\s+morning|good\s+afternoon|good\s+evening|doctor|hello\s+doctor|can\s+you\s+hear\s+me|testing|mic\s+check).*$'
]


LOCALIZED_RETAKE_MESSAGES = {
    "ta": {
        "title": "மருத்துவ அறிகுறிகள் தெளிவாகக் குறிப்பிடப்படவில்லை",
        "description": "உங்கள் குரல் பதிவில் தெளிவான மருத்துவ அறிகுறிகள் (எ.கா. காய்ச்சல், இருமல், தலைவலி, வாந்தி அல்லது வலி) கண்டறியப்படவில்லை.",
        "action": "தயவுசெய்து உங்கள் உடல்நலப் பிரச்சனையைத் தெளிவாகக் கூறி மீண்டும் பேசவும்.",
        "spoken": "உங்கள் குரலில் மருத்துவ அறிகுறிகள் தெளிவாகப் பதியவில்லை. தயவுசெய்து உங்கள் அறிகுறிகளைக் கூறி மீண்டும் பேசவும்.",
        "btn_text": "🎤 அறிகுறிகளை மீண்டும் கூறவும் (Click to Retake)"
    },
    "hi": {
        "title": "चिकित्सीय लक्षण स्पष्ट नहीं हैं",
        "description": "आपकी आवाज़ में कोई स्पष्ट चिकित्सीय लक्षण (जैसे बुखार, खांसी, सिरदर्द, उल्टी या दर्द) नहीं मिला।",
        "action": "कृपया अपने लक्षणों को स्पष्ट रूप से बताकर दोबारा बोलें।",
        "spoken": "आपकी आवाज़ में कोई लक्षण स्पष्ट नहीं हुआ। कृपया अपने लक्षण बताकर दोबारा बोलें।",
        "btn_text": "🎤 लक्षण दोबारा बोलें (Click to Retake)"
    },
    "gu": {
        "title": "તબીબી લક્ષણો સ્પષ્ટ નથી",
        "description": "તમારા અવાજમાં કોઈ સ્પષ્ટ તબીબી લક્ષણ (જેમ કે તાવ, ઉધરસ, માથાનો દુખાવો, ઉલટી અથવા દુખાવો) મળ્યું નથી.",
        "action": "કૃપા કરીને તમારા લક્ષણો સ્પષ્ટ રીતે જણાવીને ફરીથી બોલો.",
        "spoken": "તમારા લક્ષણો સ્પષ્ટ જણાયા નથી. કૃપા કરીને ફરીથી લક્ષણો બોલો.",
        "btn_text": "🎤 લક્ષણો ફરીથી બોલો (Click to Retake)"
    },
    "en": {
        "title": "No Clear Clinical Symptoms Detected",
        "description": "We could not detect specific medical symptoms (such as fever, cough, pain, vomiting, or breathing trouble) in your speech.",
        "action": "Please describe your health complaints clearly and click Retake below.",
        "spoken": "No clinical symptoms were detected. Please describe your health problem clearly and speak again.",
        "btn_text": "🎤 Click to Speak Symptoms (Retake)"
    }
}


class QueryValidator:
    """
    Validates frontline speech queries before dispatching to heavy Medical RAG and LLM.
    Prevents hallucination and repetition loops on casual greetings, empty noise, or non-medical speech.
    """

    @classmethod
    def validate_clinical_query(
        cls,
        raw_query: str,
        english_query: str,
        language: str = "en"
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validates if the user's query describes an actual medical problem or symptom.
        Returns:
        (is_valid: bool, retake_payload: Optional[Dict[str, Any]])
        """
        raw = (raw_query or "").strip()
        eng = (english_query or "").strip()

        # 1. Check minimum length
        if len(raw) < 4 or len(raw.split()) < 2:
            return False, cls._build_retake_payload(raw, language, reason="Query too short or empty")

        # 2. Check if the query is pure greeting or conversational filler
        raw_clean = re.sub(r'[^\w\s]', '', raw).strip()
        for pat in GREETING_OR_FILLER_PATTERNS:
            if re.match(pat, raw_clean, flags=re.IGNORECASE):
                # If it's a greeting, check if it also contains real clinical terms
                if not cls._contains_symptom(raw, eng):
                    return False, cls._build_retake_payload(raw, language, reason="Greeting without clinical symptoms")

        # 3. Check for presence of clinical symptoms in Indic text or English translation
        if not cls._contains_symptom(raw, eng):
            return False, cls._build_retake_payload(raw, language, reason="No clinical symptoms detected")

        # Valid clinical query!
        return True, None

    @classmethod
    def _contains_symptom(cls, raw: str, eng: str) -> bool:
        """Checks if either raw or translated query matches known symptom keywords."""
        combined = f"{raw.lower()} {eng.lower()}"
        words = set(re.findall(r'\b\w+\b', combined))
        # Direct word match
        for sym in CLINICAL_SYMPTOM_KEYWORDS:
            if sym in words or sym in combined:
                return True
        return False

    @classmethod
    def _build_retake_payload(cls, raw_query: str, language: str, reason: str) -> Dict[str, Any]:
        """Constructs structured retake guidance payload."""
        lang = language.lower().strip()
        meta = LOCALIZED_RETAKE_MESSAGES.get(lang, LOCALIZED_RETAKE_MESSAGES["en"])

        return {
            "needs_retake": True,
            "is_emergency": False,
            "query": raw_query,
            "reason": reason,
            "title": meta["title"],
            "summary": f"{meta['description']}\n\n{meta['action']}",
            "spoken_text": meta["spoken"],
            "button_text": meta["btn_text"],
            "recommended_actions": [meta["action"]],
            "warning_signs": [],
            "referral": ""
        }
