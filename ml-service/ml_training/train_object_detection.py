"""
Train Object Detection Model
"""
import sys
import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_synthetic_data(n_samples=800):
    np.random.seed(42)
    samples_per_type = n_samples // 7
    all_data = []

    for obj_type in range(7):
        if obj_type == 0:   # obstacle
            distance   = np.random.uniform(10,    300,   samples_per_type)
            confidence = np.random.uniform(0.6,   0.95,  samples_per_type)
            proximity  = np.random.uniform(500,   8000,  samples_per_type)
            ambient    = np.random.uniform(100,   1000,  samples_per_type)
        elif obj_type == 1: # person
            distance   = np.random.uniform(50,    250,   samples_per_type)
            confidence = np.random.uniform(0.75,  0.98,  samples_per_type)
            proximity  = np.random.uniform(3000,  12000, samples_per_type)
            ambient    = np.random.uniform(200,   800,   samples_per_type)
        elif obj_type == 2: # vehicle
            distance   = np.random.uniform(100,   400,   samples_per_type)
            confidence = np.random.uniform(0.7,   0.95,  samples_per_type)
            proximity  = np.random.uniform(1000,  5000,  samples_per_type)
            ambient    = np.random.uniform(300,   1200,  samples_per_type)
        elif obj_type == 3: # wall
            distance   = np.random.uniform(20,    150,   samples_per_type)
            confidence = np.random.uniform(0.85,  0.99,  samples_per_type)
            proximity  = np.random.uniform(10000, 20000, samples_per_type)
            ambient    = np.random.uniform(100,   600,   samples_per_type)
        elif obj_type == 4: # stairs
            distance   = np.random.uniform(30,    200,   samples_per_type)
            confidence = np.random.uniform(0.65,  0.90,  samples_per_type)
            proximity  = np.random.uniform(5000,  15000, samples_per_type)
            ambient    = np.random.uniform(150,   700,   samples_per_type)
        elif obj_type == 5: # door
            distance   = np.random.uniform(50,    180,   samples_per_type)
            confidence = np.random.uniform(0.75,  0.95,  samples_per_type)
            proximity  = np.random.uniform(8000,  18000, samples_per_type)
            ambient    = np.random.uniform(200,   800,   samples_per_type)
        else:               # pole
            distance   = np.random.uniform(20,    120,   samples_per_type)
            confidence = np.random.uniform(0.70,  0.92,  samples_per_type)
            proximity  = np.random.uniform(2000,  8000,  samples_per_type)
            ambient    = np.random.uniform(250,   900,   samples_per_type)

        all_data.append((
            np.column_stack([distance, confidence, proximity, ambient]),
            np.full(samples_per_type, obj_type)
        ))

    X = np.vstack([d[0] for d in all_data])
    y = np.hstack([d[1] for d in all_data])
    idx = np.random.permutation(len(X))
    return X[idx], y[idx]


def train_model():
    print("=" * 60)
    print("Training Object Detection Model")
    print("=" * 60)

    X, y = generate_synthetic_data()
    print(f"✓ Generated {len(X)} samples")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler         = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)
    print("✓ Scaled features")

    model = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
    model.fit(X_train_scaled, y_train)
    print("✓ Model trained")

    y_pred = model.predict(X_test_scaled)
    print(f"\n✓ Test Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(classification_report(
        y_test, y_pred,
        target_names=['obstacle', 'person', 'vehicle', 'wall', 'stairs', 'door', 'pole']
    ))

    # ── Fix: correct filename + save as dict with scaler ─────────────────────
    models_dir = Path(__file__).parent.parent / 'ml_models' / 'saved_models'
    models_dir.mkdir(parents=True, exist_ok=True)

    model_path = models_dir / 'object_detector.pkl'           # ← fixed name
    joblib.dump({'model': model, 'scaler': scaler}, model_path)
    print(f"\n✓ Model saved to {model_path}")

    print("=" * 60)
    print("✅ Object Detection Model Training Complete!")
    print("=" * 60)


if __name__ == '__main__':
    train_model()