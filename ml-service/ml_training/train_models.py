"""
Train All 4 ML Models
Trains: anomaly_detector, object_detector, danger_predictor, environment_classifier
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def train_all():
    print("\n" + "=" * 70)
    print("TRAINING ALL ML MODELS")
    print("=" * 70 + "\n")

    success_count = 0
    total_models  = 4

    # 1. Anomaly Detection
    try:
        print("\n[1/4] Training Anomaly Detection Model...")
        from ml_training.train_anomaly import train_model as train_anomaly
        train_anomaly()
        success_count += 1
    except Exception as e:
        print(f"❌ Failed to train anomaly model: {e}")

    # 2. Object Detection
    try:
        print("\n[2/4] Training Object Detection Model...")
        from ml_training.train_object_detection import train_model as train_object
        train_object()
        success_count += 1
    except Exception as e:
        print(f"❌ Failed to train object detection model: {e}")

    # 3. Danger Prediction
    try:
        print("\n[3/4] Training Danger Prediction Model...")
        from ml_training.train_danger_prediction import train_model as train_danger
        train_danger()
        success_count += 1
    except Exception as e:
        print(f"❌ Failed to train danger prediction model: {e}")

    # 4. Environment Classification
    try:
        print("\n[4/4] Training Environment Classification Model...")
        from ml_training.train_environment_classifier import train_model as train_env
        train_env()
        success_count += 1
    except Exception as e:
        print(f"❌ Failed to train environment classification model: {e}")

    print("\n" + "=" * 70)
    print(f"✅ Training Complete: {success_count}/{total_models} models trained successfully")
    print("=" * 70 + "\n")

    return success_count == total_models


if __name__ == '__main__':
    success = train_all()
    sys.exit(0 if success else 1)