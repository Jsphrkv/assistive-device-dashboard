"""
Train Anomaly Detection Model
"""
import sys
import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_synthetic_data(n_samples=1000):
    np.random.seed(42)
    n_normal  = int(n_samples * 0.95)
    n_anomaly = n_samples - n_normal

    normal_data = np.column_stack([
        np.random.normal(30,  5,  n_normal),
        np.random.normal(70,  15, n_normal),
        np.random.normal(40,  10, n_normal),
        np.random.normal(-50, 10, n_normal),
        np.random.poisson(0.5,    n_normal)
    ])
    anomaly_data = np.column_stack([
        np.random.normal(50,  10, n_anomaly),
        np.random.normal(15,  5,  n_anomaly),
        np.random.normal(80,  5,  n_anomaly),
        np.random.normal(-85, 5,  n_anomaly),
        np.random.poisson(5,      n_anomaly)
    ])

    X = np.vstack([normal_data, anomaly_data])
    return X


def train_model():
    print("=" * 60)
    print("Training Anomaly Detection Model")
    print("=" * 60)

    X = generate_synthetic_data()
    print(f"✓ Generated {len(X)} samples")

    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print("✓ Scaled features")

    model = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
    model.fit(X_scaled)
    print("✓ Model trained")

    # ── Fix: correct filename + save as dict with scaler ──────────────────────
    models_dir = Path(__file__).parent.parent / 'ml_models' / 'saved_models'
    models_dir.mkdir(parents=True, exist_ok=True)

    model_path = models_dir / 'anomaly_detector.pkl'          # ← fixed name
    joblib.dump({'model': model, 'scaler': scaler}, model_path)
    print(f"✓ Model saved to {model_path}")

    # Test
    test_normal = np.array([[30, 70, 40, -50, 0]])
    test_scaled = scaler.transform(test_normal)
    prediction  = model.predict(test_scaled)[0]
    print(f"✓ Test prediction: {'Anomaly' if prediction == -1 else 'Normal'}")

    print("=" * 60)
    print("✅ Anomaly Detection Model Training Complete!")
    print("=" * 60)


if __name__ == '__main__':
    train_model()