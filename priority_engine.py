"""
Priority Engine
----------------
Fuses the Gemini analysis, the district hazard profile, and the vision
detections into ONE final priority score (0-10) and priority tier, plus
generates the plain-text official incident report (Phase 5 feature).
"""

from datetime import datetime
from typing import Dict, List


def compute_priority(gemini_result: Dict, hazard_profile: Dict, vision_result: Dict) -> Dict:
    severity = float(gemini_result.get("severity", 5.0))

    # Small additional nudge if vision confirms people in frame with decent confidence
    person_conf = max(
        (d["confidence"] for d in vision_result.get("detections", [])
         if "person" in d["label"].lower()),
        default=0.0,
    )
    vision_boost = round(person_conf * 0.5, 2)

    final_score = round(min(severity + vision_boost, 10.0), 1)

    if final_score >= 8.0:
        tier = "High"
    elif final_score >= 5.0:
        tier = "Medium"
    else:
        tier = "Low"

    return {
        "priority_score": final_score,
        "priority_tier": tier,
    }


def generate_official_report(record: Dict) -> str:
    """Plain-text 'official incident report' the AI drafts for responders (Phase 5)."""
    victims = ", ".join(record.get("people_at_risk", [])) or "Not specified"
    teams = ", ".join(record.get("required_teams", [])) or "Police (default)"
    hazards = ", ".join(record.get("hazard_profile", {}).get("hazards", [])) or "Unknown"

    report = f"""INCIDENT REPORT — AI DISASTER COMMAND CENTER
================================================
Case ID:            {record.get('id')}
Time Reported:       {record.get('timestamp')}
Location:            {record.get('location_text') or 'Not provided'} ({record.get('hazard_profile', {}).get('district', 'Unknown district')}, {record.get('hazard_profile', {}).get('state', 'Unknown state')})
Coordinates:         {record.get('lat')}, {record.get('lng')}

Emergency Type:       {record.get('emergency_type')}
Priority:             {record.get('priority_score')}/10  ({record.get('priority_tier')} priority)
Victims / At Risk:    {victims}
Required Resources:   {teams}
District Hazard Profile: {hazards}

AI Summary:
{record.get('summary')}

Vision Signals ({record.get('vision_engine', 'none')}):
{_format_detections(record.get('detections', []))}
================================================
Generated automatically. Verify before dispatch.
"""
    return report


def _format_detections(detections: List[Dict]) -> str:
    if not detections:
        return "  (no image submitted)"
    return "\n".join(f"  - {d['label']} (confidence {d['confidence']})" for d in detections)
