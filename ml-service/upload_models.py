"""
Run this script LOCALLY after training your models.
It uploads all .pkl files + 'yolov5s.onnx' to Supabase Storage.
Hugging Face will download them automatically on startup.

Usage:
    cd ml-service
    python upload_models.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Point to your server's saved_models folder
SERVER_MODELS_DIR = os.path.join(
    os.path.dirname(__file__), 'ml_models', 'saved_models'
)

# Also check local saved_models
LOCAL_MODELS_DIR = os.path.join(
    os.path.dirname(__file__), 'ml_models', 'saved_models'
)

FILES_TO_UPLOAD = [
    'anomaly_detector.pkl',
    'danger_predictor.pkl',
    'environment_classifier.pkl',
    'object_detector.pkl',
    'yolov5s.onnx',
]


def find_file(filename):
    """Look for file in local dir first, then server dir."""
    for directory in [LOCAL_MODELS_DIR, SERVER_MODELS_DIR]:
        path = os.path.join(directory, filename)
        if os.path.exists(path):
            return path
    return None


def upload_all():
    from supabase import create_client

    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')

    if not url or not key:
        print("ERROR: Set SUPABASE_URL and SUPABASE_KEY in .env first")
        sys.exit(1)

    supabase = create_client(url, key)
    bucket   = 'ml-models'

    print(f"\nUploading models to Supabase Storage bucket: {bucket}\n")

    uploaded = 0
    skipped  = 0
    failed   = 0

    for filename in FILES_TO_UPLOAD:
        local_path = find_file(filename)

        if not local_path:
            print(f"   NOT FOUND: {filename} - train your models first")
            skipped += 1
            continue

        size_kb = os.path.getsize(local_path) / 1024
        print(f"   Uploading {filename} ({size_kb:.1f}KB) ...")

        try:
            with open(local_path, 'rb') as f:
                data = f.read()

            try:
                supabase.storage.from_(bucket).update(
                    filename, data, {'content-type': 'application/octet-stream'}
                )
            except Exception:
                supabase.storage.from_(bucket).upload(
                    filename, data, {'content-type': 'application/octet-stream'}
                )

            print(f"   Done: {filename}")
            uploaded += 1

        except Exception as e:
            print(f"   FAILED: {filename} - {e}")
            failed += 1

    print(f"\nResults: {uploaded} uploaded, {skipped} skipped, {failed} failed")

    if uploaded > 0:
        print("\nNext steps:")
        print("  1. Push ml-service/ to your Hugging Face Space repo")
        print("  2. Models will download automatically on startup")
        print("  3. Update ML_URL in your Pi .env:")
        print("     ML_URL=https://your-username-assistive-device-ml.hf.space")


if __name__ == '__main__':
    upload_all()