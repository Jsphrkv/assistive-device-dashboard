"""
Train All 5 ML Models
Trains: anomaly, maintenance, object_detection, danger_prediction, environment_classification
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def train_all():
    """Train all 5 models"""
    print("\n" + "=" * 70)
    print("TRAINING ALL ML MODELS")
    print("=" * 70 + "\n")
    
    success_count = 0
    total_models = 5
    
    # 1. Train Anomaly Detection
    try:
        print("\n[1/5] Training Anomaly Detection Model...")
        from .train_anomaly import train_model as train_anomaly
        train_anomaly()
        success_count += 1
    except Exception as e:
        print(f"❌ Failed to train anomaly model: {e}")
    
    # 2. Train Maintenance Prediction
    try:
        print("\n[2/5] Training Maintenance Prediction Model...")
        from .train_maintenance import train_model as train_maintenance
        train_maintenance()
        success_count += 1
    except Exception as e:
        print(f"❌ Failed to train maintenance model: {e}")
    
    # 3. Train Object Detection
    try:
        print("\n[3/5] Training Object Detection Model...")
        from .train_object_detection import train_model as train_object_detection
        train_object_detection()
        success_count += 1
    except Exception as e:
        print(f"❌ Failed to train object detection model: {e}")
    
    # 4. Train Danger Prediction
    try:
        print("\n[4/5] Training Danger Prediction Model...")
        from .train_danger_prediction import train_model as train_danger
        train_danger()
        success_count += 1
    except Exception as e:
        print(f"❌ Failed to train danger prediction model: {e}")
    
    # 5. Train Environment Classification
    try:
        print("\n[5/5] Training Environment Classification Model...")
        from .train_environment_classifier import train_model as train_environment
        train_environment()
        success_count += 1
    except Exception as e:
        print(f"❌ Failed to train environment classification model: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Training Complete: {success_count}/{total_models} models trained successfully")
    print("=" * 70 + "\n")
    
    return success_count == total_models

if __name__ == '__main__':
    success = train_all()
    sys.exit(0 if success else 1)