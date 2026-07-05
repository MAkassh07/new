"""
India Hazard Intelligence Knowledge Base
-----------------------------------------
Maps districts/cities across India to their known disaster profile
(the hazards that are actually likely to occur there), based on the
general public hazard categories published by NDMA / IMD / NRSC-ISRO.

This is a STARTER dataset for the hackathon prototype — not exhaustive.
Add more rows to DISTRICT_HAZARDS to grow coverage. The lookup function
does case-insensitive substring matching, so "sivakasi", "Sivakasi",
"near sivakasi" all resolve to the same profile.
"""

from typing import Dict, List, Optional

# district / city (lowercase key) -> (state, [hazards])
DISTRICT_HAZARDS: Dict[str, Dict] = {
    # Tamil Nadu
    "chennai":      {"state": "Tamil Nadu", "hazards": ["Urban Flood", "Cyclone", "Storm Surge", "Heavy Rain"]},
    "cuddalore":    {"state": "Tamil Nadu", "hazards": ["Cyclone", "Tsunami", "Coastal Flood"]},
    "nagapattinam": {"state": "Tamil Nadu", "hazards": ["Cyclone", "Tsunami", "Coastal Flood"]},
    "nilgiris":     {"state": "Tamil Nadu", "hazards": ["Landslide", "Heavy Rain", "Road Blockage"]},
    "ooty":         {"state": "Tamil Nadu", "hazards": ["Landslide", "Cloudburst", "Heavy Rain", "Road Blockage", "Tourist Stranding"]},
    "kodaikanal":   {"state": "Tamil Nadu", "hazards": ["Landslide", "Cloudburst", "Heavy Rain", "Road Blockage", "Tourist Stranding"]},
    "dindigul":     {"state": "Tamil Nadu", "hazards": ["Landslide", "Heavy Rain"]},
    "theni":        {"state": "Tamil Nadu", "hazards": ["Landslide", "Flash Flood", "Heavy Rain"]},
    "coimbatore":   {"state": "Tamil Nadu", "hazards": ["Heavy Rain", "Drought (fringe areas)"]},
    "madurai":      {"state": "Tamil Nadu", "hazards": ["Heavy Rain", "Heatwave"]},
    "virudhunagar": {"state": "Tamil Nadu", "hazards": ["Fireworks Industrial Fire", "Chemical Explosion"]},
    "sivakasi":     {"state": "Tamil Nadu", "hazards": ["Fireworks Industrial Fire", "Chemical Explosion"]},
    "thanjavur":    {"state": "Tamil Nadu", "hazards": ["Flood", "Heavy Rain"]},
    "tiruvallur":   {"state": "Tamil Nadu", "hazards": ["Urban Flood", "Cyclone"]},
    "kanyakumari":  {"state": "Tamil Nadu", "hazards": ["Cyclone", "Tsunami", "Coastal Flood"]},

    # Kerala
    "wayanad":      {"state": "Kerala", "hazards": ["Landslide", "Heavy Rain"]},
    "idukki":       {"state": "Kerala", "hazards": ["Landslide", "Dam Overflow", "Heavy Rain"]},
    "ernakulam":    {"state": "Kerala", "hazards": ["Urban Flood", "Heavy Rain"]},
    "kochi":        {"state": "Kerala", "hazards": ["Urban Flood", "Cyclone", "Coastal Flood"]},

    # Himachal Pradesh
    "kullu":        {"state": "Himachal Pradesh", "hazards": ["Landslide", "Avalanche", "Flash Flood"]},
    "shimla":       {"state": "Himachal Pradesh", "hazards": ["Landslide", "Cloudburst", "Snowfall", "Road Collapse"]},
    "manali":       {"state": "Himachal Pradesh", "hazards": ["Landslide", "Avalanche", "Flash Flood", "Tourist Stranding"]},

    # Uttarakhand
    "chamoli":      {"state": "Uttarakhand", "hazards": ["Avalanche", "Cloudburst", "Flash Flood", "Landslide"]},
    "uttarkashi":   {"state": "Uttarakhand", "hazards": ["Landslide", "Cloudburst", "Flash Flood"]},
    "dehradun":     {"state": "Uttarakhand", "hazards": ["Flash Flood", "Landslide"]},

    # Assam / Northeast
    "dibrugarh":    {"state": "Assam", "hazards": ["Flood", "Riverbank Erosion"]},
    "guwahati":     {"state": "Assam", "hazards": ["Flood", "Earthquake"]},

    # Bihar
    "darbhanga":    {"state": "Bihar", "hazards": ["Flood"]},
    "patna":        {"state": "Bihar", "hazards": ["Flood", "Heatwave"]},

    # Odisha
    "puri":         {"state": "Odisha", "hazards": ["Cyclone", "Storm Surge", "Coastal Flood"]},
    "bhubaneswar":  {"state": "Odisha", "hazards": ["Cyclone", "Heavy Rain"]},

    # Gujarat
    "kutch":        {"state": "Gujarat", "hazards": ["Earthquake", "Cyclone", "Drought"]},
    "ahmedabad":    {"state": "Gujarat", "hazards": ["Heatwave", "Urban Flood"]},
    "surat":        {"state": "Gujarat", "hazards": ["Urban Flood", "Cyclone"]},

    # Rajasthan
    "jaisalmer":    {"state": "Rajasthan", "hazards": ["Heatwave", "Drought", "Dust Storm"]},
    "jodhpur":      {"state": "Rajasthan", "hazards": ["Heatwave", "Drought"]},

    # Maharashtra
    "mumbai":       {"state": "Maharashtra", "hazards": ["Urban Flood", "Cyclone", "Building Collapse"]},
    "pune":         {"state": "Maharashtra", "hazards": ["Urban Flood", "Landslide (Ghat sections)"]},

    # Karnataka
    "bengaluru":    {"state": "Karnataka", "hazards": ["Urban Flood", "Lake Overflow"]},
    "kodagu":       {"state": "Karnataka", "hazards": ["Landslide", "Heavy Rain", "Flash Flood"]},

    # Telangana / AP
    "hyderabad":    {"state": "Telangana", "hazards": ["Urban Flood", "Heatwave"]},
    "vizag":        {"state": "Andhra Pradesh", "hazards": ["Cyclone", "Storm Surge", "Industrial Accident"]},
    "visakhapatnam":{"state": "Andhra Pradesh", "hazards": ["Cyclone", "Storm Surge", "Industrial Accident"]},

    # West Bengal
    "kolkata":      {"state": "West Bengal", "hazards": ["Urban Flood", "Cyclone", "Storm Surge"]},
    "sundarbans":   {"state": "West Bengal", "hazards": ["Cyclone", "Storm Surge", "Coastal Erosion"]},

    # Delhi / NCR
    "delhi":        {"state": "Delhi", "hazards": ["Heatwave", "Air Pollution", "Building Fire", "Urban Flood"]},
    "gurugram":     {"state": "Haryana", "hazards": ["Urban Flood", "Air Pollution"]},
    "noida":        {"state": "Uttar Pradesh", "hazards": ["Urban Flood", "Air Pollution", "Building Collapse"]},

    # J&K / Ladakh
    "srinagar":     {"state": "Jammu & Kashmir", "hazards": ["Flood", "Snowfall", "Earthquake"]},
    "leh":          {"state": "Ladakh", "hazards": ["Flash Flood", "Avalanche", "Extreme Cold"]},
}

# Fallback hazards keyed by generic terrain/region keyword, used when the
# exact district isn't in the table but the user's text mentions a type of area.
KEYWORD_FALLBACKS: Dict[str, List[str]] = {
    "coastal": ["Cyclone", "Storm Surge", "Coastal Flood", "Tsunami"],
    "hill": ["Landslide", "Cloudburst", "Road Blockage"],
    "hilly": ["Landslide", "Cloudburst", "Road Blockage"],
    "desert": ["Heatwave", "Drought", "Dust Storm"],
    "industrial": ["Chemical Accident", "Industrial Fire", "Explosion"],
    "urban": ["Urban Flood", "Building Fire", "Air Pollution"],
    "himalaya": ["Avalanche", "Landslide", "Cloudburst", "Earthquake"],
}

DEFAULT_PROFILE = {"state": "Unknown", "hazards": ["Flood", "Fire", "Medical Emergency"]}


def get_hazard_profile(location_text: Optional[str]) -> Dict:
    """
    Look up the disaster profile for a free-text location string.
    Returns {"district": str, "state": str, "hazards": [str, ...], "matched": bool}
    """
    if not location_text:
        return {"district": None, **DEFAULT_PROFILE, "matched": False}

    text = location_text.strip().lower()

    # 1) Exact / substring match against known districts (longest key first
    #    so "greater chennai" doesn't accidentally match a shorter unrelated key)
    for key in sorted(DISTRICT_HAZARDS.keys(), key=len, reverse=True):
        if key in text:
            profile = DISTRICT_HAZARDS[key]
            return {
                "district": key.title(),
                "state": profile["state"],
                "hazards": profile["hazards"],
                "matched": True,
            }

    # 2) Fallback on generic terrain keywords mentioned in the location text
    for keyword, hazards in KEYWORD_FALLBACKS.items():
        if keyword in text:
            return {
                "district": location_text.title(),
                "state": "Unknown",
                "hazards": hazards,
                "matched": True,
            }

    # 3) Nothing matched — return a generic default so the pipeline never breaks
    return {"district": location_text.title(), **DEFAULT_PROFILE, "matched": False}


def hazard_is_expected(emergency_type: str, hazard_profile: Dict) -> bool:
    """True if the reported emergency type is one of the district's known hazards."""
    if not emergency_type:
        return False
    et = emergency_type.lower()
    return any(et in h.lower() or h.lower() in et for h in hazard_profile.get("hazards", []))
