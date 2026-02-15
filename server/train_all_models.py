"""
Train All ML Models Script
Root-level training script for deployment/build
Trains: anomaly, maintenance, object_detection, danger_prediction, environment_classification
"""
import sys
from pathlib import Path

# Add app to Python path
sys.path.insert(0, str(Path(__file__).parent / 'app'))

def main():
    """Train all 5 models"""
    print("\n" + "=" * 80)
    print("TRAINING ALL ML MODELS FOR ASSISTIVE DEVICE SYSTEM")
    print("=" * 80 + "\n")
    
    results = {}
    
    # 1. Train Anomaly Detection Model
    try:
        print("\n[1/5] Training Anomaly Detection Model...")
        from app.ml_training.train_anomaly import train_model
        train_model()
        results['anomaly'] = {'status': 'success'}
        print("✅ Anomaly detection model trained successfully")
    except Exception as e:
        print(f"❌ Anomaly model training failed: {e}")
        results['anomaly'] = {'status': 'failed', 'error': str(e)}
    
    # 2. Train Maintenance Prediction Model
    try:
        print("\n[2/5] Training Maintenance Prediction Model...")
        from app.ml_training.train_maintenance import train_model
        train_model()
        results['maintenance'] = {'status': 'success'}
        print("✅ Maintenance prediction model trained successfully")
    except Exception as e:
        print(f"❌ Maintenance model training failed: {e}")
        results['maintenance'] = {'status': 'failed', 'error': str(e)}
    
    # 3. Train Object Detection Model
    try:
        print("\n[3/5] Training Object Detection Model...")
        from app.ml_training.train_object_detection import train_model
        train_model()
        results['object_detection'] = {'status': 'success'}
        print("✅ Object detection model trained successfully")
    except Exception as e:
        print(f"❌ Object detection model training failed: {e}")
        results['object_detection'] = {'status': 'failed', 'error': str(e)}
    
    # 4. Train Danger Prediction Model
    try:
        print("\n[4/5] Training Danger Prediction Model...")
        from app.ml_training.train_danger_prediction import train_model
        train_model()
        results['danger_prediction'] = {'status': 'success'}
        print("✅ Danger prediction model trained successfully")
    except Exception as e:
        print(f"❌ Danger prediction model training failed: {e}")
        results['danger_prediction'] = {'status': 'failed', 'error': str(e)}
    
    # 5. Train Environment Classification Model
    try:
        print("\n[5/5] Training Environment Classification Model...")
        from app.ml_training.train_environment_classifier import train_model
        train_model()
        results['environment_classification'] = {'status': 'success'}
        print("✅ Environment classification model trained successfully")
    except Exception as e:
        print(f"❌ Environment classification model training failed: {e}")
        results['environment_classification'] = {'status': 'failed', 'error': str(e)}
    
    # Print summary
    print("\n" + "=" * 80)
    print("TRAINING SUMMARY")
    print("=" * 80)
    
    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    total_count = len(results)
    
    for model_name, result in results.items():
        status_icon = "✅" if result['status'] == 'success' else "❌"
        print(f"{status_icon} {model_name.upper().replace('_', ' ')}: {result['status'].upper()}")
        if result['status'] == 'failed':
            print(f"   Error: {result['error']}")
    
    print("\n" + "=" * 80)
    print(f"Results: {success_count}/{total_count} models trained successfully")
    print("=" * 80)
    
    # Check if all succeeded
    all_success = all(r['status'] == 'success' for r in results.values())
    
    if all_success:
        print("\n✅ All models trained successfully!")
        print("\nNext steps:")
        print("1. Models saved in: app/ml_models/saved_models/")
        print("2. Restart your Flask server to load the new models")
        print("3. Test the models via API endpoints:")
        print("   - POST /api/ml/detect/anomaly")
        print("   - POST /api/ml/predict/maintenance")
        print("   - POST /api/ml/detect/object")
        print("   - POST /api/ml/predict/danger")
        print("   - POST /api/ml/classify/environment")
    else:
        print("\n⚠️  Some models failed to train. Check errors above.")
        print("The API will use fallback predictions for failed models.")
        return 1
    
    print("\n" + "=" * 80 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())