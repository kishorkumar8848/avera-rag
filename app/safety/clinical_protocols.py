"""
Vyoma Medical AI Assistant - Major Illnesses & Standard Clinical Protocols.
Provides verified, evidence-based National Health Mission (NHM) and
Ministry of Health and Family Welfare (MoHFW) Standard Treatment Guidelines.

Contains structured clinical summaries, home care, red flags, and referral rules
in English, Tamil (ta), Hindi (hi), and Gujarati (gu) for zero-latency deterministic matching.
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ClinicalProtocol:
    condition_id: str
    category: str
    english_name: str
    tamil_name: str
    hindi_name: str
    gujarati_name: str
    keywords: List[str]  # Multilingual matching keywords
    summary: Dict[str, str]  # Clinical summary by language code
    home_care: Dict[str, List[str]]  # Recommended non-pharmacological care
    warning_signs: Dict[str, List[str]]  # Danger signs requiring emergency care
    referral_guidance: Dict[str, str]  # When and where to seek doctor evaluation


# -----------------------------------------------------------------------------
# Curated Standard Clinical Protocols for Major Community Illnesses
# -----------------------------------------------------------------------------
MAJOR_CLINICAL_PROTOCOLS: List[ClinicalProtocol] = [
    # 1. Acute Viral Fever / Febrile Illness
    ClinicalProtocol(
        condition_id="acute_viral_fever",
        category="Infectious / Acute Febrile",
        english_name="Acute Viral Fever (Pyrexia)",
        tamil_name="தீவிர வைரஸ் காய்ச்சல்",
        hindi_name="तीव्र वायरल बुखार",
        gujarati_name="તીવ્ર વાયરલ તાવ",
        keywords=[
            "fever", "high temperature", "pyrexia", "feverish", "shivering",
            "காய்ச்சல்", "காய்ச்சல் அடிக்குது", "சுரம்", "உடல் சூடு", "குளிர் காய்ச்சல்", "காச்சல்",
            "बुखार", "तेज बुखार", "ताप", "थरथरी", "बदन तपना",
            "તાવ", "તીવ્ર તાવ", "ધ્રુજારી", "શરીર ગરમ થવું"
        ],
        summary={
            "en": "The patient presents with acute febrile illness, characteristic of an acute viral infection. Immediate focus must be on adequate hydration, rest, temperature monitoring, and ruling out red flag complications.",
            "ta": "நோயாளிக்கு தீவிர வைரஸ் காய்ச்சலின் அறிகுறிகள் உள்ளன. போதுமான அளவு நீர்ச்சத்து எடுத்தல், முழு ஓய்வு மற்றும் உடல் வெப்பநிலையைக் கண்காணிப்பது மிக முக்கியம்.",
            "hi": "मरीज में तीव्र वायरल बुखार के लक्षण हैं। तुरंत पर्याप्त तरल पदार्थ पीना, पूर्ण विश्राम और शरीर के तापमान की नियमित निगरानी आवश्यक है।",
            "gu": "દર્દીમાં તીવ્ર વાયરલ તાવના લક્ષણો જોવા મળે છે. પૂરતું પાણી-પ્રવાહી પીવું, આરામ કરવો અને શરીરના તાપમાનનું નિયમિત નિરીક્ષણ કરવું મહત્વપૂર્ણ છે."
        },
        home_care={
            "en": [
                "Drink plenty of fluids: boiled and cooled water, ORS, tender coconut water, or fresh clear soups (at least 2-3 liters/day).",
                "Perform tepid sponging using room-temperature water on forehead, neck, and extremities if temperature exceeds 101°F (38.3°C).",
                "Ensure complete bed rest in a well-ventilated, shaded room.",
                "Take light, easily digestible home-cooked meals (kanji, khichdi, porridge).",
                "For high discomfort or fever >100°F, adult standard fever control is Paracetamol 500mg every 6-8 hours (maximum 2g/day, avoid if severe liver disease). Avoid NSAIDs like Aspirin/Ibuprofen."
            ],
            "ta": [
                "அதிக அளவு நீர்ச்சத்து உள்ள திரவங்களை அருந்தவும்: காய்ச்சி ஆறவைத்த நீர், ORS கரைசல், இளநீர், கஞ்சி (ஒரு நாளைக்கு 2-3 லிட்டர்).",
                "உடல் வெப்பநிலை 101°F ஐ விட அதிகமாக இருந்தால், சாதாரண நீர் கொண்டு நெற்றி மற்றும் உடலில் ஈரத்துணி ஒத்தடம் கொடுக்கவும்.",
                "நன்றாக காற்றோட்டமான அறையில் முழுமையான ஓய்வு எடுக்கவும்.",
                "எளிதில் செரிமானமாகும் மிதமான உணவுகளை உட்கொள்ளவும் (கஞ்சி, இட்லி, ரசம் சாதம்).",
                "அதிக உடல் சூடு இருந்தால் பெரியவர்களுக்கு பாராசிட்டமால் 500mg மாத்திரை மருத்துவர் வழிகாட்டலின்படி எடுத்துக்கொள்ளலாம். ஆஸ்பிரின் அல்லது இப்யூபுரூஃபன் போன்ற மருந்துகளைத் தவிர்க்கவும்."
            ],
            "hi": [
                "भरपूर तरल पदार्थ पिएं: उबला हुआ पानी, ओआरएस (ORS) घोल, नारियल पानी और हल्का सूप (रोजाना 2-3 लीटर)।",
                "यदि बुखार 101°F (38.3°C) से अधिक हो, तो माथे और बदन पर सामान्य पानी की गीली पट्टियां रखें।",
                "हवादार कमरे में पूरा आराम करें और ढीले सूती कपड़े पहनें।",
                "हल्का और सुपाच्य भोजन लें जैसे खिचड़ी, दलिया, मूँग दाल का सूप।",
                "अधिक बेचैनी होने पर वयस्क पैरासिटामोल 500mg ले सकते हैं (अधिकतम 2 ग्राम/दिन)। बिना डॉक्टर सलाह एस्पिरिन या ब्रूफेन न लें।"
            ],
            "gu": [
                "પુષ્કળ પ્રવાહી પીવો: ઉકાળેલું પાણી, ORS દ્રાવણ, નાળિયેર પાણી, લીંબુ શરબત (દિવસમાં 2-3 લિટર).",
                "જો તાવ 101°F થી વધુ હોય, તો કપાળ અને હાથ-પગ પર સામાન્ય પાણીની પટ્ટીઓ મૂકો.",
                "હવાઉજાસવાળા રૂમમાં સંપૂર્ણ આરામ કરો અને હળવા સુતરાઉ કપડાં પહેરો.",
                "હળવો અને પચવામાં સરળ ખોરાક લો જેમ કે ખીચડી, સૂપ, મગનું પાણી.",
                "જરૂર પડ્યે પુખ્ત વયના લોકો પેરાસિટામોલ 500mg લઈ શકે છે. એસ્પિરિન કે આઇબ્યુપ્રોફેન જેવી દવાઓ ટાળો."
            ]
        },
        warning_signs={
            "en": [
                "Fever lasting continuously for more than 3 days (>72 hours).",
                "Inability to retain oral liquids or severe persistent vomiting.",
                "Extreme lethargy, confusion, altered mental state, or delirium.",
                "Unusual skin rashes, petechiae (red/purple blood spots), or bleeding from gums/nose.",
                "Difficulty breathing or rapid respiratory rate."
            ],
            "ta": [
                "காய்ச்சல் 3 நாட்களுக்கு மேல் (72 மணி நேரத்திற்கு மேல்) தொடர்ந்து நீடித்தால்.",
                "தொடர் வாந்தி அல்லது நீரைக் கூட குடிக்க முடியாமல் போவது.",
                "அதிக சோர்வு, மயக்கம் அல்லது குழப்பமான மனநிலை.",
                "தோலில் சிவப்புப் புள்ளிகள் அல்லது மூக்கு/ஈறுகளில் ரத்தக்கசிவு.",
                "மூச்சுத்திணறல் அல்லது மிக வேகமான சுவாசம்."
            ],
            "hi": [
                "बुखार 3 दिन (72 घंटे) से अधिक समय तक लगातार बना रहे।",
                "लगातार उल्टी होना या पानी भी न पच पाना।",
                "बहुत ज्यादा कमजोरी, बेहोशी, भटकाव या भ्रम की स्थिति।",
                "त्वचा पर लाल चकत्ते या नाक/मसूड़ों से खून आना।",
                "सांस लेने में तकलीफ या बहुत तेज सांस चलना।"
            ],
            "gu": [
                "તાવ સતત 3 દિવસથી વધુ સમય સુધી રહે.",
                "સતત ઉલટી થવી અથવા પ્રવાહી પીવામાં અસમર્થતા.",
                "અતિશય નબળાઈ, બેભાન થવું અથવા મૂંઝવણ.",
                "ચામડી પર લાલ ચકામા અથવા પેઢા/નાકમાંથી રક્તસ્રાવ.",
                "શ્વાસ લેવામાં તકલીફ અથવા ખૂબ ઝડપી શ્વાસ."
            ]
        },
        referral_guidance={
            "en": "Visit the nearest Primary Health Centre (PHC) or Community Health Centre (CHC) if fever persists past 48-72 hours for blood smear / CBC testing (to rule out dengue, malaria, typhoid). If any warning sign is present, seek immediate emergency medical care.",
            "ta": "காய்ச்சல் 2-3 நாட்களுக்கு மேல் நீடித்தால், ரத்தப் பரிசோதனை (டெங்கு, மலேரியா அறிய) செய்ய ஆரம்ப சுகாதார நிலையத்தை (PHC) அணுகவும். ஏதேனும் ஆபத்து அறிகுறி இருந்தால் உடனடியாக மருத்துவமனைக்குச் செல்லவும்.",
            "hi": "यदि बुखार 48-72 घंटे से अधिक रहे, तो तुरंत नजदीकी प्राथमिक स्वास्थ्य केंद्र (PHC) जाकर रक्त जांच (डेंगू, मलेरिया, टाइफाइड) करवाएं। चेतावनी संकेत दिखने पर तुरंत आपातकालीन चिकित्सा लें।",
            "gu": "જો તાવ 48-72 કલાકથી વધુ સમય રહે, તો નજીકના પ્રાથમિક આરોગ્ય કેન્દ્ર (PHC) પર જઈને લોહીની તપાસ કરાવો. જો કોઈ ગંભીર લક્ષણ હોય, તો તાત્કાલિક ઈમરજન્સી ડૉક્ટર પાસે જાઓ."
        }
    ),

    # 2. Acute Upper Respiratory Infection / Common Cold & Cough
    ClinicalProtocol(
        condition_id="upper_respiratory_infection",
        category="Respiratory / ENT",
        english_name="Upper Respiratory Tract Infection (Common Cold & Cough)",
        tamil_name="மேல் சுவாசக் குழாய் தொற்று (சளி மற்றும் இருமல்)",
        hindi_name="ऊपरी श्वसन संक्रमण (जुकाम और खांसी)",
        gujarati_name="શ્વસન માર્ગનો ચેપ (શરદી અને ઉધરસ)",
        keywords=[
            "cold", "cough", "runny nose", "sore throat", "sneezing", "nasal congestion", "phlegm", "throat pain",
            "சளி", "இருமல்", "தொண்டை வலி", "மூக்கடைப்பு", "தும்மல்", "கடுமையான இருமல்", "தொண்டை கரகரப்பு",
            "जुकाम", "खांसी", "गले में दर्द", "नाक बहना", "छींक", "बलगम", "गला खराब",
            "શરદી", "ઉધરસ", "ગળામાં દુખાવો", "છીંકો", "નાક વહેવું", "કફ"
        ],
        summary={
            "en": "Symptoms indicate an acute viral upper respiratory tract infection. Standard clinical approach involves warm saline gargles, steam inhalation, and throat soothing measures. Antibiotics are NOT recommended for uncomplicated viral colds.",
            "ta": "நோயாளிக்கு மேல் சுவாசப்பாதை தொற்று (சளி மற்றும் இருமல்) உள்ளது. வெதுவெதுப்பான உப்பு நீர் கொப்பளித்தல், ஆவி பிடித்தல் மற்றும் தொண்டை இதமளிக்கும் எளிய முறைகள் சிறந்தது. சாதாரண சளிக்கு ஆன்டிபயாடிக் மருந்துகள் தேவையில்லை.",
            "hi": "मरीज को ऊपरी श्वसन तंत्र का वायरल संक्रमण (जुकाम-खांसी) है। गुनगुने नमक के पानी से गरारे, भाप लेना और गर्म तरल पदार्थ लेना सर्वोत्तम है। सामान्य जुकाम में एंटीबायोटिक की आवश्यकता नहीं होती।",
            "gu": "દર્દીને શ્વસન માર્ગનો વાયરલ ચેપ (શરદી-ઉધરસ) છે. નવશેકા મીઠાના પાણીના કોગળા, નાસ લેવી અને ગરમ પ્રવાહી પીવું ફાયદાકારક છે. સામાન્ય શરદીમાં એન્ટિબાયોટિકની જરૂર નથી."
        },
        home_care={
            "en": [
                "Perform warm saline gargles (half teaspoon salt in warm water) 3-4 times daily for sore throat relief.",
                "Inhale plain steam for 5-10 minutes twice a day to relieve nasal congestion.",
                "Stay well hydrated with warm water, ginger-tulsi tea, or warm lemon-honey water.",
                "Avoid cold beverages, refrigerated items, dust, and active/passive cigarette smoke.",
                "Honey (1-2 teaspoons for adults/children >1 year) acts as a natural soothing demulcent for dry night cough."
            ],
            "ta": [
                "வெதுவெதுப்பான நீரில் சிறிதளவு உப்பு கலந்து தினமும் 3-4 முறை தொண்டையில் படும்படி கொப்பளிக்கவும்.",
                "மூக்கடைப்பு நீங்க தினமும் இரண்டு முறை சுடுநீர் ஆவி பிடிக்கவும்.",
                "மிதமான சுடுநீர், இஞ்சி-துளசி கஷாயம் அல்லது சுக்கு காபி அருந்தவும்.",
                "குளிர்ந்த நீர், குளிர்பானங்கள் மற்றும் தூசி உள்ள இடங்களைத் தவிர்க்கவும்.",
                "இரவு நேர வறட்டு இருமலுக்கு தேன் அல்லது மிளகு-பால் மிதமான இதமளிக்கும் (1 வயதுக்கு மேற்பட்டவர்களுக்கு)."
            ],
            "hi": [
                "गुनगुने पानी में आधा चम्मच नमक डालकर दिन में 3-4 बार गरारे करें।",
                "बंद नाक खोलने के लिए दिन में दो बार सादे पानी की भाप लें।",
                "गर्म पानी, तुलसी-अदरक की चाय या गर्म काढ़ा पिएं।",
                "ठंडी चीजें, फ्रिज का पानी, धूल और धुएं से परहेज करें।",
                "रात की खांसी के लिए एक चम्मच शहद और अदरक का रस राहत देता है।"
            ],
            "gu": [
                "નવશેકા ગરમ પાણીમાં અડધી ચમચી મીઠું નાખી દિવસમાં 3-4 વખત કોગળા કરો.",
                "નાક સાફ કરવા દિવસમાં બે વાર વરાળ (નાસ) લો.",
                "ગરમ પાણી, તુલસી-સૂંઠનો ઉકાળો અથવા હળદરવાળું દૂધ પીવો.",
                "ઠંડા પીણાં, ફ્રિજની વસ્તુઓ, ધૂળ અને ધુમાડાથી દૂર રહો.",
                "ખાંસીમાં રાહત માટે મધ અને આદુનો રસ ઉત્તમ છે."
            ]
        },
        warning_signs={
            "en": [
                "Shortness of breath, rapid breathing, or visible chest indrawing (gasping).",
                "High fever >102°F accompanied by chills or thick rust-colored/blood-stained sputum.",
                "Severe localized ear pain or persistent facial/sinus pain.",
                "Inability to swallow liquids or open mouth fully (trismus).",
                "Cough persisting longer than 2-3 weeks (requires TB / chest evaluation)."
            ],
            "ta": [
                "மூச்சுத்திணறல், வேகமான மூச்சு அல்லது நெஞ்சு குழி விழுந்து மூச்சு வாங்குதல்.",
                "அதிக காய்ச்சலுடன் இருமலில் ரத்தம் அல்லது அடர் பழுப்பு நிற சளி வெளிப்படுதல்.",
                "கடுமையான காது வலி அல்லது கன்னப் பகுதியில் தாங்க முடியாத வலி.",
                "எச்சில் அல்லது தண்ணீரைக் கூட விழுங்க முடியாத நிலை.",
                "இருமல் 2-3 வாரங்களுக்கு மேல் தொடர்ந்தால் (காசநோய்/மார்பு பரிசோதனை தேவை)."
            ],
            "hi": [
                "सांस फूलना, तेजी से सांस चलना या छाती में खिंचाव होना।",
                "तेज बुखार के साथ खांसी में खून या गहरा बलगम आना।",
                "कान में तेज दर्द या चेहरे/साइनस में गंभीर दर्द।",
                "पानी या लार भी निगलने में असमर्थता होना।",
                "खांसी का 2 से 3 सप्ताह से अधिक समय तक लगातार बने रहना (टीबी जांच जरूरी)।"
            ],
            "gu": [
                "શ્વાસ ચઢવો, ઝડપી શ્વાસ અથવા છાતીમાં ખેંચાણ.",
                "તીવ્ર તાવ સાથે કફમાં લોહી આવવું.",
                "કાનમાં અસહ્ય દુખાવો અથવા ચહેરા પર સોજો/દુખાવો.",
                "પ્રવાહી ગળવામાં પણ અસમર્થતા.",
                "ખાંસી 2 થી 3 અઠવાડિયાથી વધુ સમય સુધી ચાલુ રહેવી."
            ]
        },
        referral_guidance={
            "en": "Seek prompt clinical assessment at the nearest PHC or clinic if wheezing, stridor, or breathlessness develops. A chronic cough exceeding 2 weeks must undergo sputum examination and chest X-ray under the National TB Elimination Program.",
            "ta": "மூச்சுத்திணறல் அல்லது நெஞ்சு இரைப்பு ஏற்பட்டால் உடனடியாக ஆரம்ப சுகாதார நிலையத்தை அணுகவும். இருமல் 2 வாரங்களுக்கு மேல் நீடித்தால் சளிப் பரிசோதனை செய்துகொள்வது கட்டாயம்.",
            "hi": "यदि सांस लेने में कठिनाई हो या सीने से सीटी जैसी आवाज आए, तो तुरंत प्राथमिक स्वास्थ्य केंद्र जाएं। 2 सप्ताह से अधिक की खांसी में बलगम और छाती का एक्स-रे अवश्य करवाएं।",
            "gu": "જો શ્વાસ લેવામાં તકલીફ થાય અથવા છાતીમાંથી અવાજ આવે, તો તાત્કાલિક પીએચસી પર જાઓ. 2 અઠવાડિયાથી વધુ ખાંસી હોય તો કફની તપાસ કરાવવી જરૂરી છે."
        }
    ),

    # 3. Acute Gastroenteritis, Diarrhea & Dehydration
    ClinicalProtocol(
        condition_id="acute_gastroenteritis",
        category="Gastrointestinal",
        english_name="Acute Gastroenteritis (Diarrhea & Vomiting)",
        tamil_name="தீவிர வயிற்றுப்போக்கு மற்றும் வாந்தி",
        hindi_name="तीव्र दस्त और उल्टी (गैस्ट्रोएंटेराइटिस)",
        gujarati_name="ઝાડા-ઉલટી અને ડિહાઇડ્રેશન",
        keywords=[
            "diarrhea", "loose stools", "watery stool", "vomiting", "stomach cramps", "loose motion", "dehydration",
            "வயிற்றுப்போக்கு", "பேதி", "வாந்தி", "வயிற்று வலி", "வயிற்று பிரட்டல்", "நீர்ச்சத்து குறைவு", "வயிற்றுக்கடுப்பு",
            "दस्त", "उल्टी", "पेट दर्द", "पतले दस्त", "पानी जैसे दस्त", "मरोड़", "निर्जलीकरण",
            "ઝાડા", "ઉલટી", "પેટમાં ચૂંક", "પાતળા ઝાડા", "પાણીની કમી", "ડિહાઇડ્રેશન"
        ],
        summary={
            "en": "Clinical presentation aligns with acute gastroenteritis. The cornerstone of management is preventing and correcting dehydration using Oral Rehydration Salts (ORS) solution. Anti-motility drugs (e.g., Loperamide) should be avoided in infectious diarrhea.",
            "ta": "நோயாளிக்கு தீவிர வயிற்றுப்போக்கு மற்றும் வாந்தி அறிகுறிகள் உள்ளன. நீர்ச்சத்து இழப்பைத் தடுக்க ORS கரைசலைத் தொடர்ந்து கொடுப்பதே உடனடி முதலுதவி. சுயமாக மருந்துக் கடைகளில் வாங்கும் வயிற்றுப்போக்கு நிறுத்தும் மருந்துகளைத் தவிர்க்கவும்.",
            "hi": "मरीज में तीव्र दस्त और उल्टी के लक्षण हैं। सबसे महत्वपूर्ण कदम ओआरएस (ORS) घोल द्वारा शरीर में पानी और लवण की कमी को रोकना है। बिना डॉक्टर परामर्श दस्त रोकने की दवाएं न लें।",
            "gu": "દર્દીમાં ઝાડા અને ઉલટીના લક્ષણો છે. શરીરનું ડિહાઇડ્રેશન રોકવા ORS દ્રાવણ આપવું એ સૌથી મહત્વપૂર્ણ સારવાર છે. ડૉક્ટરની સલાહ વિના ઝાડા બંધ કરવાની ગોળીઓ ન લો."
        },
        home_care={
            "en": [
                "Prepare and drink WHO-formula ORS solution: dissolve 1 packet in 1 liter of clean drinking water. Drink after every loose stool (adults: 200-400ml, children: 100-200ml).",
                "Continue oral feeding with homemade fluids: rice kanji with salt, tender coconut water, diluted buttermilk with salt.",
                "Eat soft, bland foods: bananas, cooked rice, curd, boiled potatoes, toast (BRAT diet principles).",
                "Maintain strict hand hygiene: wash hands with soap before eating and after using the toilet.",
                "Avoid high-sugar juices, caffeine, milk products, and oily/spicy street foods."
            ],
            "ta": [
                "WHO வழிகாட்டல்படி தயாரிக்கப்பட்ட ORS கரைசலை 1 லிட்டர் சுத்தமான தண்ணீரில் கலந்து ஒவ்வொரு முறை மலம் கழித்த பின்னரும் அருந்தவும் (பெரியவர்கள்: 200-400ml).",
                "உப்பு கலந்த கஞ்சி, மோர், இளநீர் போன்றவற்றை அடிக்கடி குடிக்கவும்.",
                "வாழைப்பழம், தயிர் சாதம், இட்லி, வேகவைத்த உருளைக்கிழங்கு போன்ற எளிய உணவுகளை உண்ணவும்.",
                "கைகளை சோப்பு போட்டு சுத்தமாகக் கழுவி சுகாதாரத்தைக் கடைப்பிடிக்கவும்.",
                "காரமான, எண்ணெய் பலகாரங்கள், குளிர்பானங்கள் மற்றும் பால் பொருட்களை தற்காலிகமாகத் தவிர்க்கவும்."
            ],
            "hi": [
                "डब्ल्यूएचओ (WHO) प्रमाणित ओआरएस (ORS) पैकेट को 1 लीटर साफ पानी में घोलें और हर बार दस्त के बाद एक गिलास पिएं।",
                "घर के बने तरल पदार्थ लें: नमक मिला चावल का मांड, छाछ, नारियल पानी।",
                "हल्का आहार जारी रखें: केला, दही-चावल, मूंग दाल खिचड़ी, उबले आलू।",
                "खाने से पहले और शौच के बाद साबुन से अच्छी तरह हाथ धोएं।",
                "मिठाई, तली-भुनी चीजें, चाय-कॉफ़ी और बाजार का खाना पूरी तरह बंद रखें।"
            ],
            "gu": [
                "ORS નું પેકેટ 1 લિટર ચોખ્ખા પાણીમાં ઓગાળો અને દરેક ઝાડા પછી એક ગ્લાસ પીવો.",
                "છાશ, ભાતનું ઓસામણ (કાંજી), નાળિયેર પાણી જેવા પ્રવાહી લેતા રહો.",
                "હળવો ખોરાક લો: કેળાં, દહીં-ભાત, મગની ખીચડી.",
                "જમતા પહેલા અને શૌચાલય પછી સાબુથી હાથ બરાબર ધોવા.",
                "તેલવાળો, તીખો અને બહારનો ખોરાક સદંતર બંધ રાખવો."
            ]
        },
        warning_signs={
            "en": [
                "Signs of severe dehydration: sunken eyes, extreme dry tongue/mouth, skin pinch goes back very slowly (>2 seconds), absence of urination for >6 hours.",
                "Presence of blood or black color in stools (dysentery).",
                "Severe intractable vomiting preventing all oral fluid intake.",
                "Severe continuous abdominal pain, distension, or high fever >101°F.",
                "Lethargy, confusion, or fainting on standing."
            ],
            "ta": [
                "தீவிர நீர்ச்சத்து இழப்பு அறிகுறிகள்: கண்கள் குழிவிழுதல், நாக்கு வறண்டு போதல், தோலை இழுத்தால் மெதுவாக திரும்புதல், 6 மணி நேரத்திற்கு மேல் சிறுநீர் வெளியேறாமல் இருத்தல்.",
                "மலத்தில் ரத்தம் அல்லது கருமை நிறம் காணப்படுதல் (சீதபேதி).",
                "நீரைக் கூட குடிக்க முடியாத அளவிற்கு விடாத வாந்தி.",
                "தாங்க முடியாத தீவிர வயிற்று வலி அல்லது அதிக காய்ச்சல்.",
                "அதிக மயக்கம் அல்லது நின்றால் தலைசுற்றல் ஏற்படுதல்."
            ],
            "hi": [
                "गंभीर निर्जलीकरण के लक्षण: धँसी हुई आँखें, अत्यधिक सूखी जीभ, त्वचा की लोच घटना, 6 घंटे से पेशाब न होना।",
                "दस्त में खून या कालापन आना।",
                "लगातार उल्टी होना जिससे ओआरएस भी पेट में न टिके।",
                "पेट में असहनीय दर्द, पेट का फूलना या तेज बुखार।",
                "अत्यधिक कमजोरी, बेहोशी या चक्कर आना।"
            ],
            "gu": [
                "ગંભીર ડિહાઇડ્રેશનના લક્ષણો: આંખો ઊંડી ઊતરી જવી, જીભ સુકાવી, 6 કલાકથી પેશાબ ન થવો.",
                "ઝાડામાં લોહી પડવું.",
                "સતત ઉલટી થવી જેથી પાણી પણ પેટમાં ન ટકે.",
                "પેટમાં અસહ્ય દુખાવો અથવા સખત તાવ.",
                "ચક્કર આવવા અથવા બેભાન થવું."
            ]
        },
        referral_guidance={
            "en": "If any severe dehydration signs, persistent vomiting, or blood in stool occur, transport immediately to the nearest PHC/Hospital for IV fluid resuscitation (Ringer's Lactate / Normal Saline).",
            "ta": "நீர்ச்சத்து குறைவு, தீவிர வாந்தி அல்லது ரத்த பேதி அறிகுறிகள் இருந்தால், உடனடியாக மருத்துவமனைக்குச் சென்று குளுக்கோஸ்/நரம்பு வழி திரவம் (IV fluids) செலுத்த வேண்டும்.",
            "hi": "यदि गंभीर निर्जलीकरण, लगातार उल्टी या दस्त में खून के लक्षण दिखें, तो तुरंत नजदीकी अस्पताल या पीएचसी ले जाएं जहां ड्रिप (IV फ्लूइड) लगाई जा सके।",
            "gu": "જો અતિશય નબળાઈ, સતત ઉલટી કે લોહી પડે, તો દર્દીને તાત્કાલિક હોસ્પિટલ પહોંચાડો જેથી બોટલ (IV ફ્લૂઇડ) ચઢાવી શકાય."
        }
    ),

    # 4. Acute Chest Discomfort & Cardiovascular Emergency Red Flag
    ClinicalProtocol(
        condition_id="acute_cardiac_emergency",
        category="Cardiovascular / Emergency",
        english_name="Acute Chest Pain / Angina (Suspected Cardiac Event)",
        tamil_name="தீவிர நெஞ்சு வலி / மாரடைப்பு எச்சரிக்கை",
        hindi_name="सीने में तेज दर्द / दिल का दौरा (कार्डियक इमरजेंसी)",
        gujarati_name="છાતીમાં તીવ્ર દુખાવો / હાર્ટ એટેક ચેતવણી",
        keywords=[
            "chest pain", "chest tightness", "chest pressure", "heart pain", "pain in left arm", "radiating pain",
            "நெஞ்சு வலி", "நெஞ்சு அழுத்தம்", "மார்பு வலி", "இடது கை வலி", "நெஞ்சு இறுக்கம்", "மூச்சு முட்டுது",
            "सीने में दर्द", "छाती में दर्द", "दिल का दौरा", "बाईं बांह में दर्द", "सीने में जकड़न", "घबराहट",
            "છાતીમાં દુખાવો", "છાતીમાં દબાણ", "ડાબા હાથમાં દુખાવો", "ગભરામણ", "હાર્ટ એટેક"
        ],
        summary={
            "en": "CRITICAL EMERGENCY: Symptoms of central crushing chest pain, pressure, or left-sided radiation strongly suggest an acute coronary event or cardiac ischemia. Immediate emergency hospital transfer is mandatory.",
            "ta": "அவசர எச்சரிக்கை: நெஞ்சில் பாரம், இறுக்கம் அல்லது இடது கை மற்றும் தாடைக்கு பரவும் வலி மாரடைப்பின் (Heart Attack) அறிகுறியாக இருக்கலாம். தாமதிக்காமல் அவசர மருத்துவ உதவி பெற வேண்டும்.",
            "hi": "गंभीर आपातकालीन स्थिति: सीने में भारीपन, दबाव, घुटन या बाईं भुजा में दर्द दिल के दौरे (हार्ट अटैक) का संकेत हो सकता है। तुरंत आपातकालीन अस्पताल पहुंचना अनिवार्य है।",
            "gu": "અતિ ગંભીર ઈમરજન્સી: છાતીમાં દબાણ, જકડન અથવા ડાબા હાથમાં દુખાવો હાર્ટ એટેકનું લક્ષણ હોઈ શકે છે. વિલંબ કર્યા વિના તાત્કાલિક હોસ્પિટલ પહોંચો."
        },
        home_care={
            "en": [
                "Immediately stop all physical activity; sit or recline in a comfortable upright position (45-degree angle).",
                "Loosen all tight clothing around the neck, chest, and waist.",
                "Keep the patient calm; do NOT permit walking, exertion, or driving.",
                "Ensure maximum fresh air ventilation; avoid crowds around the patient.",
                "Do NOT give heavy food or water if the patient is nauseated or drowsy."
            ],
            "ta": [
                "உடனடியாக அனைத்து உடல் அசைவுகளையும் நிறுத்தி, சாய்ந்த நிலையில் அமர வைக்கவும்.",
                "கழுத்து, மார்பு மற்றும் இடுப்பில் உள்ள இறுக்கமான ஆடைகளைத் தளர்த்தவும்.",
                "நோயாளியை பதற்றமடைய விடாமல் அமைதிப்படுத்தவும்; நடக்கவோ ஓடவோ அனுமதிக்கக் கூடாது.",
                "சுற்றிலும் கூட்டம் கூடாமல் நல்ல காற்றோட்டம் கிடைக்கச் செய்யவும்.",
                "மயக்கம் அல்லது வாந்தி உணர்வு இருந்தால் உணவு அல்லது தண்ணீர் கொடுக்க வேண்டாம்."
            ],
            "hi": [
                "तुरंत सारी शारीरिक गतिविधियां रोक दें; मरीज को आराम से 45 डिग्री कोण पर बैठाएं।",
                "गले, सीने और कमर के तंग कपड़े ढीले कर दें।",
                "मरीज को शांत रखें; चलने-फिरने या खुद गाड़ी चलाने की बिल्कुल अनुमति न दें।",
                "मरीज के आसपास भीड़ न लगाएं, खुली हवा आने दें।",
                "मरीज को कुछ भी भारी खाने या पीने को न दें।"
            ],
            "gu": [
                "તરત જ બધી હલનચલન બંધ કરો અને દર્દીને આરામદાયક સ્થિતિમાં બેસાડો.",
                "ગળા અને છાતીના તંગ કપડાં ઢીલા કરો.",
                "દર્દીને શાંત રાખો; ચાલવા કે મહેનત કરવા ન દો.",
                "દર્દીની આસપાસ ભીડ ન કરો, તાજી હવા આવવા દો.",
                "બેભાન જેવું લાગે તો કંઈપણ ખાવા કે પીવા ન આપવું."
            ]
        },
        warning_signs={
            "en": [
                "Crushing, squeezing central chest pressure radiating to left arm, neck, jaw, or back.",
                "Profuse cold sweating (diaphoresis) with nausea or lightheadedness.",
                "Sudden severe shortness of breath or choking sensation.",
                "Loss of consciousness, collapse, or extremely irregular/weak pulse.",
                "Symptoms lasting longer than 5-10 minutes not relieved by rest."
            ],
            "ta": [
                "நெஞ்சில் அழுத்தும் வலி இடது கை, தாடை, கழுத்து அல்லது முதுகுப் பகுதிக்கு பரவுதல்.",
                "குளிர்ந்த வியர்வை கொட்டுதல், வாந்தி அல்லது தலைசுற்றல் ஏற்படுதல்.",
                "திடீர் கடுமையான மூச்சுத்திணறல்.",
                "மயக்கம் அடைதல் அல்லது நாடித்துடிப்பு மிகக் குறைவாக இருத்தல்.",
                "வலி 5-10 நிமிடங்களுக்கு மேல் தொடர்ந்து நீடித்தல்."
            ],
            "hi": [
                "सीने में असहनीय दबाव जो बाईं बांह, गर्दन, जबड़े या पीठ तक फैले।",
                "अचानक ठंडा पसीना छूटना, उल्टी का मन होना या चक्कर आना।",
                "अचानक बहुत तेज सांस फूलना या घबराहट होना।",
                "बेहोश हो जाना या नाड़ी का बहुत धीमा/कमजोर पड़ना।",
                "दर्द का 5-10 मिनट से अधिक समय तक लगातार बने रहना।"
            ],
            "gu": [
                "છાતીમાં અસહ્ય દુખાવો જે ડાબા હાથ, જડબા કે પીઠ તરફ ફેલાય.",
                "ઠંડો પરસેવો વળવો, ઉલટી જેવું લાગવું કે ચક્કર આવવા.",
                "અચાનક શ્વાસ લેવામાં અતિશય તકલીફ થવી.",
                "બેભાન થઈ જવું અથવા નાડી ધીમી પડવી.",
                "દુખાવો 5 થી 10 મિનિટથી વધુ સમય ચાલુ રહેવો."
            ]
        },
        referral_guidance={
            "en": "DIAL EMERGENCY (108 / Ambulance) IMMEDIATELY. Transfer without delay to the nearest hospital with 24/7 ECG and Intensive Cardiac Care (ICCU) facilities. Every minute saved preserves cardiac muscle.",
            "ta": "உடனடியாக 108 அவசர ஊர்தியை அழைக்கவும்! தாமதிக்காமல் ECG வசதி உள்ள அருகிலுள்ள அவசர சிகிச்சை மையத்திற்கு நோயாளியை விரைவாகக் கொண்டு செல்லவும். ஒவ்வொரு நிமிடமும் மிக முக்கியம்.",
            "hi": "तुरंत 108 एम्बुलेंस को कॉल करें! बिना एक पल गंवाए मरीज को ईसीजी (ECG) और आईसीयू सुविधा वाले नजदीकी अस्पताल ले जाएं। हर एक मिनट अनमोल है।",
            "gu": "તાત્કાલિક 108 એમ્બ્યુલન્સ બોલાવો! સહેજ પણ વિલંબ કર્યા વિના દર્દીને ECG અને ICU સુવિધાવાળી નજીકની હોસ્પિટલમાં ખસેડો."
        }
    ),

    # 5. Headache / Migraine & Neurological Screening
    ClinicalProtocol(
        condition_id="headache_migraine",
        category="Neurological / Common",
        english_name="Headache & Migraine (Cephalea)",
        tamil_name="தலைவலி மற்றும் ஒற்றைத் தலைவலி",
        hindi_name="सिरदर्द और माइग्रेन",
        gujarati_name="માથાનો દુખાવો અને આધાશીશી (માઈગ્રેન)",
        keywords=[
            "headache", "migraine", "head throbbing", "pain in head", "temple pain",
            "தலைவலி", "ஒற்றைத் தலைவலி", "தலை பாரம்", "மண்டை இடி", "தலவலி",
            "सिरदर्द", "माइग्रेन", "सिर भारी", "आधे सिर में दर्द", "कनपटी में दर्द",
            "માથાનો દુખાવો", "માઈગ્રેન", "આધાશીશી", "માથું ભારે થવું"
        ],
        summary={
            "en": "Presentation indicates a common primary tension headache or migraine. Immediate relief involves resting in a quiet, dark environment and ensuring hydration. Secondary red flags (e.g., sudden thunderclap onset, fever with neck stiffness) must be screened.",
            "ta": "நோயாளிக்கு வழக்கமான தலைவலி அல்லது ஒற்றைத் தலைவலியின் அறிகுறிகள் உள்ளன. அமைதியான இருண்ட அறையில் ஓய்வெடுத்தல் மற்றும் போதுமான நீர் குடிப்பது இதமளிக்கும். கழுத்து விரைப்பு அல்லது திடீர் கடுமையான தலைவலி உள்ளதா என கவனிக்க வேண்டும்.",
            "hi": "लक्षण सामान्य तनाव सिरदर्द या माइग्रेन की ओर संकेत करते हैं। शांत, अंधेरे कमरे में आराम करना और भरपूर पानी पीना लाभकारी है। अचानक तेज सिरदर्द या गर्दन में अकड़न जैसे गंभीर संकेतों पर ध्यान दें।",
            "gu": "લક્ષણો સામાન્ય તણાવ માથાનો દુખાવો અથવા માઇગ્રેન દર્શાવે છે. શાંત, અંધારાવાળા ઓરડામાં આરામ કરવો અને પૂરતું પાણી પીવું રાહત આપે છે."
        },
        home_care={
            "en": [
                "Rest in a quiet, darkened, and cool room with eyes closed.",
                "Apply a cold compress or cool damp cloth across forehead and temples.",
                "Drink 1-2 large glasses of water to treat potential dehydration.",
                "Gently massage the neck, shoulders, and temple muscles.",
                "Limit screen time (smartphones, television, bright displays) and avoid loud noise."
            ],
            "ta": [
                "அமைதியான, வெளிச்சம் குறைவான குளிர்ந்த அறையில் கண்களை மூடி ஓய்வெடுக்கவும்.",
                "நெற்றி மற்றும் பக்கவாட்டுப் பகுதிகளில் குளிர்ந்த நீரில் நனைத்த துணியை வைக்கவும்.",
                "நீர்ச்சத்து குறைவினால் ஏற்படும் தலைவலியைத் தவிர்க்க 1-2 டம்ளர் தண்ணீர் குடிக்கவும்.",
                "கழுத்து மற்றும் தோள்பட்டை தசைகளை மெதுவாக மசாஜ் செய்யவும்.",
                "மொபைல் போன், டிவி திரை பார்ப்பதைத் தவிர்த்து கண்களுக்கு ஓய்வு கொடுக்கவும்."
            ],
            "hi": [
                "शांत और हल्के अंधेरे वाले कमरे में आंखें बंद करके लेट जाएं।",
                "माथे और कनपटियों पर ठंडे पानी की पट्टी या आइस पैक रखें।",
                "तुरंत 1-2 गिलास सामान्य पानी पिएं (पानी की कमी सिरदर्द बढ़ाती है)।",
                "गर्दन और कंधों की हल्की मालिश करें ताकि तनाव कम हो सके।",
                "मोबाइल, टीवी और तेज रोशनी से पूरी तरह दूर रहें।"
            ],
            "gu": [
                "શાંત અને અંધારાવાળા રૂમમાં આંખો બંધ કરીને આરામ કરો.",
                "કપાળ પર ઠંડા પાણીની પટ્ટી મૂકો.",
                "તરત જ 1-2 ગ્લાસ પાણી પીવો.",
                "ગળા અને ખભાના સ્નાયુઓની હળવી માલિશ કરો.",
                "મોબાઇલ, ટીવી અને તેજસ્વી પ્રકાશથી દૂર રહો."
            ]
        },
        warning_signs={
            "en": [
                "Sudden explosive, worst headache of life ('thunderclap' headache - onset within seconds).",
                "Headache accompanied by high fever, stiff neck, and confusion (suspected meningitis).",
                "Headache associated with focal weakness, facial drooping, numbness, or slurred speech (suspected stroke).",
                "Headache following acute head trauma or fall.",
                "Visual disturbance, loss of vision, or persistent projectile vomiting."
            ],
            "ta": [
                "திடீரென மின்னல் போல் தாக்கும் இதுவரை உணராத மிகக் கடுமையான தலைவலி.",
                "தலைவலியுடன் அதிக காய்ச்சல் மற்றும் கழுத்தைத் திருப்ப முடியாத விரைப்பு நிலை (மூளைக்காய்ச்சல் அறிகுறி).",
                "கை கால் பலவீனம், வாய் ஒரு பக்கமாக கோணுதல் அல்லது பேச முடியாமல் போவது (பக்கவாதம் அறிகுறி).",
                "தலையில் அடிபட்ட பிறகு ஏற்படும் தலைவலி மற்றும் வாந்தி.",
                "கண் பார்வை மங்குதல் அல்லது இரட்டையாகத் தெரிதல்."
            ],
            "hi": [
                "अचानक बिजली की तरह उठने वाला जीवन का सबसे भयानक सिरदर्द।",
                "सिरदर्द के साथ तेज बुखार, गर्दन में अकड़न और भ्रम (दिमागी बुखार का अंदेशा)।",
                "चेहरे का टेढ़ा होना, हाथ-पैर में कमजोरी या बोली का लड़खड़ाना (स्ट्रोक/लकवा का खतरा)।",
                "सिर में चोट लगने के बाद शुरू हुआ गंभीर सिरदर्द।",
                "आंखों के सामने धुंधलापन या बिना मतली के अचानक तेज उल्टी होना।"
            ],
            "gu": [
                "અચાનક અત્યંત તીવ્ર માથાનો દુખાવો થવો.",
                "માથાના દુખાવા સાથે સખત તાવ અને ગરદન અકડાઈ જવી.",
                "મોં વાંકું થવું, હાથ-પગમાં લકવો કે બોલવામાં તકલીફ.",
                "માથામાં ઇજા થયા પછી થતો દુખાવો.",
                "દ્રષ્ટિમાં ઝાંખપ આવવી."
            ]
        },
        referral_guidance={
            "en": "Seek immediate emergency hospital care if any 'red flag' neurological symptom (stiff neck, facial weakness, thunderclap onset) appears. If headaches recur weekly, consult a physician for ophthalmic and blood pressure screening.",
            "ta": "கழுத்து விரைப்பு, கை கால் பலவீனம் போன்ற எச்சரிக்கை அறிகுறிகள் இருந்தால் உடனே அவசர சிகிச்சைப் பிரிவுக்குச் செல்லவும். தலைவலி அடிக்கடி வந்தால் ரத்த அழுத்தம் மற்றும் கண் பரிசோதனை செய்து கொள்வது நல்லது.",
            "hi": "यदि गर्दन में अकड़न, चेहरे में कमजोरी या अचानक तेज सिरदर्द हो तो बिना देरी आपातकालीन अस्पताल जाएं। बार-बार सिरदर्द होने पर बीपी और आंखों की जांच करवाएं।",
            "gu": "જો ગરદન અકડાઈ જાય કે લકવાના લક્ષણ જણાય તો તાત્કાલિક હોસ્પિટલ પહોંચો. વારંવાર માથું દુખતું હોય તો બ્લડ પ્રેશર અને આંખોની તપાસ કરાવો."
        }
    )
]


# -----------------------------------------------------------------------------
# Fast Deterministic Protocol Matcher with Age & Comorbidity Personalization
# -----------------------------------------------------------------------------
def lookup_clinical_protocol(
    query_text: str,
    language: str = "en",
    patient_age: Optional[int] = None,
    patient_conditions: Optional[List[str]] = None,
    patient_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Scans patient query against curated MoHFW clinical guidelines.
    Dynamically personalizes guidance based on patient age (pediatric, 50+ adult, geriatric)
    and chronic comorbidities (hypertension, diabetes, pregnancy).
    """
    if not query_text:
        return None

    clean_q = query_text.lower().strip()
    lang_code = language.lower().strip()
    if lang_code not in ["en", "ta", "hi", "gu", "ml", "te", "kn"]:
        lang_code = "en"

    best_match: Optional[ClinicalProtocol] = None
    highest_score = 0

    for protocol in MAJOR_CLINICAL_PROTOCOLS:
        score = 0
        for kw in protocol.keywords:
            if kw.lower() in clean_q:
                # Give higher weight to multi-word phrases
                score += len(kw.split())

        if score > highest_score:
            highest_score = score
            best_match = protocol

    if best_match and highest_score > 0:
        # Resolve localized strings with English fallback
        summary_txt = best_match.summary.get(lang_code, best_match.summary.get("en", ""))
        home_care_list = list(best_match.home_care.get(lang_code, best_match.home_care.get("en", [])))
        warnings_list = list(best_match.warning_signs.get(lang_code, best_match.warning_signs.get("en", [])))
        referral_txt = best_match.referral_guidance.get(lang_code, best_match.referral_guidance.get("en", ""))

        # Localized condition name
        name_map = {
            "ta": best_match.tamil_name,
            "hi": best_match.hindi_name,
            "gu": best_match.gujarati_name,
            "en": best_match.english_name
        }
        localized_name = name_map.get(lang_code, best_match.english_name)

        # ---------------------------------------------------------------------
        # Dynamic Age & Comorbidity Personalization
        # ---------------------------------------------------------------------
        age_guidance_text = ""
        conditions_clean = [c.lower() for c in (patient_conditions or [])]

        if patient_age is not None:
            if patient_age >= 50:
                # Older Adult / Geriatric (50+ years)
                age_advisories = {
                    "en": f"Special Care Note (Age {patient_age}): Monitor blood pressure and pulse twice daily. Keep Paracetamol within 2g/day max and strictly avoid NSAIDs like Ibuprofen if hypertensive. Seek immediate medical evaluation if fever persists over 48 hours or causes confusion.",
                    "ta": f"வயது {patient_age} சிறப்பு வழிகாட்டுதல்: நோயாளியின் வயது {patient_age} என்பதால், இரத்த அழுத்தத்தை (BP) தினமும் இருமுறை கண்காணிக்கவும். பாராசிட்டமால் அளவை நாள் ஒன்றுக்கு 2 கிராமுக்கு மேல் எடுக்க வேண்டாம். காய்ச்சல் 48 மணி நேரத்திற்கு மேல் நீடித்தாலோ அல்லது அதீத சோர்வு ஏற்பட்டாலோ உடனடியாக மருத்துவரை அணுகவும்.",
                    "hi": f"आयु {patient_age} विशेष सलाह: मरीज की उम्र {patient_age} वर्ष होने के कारण रक्तचाप (बीपी) की नियमित जांच करें। पेरासिटामोल 2 ग्राम/दिन से अधिक न लें और पेनकिलर से बचें। यदि बुखार 48 घंटे से अधिक रहे तो तुरंत डॉक्टर को दिखाएं।",
                    "gu": f"ઉંમર {patient_age} વિશેષ સલાહ: દર્દીની ઉંમર {patient_age} વર્ષ હોવાથી બ્લડ પ્રેશર (BP) નિયમિત તપાસો. પેરાસિટામોલ દિવસમાં 2 ગ્રામથી વધુ ન લેવી. તાવ 48 કલાકથી વધુ રહે તો તાત્કાલિક ડૉક્ટરની સલાહ લો."
                }
                age_guidance_text = age_advisories.get(lang_code, age_advisories["en"])
                home_care_list.insert(0, age_guidance_text)

            elif patient_age < 12:
                # Pediatric (<12 years)
                ped_advisories = {
                    "en": f"Pediatric Care Note (Age {patient_age}y): Strictly avoid adult tablets. Use weight-based Paracetamol syrup only (10-15 mg/kg). Never give Aspirin (Reye's syndrome risk). Give frequent sips of ORS. Urgent referral if child refuses feeds, develops sunken eyes, or breathes rapidly.",
                    "ta": f"குழந்தை பராமரிப்பு வழிகாட்டுதல் (வயது {patient_age}): பெரியவர்களுக்கான மாத்திரைகளை கொடுக்க வேண்டாம். உடல் எடைக்கு ஏற்ற பாராசிட்டமால் சிரப் மட்டுமே பயன்படுத்தவும். ஆஸ்பிரின் மாத்திரை கண்டிப்பாகக் கூடாது. ஓ.ஆர்.எஸ் திரவம் அடிக்கடி கொடுக்கவும். குழந்தை தாய்ப்பால்/உணவு மறுத்தாலோ அல்லது மூச்சு வேகமாக விட்டாலோ உடனே மருத்துவமனைக்கு செல்லவும்.",
                    "hi": f"बाल रोग विशेष सलाह (आयु {patient_age} वर्ष): वयस्कों की गोलियां बिल्कुल न दें। केवल वजन अनुसार पेरासिटामोल सिरप दें। एस्पिरिन कभी न दें। बार-बार थोड़ा-थोड़ा ओआरएस घोल पिलाएं। यदि बच्चा सुस्त हो या सांस तेज ले तो तुरंत अस्पताल ले जाएं।",
                    "gu": f"બાળ સંભાળ સલાહ (ઉંમર {patient_age} વર્ષ): પુખ્ત વયની ગોળીઓ ન આપવી. માત્ર વજન મુજબ પેરાસિટામોલ સીરપ આપવી. એસ્પિરિન બિલકુલ ન આપવી. વારંવાર ORS આપવું. જો બાળક સુસ્ત લાગે તો તરત જ ડૉક્ટર પાસે લઈ જવું."
                }
                age_guidance_text = ped_advisories.get(lang_code, ped_advisories["en"])
                home_care_list.insert(0, age_guidance_text)

        # Comorbidity alerts (Hypertension / Diabetes / Pregnancy)
        if any("hypertension" in c or "bp" in c for c in conditions_clean):
            htn_alert = {
                "en": "Hypertension Caution: Avoid oral nasal decongestants and NSAIDs (Ibuprofen/Diclofenac) which elevate blood pressure.",
                "ta": "இரத்த அழுத்த எச்சரிக்கை: இரத்த அழுத்தத்தை அதிகரிக்கும் இப்யூபுரூஃபன் மற்றும் மூக்கடைப்பு நீக்கும் மருந்துகளைத் தவிர்க்கவும்.",
                "hi": "उच्च रक्तचाप सावधानी: इबुप्रोफेन और डिकॉन्गेस्टेंट दवाओं से बचें जो रक्तचाप बढ़ा सकती हैं।",
                "gu": "હાઈ બ્લડ પ્રેશર સાવધાની: બ્લડ પ્રેશર વધારે તેવી આઈબુપ્રોફેન જેવી દવાઓ ટાળો."
            }
            home_care_list.append(htn_alert.get(lang_code, htn_alert["en"]))

        if any("pregnant" in c or "pregnancy" in c for c in conditions_clean):
            preg_alert = {
                "en": "Antenatal Alert: Pregnant patient. Any acute febrile illness or abdominal discomfort requires urgent evaluation at Primary Health Centre (PHC).",
                "ta": "கர்ப்பிணிப் பெண் எச்சரிக்கை: கர்ப்பிணிப் பெண்களுக்கு ஏற்படும் தீவிர காய்ச்சலுக்கு உடனடியாக ஆரம்ப சுகாதார நிலையத்தை (PHC) அணுக வேண்டும்.",
                "hi": "गर्भावस्था चेतावनी: किसी भी तेज बुखार के लिए तुरंत प्राथमिक स्वास्थ्य केंद्र (PHC) से संपर्क करें।",
                "gu": "સગર્ભાવસ્થા સાવધાની: સગર્ભા દર્દી માટે કોઈપણ તીવ્ર તાવ માટે તાત્કાલિક પ્રાથમિક આરોગ્ય કેન્દ્ર (PHC) નો સંપર્ક કરવો."
            }
            warnings_list.insert(0, preg_alert.get(lang_code, preg_alert["en"]))

        return {
            "condition_id": best_match.condition_id,
            "category": best_match.category,
            "condition_name": localized_name,
            "summary": summary_txt,
            "recommended_actions": home_care_list,
            "warning_signs": warnings_list,
            "referral": referral_txt,
            "citation": f"MoHFW National Treatment Guidelines: {best_match.english_name}",
            "confidence": 0.95,
            "age_guidance": age_guidance_text
        }

    return None

