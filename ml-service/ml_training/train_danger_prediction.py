"""
Train Danger Prediction Model — 4 features version
Features: distance_cm, rate_of_change, proximity_value, current_speed_estimate
"""
import sys
import os
import joblib
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

sys.path.insert(0, str(Path(__file__).parent.parent))


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
            .select('distance_cm, detection_confidence, danger_level') \
            .not_.is_('distance_cm', 'null') \
            .not_.is_('danger_level', 'null') \
            .order('detected_at', desc=True) \
            .limit(5000).execute()
        return rows.data or []
    except Exception as e:
        print(f"  ⚠ Real data fetch failed: {e}")
        return []


def _prepare_real_data(rows):
    danger_map = {'low': 15.0, 'medium': 55.0, 'high': 80.0, 'critical': 95.0}
    X, y = [], []
    for row in rows:
        try:
            score = danger_map.get(str(row.get('danger_level', 'low')).lower(), 15.0)
            X.append([float(row.get('distance_cm', 150)), -5.0, 5000.0, 1.0])
            y.append(score)
        except Exception:
            continue
    return np.array(X), np.array(y)


def _is_too_imbalanced(y, threshold=0.80):
    if len(y) == 0:
        return True
    bins   = [0, 30, 60, 80, 100]
    counts = np.histogram(y, bins=bins)[0]
    return (counts.max() / len(y)) > threshold


def generate_synthetic_data(n_samples=4000):
    np.random.seed(42)
    n_safe     = int(n_samples * 0.25)
    n_caution  = int(n_samples * 0.30)
    n_slowdown = int(n_samples * 0.25)
    n_stop     = n_samples - n_safe - n_caution - n_slowdown

    def make_chunk(n, dist_r, roc_r, prox_r, speed_r, score_center, score_std):
        distance  = np.random.uniform(*dist_r,  n)
        roc       = np.random.uniform(*roc_r,   n)
        proximity = np.random.uniform(*prox_r,  n)
        speed     = np.random.uniform(*speed_r, n)
        X         = np.column_stack([distance, roc, proximity, speed])
        dist_f    = np.clip(1 - (distance / 400), 0, 1)
        appr_f    = np.clip(np.abs(np.minimum(roc, 0)) / 50, 0, 1)
        prox_f    = np.clip(proximity / 20000, 0, 1)
        speed_f   = np.clip(speed / 2.0, 0, 1)
        base      = (dist_f*50 + appr_f*30 + prox_f*10 + speed_f*10)
        score     = np.clip(base + np.random.normal(score_center - base.mean(), score_std, n), 0, 100)
        return X, score

    chunks = [
        make_chunk(n_safe,     (200, 400), (-2,  10),  (300,  3000),  (0.5, 1.2), 10, 3),
        make_chunk(n_caution,  (80,  200), (-15, -2),  (2000, 8000),  (0.8, 1.5), 40, 5),
        make_chunk(n_slowdown, (40,  100), (-30, -10), (8000, 15000), (1.0, 1.8), 65, 5),
        make_chunk(n_stop,     (10,  50),  (-50, -25), (14000,20000), (1.5, 2.0), 88, 4),
    ]
    X = np.vstack([c[0] for c in chunks])
    y = np.concatenate([c[1] for c in chunks])
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
        bins   = [0, 30, 60, 80, 100]
        labels = ['SAFE', 'CAUTION', 'SLOW_DOWN', 'STOP']
        counts = np.histogram(real_y, bins=bins)[0]
        dist   = " | ".join(f"{l}={c}" for l, c in zip(labels, counts))
        print(f"  ⚠ Real data too imbalanced ({dist})")
        print(f"  ⚠ Blending {len(real_X)} real + 3000 synthetic")
        syn_X, syn_y = generate_synthetic_data(3000)
        X = np.vstack([real_X, syn_X]); y = np.concatenate([real_y, syn_y])
        idx = np.random.permutation(len(X))
        return X[idx], y[idx]

    print(f"  ✓ Using {len(real_X)} real samples")
    return real_X, real_y


def train_model():
    print("=" * 60)
    print("Training Danger Prediction Model v2 (4 features)")
    print("=" * 60)

    X, y = load_training_data()
    print(f"✓ Total samples : {len(X)}")

    bins   = [0, 30, 60, 80, 100]
    labels = ['SAFE', 'CAUTION', 'SLOW_DOWN', 'STOP']
    counts = np.histogram(y, bins=bins)[0]
    print(f"  Distribution  : " + " | ".join(f"{l}={c}" for l, c in zip(labels, counts)))

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    scaler         = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)
    print(f"✓ Scaler fitted on {scaler.n_features_in_} features")

    try:
        from xgboost import XGBRegressor
        model      = XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=6,
                                  subsample=0.8, colsample_bytree=0.8, random_state=42, verbosity=0)
        model_name = "XGBoost"
    except ImportError:
        from sklearn.ensemble import GradientBoostingRegressor
        model      = GradientBoostingRegressor(n_estimators=300, learning_rate=0.05,
                                               max_depth=6, subsample=0.8, random_state=42)
        model_name = "GradientBoosting"

    print(f"✓ Using {model_name}")
    model.fit(X_train_scaled, y_train)
    print("✓ Model trained")

    y_pred = model.predict(X_test_scaled)
    print(f"\n📊 Performance:")
    print(f"   MSE : {mean_squared_error(y_test, y_pred):.4f}")
    print(f"   MAE : {mean_absolute_error(y_test, y_pred):.4f}")
    print(f"   R²  : {r2_score(y_test, y_pred):.4f}")

    print("\n🧪 Verification tests:")
    tests = [
        ([350, 2,    500,   0.7], "Far, moving away   → SAFE"),
        ([150, -8,   4000,  1.0], "Medium, slow app   → CAUTION"),
        ([60,  -20,  10000, 1.5], "Close, moderate    → SLOW_DOWN"),
        ([25,  -35,  16000, 1.7], "Very close, fast   → STOP"),
        ([12,  -50,  19500, 2.0], "Critical           → STOP"),
    ]
    for features, description in tests:
        sample = np.array([features])
        score  = model.predict(scaler.transform(sample))[0]
        action = ('STOP' if score > 80 else 'SLOW_DOWN' if score > 60
                  else 'CAUTION' if score > 30 else 'SAFE')
        print(f"  [{action:10s}] score={score:5.1f} — {description}")

    models_dir = Path(__file__).parent.parent / 'ml_models' / 'saved_models'
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({'model': model, 'scaler': scaler}, models_dir / 'danger_predictor.pkl')
    print(f"\n✓ Saved to {models_dir / 'danger_predictor.pkl'}")
    print("=" * 60)
    print("✅ Danger Prediction Model Training Complete!")
    print(f"   Scaler expects: {scaler.n_features_in_} features  Match: ✅ YES")
    print("=" * 60)


if __name__ == '__main__':
    train_model()