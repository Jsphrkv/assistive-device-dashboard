import os
import joblib
from pathlib import Path

MODELS_DIR = Path(__file__).parent / 'saved_models'

def load_model(name):
    """Load a sklearn model bundle from local saved_models/."""
    path = MODELS_DIR / f'{name}.pkl'
    if path.exists():
        try:
            return joblib.load(path)
        except Exception as e:
            print(f"[ModelLoader] Failed to load {name}: {e}")
    return None  # triggers rule-based fallback in ml_service.py

def get_yolo_model_path():
    """Return YOLO onnx path if it exists."""
    path = MODELS_DIR / 'yolov5s.onnx'
    return str(path) if path.exists() else None