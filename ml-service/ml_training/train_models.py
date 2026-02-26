"""
Train All 4 ML Models
Trains: anomaly_detector, object_detector, danger_predictor, environment_classifier

Usage:
    cd ml-service
    python ml_training/train_all.py

After training, copy .pkl files to your HF repo:
    cp ml_models/saved_models/*.pkl ../capstone2_proj/ml_models/saved_models/
    cp ml_models/saved_models/yolov5s.onnx ../capstone2_proj/ml_models/saved_models/

Then push to HF:
    cd ../capstone2_proj
    git add ml_models/saved_models/
    git commit -m "Update trained models"
    git push
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def train_all():
    print("\n" + "=" * 70)
    print("TRAINING ALL ML MODELS (v2)")
    print("Each model tries real Supabase data first, falls back to synthetic")
    print("=" * 70 + "\n")

    results       = {}
    total_models  = 4
    start_total   = time.time()

    # 1. Anomaly Detection
    try:
        print("\n[1/4] Training Anomaly Detection Model...")
        t = time.time()
        from ml_training.train_anomaly import train_model as train_anomaly
        train_anomaly()
        results['anomaly_detector'] = f"✅ ({time.time()-t:.1f}s)"
    except Exception as e:
        results['anomaly_detector'] = f"❌ {e}"
        print(f"❌ Failed: {e}")

    # 2. Object Detection
    try:
        print("\n[2/4] Training Object Detection Model...")
        t = time.time()
        from ml_training.train_object_detection import train_model as train_object
        train_object()
        results['object_detector'] = f"✅ ({time.time()-t:.1f}s)"
    except Exception as e:
        results['object_detector'] = f"❌ {e}"
        print(f"❌ Failed: {e}")

    # 3. Danger Prediction
    try:
        print("\n[3/4] Training Danger Prediction Model...")
        t = time.time()
        from ml_training.train_danger_prediction import train_model as train_danger
        train_danger()
        results['danger_predictor'] = f"✅ ({time.time()-t:.1f}s)"
    except Exception as e:
        results['danger_predictor'] = f"❌ {e}"
        print(f"❌ Failed: {e}")

    # 4. Environment Classification
    try:
        print("\n[4/4] Training Environment Classification Model...")
        t = time.time()
        from ml_training.train_environment_classifier import train_model as train_env
        train_env()
        results['environment_classifier'] = f"✅ ({time.time()-t:.1f}s)"
    except Exception as e:
        results['environment_classifier'] = f"❌ {e}"
        print(f"❌ Failed: {e}")

    # Summary
    total_time    = time.time() - start_total
    success_count = sum(1 for v in results.values() if v.startswith("✅"))

    print("\n" + "=" * 70)
    print(f"TRAINING COMPLETE — {success_count}/{total_models} models trained ({total_time:.1f}s total)")
    print("=" * 70)
    for model, result in results.items():
        print(f"  {result}  {model}.pkl")

    if success_count == total_models:
        print("\n📦 Next steps:")
        print("  1. Copy models to your HF repo:")
        print("     cp ml_models/saved_models/*.pkl ../capstone2_proj/ml_models/saved_models/")
        print("  2. Push to HF:")
        print("     cd ../capstone2_proj && git add ml_models/saved_models/ && git commit -m 'Update models' && git push")
        print("\n  ✅ HF Space will auto-restart and load new models")
    else:
        print("\n⚠️  Some models failed — check errors above before deploying")

    return success_count == total_models


if __name__ == '__main__':
    success = train_all()
    sys.exit(0 if success else 1)