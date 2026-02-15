"""
Train Anomaly Detection Model
"""
import sys
import os
import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def generate_synthetic_data(n_samples=1000):
    """Generate synthetic telemetry data"""
    np.random.seed(42)
    
    n_normal = int(n_samples * 0.95)
    n_anomaly = n_samples - n_normal
    
    # Normal data
    normal_data = np.column_stack([
        np.random.normal(30, 5, n_normal),      # temperature
        np.random.normal(70, 15, n_normal),     # battery_level
        np.random.normal(40, 10, n_normal),     # cpu_usage
        np.random.normal(-50, 10, n_normal),    # rssi
        np.random.poisson(0.5, n_normal)        # error_count
    ])
    
    # Anomaly data
    anomaly_data = np.column_stack([
        np.random.normal(50, 10, n_anomaly),    # high temp
        np.random.normal(15, 5, n_anomaly),     # low battery
        np.random.normal(80, 5, n_anomaly),     # high cpu
        np.random.normal(-85, 5, n_anomaly),    # poor signal
        np.random.poisson(5, n_anomaly)         # many errors
    ])
    
    X = np.vstack([normal_data, anomaly_data])
    y = np.hstack([np.zeros(n_normal), np.ones(n_anomaly)])
    
    return X, y

def train_model():
    """Train and save anomaly detection model"""
    print("=" * 60)
    print("Training Anomaly Detection Model")
    print("=" * 60)
    
    # Generate data
    X, y = generate_synthetic_data()
    print(f"✓ Generated {len(X)} samples")
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print("✓ Scaled features")
    
    # Train model
    model = IsolationForest(
        contamination=0.05,
        random_state=42,
        n_estimators=100
    )
    model.fit(X_scaled)
    print("✓ Model trained")
    
    # Save model
    models_dir = Path(__file__).parent.parent / 'ml_models' / 'saved_models'
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / 'anomaly_model.joblib'
    joblib.dump({
        'model': model,
        'scaler': scaler
    }, model_path)
    print(f"✓ Model saved to {model_path}")
    
    # Test prediction
    test_normal = [[30, 70, 40, -50, 0]]
    test_scaled = scaler.transform(test_normal)
    prediction = model.predict(test_scaled)[0]
    print(f"✓ Test prediction: {'Anomaly' if prediction == -1 else 'Normal'}")
    
    print("=" * 60)
    print("✅ Anomaly Detection Model Training Complete!")
    print("=" * 60)

if __name__ == '__main__':
    train_model()