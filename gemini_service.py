"""
Gemini Analysis Service
------------------------
Turns a raw citizen report (text + hazard context + detected objects)
into a structured emergency assessment:

    {
        "emergency_type": "Flood",
        "severity": 8.5,               # 0-10
        "people_at_risk": ["Elderly"],
        "required_teams": ["Fire & Rescue", "Ambulance"],
        "summary": "..."
    }

If a GEMINI_API_KEY environment variable is set AND the google-generativeai
package is installed, this calls the real Gemini API. Otherwise it falls
back to a transparent rule-based analyzer so the whole prototype still
runs end-to-end offline / without any API key (useful for local dev and
for judges who don't have your key).
"""

import os
import json
import re
from typing import Dict, List, Optional

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
_gemini_model = None

if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:  # library missing or bad key — degrade gracefully
        print(f"[gemini_service] Gemini unavailable, using rule-based fallback: {e}")
        _gemini_model = None


# ---------------------------------------------------------------------------
# Rule-based fallback (also doubles as a readable spec for the Gemini prompt)
# ---------------------------------------------------------------------------

EMERGENCY_KEYWORDS = {
    "Flood":               (["flood", "water entered", "water rising", "submerged", "waterlogged"], 6.5),
    "Fire":                (["fire", "smoke", "burning", "blaze"], 7.0),
    "Explosion":           (["explosion", "blast", "cracker", "chemical leak"], 8.5),
    "Earthquake":          (["earthquake", "tremor", "shaking", "quake"], 8.0),
    "Landslide":           (["landslide", "mudslide", "hillside collapse", "debris flow"], 7.5),
    "Building Collapse":   (["building collapsed", "wall collapsed", "structure collapse", "roof fell"], 8.0),
    "Medical Emergency":   (["injured", "bleeding", "unconscious", "heart attack", "not breathing", "labour pain", "pregnant"], 7.0),
    "Cyclone":             (["cyclone", "storm surge", "high winds", "hurricane"], 7.5),
    "Road Accident":       (["accident", "crash", "collision", "overturned vehicle"], 6.0),
    "Drowning":            (["drowning", "swept away", "river current"], 8.5),
}

VULNERABLE_KEYWORDS = {
    "Elderly": ["grandmother", "grandfather", "elderly", "old age", "senior citizen"],
    "Children": ["child", "children", "kid", "baby", "infant", "toddler"],
    "Pregnant Woman": ["pregnant", "labour", "labor pain"],
    "Disabled Person": ["disabled", "wheelchair", "handicapped"],
}

SEVERITY_BOOST_KEYWORDS = ["trapped", "stuck", "can't move", "cannot move", "no help", "urgent", "dying", "critical"]

TEAM_MAP = {
    "Flood": ["Fire & Rescue", "NDRF Boat Unit"],
    "Fire": ["Fire & Rescue"],
    "Explosion": ["Fire & Rescue", "Bomb Disposal", "Ambulance"],
    "Earthquake": ["NDRF", "Fire & Rescue", "Ambulance"],
    "Landslide": ["NDRF", "Fire & Rescue"],
    "Building Collapse": ["NDRF", "Fire & Rescue", "Ambulance"],
    "Medical Emergency": ["Ambulance"],
    "Cyclone": ["NDRF", "Fire & Rescue"],
    "Road Accident": ["Ambulance", "Police"],
    "Drowning": ["Fire & Rescue", "Ambulance"],
}


def _detect_emergency_type(text: str) -> (str, float):
    text_l = text.lower()
    best_type, best_score, best_hits = "Unclassified Emergency", 5.0, 0
    for etype, (keywords, base_severity) in EMERGENCY_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text_l)
        if hits > best_hits:
            best_type, best_score, best_hits = etype, base_severity, hits
    return best_type, best_score


def _detect_vulnerable_people(text: str) -> List[str]:
    text_l = text.lower()
    found = []
    for group, keywords in VULNERABLE_KEYWORDS.items():
        if any(kw in text_l for kw in keywords):
            found.append(group)
    return found


def rule_based_analysis(text: str, hazard_profile: Dict, detected_objects: List[str]) -> Dict:
    text = text or ""
    emergency_type, severity = _detect_emergency_type(text)

    # Boost severity if urgency language is present
    if any(kw in text.lower() for kw in SEVERITY_BOOST_KEYWORDS):
        severity += 1.0

    # Boost if vision pipeline detected people in the frame
    if detected_objects and any("person" in o.lower() for o in detected_objects):
        severity += 0.5

    # Boost if this matches the district's known hazard profile (context-aware AI)
    from hazard_knowledge_base import hazard_is_expected
    if hazard_is_expected(emergency_type, hazard_profile):
        severity += 1.0

    people_at_risk = _detect_vulnerable_people(text)
    if people_at_risk:
        severity += 0.5

    severity = round(min(severity, 10.0), 1)
    required_teams = TEAM_MAP.get(emergency_type, ["Police"])

    location_bit = f" in {hazard_profile['district']}" if hazard_profile.get("district") else ""
    people_bit = f" Vulnerable individuals reported: {', '.join(people_at_risk)}." if people_at_risk else ""
    summary = (
        f"{emergency_type} reported{location_bit}. "
        f"Citizen message: \"{text.strip()}\"{people_bit}"
    ).strip()

    return {
        "emergency_type": emergency_type,
        "severity": severity,
        "people_at_risk": people_at_risk,
        "required_teams": required_teams,
        "summary": summary,
        "source": "rule_based_fallback",
    }


# ---------------------------------------------------------------------------
# Real Gemini call
# ---------------------------------------------------------------------------

PROMPT_TEMPLATE = """You are the triage AI inside an emergency disaster command center in India.
Analyze the citizen report below and reason using the local hazard context provided.
Respond with ONLY a valid JSON object, no markdown, no extra text, with exactly these keys:
emergency_type (string), severity (number 0-10), people_at_risk (array of strings),
required_teams (array of strings, choose from: "Fire & Rescue", "Ambulance", "Police",
"NDRF", "NDRF Boat Unit", "Bomb Disposal"), summary (a short factual incident summary).

District: {district}
State: {state}
Known local hazards for this district: {hazards}
Objects detected in uploaded image (if any): {objects}

Citizen report text:
\"\"\"{text}\"\"\"
"""


def analyze_report(text: str, hazard_profile: Dict, detected_objects: Optional[List[str]] = None) -> Dict:
    detected_objects = detected_objects or []

    if _gemini_model is not None:
        prompt = PROMPT_TEMPLATE.format(
            district=hazard_profile.get("district") or "Unknown",
            state=hazard_profile.get("state") or "Unknown",
            hazards=", ".join(hazard_profile.get("hazards", [])) or "None on file",
            objects=", ".join(detected_objects) or "None",
            text=text or "",
        )
        try:
            response = _gemini_model.generate_content(prompt)
            raw = response.text.strip()
            raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()
            data = json.loads(raw)
            data.setdefault("people_at_risk", [])
            data.setdefault("required_teams", ["Police"])
            data["severity"] = round(float(data.get("severity", 5.0)), 1)
            data["source"] = "gemini"
            return data
        except Exception as e:
            print(f"[gemini_service] Gemini call failed, using fallback: {e}")

    return rule_based_analysis(text, hazard_profile, detected_objects)
