"""
Train Maintenance Prediction Model
"""
import sys
import os
import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent))

def generate_synthetic_data(n_samples=500):
    """Generate synthetic maintenance data"""
    np.random.seed(42)
    
    # Features: battery_health, usage_hours, temperature_avg, error_count, days_since_maintenance
    X = np.column_stack([
        np.random.uniform(30, 100, n_samples),   # battery_health
        np.random.uniform(0, 2000, n_samples),   # usage_hours
        np.random.uniform(20, 50, n_samples),    # temperature_avg
        np.random.poisson(2, n_samples),         # error_count
        np.random.uniform(0, 180, n_samples)     # days_since_maintenance
    ])
    
    # Calculate maintenance need
    maintenance_score = (
        (100 - X[:, 0]) / 100 * 0.3 +      # Lower battery health = higher score
        (X[:, 1] / 2000) * 0.3 +            # More usage = higher score
        ((X[:, 2] - 25) / 25) * 0.2 +       # Higher temp = higher score
        (X[:, 3] / 10) * 0.1 +              # More errors = higher score
        (X[:, 4] / 180) * 0.1                # More days = higher score
    )
    
    maintenance_score += np.random.normal(0, 0.1, n_samples)
    y = (maintenance_score > 0.5).astype(int)
    
    return X, y

def train_model():
    """Train and save maintenance prediction model"""
    print("=" * 60)
    print("Training Maintenance Prediction Model")
    print("=" * 60)
    
    # Generate data
    X, y = generate_synthetic_data()
    print(f"✓ Generated {len(X)} samples")
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print("✓ Scaled features")
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        max_depth=10
    )
    model.fit(X_scaled, y)
    print("✓ Model trained")
    
    # Save model
    models_dir = Path(__file__).parent.parent / 'ml_models' / 'saved_models'
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / 'maintenance_model.joblib'
    joblib.dump({
        'model': model,
        'scaler': scaler
    }, model_path)
    print(f"✓ Model saved to {model_path}")
    
    # Test prediction
    test_data = [[50, 1000, 35, 5, 90]]  # Moderate usage
    test_scaled = scaler.transform(test_data)
    prediction = model.predict(test_scaled)[0]
    prob = model.predict_proba(test_scaled)[0][1]
    print(f"✓ Test prediction: {'Needs maintenance' if prediction == 1 else 'OK'} (prob: {prob:.2f})")
    
    print("=" * 60)
    print("✅ Maintenance Prediction Model Training Complete!")
    print("=" * 60)

if __name__ == '__main__':
    train_model()