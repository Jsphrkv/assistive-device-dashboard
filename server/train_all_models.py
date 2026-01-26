import sys
from app.ml_training.train_anomaly import train_anomaly_model
from app.ml_training.train_activity import train_activity_model
from app.ml_training.train_maintenance import train_maintenance_model

def main():
    """Train all models"""
    print("\n" + "="*80)
    print("TRAINING ALL ML MODELS FOR IoT SYSTEM")
    print("="*80 + "\n")
    
    results = {}
    
    # Train Anomaly Detection Model
    try:
        print("\n[1/3] Training Anomaly Detection Model...")
        model, scaler, metrics = train_anomaly_model(use_synthetic=True)
        results['anomaly'] = {
            'status': 'success',
            'metrics': metrics
        }
    except Exception as e:
        print(f"❌ Anomaly model training failed: {e}")
        results['anomaly'] = {
            'status': 'failed',
            'error': str(e)
        }
    
    # Train Activity Recognition Model
    try:
        print("\n[2/3] Training Activity Recognition Model...")
        model, scaler, encoder, metrics = train_activity_model(use_synthetic=True)
        results['activity'] = {
            'status': 'success',
            'metrics': metrics
        }
    except Exception as e:
        print(f"❌ Activity model training failed: {e}")
        results['activity'] = {
            'status': 'failed',
            'error': str(e)
        }
    
    # Train Maintenance Prediction Model
    try:
        print("\n[3/3] Training Maintenance Prediction Model...")
        model, scaler, metrics = train_maintenance_model(use_synthetic=True)
        results['maintenance'] = {
            'status': 'success',
            'metrics': metrics
        }
    except Exception as e:
        print(f"❌ Maintenance model training failed: {e}")
        results['maintenance'] = {
            'status': 'failed',
            'error': str(e)
        }
    
    # Print summary
    print("\n" + "="*80)
    print("TRAINING SUMMARY")
    print("="*80)
    
    for model_name, result in results.items():
        status_icon = "✅" if result['status'] == 'success' else "❌"
        print(f"\n{status_icon} {model_name.upper()} MODEL:")
        
        if result['status'] == 'success':
            metrics = result['metrics']
            print(f"   Accuracy:  {metrics.get('accuracy', 0):.4f}")
            print(f"   Precision: {metrics.get('precision', 0):.4f}")
            print(f"   Recall:    {metrics.get('recall', 0):.4f}")
            print(f"   F1 Score:  {metrics.get('f1_score', 0):.4f}")
        else:
            print(f"   Error: {result['error']}")
    
    print("\n" + "="*80)
    
    # Check if all succeeded
    all_success = all(r['status'] == 'success' for r in results.values())
    
    if all_success:
        print("✅ All models trained successfully!")
        print("\nNext steps:")
        print("1. Models are saved in: app/ml_models/saved_models/")
        print("2. Restart your Flask server to load the new models")
        print("3. Test the models via your API endpoints")
    else:
        print("⚠ Some models failed to train. Check errors above.")
        return 1
    
    print("="*80 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())