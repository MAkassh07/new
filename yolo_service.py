"""
Vision Detection Service
-------------------------
Tries real YOLOv8 (via ultralytics) first. If that package/model isn't
available in the current environment, falls back to a lightweight,
genuinely-computed pixel/colour-distribution heuristic (using Pillow) so
the pipeline still returns real, image-derived signals instead of
hardcoded fake data — clearly labelled as a fallback in the response.

Swap in your trained disaster-specific YOLOv8 weights by setting
YOLO_WEIGHTS_PATH below once you have them.
"""

import os
from typing import List, Dict

YOLO_WEIGHTS_PATH = os.environ.get("YOLO_WEIGHTS_PATH", "yolov8n.pt")

_yolo_model = None
_yolo_available = False

try:
    from ultralytics import YOLO
    _yolo_model = YOLO(YOLO_WEIGHTS_PATH)
    _yolo_available = True
except Exception as e:
    print(f"[yolo_service] ultralytics/YOLO not available, using pixel-heuristic fallback: {e}")
    _yolo_available = False


def _run_yolo(image_path: str) -> List[Dict]:
    results = _yolo_model(image_path, verbose=False)
    detections = []
    for r in results:
        names = r.names
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            detections.append({"label": names.get(cls_id, str(cls_id)), "confidence": round(conf, 2)})
    return detections


def _run_pixel_heuristic(image_path: str) -> List[Dict]:
    """
    A real (not fake) but simple analysis of the image's colour makeup,
    used only when YOLOv8 isn't installed. It actually opens and reads
    the pixels — it just uses colour statistics instead of a trained
    object detector, so treat these as low-confidence hints, not
    verified detections.
    """
    from PIL import Image
    import numpy as np

    detections = []
    try:
        img = Image.open(image_path).convert("RGB").resize((160, 160))
        arr = np.asarray(img).astype(float) / 255.0
        r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]

        blue_ratio = float(((b > r) & (b > g)).mean())
        if blue_ratio > 0.18:
            detections.append({"label": "Water (heuristic)", "confidence": round(min(blue_ratio * 1.5, 0.95), 2)})

        red_orange_ratio = float(((r > 0.5) & (r > g * 1.3) & (r > b * 1.3)).mean())
        if red_orange_ratio > 0.05:
            detections.append({"label": "Fire/Smoke (heuristic)", "confidence": round(min(red_orange_ratio * 3, 0.9), 2)})

        dark_ratio = float(((r + g + b) / 3 < 0.25).mean())
        if dark_ratio > 0.35:
            detections.append({"label": "Debris/Low-light scene (heuristic)", "confidence": round(min(dark_ratio, 0.85), 2)})

        if not detections:
            detections.append({"label": "No strong visual signal (heuristic)", "confidence": 0.3})

    except Exception as e:
        detections.append({"label": f"Image could not be analyzed: {e}", "confidence": 0.0})

    return detections


def detect_objects(image_path: str) -> Dict:
    """
    Returns: {
        "engine": "yolov8" | "pixel_heuristic",
        "detections": [{"label": str, "confidence": float}, ...]
    }
    """
    if not image_path or not os.path.exists(image_path):
        return {"engine": "none", "detections": []}

    if _yolo_available:
        try:
            return {"engine": "yolov8", "detections": _run_yolo(image_path)}
        except Exception as e:
            print(f"[yolo_service] YOLO inference failed, falling back: {e}")

    return {"engine": "pixel_heuristic", "detections": _run_pixel_heuristic(image_path)}
