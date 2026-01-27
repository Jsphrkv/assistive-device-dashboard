#!/usr/bin/env python3
"""
Train ML models on deployment
Ensures models are compatible with server environment
"""

import os
import sys

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

def train_models():
    """Train all ML models"""
    print("\n" + "="*60)
    print("TRAINING ML MODELS ON DEPLOYMENT")
    print("="*60 + "\n")
    
    try:
        # Import training functions
        from app.ml_training.train_anomaly import train_anomaly_model
        from app.ml_training.train_activity import train_activity_model
        from app.ml_training.train_maintenance import train_maintenance_model
        
        print("✓ Training modules imported successfully\n")
        
        # Train anomaly detection
        print("[1/3] Training Anomaly Detection Model...")
        print("-" * 60)
        try:
            model, scaler, metrics = train_anomaly_model(use_synthetic=True)
            print(f"✓ Anomaly model trained - Accuracy: {metrics.get('accuracy', 0):.4f}\n")
        except Exception as e:
            print(f"✗ Anomaly training failed: {e}\n")
            return False
        
        # Train activity recognition
        print("[2/3] Training Activity Recognition Model...")
        print("-" * 60)
        try:
            model, scaler, encoder, metrics = train_activity_model(use_synthetic=True)
            print(f"✓ Activity model trained - Accuracy: {metrics.get('accuracy', 0):.4f}\n")
        except Exception as e:
            print(f"✗ Activity training failed: {e}\n")
            return False
        
        # Train maintenance prediction
        print("[3/3] Training Maintenance Prediction Model...")
        print("-" * 60)
        try:
            model, scaler, metrics = train_maintenance_model(use_synthetic=True)
            print(f"✓ Maintenance model trained - Accuracy: {metrics.get('accuracy', 0):.4f}\n")
        except Exception as e:
            print(f"✗ Maintenance training failed: {e}\n")
            return False
        
        print("="*60)
        print("✅ ALL MODELS TRAINED SUCCESSFULLY!")
        print("="*60 + "\n")
        
        return True
        
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
        print("\n⚠ Warning: Models not trained, but deployment will continue.")
        print("The API will use fallback predictions until models are trained.\n")
    
    # Don't fail the build - just continue with fallback mode
    sys.exit(0)