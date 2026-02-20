"""
Model Loader
Downloads all model files from Supabase Storage on startup.
"""

import os
import joblib

MODELS_DIR  = os.path.join(os.path.dirname(__file__), 'saved_models')
BUCKET_NAME = 'ml-models'

MODEL_FILES = [
    'anomaly_detector.pkl',
    'danger_predictor.pkl',
    'environment_classifier.pkl',
    'object_detector.pkl',
    'yolov5n.onnx',
]


def _get_supabase():
    from app.services.supabase_client import get_supabase
    return get_supabase()


def download_all_models():
    """Download all models from Supabase Storage on startup."""
    os.makedirs(MODELS_DIR, exist_ok=True)

    print("\n🔍 Checking ML models...")

    try:
        supabase = _get_supabase()
    except Exception as e:
        print(f"Cannot connect to Supabase: {e}")
        print("ML endpoints will use rule-based fallback logic\n")
        return

    for filename in MODEL_FILES:
        local_path = os.path.join(MODELS_DIR, filename)

        if os.path.exists(local_path):
            size_kb = os.path.getsize(local_path) / 1024
            print(f"   Already cached: {filename} ({size_kb:.1f}KB)")
            continue

        try:
            print(f"   Downloading {filename} ...")
            data = supabase.storage.from_(BUCKET_NAME).download(filename)
            with open(local_path, 'wb') as f:
                f.write(data)
            print(f"   Done: {filename} ({len(data) / 1024:.1f}KB)")
        except Exception as e:
            print(f"   Not found in Supabase: {filename} - will use fallback")

    print("Model check complete\n")


def load_model(name):
    """Load a .pkl model. Returns None if not found."""
    path = os.path.join(MODELS_DIR, f"{name}.pkl")
    if not os.path.exists(path):
        return None
    try:
        return joblib.load(path)
    except Exception as e:
        print(f"Failed to load {name}: {e}")
        return None


def get_yolo_model_path():
    """Return path to yolov5n.onnx or None if not downloaded."""
    path = os.path.join(MODELS_DIR, 'yolov5n.onnx')
    return path if os.path.exists(path) else None


def upload_model(local_path, filename):
    """Upload a trained model to Supabase Storage. Run locally only."""
    supabase = _get_supabase()
    with open(local_path, 'rb') as f:
        data = f.read()
    try:
        supabase.storage.from_(BUCKET_NAME).update(
            filename, data, {'content-type': 'application/octet-stream'}
        )
        print(f"Updated {filename} in Supabase Storage")
    except Exception:
        supabase.storage.from_(BUCKET_NAME).upload(
            filename, data, {'content-type': 'application/octet-stream'}
        )
        print(f"Uploaded {filename} to Supabase Storage")