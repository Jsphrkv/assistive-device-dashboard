"""
Train ML Models on Deployment
Root-level script for training models during build/deployment
Trains: anomaly, maintenance, object_detection, danger_prediction, environment_classification
"""
import os
import sys

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

def train_models():
    """Train all 5 ML models"""
    print("\n" + "="*60)
    print("TRAINING ML MODELS ON DEPLOYMENT")
    print("="*60 + "\n")
    
    try:
        # Import training functions
        from app.ml_training.train_anomaly import train_model as train_anomaly
        from app.ml_training.train_maintenance import train_model as train_maintenance
        from app.ml_training.train_object_detection import train_model as train_object_detection
        from app.ml_training.train_danger_prediction import train_model as train_danger
        from app.ml_training.train_environment_classifier import train_model as train_environment
        
        print("✓ Training modules imported successfully\n")
        
        success_count = 0
        total_models = 5
        
        # 1. Train anomaly detection
        print("[1/5] Training Anomaly Detection Model...")
        print("-" * 60)
        try:
            train_anomaly()
            print("✓ Anomaly model trained successfully\n")
            success_count += 1
        except Exception as e:
            print(f"✗ Anomaly training failed: {e}\n")
        
        # 2. Train maintenance prediction
        print("[2/5] Training Maintenance Prediction Model...")
        print("-" * 60)
        try:
            train_maintenance()
            print("✓ Maintenance model trained successfully\n")
            success_count += 1
        except Exception as e:
            print(f"✗ Maintenance training failed: {e}\n")
        
        # 3. Train object detection
        print("[3/5] Training Object Detection Model...")
        print("-" * 60)
        try:
            train_object_detection()
            print("✓ Object detection model trained successfully\n")
            success_count += 1
        except Exception as e:
            print(f"✗ Object detection training failed: {e}\n")
        
        # 4. Train danger prediction
        print("[4/5] Training Danger Prediction Model...")
        print("-" * 60)
        try:
            train_danger()
            print("✓ Danger prediction model trained successfully\n")
            success_count += 1
        except Exception as e:
            print(f"✗ Danger prediction training failed: {e}\n")
        
        # 5. Train environment classification
        print("[5/5] Training Environment Classification Model...")
        print("-" * 60)
        try:
            train_environment()
            print("✓ Environment classification model trained successfully\n")
            success_count += 1
        except Exception as e:
            print(f"✗ Environment classification training failed: {e}\n")
        
        print("="*60)
        if success_count == total_models:
            print(f"✅ ALL {total_models} MODELS TRAINED SUCCESSFULLY!")
        else:
            print(f"⚠️  {success_count}/{total_models} MODELS TRAINED")
            print("Failed models will use fallback predictions")
        print("="*60 + "\n")
        
        return success_count > 0  # At least one model trained
        
    except ImportError as e:
        print(f"\n✗ Failed to import training modules: {e}")
        print("This is expected if ml_training directory doesn't exist yet.")
        print("Models will use fallback predictions.\n")
        return False
    
    except Exception as e:
        print(f"\n✗ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = train_models()
    
    if not success:
        print("\n⚠️  Warning: Models not trained, but deployment will continue.")
        print("The API will use fallback predictions until models are trained.\n")
    
    # Don't fail the build - just continue with fallback mode
    sys.exit(0)