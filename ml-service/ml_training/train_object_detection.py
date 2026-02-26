"""
Train Object Detection Model (sklearn classifier)
Features: distance_cm, detection_confidence, proximity_value, ambient_light
Classes:  obstacle, person, vehicle, wall, stairs, door, pole
"""
import sys
import os
import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

sys.path.insert(0, str(Path(__file__).parent.parent))

ALL_CLASSES = ['obstacle', 'person', 'vehicle', 'wall', 'stairs', 'door', 'pole']
CLASS_MAP   = {name: i for i, name in enumerate(ALL_CLASSES)}


def _fetch_real_data():
    try:
        from supabase import create_client
        from dotenv import load_dotenv
        load_dotenv()
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        if not url or not key:
            print("  ⚠ No Supabase credentials")
            return []
        supabase = create_client(url, key)
        rows = supabase.table('detection_logs') \
            .select('distance_cm, detection_confidence, object_detected') \
            .not_.is_('distance_cm', 'null') \
            .not_.is_('object_detected', 'null') \
            .order('detected_at', desc=True) \
            .limit(5000).execute()
        return rows.data or []
    except Exception as e:
        print(f"  ⚠ Real data fetch failed: {e}")
        return []


def _prepare_real_data(rows):
    X, y = [], []
    for row in rows:
        try:
            obj = str(row.get('object_detected', 'obstacle')).lower().strip()
            if obj not in CLASS_MAP:
                obj = 'obstacle'
            X.append([
                float(row.get('distance_cm', 150)),
                float(row.get('detection_confidence', 0.75)),
                5000.0,
                400.0,
            ])
            y.append(CLASS_MAP[obj])
        except Exception:
            continue
    return np.array(X), np.array(y)


def _is_too_imbalanced(y, threshold=0.80):
    if len(y) == 0:
        return True
    counts = np.bincount(y.astype(int), minlength=len(ALL_CLASSES))
    return (counts.max() / len(y)) > threshold


def generate_synthetic_data(n_samples=4200):
    np.random.seed(42)
    n_per_class = n_samples // len(ALL_CLASSES)
    class_profiles = {
        'obstacle': ((10, 300),  (0.55, 0.92), (500,   9000),  (100, 1000)),
        'person':   ((40, 250),  (0.72, 0.98), (2000,  12000), (200, 900)),
        'vehicle':  ((80, 400),  (0.68, 0.95), (800,   6000),  (300, 1300)),
        'wall':     ((15, 120),  (0.82, 0.99), (9000,  20000), (100, 600)),
        'stairs':   ((25, 180),  (0.60, 0.88), (4000,  14000), (150, 750)),
        'door':     ((40, 160),  (0.72, 0.95), (7000,  17000), (200, 850)),
        'pole':     ((15, 100),  (0.65, 0.90), (1500,  7500),  (250, 950)),
    }
    all_X, all_y = [], []
    for cls_name, (dist_r, conf_r, prox_r, amb_r) in class_profiles.items():
        n    = n_per_class
        dist = np.clip(np.random.uniform(*dist_r, n) + np.random.normal(0, 2, n), 5, 400)
        conf = np.clip(np.random.uniform(*conf_r, n), 0.3, 1.0)
        prox = np.clip(np.random.uniform(*prox_r, n) + np.random.normal(0, 100, n), 100, 20000)
        amb  = np.clip(np.random.uniform(*amb_r,  n), 50, 3000)
        all_X.append(np.column_stack([dist, conf, prox, amb]))
        all_y.append(np.full(n, CLASS_MAP[cls_name]))
    X = np.vstack(all_X); y = np.hstack(all_y)
    idx = np.random.permutation(len(X))
    return X[idx], y[idx]


def load_training_data(min_samples=200):
    print("  Checking for real training data...")
    real_rows      = _fetch_real_data()
    real_X, real_y = _prepare_real_data(real_rows)

    if len(real_X) < min_samples:
        print(f"  ⚠ Only {len(real_X)} real samples — using synthetic")
        return generate_synthetic_data()

    if _is_too_imbalanced(real_y):
        print(f"  ⚠ Real data too imbalanced — blending {len(real_X)} real + 3000 synthetic")
        syn_X, syn_y = generate_synthetic_data(3000)
        X = np.vstack([real_X, syn_X]); y = np.hstack([real_y, syn_y])
        idx = np.random.permutation(len(X))
        return X[idx], y[idx]

    print(f"  ✓ Using {len(real_X)} real samples")
    return real_X, real_y


def train_model():
    print("=" * 60)
    print("Training Object Detection Model v2")
    print("=" * 60)

    X, y = load_training_data()
    print(f"✓ Total samples: {len(X)}")

    unique, counts = np.unique(y, return_counts=True)
    for u, c in zip(unique, counts):
        print(f"  {ALL_CLASSES[int(u)]}: {c} samples")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42,
        stratify=y
    )
    scaler         = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)
    print("✓ Scaled features")

    model = RandomForestClassifier(
        n_estimators=200, max_depth=20,
        class_weight='balanced', random_state=42, n_jobs=-1,
    )
    model.fit(X_train_scaled, y_train)
    print("✓ Model trained")

    y_pred = model.predict(X_test_scaled)
    print(f"\n📊 Test Accuracy: {accuracy_score(y_test, y_pred):.4f}")

    # ✅ KEY FIX: only report labels that exist in the test set
    present_in_test  = sorted(np.unique(y_test).astype(int))
    present_names    = [ALL_CLASSES[i] for i in present_in_test]
    print(classification_report(y_test, y_pred,
                                labels=present_in_test,
                                target_names=present_names))

    print("\n🧪 Verification tests:")
    tests = [
        ([80,  0.85, 1500,  500],  "obstacle"),
        ([120, 0.92, 8000,  400],  "person"),
        ([200, 0.80, 2500,  800],  "vehicle"),
        ([30,  0.95, 16000, 300],  "wall"),
        ([60,  0.72, 9000,  350],  "stairs"),
        ([80,  0.88, 13000, 500],  "door"),
        ([35,  0.75, 4000,  600],  "pole"),
    ]
    for features, expected in tests:
        sample    = np.array([features])
        scaled    = scaler.transform(sample)
        pred_idx  = int(model.predict(scaled)[0])
        pred_name = ALL_CLASSES[pred_idx]
        match     = "✅" if pred_name == expected else "⚠️ "
        print(f"  {match} Expected={expected:10s} Got={pred_name}")

    models_dir = Path(__file__).parent.parent / 'ml_models' / 'saved_models'
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / 'object_detector.pkl'
    joblib.dump({'model': model, 'scaler': scaler, 'classes': ALL_CLASSES}, model_path)
    print(f"\n✓ Saved to {model_path}")
    print("=" * 60)
    print("✅ Object Detection Model Training Complete!")
    print("=" * 60)


if __name__ == '__main__':
    train_model()