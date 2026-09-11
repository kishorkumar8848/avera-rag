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
            "diarrhea", "loose stools", "watery stool", "vomiting", "loose motion", "dehydration", "watery diarrhea",
            "வயிற்றுப்போக்கு", "பேதி", "வாந்தி", "வயிற்று பிரட்டல்", "நீர்ச்சத்து குறைவு", "வயிற்றுக்கடுப்பு",
            "दस्त", "उल्टी", "पतले दस्त", "पानी जैसे दस्त", "मरोड़", "निर्जलीकरण",
            "ઝાડા", "ઉલટી", "પાતળા ઝાડા", "પાણીની કમી", "ડિહાઇડ્રેશન"
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
    ),

    # 6. Skin Rash, Allergic Dermatitis & Superficial Fungal Infection
    ClinicalProtocol(
        condition_id="skin_rash_dermatitis",
        category="Dermatology / Visual Inspection",
        english_name="Skin Rash, Allergic Dermatitis & Fungal Infection",
        tamil_name="தோல் அரிப்பு, தடிப்பு மற்றும் பூஞ்சை தொற்று",
        hindi_name="त्वचा के चकत्ते, एलर्जी और दाद-खुजली",
        gujarati_name="ચામડી પર ચકામા, ખંજવાળ અને એલર્જી",
        keywords=[
            "rash", "skin rash", "itching", "itchy", "redness", "skin allergy", "dermatitis", "eczema", "ringworm", "spots", "hives",
            "தோல் அரிப்பு", "தடிப்பு", "சிவப்பு தடிப்பு", "அரிப்பு", "படர்தாமரை", "தோல் நோய்", "ஒவ்வாமை",
            "खुजली", "चकत्ते", "लाल चकत्ते", "दाद", "खाज", "त्वचा एलर्जी", "पित्ती",
            "ચકામા", "ખંજવાળ", "લાલ ચકામા", "દાદર", "ચામડીની એલર્જી", "ધાબળા"
        ],
        summary={
            "en": "Visual and clinical findings indicate acute skin irritation, allergic dermatitis, or superficial fungal infection. Management focuses on gentle cleansing, soothing topical application, avoiding allergens, and preventing secondary infection.",
            "ta": "நோயாளிக்கு தோல் அரிப்பு, ஒவ்வாமை அல்லது பூஞ்சைத் தொற்றின் (படர்தாமரை) அறிகுறிகள் உள்ளன. பாதிக்கப்பட்ட இடத்தை சுத்தமாக வைத்திருத்தல், பருத்தி ஆடைகள் அணிதல் மற்றும் சொறிவதைத் தவிர்ப்பது முக்கியம்.",
            "hi": "लक्षण त्वचा की एलर्जी, लाल चकत्ते या दाद-खाज (फंगल इन्फेक्शन) की ओर संकेत करते हैं। प्रभावित त्वचा को साफ और सूखा रखना, सूती कपड़े पहनना और खुजलाने से बचना आवश्यक है।",
            "gu": "લક્ષણો ચામડીની એલર્જી, લાલ ચકામા અથવા દાદર દર્શાવે છે. અસરગ્રસ્ત જગ્યાને સાફ અને સૂકી રાખવી, સુતરાઉ કપડાં પહેરવા અને ખંજવાળ ન કરવી જરૂરી છે."
        },
        home_care={
            "en": [
                "Gently wash the affected skin with clean water and mild soap; pat dry with a clean soft towel (do not rub).",
                "Apply soothing Calamine lotion or pure coconut oil to relieve itching and skin dryness.",
                "Wear loose-fitting, breathable cotton clothing to prevent friction and sweat buildup.",
                "Keep fingernails trimmed short and avoid scratching to prevent secondary bacterial infection.",
                "Avoid harsh scented soaps, detergents, chemical cosmetics, or sharing personal towels and bedsheets."
            ],
            "ta": [
                "பாதிக்கப்பட்ட பகுதியை சுத்தமான நீர் மற்றும் மென்மையான சோப்பினால் கழுவி, மென்மையான துணியால் ஒற்றி எடுக்கவும் (தேய்க்கக் கூடாது).",
                "அரிப்பைக் குறைக்க கலாமின் லோஷன் (Calamine lotion) அல்லது தேங்காய் எண்ணெய் மெதுவாகத் தடவலாம்.",
                "இறுக்கமில்லாத, பருத்தி ஆடைகளை அணியவும்.",
                "நகங்களை வெட்டி சுத்தமாக வைத்திருக்கவும்; கைகளால் நகத்தைக் கொண்டு சொறிவதைத் தவிர்க்கவும்.",
                "ரசாயன வாசனை சோப்புகள், பவுடர்கள் பயன்படுத்துவதையும் பிறரின் துண்டுகளைப் பகிர்வதையும் தவிர்க்கவும்."
            ],
            "hi": [
                "प्रभावित त्वचा को सादे पानी और हल्के साबुन से धोएं और साफ तौलिये से थपथपाकर सुखाएं (रगड़ें नहीं)।",
                "खुजली शांत करने के लिए कैलामाइन लोशन या नारियल तेल लगाएं।",
                "ढीले और हवादार सूती कपड़े पहनें ताकि पसीना और घर्षण न हो।",
                "नाखून छोटे रखें और खुजलाने से बचें ताकि संक्रमण न फैले।",
                "कड़क साबुन, परफ्यूम और दूसरों के कपड़े-तौलिए इस्तेमाल न करें।"
            ],
            "gu": [
                "અસરગ્રસ્ત ભાગને ચોખ્ખા પાણીથી ધોઈને નરમ કપડાથી હળવેથી લૂછો (ઘસવું નહીં).",
                "ખંજવાળ ઓછી કરવા કેલામાઇન લોશન અથવા શુદ્ધ કોપરેલ તેલ લગાવો.",
                "ઢીલા અને સુતરાઉ કપડાં પહેરો.",
                "નખ ટૂંકા રાખો અને ખંજવાળવાનું ટાળો જેથી ચેપ ન વધે.",
                "તીવ્ર કેમિકલવાળા સાબુ અને અન્યની વસ્તુઓ વાપરવાનું ટાળો."
            ]
        },
        warning_signs={
            "en": [
                "Rapidly spreading redness accompanied by local heat, extreme pain, or high fever (suspected cellulitis).",
                "Formation of extensive blisters, peeling skin, or open oozing yellow crusts (secondary bacterial impetigo).",
                "Sudden swelling of lips, eyelids, face, or throat with difficulty breathing (severe allergic anaphylaxis).",
                "Rash covering more than 30% of total body surface area.",
                "No improvement or worsening after 5 days of conservative care."
            ],
            "ta": [
                "தோல் சிவத்தல் வேகமாக பரவுதல், அதிக வலி, சூடு அல்லது காய்ச்சல் ஏற்படுதல் (செல்லுலைடிஸ் அறிகுறி).",
                "தோலில் சீழ் கொப்புளங்கள், மஞ்சள் நிற கசிவு அல்லது தோல் உரிதல் ஏற்படுதல்.",
                "உதடு, கண் இமைகள், முகம் வீங்குதல் அல்லது திடீர் மூச்சுத்திணறல் (தீவிர ஒவ்வாமை/அனாபிலாக்சிஸ்).",
                "உடலின் பெரும்பாலான பகுதிகளில் தடிப்பு பரவுதல்.",
                "5 நாட்களுக்கு மேலாகியும் குணமாகாமல் தீவிரமடைதல்."
            ],
            "hi": [
                "लालिमा का तेजी से फैलना, बहुत तेज दर्द, त्वचा का गर्म होना या बुखार आना (सेल्युलाइटिस)।",
                "त्वचा पर बड़े छाले, पीप वाले दाने या पीली पपड़ी जमना।",
                "होंठ, पलकें या चेहरे पर सूजन और सांस लेने में कठिनाई (गंभीर एलर्जी/एनाफिलेक्सिस)।",
                "शरीर के 30% से अधिक हिस्से पर चकत्तों का फैलना।",
                "5 दिनों तक घरेलू देखभाल के बाद भी सुधार न होना।"
            ],
            "gu": [
                "લાલાશ ઝડપથી ફેલાવી, સખત દુખાવો અથવા તાવ આવવો.",
                "મોટા ફોલ્લા થવા અથવા પરુવાળા દાણા થવા.",
                "હોઠ, આંખો અથવા ચહેરા પર સોજો અને શ્વાસ લેવામાં તકલીફ.",
                "શરીરના મોટા ભાગ પર ચકામા ફેલાઈ જવા.",
                "5 દિવસ સુધી કોઈ સુધારો ન થવો."
            ]
        },
        referral_guidance={
            "en": "Refer to the Primary Health Centre (PHC) medical officer for clinical diagnosis, identification of underlying fungal/allergic etiology, and prescription of appropriate topical antifungal (Clotrimazole) or oral antihistamine (Cetirizine). If facial swelling or breathing difficulty occurs, transfer immediately to an emergency facility.",
            "ta": "பூஞ்சை அல்லது ஒவ்வாமைக்கான சரியான களிம்பு (Clotrimazole) அல்லது மாத்திரைகளைப் பெற ஆரம்ப சுகாதார நிலைய (PHC) மருத்துவரை அணுகவும். மூச்சுத்திணறல் அல்லது முக வீக்கம் இருந்தால் உடனே அவசர மருத்துவ உதவி பெறவும்.",
            "hi": "सही जांच और फंगल क्रीम (क्लोट्रिमेज़ोल) या एलर्जी की दवा के लिए प्राथमिक स्वास्थ्य केंद्र (PHC) के डॉक्टर से संपर्क करें। चेहरे पर सूजन या सांस फूलने पर तुरंत आपातकालीन केंद्र ले जाएं।",
            "gu": "યોગ્ય મલમ અથવા એલર્જીની દવા માટે નજીકના પીએચસી ડૉક્ટર પાસે તપાસ કરાવો. જો શ્વાસ લેવામાં તકલીફ જણાય તો તાત્કાલિક હોસ્પિટલ પહોંચો."
        }
    ),

    # 7. Minor Wounds, Cuts, Scrapes & Superficial Burns
    ClinicalProtocol(
        condition_id="minor_wounds_burns",
        category="Trauma / Wound Care",
        english_name="Minor Cuts, Abrasions, Wounds & Superficial Burns",
        tamil_name="சிறு காயங்கள், வெட்டுக்காயம் மற்றும் தீக்காயம்",
        hindi_name="छोटे घाव, खरोंच, चोट और सतही जलना",
        gujarati_name="નાના ઘા, છોલાવું, વાગવું અને સામાન્ય દાઝવું",
        keywords=[
            "wound", "cut", "scrape", "scratch", "abrasion", "laceration", "burns", "skin burn", "scald", "blister", "bleeding", "skin cut",
            "காயம்", "வெட்டுக் காயம்", "சிராய்ப்பு", "தீக்காயம்", "புண்", "ரத்தக்கசிவு", "கொப்புளம்",
            "घाव", "चोट", "कटना", "छिलना", "जलना", "छाला", "खून बहना", "खरोंच",
            "ઘા", "વાગવું", "છોલાવું", "દાઝવું", "લોહી નીકળવું", "ફોલ્લો"
        ],
        summary={
            "en": "Visual features show a localized cut, scrape, superficial wound, or minor burn. First priority is hemorrhage control, thorough saline/water wound irrigation, infection prevention with sterile dressing, and screening for Tetanus Toxoid (TT) vaccination.",
            "ta": "நோயாளிக்கு மேலோட்டமான வெட்டுக் காயம், சிராய்ப்பு அல்லது சிறிய தீக்காயம் ஏற்பட்டுள்ளது. ரத்தப்போக்கைக் கட்டுப்படுத்துதல், சுத்தமான நீரால் கழுவுதல், கிருமிநாசினி மருந்து வைத்து கட்டுப்போடுதல் மற்றும் டெட்டனஸ் (TT) ஊசி போடுவது அவசியம்.",
            "hi": "मरीज को हल्की चोट, खरोंच, घाव या सामान्य रूप से जलने की समस्या है। सबसे पहले खून रोकना, साफ पानी से धोना, रोगाणुरोधी मरहम लगाना और टिटनेस (TT) इंजेक्शन की जरूरत देखना आवश्यक है।",
            "gu": "દર્દીને સામાન્ય ઘા, છોલાવું કે સામાન્ય દાઝવાની તકલીફ છે. પ્રાથમિક સારવારમાં લોહી બંધ કરવું, ચોખ્ખા પાણીથી ધોવું, પાટો બાંધવો અને ટિટનેસ (ધનુર) ના ઈન્જેક્શનની તપાસ કરવી જરૂરી છે."
        },
        home_care={
            "en": [
                "For cuts/wounds: Apply direct gentle pressure with a clean cloth or sterile gauze for 3-5 minutes to control minor bleeding.",
                "Rinse the wound thoroughly under clean running tap water for 5 minutes to wash away dirt and debris. Avoid harsh spirit directly in deep open cuts.",
                "Apply thin layer of Povidone-Iodine (5%) or topical antibiotic ointment and cover with sterile dry gauze.",
                "For minor burns: Immediately hold under cool running tap water for 10-15 minutes. NEVER apply ice, toothpaste, turmeric, mud, or butter.",
                "Do NOT intentionally pop burn blisters, as the intact skin blister acts as a natural sterile barrier against infection."
            ],
            "ta": [
                "ரத்தப்போக்கு இருந்தால் சுத்தமான துணியை வைத்து 3-5 நிமிடங்கள் மிதமான அழுத்தம் கொடுத்து ரத்தத்தை நிறுத்தவும்.",
                "காயத்தில் உள்ள தூசிகளை அகற்ற சுத்தமான ஓடும் தண்ணீரில் 5 நிமிடங்கள் நன்கு கழுவவும். ஆழமான காயத்தில் நேரடியாக ஸ்பிரிட் ஊற்ற வேண்டாம்.",
                "பொவிடோன் அயோடின் (Povidone-Iodine) அல்லது ஆன்டிசெப்டிக் களிம்பு தடவி சுத்தமான பஞ்சு அல்லது துணியால் கட்டுப்போடவும்.",
                "தீக்காயங்களுக்கு: உடனடியாக 10-15 நிமிடங்கள் குளிர்ந்த ஓடும் தண்ணீரில் காட்டவும். ஐஸ் கட்டி, பற்பசை (toothpaste), அல்லது வெண்ணெய் தடவக் கூடாது.",
                "தீக்காயக் கொப்புளங்களை ஊசியால் குத்தி உடைக்க வேண்டாம்; அது தொற்று ஏற்படாமல் காக்கும் இயற்கை கவசம்."
            ],
            "hi": [
                "खून बहने पर साफ कपड़े या पट्टी से 3-5 मिनट तक सीधा हल्का दबाव बनाएं।",
                "घाव को बहते साफ पानी से 5 मिनट तक अच्छी तरह धोएं ताकि धूल-मिट्टी निकल जाए। गहरे घाव में सीधा स्पिरिट न डालें।",
                "पोविडोन-आयोडीन (Povidone-Iodine) या एंटीसेप्टिक मरहम लगाएं और साफ सूती पट्टी बांधें।",
                "जलने पर: तुरंत 10-15 मिनट तक नल के ठंडे पानी में रखें। कभी भी बर्फ, टूथपेस्ट या हल्दी न लगाएं।",
                "जलने के छालों (ब्लिस्टर्स) को कभी न फोड़ें; यह संक्रमण से बचाने वाली प्राकृतिक परत है।"
            ],
            "gu": [
                "લોહી નીકળતું હોય તો ચોખ્ખા કપડાથી 3-5 મિનિટ દબાવી રાખો.",
                "ઘાને નળના વહેતા ચોખ્ખા પાણી નીચે 5 મિનિટ ધોવો જેથી ધૂળ નીકળી જાય.",
                "પોવિડોન-આયોડિન મલમ લગાવો અને જંતુરહિત પાટો બાંધો.",
                "દાઝવા પર: તરત જ 10-15 મિનિટ સામાન્ય વહેતા પાણીમાં રાખો. ક્યારેય બરફ કે ટૂથપેસ્ટ ન લગાવવી.",
                "દાઝેલા ફોલ્લાને ક્યારેય ફોડવા નહીં."
            ]
        },
        warning_signs={
            "en": [
                "Arterial spurting blood or persistent bleeding not controlled after 10 minutes of continuous direct pressure.",
                "Deep puncture wound (from rusty nail, metal, animal bite, or glass) requiring urgent Tetanus Toxoid (TT) vaccination.",
                "Inability to move the injured limb, numbness, tingling, or loss of sensation distal to the cut.",
                "Wound showing signs of secondary infection after 24-48 hours: increasing throbbing pain, warmth, foul smell, or yellowish pus.",
                "Burn involving the face, hands, feet, joints, genitalia, or electrical/chemical burns."
            ],
            "ta": [
                "10 நிமிட அழுத்தத்திற்குப் பிறகும் நிற்காத தொடர் ரத்தப்போக்கு.",
                "துருப்பிடித்த ஆணி, கம்பி, கண்ணாடி அல்லது விலங்கு கடியால் ஏற்பட்ட ஆழமான காயம் (உடனடி டெட்டனஸ் TT ஊசி தேவை).",
                "காயம் பட்ட கை அல்லது கால்களை அசைக்க முடியாமல் போவது அல்லது மரத்துப்போவது.",
                "24-48 மணி நேரத்திற்குப் பின் காயத்தில் தாங்க முடியாத வலி, வீக்கம், துர்நாற்றம் அல்லது சீழ் வடிதல்.",
                "முகம், கை, பாதம், மூட்டுகள் அல்லது பிறப்புறுப்பில் ஏற்பட்ட தீக்காயங்கள்."
            ],
            "hi": [
                "लगातार 10 मिनट दबाने के बाद भी खून का न रुकना या फव्वारे की तरह निकलना।",
                "जंग लगी कील, शीशा या जानवर के काटने से हुआ गहरा घाव (टिटनेस TT का टीका जरूरी)।",
                "चोट वाले अंग का सुन्न पड़ना या हिलाने में असमर्थता।",
                "घाव में 24 घंटे बाद तेज टीस, बदबू या पीप आना (गंभीर संक्रमण)।",
                "चेहरे, हाथ, पैर या जोड़ों पर गहरा जलना।"
            ],
            "gu": [
                "10 મિનિટ દબાવ્યા પછી પણ લોહી બંધ ન થવું.",
                "કાટવાળી ખીલી, કાચ કે જાનવર કરડવાથી થયેલો ઊંડો ઘા (ટિટનેસ ઇન્જેક્શન જરૂરી).",
                "અંગ સુન્ન થઈ જવું કે હલનચલન ન થવું.",
                "ઘામાંથી પરુ નીકળવું અથવા અસહ્ય દુખાવો થવો.",
                "ચહેરા કે હાથ-પગ પર ગંભીર દાઝવું."
            ]
        },
        referral_guidance={
            "en": "Visit the nearest Primary Health Centre (PHC) within 24 hours for evaluation of wound closure (suturing if wound edges are gapped >0.5cm), Tetanus Toxoid (TT) booster verification (if last dose was >5 years ago), and sterile dressing renewal.",
            "ta": "தையல் போட வேண்டிய ஆழமான காயங்கள் மற்றும் டெட்டனஸ் (TT) தடுப்பூசி போட்டுக்கொள்ள உடனடியாக ஆரம்ப சுகாதார நிலையத்தை (PHC) அணுகவும்.",
            "hi": "गहरे घाव में टांके लगाने और टिटनेस (TT) इंजेक्शन लगवाने के लिए 24 घंटे के भीतर नजदीकी प्राथमिक स्वास्थ्य केंद्र (PHC) जाएं।",
            "gu": "ટાંકા લેવા પડે તેવા ઊંડા ઘા અને ધનુર (TT) ના ઈન્જેક્શન માટે 24 કલાકમાં નજીકના પીએચસી પર જાઓ."
        }
    ),

    # 8. Acute Conjunctivitis & Red Eye Infection (Pink Eye)
    ClinicalProtocol(
        condition_id="acute_conjunctivitis",
        category="Ophthalmology / Visual Inspection",
        english_name="Acute Conjunctivitis & Red Eye (Pink Eye)",
        tamil_name="கண் சிவப்பு மற்றும் கண் தொற்று (மெட்ராஸ் ஐ)",
        hindi_name="आँख आना, लाल आँख और आँख का संक्रमण",
        gujarati_name="લાલ આંખ, આંખ આવવી અને નેત્રસ્તર દાહ",
        keywords=[
            "eye", "eyes", "red eye", "red eyes", "pink eye", "pink eyes", "conjunctivitis", "eye discharge", "watery eye", "watery eyes",
            "sticky eye", "sticky eyes", "eye burning", "eyes burning", "madras eye", "eye infection", "eyes red", "eye redness", "discharge",
            "கண்", "கண்கள்", "கண் சிவப்பு", "கண் வலி", "கண் தொற்று", "கண் நீர் வடிதல்", "மெட்ராஸ் ஐ", "கண் எரிச்சல்", "கண் பீளை",
            "आँख", "आँखों", "आँख आना", "आँख लाल", "आँख से पानी", "आँखों में जलन", "आँख चिपकना", "आँख में कीचड़",
            "આંખ", "લાલ આંખ", "આંખ આવવી", "આંખમાં બળતરા", "આંખમાંથી પાણી", "આંખ ચોંટવી"
        ],
        summary={
            "en": "Clinical presentation aligns with acute infectious or allergic conjunctivitis ('Pink Eye'). Standard care consists of cold saline eyelid cleansing, personal hygiene isolation, resting eyes, and strictly avoiding unprescribed steroid eye drops.",
            "ta": "நோயாளிக்கு கண் சிவப்பு மற்றும் கண் தொற்றின் (மெட்ராஸ் ஐ) அறிகுறிகள் உள்ளன. சுத்தமான நீரால் கண்களைக் கழுவுதல், தனித் துண்டு பயன்படுத்துதல் மற்றும் மருத்துவர் பரிந்துரையின்றி கடைகளில் கண் சொட்டு மருந்து வாங்குவதைத் தவிர்ப்பது முக்கியம்.",
            "hi": "मरीज में आँख आने (कंजंक्टिवाइटिस/गुलाबी आँख) के लक्षण हैं। सादे ठंडे पानी से पलकें साफ करना, अलग तौलिया रखना और बिना डॉक्टर सलाह कोई भी आई ड्रॉप न डालना आवश्यक है।",
            "gu": "દર્દીમાં આંખ આવવાના (લાલ આંખ) લક્ષણો છે. ઠંડા પાણીથી આંખો સાફ કરવી, અલગ રૂમાલ રાખવો અને ડૉક્ટરની સલાહ વગર કોઈ પણ આઈ ડ્રોપ્સ ન વાપરવા."
        },
        home_care={
            "en": [
                "Clean the crusting around eyelids using a clean cotton ball soaked in boiled, cooled water or normal saline, wiping from inner to outer corner. Use a separate cotton ball for each eye.",
                "Apply cold compresses (clean cloth dampened with cool water) over closed eyelids for 5-10 minutes to soothe burning and swelling.",
                "Wash hands thoroughly with soap and water before and after touching the face.",
                "Do NOT share towels, handkerchiefs, pillows, or eye drops with family members to prevent viral transmission.",
                "Wear dark protective sunglasses outdoors to reduce glare/light sensitivity and avoid eye rubbing."
            ],
            "ta": [
                "காய்ச்சி ஆறவைத்த நீரில் நனைத்த பஞ்சு கொண்டு இமைகளில் உள்ள பீளையை உள்பக்கமிருந்து வெளிப்பக்கமாக மெதுவாகத் துடைக்கவும். இரண்டு கண்களுக்கும் தனித்தனி பஞ்சு பயன்படுத்தவும்.",
                "கண்களை மூடிய நிலையில் குளிர்ந்த நீரில் நனைத்த சுத்தமான துணியை 5-10 நிமிடங்கள் ஒத்தடம் கொடுக்கவும்.",
                "கண்களைத் தொடுவதற்கு முன்னும் பின்னும் சோப்பு போட்டு கைகளை சுத்தமாகக் கழுவவும்.",
                "துண்டு, தலையணை, கைக்குட்டைகளை குடும்பத்தினருடன் பகிரக் கூடாது.",
                "வெளியில் செல்லும்போது கூலிங்கிளாஸ் (கருப்பு கண்ணாடி) அணியவும்; கண்களை கசக்கக் கூடாது."
            ],
            "hi": [
                "उबले और ठंडे पानी में भीगी साफ रुई से पलकों का कीचड़ अंदर से बाहर की ओर पोंछें। दोनों आंखों के लिए अलग रुई इस्तेमाल करें।",
                "आंखें बंद करके ठंडे पानी की साफ पट्टी 5-10 मिनट रखें ताकि जलन और सूजन कम हो।",
                "आंखों को छूने से पहले और बाद में साबुन से हाथ धोएं।",
                "अपना तौलिया, तकिया और रुमाल दूसरों से बिल्कुल अलग रखें।",
                "धूप में काला चश्मा पहनें और आंखों को रगड़ें नहीं।"
            ],
            "gu": [
                "ઉકાળીને ઠંડા કરેલા પાણીમાં રૂ બોળીને આંખો અંદરથી બહારની તરફ સાફ કરો. બંને આંખ માટે અલગ રૂ વાપરો.",
                "બંધ આંખો પર ઠંડા પાણીની પટ્ટી 5-10 મિનિટ મૂકો.",
                "હાથ વારંવાર સાબુથી ધોવા.",
                "રૂમાલ અને તકિયો અલગ રાખવો.",
                "બહાર જતી વખતે કાળો ચશ્મો પહેરવો અને આંખ ચોળવી નહીં."
            ]
        },
        warning_signs={
            "en": [
                "Severe, deep, throbbing ocular pain or feeling of sharp foreign object in eye.",
                "Noticeable decrease in vision, blurring, or seeing colored halos around lights.",
                "Extreme sensitivity to light (photophobia) preventing opening of the eye.",
                "Cloudiness or white/opaque spot on the cornea (black part of the eye).",
                "Unequal pupil size or pupil unresponsive to light."
            ],
            "ta": [
                "தாங்க முடியாத கடுமையான கண் வலி அல்லது கண்ணுக்குள் ஏதோ குத்துவது போன்ற உணர்வு.",
                "பார்வை மங்குதல் அல்லது வெளிச்சத்தைச் சுற்றி வளையங்கள் தெரிதல்.",
                "வெளிச்சத்தைப் பார்க்கவே முடியாத அதீத கூச்ச உணர்வு.",
                "கருவிழியில் (cornea) வெள்ளை நிற புள்ளி அல்லது மங்கலான நிலை ஏற்படுதல்.",
                "கண் பாப்பாவின் அளவில் மாற்றம் ஏற்படுதல்."
            ],
            "hi": [
                "आंख में असहनीय तेज दर्द या कुछ चुभने का गंभीर अहसास।",
                "दिखाई देने में कमी, धुंधलापन या रोशनी के आसपास घेरे दिखना।",
                "रोशनी से इतनी परेशानी कि आंख खोलना असंभव हो।",
                "पुतली (काले हिस्से) पर सफेद धब्बा या धुंधलापन आना।",
                "दोनों आंखों की पुतलियों के आकार में अंतर होना।"
            ],
            "gu": [
                "આંખમાં અસહ્ય તીવ્ર દુખાવો થવો.",
                "દ્રષ્ટિ ઓછી થવી અથવા ઝાંખપ આવવી.",
                "પ્રકાશ સહન ન થવો.",
                "કીકી પર સફેદ ડાઘ કે ઝાંખપ દેખાવી.",
                "કીકીના કદમાં ફેરફાર થવો."
            ]
        },
        referral_guidance={
            "en": "Prompt clinical evaluation by a PHC medical officer or ophthalmologist is required to distinguish bacterial from viral etiology and prescribe verified antibiotic eye drops (e.g., Ciprofloxacin / Moxifloxacin). NEVER use steroid combination drops without direct slit-lamp examination.",
            "ta": "சரியான கண் சொட்டு மருந்து பெற ஆரம்ப சுகாதார நிலைய மருத்துவரை அணுகவும். மருத்துவர் ஆலோசனையின்றி மருந்தகங்களில் தானாக ஸ்டீராய்டு சொட்டு மருந்துகளை ஒருபோதும் வாங்கிப் பயன்படுத்தக் கூடாது.",
            "hi": "सही एंटीबायोटिक आई ड्रॉप्स के लिए प्राथमिक स्वास्थ्य केंद्र (PHC) के डॉक्टर या नेत्र विशेषज्ञ को दिखाएं। बिना डॉक्टर पर्ची के कभी भी स्टेरॉयड वाली ड्रॉप्स न डालें।",
            "gu": "યોગ્ય એન્ટિબાયોટિક ડ્રોપ્સ માટે પીએચસી ડૉક્ટર કે આંખના નિષ્ણાત પાસે તપાસ કરાવો. ડૉક્ટરની સલાહ વિના જાતે ટીપાં ન નાખવા."
        }
    ),

    # 9. Insect Bites, Stings & Localized Skin Abscess / Furuncle
    ClinicalProtocol(
        condition_id="insect_bite_abscess",
        category="Dermatology / Local Infection",
        english_name="Insect Bites, Stings & Localized Skin Abscess",
        tamil_name="பூச்சி கடி, வீக்கம் மற்றும் தோல் கட்டி",
        hindi_name="कीड़ा काटना, डंक और त्वचा का फोड़ा-फुंसी",
        gujarati_name="કીડા-મધમાખીનો ડંખ અને ચામડી પર ગૂમડું",
        keywords=[
            "insect bite", "bug bite", "bee sting", "wasp sting", "spider bite", "boil", "abscess", "furuncle", "swelling", "bump",
            "பூச்சி கடி", "குளவி கொட்டு", "தேனீ கொட்டு", "வீக்கம்", "கட்டி", "கொப்புளம்", "பிளவை",
            "कीड़ा काटना", "डंक", "मधुमक्खी", "सूजन", "फोड़ा", "फुंसी", "गांठ",
            "કીડાનો ડંખ", "મધમાખી", "ડંખ", "સોજો", "ગૂમડું", "ફોલ્લો", "ગાંઠ"
        ],
        summary={
            "en": "Presentation shows localized tissue reaction from an insect bite/sting or a localized cutaneous abscess (boil). First-line care includes cold compress, gentle elevation, sting removal, and warm moist heat for abscesses. Squeezing or popping must be strictly avoided.",
            "ta": "நோயாளிக்கு பூச்சி கடி, கொட்டுதல் அல்லது தோலில் சீழ் கட்டியின் அறிகுறிகள் உள்ளன. ஐஸ் ஒத்தடம் கொடுத்தல், சுத்தமாக வைத்திருத்தல் மற்றும் கட்டியை அழுத்திப் பிதுக்குவதைத் தவிர்ப்பது அவசியமான முதலுதவி.",
            "hi": "मरीज को कीड़ा काटने, डंक या त्वचा पर फोड़ा-फुंसी (एब्सेस) की समस्या है। बर्फ की सिकाई, सफाई और फोड़े को दबाकर न फोड़ना प्राथमिक उपचार है।",
            "gu": "દર્દીને કીડાનો ડંખ અથવા ચામડી પર ગૂમડાંની તકલીફ છે. બરફનો શેક કરવો અને ગૂમડાંને દબાવીને ફોડવું નહીં તે મુખ્ય સંભાળ છે."
        },
        home_care={
            "en": [
                "For insect stings: Gently scrape away visible stinger with a blunt edge (e.g., edge of a card). Do not squeeze with tweezers.",
                "Wash the bite area thoroughly with soap and water.",
                "Apply an ice pack wrapped in a clean cloth for 10-15 minutes every hour to reduce local pain and swelling.",
                "Apply Calamine lotion or a paste of baking soda and water to alleviate itching and pain.",
                "For skin boils/abscesses: Apply a clean warm, moist compress for 10-15 minutes 3-4 times daily to promote natural circulation. NEVER squeeze, press, or pierce a boil."
            ],
            "ta": [
                "கொட்டிய விஷ முள் தெரிந்தால் நகம் அல்லது அட்டை கொண்டு மெதுவாக சுரண்டி எடுக்கவும்; இடுக்கிகளால் பிதுக்க வேண்டாம்.",
                "கடித்த இடத்தை சோப்பு மற்றும் தண்ணீரால் சுத்தமாகக் கழுவவும்.",
                "வீக்கம் மற்றும் வலியைக் குறைக்க துணியில் சுற்றிய ஐஸ் கட்டியை 10-15 நிமிடங்கள் ஒத்தடம் கொடுக்கவும்.",
                "அரிப்பு குறைய கலாமின் லோஷன் தடவலாம்.",
                "கட்டிகளுக்கு: சுடுநீரில் நனைத்த துணியால் தினமும் 3-4 முறை வெதுவெதுப்பான ஒத்தடம் கொடுக்கவும். கட்டியை ஒருபோதும் கையால் பிதுக்கக் கூடாது."
            ],
            "hi": [
                "यदि डंक दिख रहा हो तो किसी कार्ड के किनारे से खुरच कर निकालें; चिमटी से दबाकर न खींचें।",
                "प्रभावित जगह को साबुन और पानी से अच्छी तरह धोएं।",
                "दर्द और सूजन कम करने के लिए कपड़े में लपेटकर बर्फ की 10-15 मिनट सिकाई करें।",
                "खुजली शांत करने के लिए कैलामाइन लोशन लगाएं।",
                "फोड़े-फुंसी के लिए: दिन में 3-4 बार गर्म पानी की गीली पट्टी रखें ताकि स्वाभाविक रूप से आराम मिले। फोड़े को कभी दबाकर न फोड़ें।"
            ],
            "gu": [
                "ડંખ દેખાતો હોય તો કાર્ડની ધારથી હળવેથી કાઢી લો; દબાવવું નહીં.",
                "જગ્યાને સાબુ અને પાણીથી બરાબર ધોઈ લો.",
                "સોજો અને દુખાવો ઘટાડવા કપડામાં બરફ લપેટીને 10-15 મિનિટ શેક કરો.",
                "ખંજવાળ માટે કેલામાઇન લોશન લગાવો.",
                "ગૂમડાં માટે: દિવસમાં 3-4 વાર ગરમ પાણીનો શેક કરવો. ગૂમડાંને ક્યારેય દબાવવું નહીં."
            ]
        },
        warning_signs={
            "en": [
                "Systemic allergic reaction (Anaphylaxis): sudden difficulty breathing, throat constriction, wheezing, swelling of tongue/lips, or fainting.",
                "Bite from a known venomous snake, scorpion, or spider requiring emergency antiserum.",
                "Rapidly expanding red streak spreading upward from the bite site (lymphangitis).",
                "Abscess larger than 5cm, extremely hard, throbbing intensely, or accompanied by high fever >101°F.",
                "Boils located on the central face ('danger triangle of the face' between nose and upper lip)."
            ],
            "ta": [
                "திடீர் மூச்சுத்திணறல், நாக்கு/தொண்டை வீங்குதல், குரல் மாறுதல் அல்லது மயக்கம் (தீவிர அனாபிலாக்சிஸ் எச்சரிக்கை).",
                "விஷப் பாம்பு, தேள் அல்லது விஷப் பூச்சி கடித்திருந்தால் (உடனடி முறி மருந்து தேவை).",
                "கடித்த இடத்திலிருந்து சிவப்பு கோடு போல் நரம்பு வழியாக வேகமாக மேல்நோக்கிப் பரவுதல்.",
                "கட்டி 5 செ.மீ விட பெரியதாக இருத்தல், தாங்க முடியாத வலி அல்லது அதிக காய்ச்சல் ஏற்படுதல்.",
                "மூக்கு மற்றும் மேல் உதட்டுக்கு இடைப்பட்ட ஆபத்தான முக்கோணப் பகுதியில் உள்ள கட்டிகள்."
            ],
            "hi": [
                "सांस लेने में भारी तकलीफ, गले में घुटन, होंठ-जीभ में सूजन या बेहोशी (एनाफिलेक्सिस आपातकाल)।",
                "जहरीले सांप, बिच्छू या मकड़ी का काटना (तुरंत एंटी-वेनम की जरूरत)।",
                "डंक वाली जगह से ऊपर की ओर लाल लकीर का तेजी से बढ़ना।",
                "फोड़ा 5 सेमी से बड़ा होना, बहुत तेज टीस मारना या तेज बुखार आना।",
                "नाक और ऊपरी होंठ के बीच के चेहरे के संवेदनशील हिस्से पर फोड़ा होना।"
            ],
            "gu": [
                "શ્વાસ લેવામાં તકલીફ, ગળું રુંધાવું, હોઠ-જીભ પર સોજો અથવા બેભાન થવું.",
                "ઝેરી સાપ કે વીંછીનો ડંખ.",
                "ડંખવાળી જગ્યાએથી લાલ રેખા આગળ વધવી.",
                "ગૂમડું ઘણું મોટું થવું અથવા સખત તાવ આવવો.",
                "ચહેરા પર નાક અને હોઠ વચ્ચે ગૂમડું થવું."
            ]
        },
        referral_guidance={
            "en": "EMERGENCY: If any signs of systemic allergy (breathing distress, facial swelling) occur, call 108 or transfer immediately to hospital for intramuscular Epinephrine. For large fluctuating abscesses, refer to PHC for minor surgical incision and drainage (I&D) under local anesthesia.",
            "ta": "மூச்சுத்திணறல் அல்லது முக வீக்கம் இருந்தால் உடனடியாக 108 அவசர ஊர்தியை அழைத்து மருத்துவமனைக்குச் செல்லவும். பெரிய சீழ் கட்டிகளுக்கு ஆரம்ப சுகாதார நிலையத்தில் சிறு அறுவை சிகிச்சை மூலம் சீழை அகற்ற வேண்டும்.",
            "hi": "यदि सांस लेने में तकलीफ या चेहरे पर सूजन हो तो तुरंत 108 पर कॉल करें या आपातकालीन अस्पताल जाएं। बड़े फोड़े के लिए पीएचसी जाकर डॉक्टर से सफाई करवाएं।",
            "gu": "જો શ્વાસ લેવામાં તકલીફ થાય તો તાત્કાલિક 108 બોલાવો. મોટા ગૂમડાં માટે પીએચસી પર જઈને ડૉક્ટરની સલાહ મુજબ સારવાર કરાવો."
        }
    ),

    # 10. Shoulder Pain & Musculoskeletal Joint Strain
    ClinicalProtocol(
        condition_id="musculoskeletal_shoulder_joint_pain",
        category="Musculoskeletal / Orthopedic",
        english_name="Shoulder Pain and Joint Strain",
        tamil_name="தோள் பட்டை மற்றும் மூட்டு வலி",
        hindi_name="कंधे और जोड़ों का दर्द",
        gujarati_name="ખભા અને સાંધાનો દુખાવો",
        keywords=[
            "shoulder", "shoulder pain", "shoulder ache", "rotator cuff", "dislocated shoulder",
            "shoulder dislocation", "frozen shoulder", "shoulder injury", "collarbone", "shoulder joint",
            "deltoid", "arm pain", "shoulder strain", "joint strain", "sprain", "stiff shoulder",
            "தோள்", "தோள்பட்டை", "தோள் பட்டை", "தோள் வலி", "தோள்பட்டை வலி", "தோள் பட்டை வலி",
            "कंधा", "कंधे", "कंधों", "कंधे में दर्द", "कंधे का दर्द", "कंधा दर्द", "कंधे की चोट", "हाथ में दर्द", "कंधा उतरना",
            "ખભો", "ખભા", "ખભાનો દુખાવો", "ખભામાં દુખાવો", "ખભાની ઈજા", "હાથનો દુખાવો", "સાંધાનો દુખાવો"
        ],
        summary={
            "en": "The patient reports shoulder pain, commonly resulting from acute muscle strain, rotator cuff tendinitis, joint sprain, or posture/overuse injury. Immediate first aid emphasizes joint resting, cold therapy, and gentle support to avoid aggravating the joint.",
            "ta": "நோயாளிக்கு தோள் பட்டை வலி மற்றும் தசை இறுக்கத்தின் அறிகுறிகள் உள்ளன. இது தசைப்பிடிப்பு, தசைநார் காயம் அல்லது அதிக பளு தூக்குவதால் ஏற்படலாம். மூட்டுக்கு ஓய்வளித்தல், ஐஸ் ஒத்தடம் மற்றும் மிதமான ஆதரவு உடனடி நிவாரணம் தரும்.",
            "hi": "मरीज को कंधे में दर्द और मांसपेशियों के खिंचाव के लक्षण हैं। यह वजन उठाने, गलत मुद्रा या खिंचाव के कारण हो सकता है। कंधे को आराम देना और ठंडी सिकाई करना तुरंत राहत देता है।",
            "gu": "દર્દીને ખભામાં દુખાવો અને સ્નાયુમાં ખેંચાણના લક્ષણો છે. આ ભારે વજન ઊંચકવાથી કે સ્નાયુની ઈજાને કારણે હોઈ શકે છે. ખભાને આરામ આપવો અને બરફનો શેક કરવો ફાયદાકારક છે."
        },
        home_care={
            "en": [
                "Rest the affected shoulder completely and strictly avoid heavy lifting, sudden jerks, or overhead arm reaching for 48-72 hours.",
                "Apply an ice pack wrapped in a cloth or clean towel for 15-20 minutes every 3-4 hours during the first 48 hours to minimize inflammation and pain.",
                "Support the arm in a comfortable resting position using a soft pillow or simple arm sling if moving causes sharp pain.",
                "After 48 hours, switch to mild warm compresses and begin very gentle, pain-free pendulum swinging arm movements.",
                "For acute pain relief, adult standard medication is Paracetamol 500mg up to twice or thrice daily after meals if not contraindicated. Avoid heavy NSAIDs if hypertensive."
            ],
            "ta": [
                "பாதிக்கப்பட்ட தோள்பட்டைக்கு முழு ஓய்வு அளிக்கவும்; கனமான பொருள்களைத் தூக்குவதையோ கையை தலைக்கு மேல் தூக்குவதையோ 48 மணி நேரத்திற்கு தவிர்க்கவும்.",
                "வலியை குறைக்க ஒரு துணியில் சுற்றப்பட்ட ஐஸ் கட்டியை வலி உள்ள இடத்தில் 15-20 நிமிடங்கள் வரை ஒத்தடம் கொடுக்கவும் (ஒரு நாளைக்கு 3-4 முறை).",
                "கை அசையும்போது தீவிர வலி இருந்தால் தலையணை அல்லது ஸ்லிங் (துணி தாங்கி) கொண்டு கைக்கு ஆதரவு அளிக்கவும்.",
                "48 மணி நேரத்திற்குப் பிறகு மிதமான வெந்நீர் ஒத்தடம் கொடுத்து கையை மெதுவாக முன்னும் பின்னும் அசைக்கும் எளிய பயிற்சிகளைச் செய்யவும்.",
                "தாங்க முடியாத வலிக்கு பாராசிட்டமால் 500mg மாத்திரை மருத்துவர் ஆலோசனையுடன் எடுத்துக்கொள்ளலாம்; வலி நிவாரணி தைலங்களை மென்மையாகத் தடவலாம்."
            ],
            "hi": [
                "कंधे को पूरा आराम दें; अगले 48 घंटों तक कोई भी भारी वजन उठाने या हाथ को ऊपर उठाने से बचें।",
                "दर्द और सूजन कम करने के लिए कपड़े में लपेटकर बर्फ से 15-20 मिनट सिकाई करें (दिन में 3-4 बार)।",
                "यदि हाथ हिलाने पर तेज दर्द हो तो तकिए या आर्म स्लिंग से हाथ को सहारा देकर रखें।",
                "48 घंटे बाद हल्की गर्म सिकाई करें और बिना जोर लगाए हाथ को धीरे-धीरे हिलाने का व्यायाम करें।",
                "दर्द से राहत के लिए आवश्यकतानुसार पैरासिटामोल 500mg ले सकते हैं।"
            ],
            "gu": [
                "ખભાને સંપૂર્ણ આરામ આપો; ભારે વજન ઊંચકવું કે હાથ ઊંચો કરવાનું ટાળો.",
                "સોજો અને દુખાવો ઘટાડવા કપડામાં બરફ લપેટીને 15-20 મિનિટ શેક કરો.",
                "હાથ હલાવવામાં દુખાવો થતો હોય તો ગળામાં પટ્ટો અથવા ઓશીકું રાખીને હાથને ટેકો આપો.",
                "48 કલાક પછી હળવો ગરમ શેક કરી ધીમે ધીમે હાથની હળવી કસરત કરો.",
                "જરૂર જણાય તો પેરાસિટામોલ 500mg ગોળી લઈ શકાય."
            ]
        },
        warning_signs={
            "en": [
                "Sudden visible deformity, abnormal joint protrusion, or suspected shoulder dislocation.",
                "Complete inability to raise or rotate the arm, or loss of sensation in the arm/fingers.",
                "Numbness, tingling, severe coldness, or blue/pale discoloration of hand and fingers.",
                "Chest tightness, pressure, or shortness of breath radiating to the left shoulder (Cardiac Emergency - Call 108 immediately!).",
                "Severe unbearable pain immediately following a fall, collision, or direct physical impact."
            ],
            "ta": [
                "தோள்பட்டை மூட்டு விலகியிருத்தல் (Dislocation) அல்லது மூட்டில் அசாதாரண வீக்கம்/வடிவ மாற்றம் ஏற்படுதல்.",
                "கையை சிறிதும் அசைக்கவோ மேலே தூக்கவோ முடியாத நிலை அல்லது விரல்களில் உணர்வின்மை.",
                "கைகளில் மரத்துப்போதல், ஊசி குத்துவது போன்ற உணர்வு அல்லது கை நீல நிறமாக மாறுதல்.",
                "இடது தோள்பட்டையில் வலி பரவும் நெஞ்சு வலி, நெஞ்சு இறுக்கம் அல்லது அதீத வியர்வை (மாரடைப்பு ஆபத்து - உடனே 108 அழைக்கவும்!).",
                "விபத்து அல்லது கீழே விழுந்ததால் ஏற்பட்ட தாங்க முடியாத வலி."
            ],
            "hi": [
                "कंधे का अपनी जगह से खिसक जाना (डिसलोकेशन) या स्पष्ट रूप से टेढ़ा दिखना।",
                "हाथ को बिल्कुल भी न उठा पाना या उंगलियों का सुन्न हो जाना।",
                "हाथ में झुनझुनी, अत्यधिक ठंडक या नीलापन आना।",
                "बाएं कंधे की ओर जाता हुआ सीने का दर्द या भारीपन (हार्ट अटैक का खतरा - तुरंत 108 बुलाएं)।",
                "चोट या गिरने के बाद असहनीय दर्द होना।"
            ],
            "gu": [
                "ખભાનું સાંધામાંથી ખસી જવું અથવા સોજો આવવો.",
                "હાથ સહેજ પણ ઊંચો ન થઈ શકવો અથવા આંગળીઓ સુન્ન થવી.",
                "ડાબા ખભામાં દુખાવાની સાથે છાતીમાં દબાણ કે શ્વાસ ચઢવો (હાર્ટ એટેકનો સંકેત - તાત્કાલિક 108 બોલાવો).",
                "ઈજા કે અકસ્માત પછી અસહ્ય દુખાવો થવો."
            ]
        },
        referral_guidance={
            "en": "Visit the Primary Health Centre (PHC) medical officer or orthopedic specialist for an X-ray and clinical examination if pain persists beyond 3-5 days, or immediately if there is a fall, visible deformity, or inability to move the arm.",
            "ta": "வலி 3-5 நாட்களுக்கு மேல் நீடித்தாலோ அல்லது கீழே விழுந்ததால் ஏற்பட்ட காயமாக இருந்தாலோ, எக்ஸ்-ரே (X-Ray) பரிசோதனை செய்ய ஆரம்ப சுகாதார நிலையத்தை (PHC) அணுகவும்.",
            "hi": "यदि दर्द 3-5 दिनों से अधिक बना रहे या चोट लगी हो, तो एक्स-रे और जांच के लिए प्राथमिक स्वास्थ्य केंद्र (PHC) या हड्डी के डॉक्टर से परामर्श लें।",
            "gu": "જો દુખાવો 3-5 દિવસથી વધુ રહે અથવા ઈજા થઈ હોય, તો એક્સ-રે અને તપાસ માટે નજીકના પ્રાથમિક આરોગ્ય કેન્દ્ર (PHC) પર જાઓ."
        }
    ),

    # 11. Low Back Pain & Lumbar Strain
    ClinicalProtocol(
        condition_id="back_pain_lumbar_strain",
        category="Musculoskeletal / Orthopedic",
        english_name="Low Back Pain and Lumbar Strain",
        tamil_name="முதுகு வலி மற்றும் இடுப்பு வலி",
        hindi_name="कमर और पीठ दर्द",
        gujarati_name="કમર અને પીઠનો દુખાવો",
        keywords=[
            "back pain", "lower back", "lumbar", "spine", "sciatica", "slip disc", "stiff back",
            "முதுகு வலி", "முதுகு", "இடுப்பு வலி", "இடுப்பு", "தண்டுவடம்", "இடுப்பு பிடிப்பு",
            "पीठ दर्द", "कमर दर्द", "कमर", "रीढ़ की हड्डी", "सायटिका",
            "પીઠનો દુખાવો", "કમરનો દુખાવો", "કમર", "સાયટિકા"
        ],
        summary={
            "en": "Symptoms indicate acute mechanical low back strain. Standard non-pharmacological care involves active gentle mobility, avoiding prolonged bed rest, using a firm mattress, and applying local heat or cold packs.",
            "ta": "நோயாளிக்கு தசைப்பிடிப்பு சார்ந்த முதுகு மற்றும் இடுப்பு வலி உள்ளது. நீண்ட நேரம் ஒரே இடத்தில் உட்காருவதைத் தவிர்ப்பதும், மிதமான வெந்நீர் ஒத்தடமும் நல்ல பலன் தரும்.",
            "hi": "मरीज को कमर की मांसपेशियों में खिंचाव का दर्द है। बहुत देर तक बिस्तर पर लेटे रहने के बजाय हल्की चहलकदमी और गर्म सिकाई से आराम मिलता है।",
            "gu": "દર્દીને કમરના સ્નાયુઓમાં ખેંચાણનો દુખાવો છે. લાંબા સમય સુધી એક જગ્યાએ બેસવાનું ટાળવું અને ગરમ શેક કરવો સારો રહે છે."
        },
        home_care={
            "en": [
                "Avoid prolonged bed rest; maintain gentle walking and activities within pain limits.",
                "Apply warm compresses or an ice pack to the lower back for 15-20 minutes, 2-3 times daily.",
                "Sleep on a firm, supportive mattress; placing a pillow under the knees relieves spinal pressure.",
                "Avoid heavy weight lifting, sudden bending, or twisting the spine.",
                "Perform gentle core and back stretches once acute severe pain subsides."
            ],
            "ta": [
                "நாள் முழுவதும் படுக்கையிலேயே இருக்க வேண்டாம்; மிதமான நடைப்பயிற்சியை மேற்கொள்ளவும்.",
                "முதுகு பகுதியில் 15-20 நிமிடங்கள் வெந்நீர் ஒத்தடம் அல்லது ஐஸ் ஒத்தடம் கொடுக்கவும்.",
                "உறுதியான படுக்கையில் படுக்கவும்; முழங்கால்களுக்கு அடியில் தலையணை வைப்பது இடுப்பு அழுத்தத்தைக் குறைக்கும்.",
                "குனிந்து அதிக எடையைத் தூக்குவதையோ, உடலை திடீரென திருப்புவதையோ தவிர்க்கவும்."
            ],
            "hi": [
                "पूरा दिन बिस्तर पर न रहें; हल्का चलना-फिरना जारी रखें।",
                "कमर पर 15-20 मिनट गर्म पानी की थैली या बर्फ से सिकाई करें।",
                "सख्त गद्दे पर सोएं और घुटनों के नीचे तकिया रखें।",
                "झुककर भारी सामान न उठाएं।"
            ],
            "gu": [
                "આખો દિવસ પલંગ પર સૂઈ ન રહેવું; હળવું ચાલવાનું રાખો.",
                "કમર પર 15-20 મિનિટ ગરમ પાણીની થેલીથી શેક કરો.",
                "વધુ વજન ઉપાડવાનું કે અચાનક વળવાનું ટાળો."
            ]
        },
        warning_signs={
            "en": [
                "Loss of bowel or bladder control (Cauda Equina syndrome - Red Flag Emergency!).",
                "Progressive numbness, weakness, or 'pins and needles' sensation radiating down both legs.",
                "Back pain accompanied by high fever or unexplained weight loss.",
                "Severe back pain after a high-velocity road accident or significant fall."
            ],
            "ta": [
                "சிறுநீர் அல்லது மலம் கழிப்பதைக் கட்டுப்படுத்த முடியாத நிலை (அவசர மருத்துவ உதவி தேவை!).",
                "கால்களில் உணர்வின்மை அல்லது மரத்துப்போதல் ஏற்படுதல்.",
                "முதுகு வலியுடன் கூடிய தீவிர காய்ச்சல்."
            ],
            "hi": [
                "पेशाब या शौच पर नियंत्रण खो जाना (तत्काल आपातकालीन चिकित्सा जरूरी)।",
                "पैरों में सुन्नपन या कमजोरी का बढ़ना।",
                "कमर दर्द के साथ तेज बुखार होना।"
            ],
            "gu": [
                "પેશાબ કે શૌચ પરનો કાબૂ ગુમાવવો (તાત્કાલિક હોસ્પિટલ જવું).",
                "પગમાં સુન્નતા કે નબળાઈ વધવી."
            ]
        },
        referral_guidance={
            "en": "Consult a PHC medical officer if back pain persists beyond 7 days or radiates down below the knee. Immediate hospital transfer if bowel/bladder control is impaired.",
            "ta": "முதுகு வலி 7 நாட்களுக்கு மேல் நீடித்தாலோ அல்லது கால்களுக்குப் பரவினாலோ ஆரம்ப சுகாதார நிலையத்தை அணுகவும்.",
            "hi": "यदि कमर दर्द 7 दिनों से अधिक रहे तो पीएचसी जाकर डॉक्टर को दिखाएं।",
            "gu": "જો કમરનો દુખાવો અઠવાડિયાથી વધુ સમય રહે તો પ્રાથમિક આરોગ્ય કેન્દ્ર પર તપાસ કરાવો."
        }
    ),

    # 12. Knee & Leg Joint Pain / Arthritis
    ClinicalProtocol(
        condition_id="knee_and_leg_joint_pain",
        category="Musculoskeletal / Orthopedic",
        english_name="Knee Joint Pain and Strain",
        tamil_name="முழங்கால் மற்றும் மூட்டு வலி",
        hindi_name="घुटने और जोड़ों का दर्द",
        gujarati_name="ઘૂંટણ અને સાંધાનો દુખાવો",
        keywords=[
            "knee", "knee pain", "joint pain", "arthritis", "swollen knee", "leg joint", "knee strain",
            "முழங்கால் வலி", "முட்டி வலி", "மூட்டு வலி", "கால் மூட்டு வலி", "முட்டி வீக்கம்", "முழங்கால் தேய்மானம்",
            "घुटना", "घुटने का दर्द", "जोड़ों में दर्द", "गठिया", "घुटने की सूजन",
            "ઘૂંટણ", "ઘૂંટણનો દુખાવો", "સાંધાનો સોજો", "સંધિવા"
        ],
        summary={
            "en": "The patient reports knee joint pain, commonly related to ligament strain, meniscus irritation, or early degenerative joint changes (osteoarthritis). Management emphasizes joint protection, cold/warm therapy, and quadriceps strengthening.",
            "ta": "நோயாளிக்கு முழங்கால் மூட்டு வலி மற்றும் வீக்கம் உள்ளது. மூட்டுக்கு அதிக சுமை கொடுக்காமல் ஓய்வளித்தல் மற்றும் எளிய மூட்டு பயிற்சிகள் நிவாரணம் அளிக்கும்.",
            "hi": "मरीज को घुटने में दर्द और सूजन के लक्षण हैं। घुटने पर अधिक दबाव न डालना और सिकाई करना लाभकारी है।",
            "gu": "દર્દીને ઘૂંટણમાં દુખાવો અને સોજો છે. ઘૂંટણ પર વધુ ભાર ન આપવો અને શેક કરવો યોગ્ય છે."
        },
        home_care={
            "en": [
                "Avoid deep squatting, sitting cross-legged on the floor, and repetitive stair climbing.",
                "Apply an ice pack for acute swelling (15-20 min), or warm compress for morning stiffness.",
                "Wear well-cushioned footwear and use a supportive elastic knee brace while walking.",
                "Perform gentle straight-leg raises to strengthen quadriceps without loading the joint."
            ],
            "ta": [
                "சம்மணமிட்டு தரையில் அமர்வதையும், முழங்காலை மடக்கி உட்காருவதையும் தவிர்க்கவும்.",
                "வீக்கம் இருந்தால் ஐஸ் ஒத்தடமும், அதிக இறுக்கம் இருந்தால் வெந்நீர் ஒத்தடமும் கொடுக்கவும்.",
                "நடைப்பயிற்சியின் போது முழங்கால் பேண்ட் (Knee Cap) அணிந்து கொள்ளவும்."
            ],
            "hi": [
                "जमीन पर पालथी मारकर बैठने और सीढ़ियां चढ़ने-उतरने से बचें।",
                "सूजन होने पर बर्फ और अकड़न होने पर गर्म पानी की सिकाई करें।",
                "चलते समय नी-कैप (Knee Cap) का उपयोग करें।"
            ],
            "gu": [
                "પલાંઠી વાળીને જમીન પર બેસવાનું ટાળો.",
                "ચાલતી વખતે ઘૂંટણ પર પટ્ટો (Knee Cap) પહેરો."
            ]
        },
        warning_signs={
            "en": [
                "Complete inability to bear weight on the leg or sudden locking of the knee joint.",
                "Severe red, hot, exquisitely tender swelling (rule out septic arthritis / acute gout).",
                "Gross visible joint deformity following an injury."
            ],
            "ta": [
                "காலில் கொஞ்சமும் எடையைத் தாங்க முடியாத நிலை அல்லது முழங்கால் லாக் ஆகி மடங்காமல் போதல்.",
                "முழங்கால் அதிக சூடாகவும், சிவந்தும் காணப்படுதல்."
            ],
            "hi": [
                "पैर पर बिल्कुल वजन न दे पाना या घुटने का मुड़ना बंद हो जाना।",
                "घुटने में अत्यधिक लाली, गर्मी और असहनीय दर्द होना।"
            ],
            "gu": [
                "પગ પર જરાય વજન ન દઈ શકવું અથવા ઘૂંટણ અટકી જવું."
            ]
        },
        referral_guidance={
            "en": "Refer to PHC for X-ray and medical review if pain limits walking or lasts beyond 1-2 weeks.",
            "ta": "வலி 1-2 வாரங்களுக்கு மேல் நீடித்தால் எக்ஸ்-ரே எடுக்க ஆரம்ப சுகாதார நிலையத்தை அணுகவும்.",
            "hi": "यदि दर्द 1-2 सप्ताह से अधिक रहे तो एक्स-रे के लिए प्राथमिक स्वास्थ्य केंद्र जाएं।",
            "gu": "જો દુખાવો લાંબો સમય રહે તો પ્રાથમિક આરોગ્ય કેન્દ્ર પર સંપર્ક કરવો."
        }
    ),

    # 13. Abdominal Pain & Gastritis / Acidity
    ClinicalProtocol(
        condition_id="abdominal_pain_gastritis",
        category="Gastrointestinal",
        english_name="Abdominal Pain, Gastritis and Acidity",
        tamil_name="வயிற்று வலி மற்றும் அசிடிட்டி / நெஞ்செரிச்சல்",
        hindi_name="पेट दर्द, गैस और एसिडिटी",
        gujarati_name="પેટમાં દુખાવો, ગેસ અને એસિડિટી",
        keywords=[
            "stomach", "stomach pain", "stomach ache", "belly pain", "abdominal pain", "gastritis", "acidity",
            "heartburn", "indigestion", "gas", "bloating", "acid reflux", "stomach burning",
            "வயிற்று வலி", "வயிறு வலி", "வயிறு", "வயித்து வலி", "அசிடிட்டி", "நெஞ்செரிச்சல்", "செரிமானமின்மை", "வயிறு உப்புசம்", "வாயு",
            "पेट", "पेट दर्द", "पेट में दर्द", "एसिडिटी", "गैस", "सीने में जलन", "बदहजमी", "अपच", "पेट जलन",
            "પેટ", "પેટનો દુખાવો", "પેટમાં દુખાવો", "એસિડિટી", "ગેસ", "અપચો", "છાતીમાં બળતરા"
        ],
        summary={
            "en": "The patient reports abdominal discomfort or epigastric pain, commonly related to hyperacidity, gastritis, or dietary indigestion. Initial home measures focus on bland dietary management and avoiding irritants.",
            "ta": "நோயாளிக்கு வயிற்று வலி மற்றும் நெஞ்செரிச்சல் / அசிடிட்டியின் அறிகுறிகள் உள்ளன. காரமான உணவுகளைத் தவிர்த்து, எளிதில் செரிமானமாகும் உணவுகளை உண்பது நிவாரணம் அளிக்கும்.",
            "hi": "मरीज को पेट दर्द, एसिडिटी या सीने में जलन की समस्या है। हल्का और सादा भोजन करना तथा तली-भुनी चीजों से परहेज करना जरूरी है।",
            "gu": "દર્દીને પેટમાં દુખાવો, એસિડિટી કે ગેસની તકલીફ છે. સાદો ખોરાક લેવો અને મસાલેદાર વસ્તુઓ ટાળવી જરૂરી છે."
        },
        home_care={
            "en": [
                "Eat small, frequent meals rather than large heavy portions.",
                "Strictly avoid oily, spicy, deep-fried foods, tea, coffee, carbonated drinks, and tobacco.",
                "Drink adequate plain room-temperature water or cool buttermilk (chaas).",
                "Do not lie down flat immediately after eating; wait at least 2 hours before sleeping."
            ],
            "ta": [
                "ஒரே நேரத்தில் அதிகமாக சாப்பிடாமல், சீரான இடைவெளியில் குறைந்த அளவு உணவு உட்கொள்ளவும்.",
                "அதிக காரம், எண்ணெய் பலகாரங்கள், டீ, காபி மற்றும் புகையிலையைத் தவிர்க்கவும்.",
                "சீரகத் தண்ணீர், மோர் அல்லது இளநீர் அருந்துவது வயிற்று எரிச்சலைத் தணிக்கும்.",
                "சாப்பிட்டவுடன் படுக்கக் கூடாது; குறைந்தது 2 மணி நேரம் கழித்து தூங்கச் செல்லவும்."
            ],
            "hi": [
                "एक साथ ज्यादा खाने के बजाय थोड़ा-थोड़ा करके खाएं।",
                "अधिक मिर्च-मसालेदार, तला हुआ खाना, चाय और कॉफी से परहेज करें।",
                "छाछ, नारियल पानी या जीरे का पानी पिएं।",
                "खाना खाने के तुरंत बाद न लेटें।"
            ],
            "gu": [
                "થોડું થોડું કરીને દિવસમાં ઘણી વાર ખાવું.",
                "તીખો, તળેલો ખોરાક અને ચા-કોફી ટાળો.",
                "છાશ અથવા નાળિયેર પાણી પીવું હિતકારક છે."
            ]
        },
        warning_signs={
            "en": [
                "Severe, rigid, board-like abdominal tenderness (Acute Abdomen - Surgical Emergency!).",
                "Vomiting of blood (hematemesis) or dark coffee-ground material.",
                "Passing black tarry stools (melena) indicating internal bleeding.",
                "Severe pain radiating through to the back or accompanied by high fever and jaundice."
            ],
            "ta": [
                "வயிறு பலகை போல் விரைத்துப்போய் தாங்க முடியாத வலி ஏற்படுதல் (அவசர அறுவை சிகிச்சை தேவைப்படலாம்!).",
                "வாந்தியில் ரத்தம் வருதல் அல்லது கருப்பு நிற மலம் போதல்.",
                "வயிற்று வலியுடன் கடுமையான காய்ச்சல் அல்லது மஞ்சள் காமாலை ஏற்படுதல்."
            ],
            "hi": [
                "पेट का पत्थर जैसा सख्त हो जाना और बहुत तेज दर्द (आपातकालीन स्थिति)।",
                "उल्टी में खून आना या काले रंग का मल आना।",
                "तेज दर्द के साथ तेज बुखार या पीलिया होना।"
            ],
            "gu": [
                "પેટ પથ્થર જેવું કડક થવું અને અસહ્ય દુખાવો.",
                "ઉલટીમાં લોહી પડવું કે કાળો ઝાડો થવો."
            ]
        },
        referral_guidance={
            "en": "Refer promptly to Primary Health Centre (PHC) if pain lasts > 48 hours or if any danger signs appear.",
            "ta": "வலி 48 மணி நேரத்திற்கு மேல் நீடித்தாலோ அல்லது ஆபத்து அறிகுறிகள் தோன்றினாலோ உடனடியாக ஆரம்ப சுகாதார நிலையத்திற்கு செல்லவும்.",
            "hi": "यदि दर्द 2 दिन से अधिक रहे तो तुरंत पीएचसी पर डॉक्टर से जांच करवाएं।",
            "gu": "જો દુખાવો 2 દિવસથી વધુ સમય રહે તો પ્રાથમિક આરોગ્ય કેન્દ્ર પર જાઓ."
        }
    ),

    # 14. Hypertension & Dizziness
    ClinicalProtocol(
        condition_id="hypertension_dizziness",
        category="Cardiovascular / Metabolic",
        english_name="Hypertension and Dizziness / Vertigo",
        tamil_name="உயர் இரத்த அழுத்தம் மற்றும் தலைச்சுற்றல்",
        hindi_name="उच्च रक्तचाप और चक्कर आना",
        gujarati_name="હાઈ બ્લડ પ્રેશર અને ચક્કર",
        keywords=[
            "blood pressure", "high bp", "hypertension", "dizzy", "dizziness", "giddiness", "vertigo", "faint",
            "இரத்த அழுத்தம்", "பிபி", "உயர் ரத்த அழுத்தம்", "மயக்கம்", "தலைச்சுற்றல்", "கிறுகிறுப்பு", "தலை சுற்றல்",
            "हाई बीपी", "ब्लड प्रेशर", "रक्तचाप", "चक्कर", "चक्कर आना", "बेहोशी", "सिर घूमना",
            "હાઈ બીપી", "બ્લડ પ્રેશર", "ચક્કર", "ચક્કર આવવા", "બેભાન થવું"
        ],
        summary={
            "en": "The patient reports dizziness, lightheadedness, or elevated blood pressure symptoms. Priority care involves sitting or lying down immediately to avoid falls, calm breathing, salt restriction, and blood pressure verification.",
            "ta": "நோயாளிக்கு உயர் இரத்த அழுத்தம், தலைச்சுற்றல் அல்லது மயக்கம் போன்ற அறிகுறிகள் உள்ளன. கீழே விழுந்து அடிபடாமல் இருக்க உடனே உட்காரவோ படுக்கவோ வேண்டும்.",
            "hi": "मरीज को चक्कर आने या उच्च रक्तचाप के लक्षण हैं। गिरने से बचने के लिए तुरंत बैठ जाएं या लेट जाएं और बीपी की जांच कराएं।",
            "gu": "દર્દીને ચક્કર આવવા કે બ્લડ પ્રેશર વધવાના લક્ષણો છે. તરત જ બેસી જવું અને આરામ કરવો."
        },
        home_care={
            "en": [
                "Sit or lie down immediately at the onset of dizziness to prevent falls and head injury.",
                "Drink clean water slowly; avoid sudden changes in posture from lying to standing.",
                "Reduce dietary sodium (table salt, pickles, papads, packaged snacks).",
                "Ensure quiet rest away from bright flashing screens and sudden head movements."
            ],
            "ta": [
                "தலைச்சுற்றல் ஏற்பட்டால் கீழே விழுவதைத் தடுக்க உடனடியாக உட்காரவும் அல்லது படுக்கவும்.",
                "திடீரென எழுந்து நிற்பதைத் தவிர்க்கவும்; நிதானமாக எழ வேண்டும்.",
                "உணவில் உப்பின் அளவை வெகுவாகக் குறைக்கவும் (ஊறுகாய், அப்பளம் தவிர்க்கவும்).",
                "அமைதியான சூழலில் ஓய்வெடுக்கவும்."
            ],
            "hi": [
                "चक्कर आते ही तुरंत बैठ या लेट जाएं ताकि गिरने से चोट न लगे।",
                "अचानक उठकर खड़े न हों।",
                "खाने में नमक की मात्रा कम करें (अचार, पापड़ से परहेज करें)।"
            ],
            "gu": [
                "ચક્કર આવે ત્યારે તાત્કાલિક બેસી જાઓ.",
                "અચાનક ઊભા થવાનું ટાળો.",
                "ખોરાકમાં મીઠું ઓછું કરો."
            ]
        },
        warning_signs={
            "en": [
                "Systolic BP >= 180 mmHg or Diastolic BP >= 110 mmHg (Hypertensive Crisis!).",
                "Sudden weakness or numbness on one side of the face, arm, or leg (Stroke Warning!).",
                "Slurred speech, sudden loss of vision, or confusion.",
                "Severe chest pain radiating to left arm or back."
            ],
            "ta": [
                "இரத்த அழுத்தம் 180/110 mmHg ஐ விட அதிகமாக இருத்தல் (அவசர நிலை!).",
                "ஒரு பக்க முகம், கை அல்லது காலில் திடீர் பலவீனம் அல்லது உணர்வின்மை (பக்கவாத அறிகுறி!).",
                "பேசுவதில் குளறுபடி அல்லது பார்வை மங்குதல்."
            ],
            "hi": [
                "बीपी 180/110 से अधिक होना।",
                "चेहरे, हाथ या पैर के एक तरफ अचानक कमजोरी या सुन्नपन (लकवा/स्ट्रोक का संकेत)।",
                "बोलने में लड़खड़ाहट या सीने में तेज दर्द।"
            ],
            "gu": [
                "બ્લડ પ્રેશર 180/110 થી વધુ હોવું.",
                "શરીરના એક ભાગમાં નબળાઈ કે લકવો થવો.",
                "બોલવામાં તકલીફ થવી."
            ]
        },
        referral_guidance={
            "en": "Visit the Primary Health Centre (PHC) for blood pressure check, ECG, and physician review. Emergency 108 transfer if one-sided weakness or chest pain appears.",
            "ta": "இரத்த அழுத்தத்தை அளவிடவும் இசிஜி (ECG) பரிசோதனைக்கும் ஆரம்ப சுகாதார நிலையத்திற்கு செல்லவும்.",
            "hi": "बीपी की जांच और दवा के लिए तुरंत नजदीकी स्वास्थ्य केंद्र जाएं।",
            "gu": "બ્લડ પ્રેશરની તપાસ માટે નજીકના આરોગ્ય કેન્દ્ર પર જાઓ."
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
            kw_low = kw.lower().strip()
            if len(kw_low.split()) == 1 and len(kw_low) <= 4 and kw_low.isascii():
                # Word boundary match for short ASCII words like 'cut', 'burn', 'eye'
                if re.search(rf"\b{re.escape(kw_low)}\b", clean_q):
                    score += 1
            else:
                if kw_low in clean_q:
                    # Give higher weight to multi-word phrases
                    score += len(kw_low.split())

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

