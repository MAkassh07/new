"""
AI Disaster Command Center — Flask Backend
--------------------------------------------
Run locally:
    pip install -r requirements.txt
    python app.py
Then open http://localhost:5000

Optional environment variables (create a .env file or export these):
    GEMINI_API_KEY         -> enables real Gemini analysis (else rule-based fallback)
    YOLO_WEIGHTS_PATH      -> path to a YOLOv8 .pt file (else pixel-heuristic fallback)
    GOOGLE_MAPS_API_KEY    -> enables the live map on the dashboard
"""

import os
import uuid
from flask import Flask, request, jsonify, render_template, send_from_directory

from hazard_knowledge_base import get_hazard_profile
from gemini_service import analyze_report
from yolo_service import detect_objects
from priority_engine import compute_priority, generate_official_report
import data_store

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB upload limit


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# Frontend pages
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("report.html", maps_key=os.environ.get("GOOGLE_MAPS_API_KEY", ""))


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", maps_key=os.environ.get("GOOGLE_MAPS_API_KEY", ""))


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# ---------------------------------------------------------------------------
# API: submit a citizen report
# ---------------------------------------------------------------------------

@app.route("/api/report", methods=["POST"])
def submit_report():
    text = request.form.get("description", "").strip()
    location_text = request.form.get("location", "").strip()
    lat = request.form.get("lat")
    lng = request.form.get("lng")

    if not text and "image" not in request.files:
        return jsonify({"error": "Please provide a description or an image."}), 400

    # 1) Save uploaded image (if any)
    image_path = None
    image_url = None
    file = request.files.get("image")
    if file and file.filename and _allowed_file(file.filename):
        ext = file.filename.rsplit(".", 1)[1].lower()
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        image_path = os.path.join(UPLOAD_DIR, safe_name)
        file.save(image_path)
        image_url = f"/uploads/{safe_name}"

    # 2) Vision pipeline
    vision_result = detect_objects(image_path) if image_path else {"engine": "none", "detections": []}
    detected_labels = [d["label"] for d in vision_result["detections"]]

    # 3) District hazard profile (India Hazard Intelligence Engine)
    hazard_profile = get_hazard_profile(location_text)

    # 4) Gemini (or rule-based fallback) analysis, informed by hazard context + vision
    analysis = analyze_report(text, hazard_profile, detected_labels)

    # 5) Final priority score
    priority = compute_priority(analysis, hazard_profile, vision_result)

    # 6) Persist the case
    record = data_store.add_case({
        "description": text,
        "location_text": location_text,
        "lat": float(lat) if lat else None,
        "lng": float(lng) if lng else None,
        "image_url": image_url,
        "hazard_profile": hazard_profile,
        "emergency_type": analysis.get("emergency_type"),
        "people_at_risk": analysis.get("people_at_risk", []),
        "required_teams": analysis.get("required_teams", []),
        "summary": analysis.get("summary"),
        "analysis_source": analysis.get("source"),
        "vision_engine": vision_result.get("engine"),
        "detections": vision_result.get("detections", []),
        "priority_score": priority["priority_score"],
        "priority_tier": priority["priority_tier"],
    })

    return jsonify({
        "id": record["id"],
        "emergency_type": record["emergency_type"],
        "severity": record["priority_score"],
        "priority_score": record["priority_score"],
        "priority_tier": record["priority_tier"],
        "people_at_risk": record["people_at_risk"],
        "required_teams": record["required_teams"],
        "summary": record["summary"],
        "hazard_profile": record["hazard_profile"],
        "detections": record["detections"],
        "analysis_source": record["analysis_source"],
    }), 201


# ---------------------------------------------------------------------------
# API: dashboard data
# ---------------------------------------------------------------------------

@app.route("/api/dashboard")
def api_dashboard():
    stats = data_store.get_dashboard_stats()
    cases = sorted(data_store.get_all_cases(), key=lambda c: c["timestamp"], reverse=True)
    return jsonify({"stats": stats, "cases": cases})


@app.route("/api/report/<int:case_id>/document")
def api_official_report(case_id):
    record = data_store.get_case(case_id)
    if not record:
        return jsonify({"error": "Case not found"}), 404
    return generate_official_report(record), 200, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
