# AI Disaster Command Center — Working Prototype

A real, runnable Flask prototype implementing the 5-feature plan:
citizen reporting → AI understanding (Gemini) → image analysis (YOLO) →
officials dashboard → auto-generated incident report — plus the
**India Hazard Intelligence Engine** (district-level hazard knowledge
base) as the differentiating feature.

It runs fully offline out of the box (no API keys needed) using
transparent rule-based fallbacks, and upgrades automatically to the
real Gemini / YOLOv8 / Google Maps APIs the moment you add keys.

## 1. Run it locally

```bash
cd project
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000** — that's the "Report Emergency" page.
Open **http://localhost:5000/dashboard** for the officials view.

That's it. No API keys required to see it work end-to-end.

## 2. What's actually happening under the hood

| Feature (from your plan)        | File                        | Behavior without API keys                          | Behavior with API keys |
|----------------------------------|-----------------------------|------------------------------------------------------|--------------------------|
| AI understands the emergency     | `gemini_service.py`         | Rule-based keyword classifier (transparent, tunable)  | Real Gemini call (JSON output) |
| AI detects objects in images      | `yolo_service.py`           | Real pixel/colour-statistics analysis (Pillow) — genuinely reads the image | Real YOLOv8 detections |
| India Hazard Intelligence Engine  | `hazard_knowledge_base.py`  | ~50 districts with known hazard profiles, substring + keyword matching | Same — this part needs no API |
| Priority scoring                  | `priority_engine.py`        | Combines severity + hazard-match + vulnerable-people + vision signals into one 0–10 score | Same |
| Dashboard                         | `templates/dashboard.html` + `static/js/dashboard.js` | Live stats + case table, polls every 8s | Adds a live Google Map with colour-coded pins |
| Official report generator         | `priority_engine.py` → `/api/report/<id>/document` | Plain-text incident report, generated on demand | Same |
| Data storage                      | `data_store.py`             | JSON file at `data/db.json` | Swap this file's internals for Firestore — see comments inside |

## 3. Turning on the real APIs

Create a `.env` file (or export as environment variables) in `project/`:

```bash
GEMINI_API_KEY=your_key_here
GOOGLE_MAPS_API_KEY=your_key_here
YOLO_WEIGHTS_PATH=yolov8n.pt     # or your own fine-tuned weights
```

Then install the optional packages:

```bash
pip install google-generativeai ultralytics
```

Restart `python app.py` — the console will tell you which engines are
active (look for `[gemini_service]` / `[yolo_service]` log lines only
appear when falling back, so silence = the real APIs are being used).

## 4. Growing the Hazard Knowledge Base

Open `hazard_knowledge_base.py` and add rows to `DISTRICT_HAZARDS`:

```python
"your_district": {"state": "Your State", "hazards": ["Flood", "Cyclone"]},
```

Lookup is case-insensitive substring matching against whatever the
citizen types in the "Location" field, so partial names still resolve.

## 5. Deploying (get your judge-facing live link)

**Option A — Render.com (easiest, free tier):**
1. Push this folder to a GitHub repo.
2. On Render: New → Web Service → connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app` (add `gunicorn` to requirements.txt first)
5. Add your env vars in the Render dashboard.

**Option B — Google Cloud Run:**
```bash
gcloud run deploy ai-disaster-command-center \
  --source . \
  --set-env-vars GEMINI_API_KEY=...,GOOGLE_MAPS_API_KEY=...
```

Either way you'll get a public URL like the `https://aidisaster.web.app`
example — that's what you drop into the "Working Prototype Link" field.

## 6. Folder structure

```
project/
  app.py                    # Flask routes / API
  hazard_knowledge_base.py  # India district hazard profiles + lookup
  gemini_service.py         # AI analysis (real Gemini or rule-based)
  yolo_service.py           # Vision (real YOLOv8 or pixel heuristic)
  priority_engine.py        # Final scoring + official report text
  data_store.py             # JSON file "database" (swap for Firestore)
  requirements.txt
  templates/
    report.html
    dashboard.html
  static/
    css/style.css
    js/report.js
    js/dashboard.js
  uploads/                  # citizen-submitted photos land here
  data/db.json              # all case records
```

## 7. Known limitations (be upfront with judges about these)

- The rule-based / pixel-heuristic fallbacks are intentionally simple —
  they're there so the demo always works, not as a claim of production
  accuracy. Say so if asked; it's a strength ("we designed for graceful
  degradation"), not a weakness.
- `data/db.json` is fine for a hackathon demo; it is **not** concurrent-safe
  at real scale — that's exactly what the Firestore swap in
  `data_store.py` is for.
- The Hazard Knowledge Base currently covers ~50 districts as a proof of
  concept, not all ~766 districts in India.
