"""
Train Anomaly Detection Model  (v3)
Detects abnormal sensor behavior — sensor malfunction, sudden jumps,
physically impossible readings from the HC-SR04 + VCNL4010 combo.

v3 changes vs v2:
  - Real data fetch ENABLED (was commented out)
  - Blends real + synthetic to always guarantee anomaly coverage
  - Why ml_predictions, NOT detection_logs?
      detection_logs stores raw per-detection columns (distance_cm, object_detected).
      Anomaly detection needs COMPUTED features: ambient_light, rate_of_change,
      detection_count — these are aggregated values stored as input_data JSON
      in ml_predictions. Use inject_training_data.py to populate them.
"""
import sys
import os
import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent))

# [0] distance_cm, [1] proximity_value, [2] ambient_light,
# [3] rate_of_change, [4] detection_count


# ─────────────────────────────────────────────────────────────────────────────
# REAL DATA  →  ml_predictions
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_real_data():
    try:
        from supabase import create_client
        from dotenv import load_dotenv
        load_dotenv()
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        if not url or not key:
            print("  ⚠ No Supabase credentials — skipping real data fetch")
            return []
        supabase = create_client(url, key)
        rows = supabase.table('ml_predictions') \
            .select('input_data, prediction_result') \
            .eq('prediction_type', 'anomaly') \
            .order('created_at', desc=True) \
            .limit(5000) \
            .execute()
        return rows.data or []
    except Exception as e:
        print(f"  ⚠ Real data fetch failed: {e}")
        return []


def _prepare_real_data(rows):
    X = []
    for row in rows:
        try:
            inp = row.get('input_data', {})
            X.append([
                float(inp.get('distance_cm',      100)),
                float(inp.get('proximity_value',  5000)),
                float(inp.get('ambient_light',    400)),
                float(inp.get('rate_of_change',   0)),
                float(inp.get('detection_count',  2)),
            ])
        except Exception:
            continue
    return np.array(X) if X else np.array([]).reshape(0, 5)


def load_training_data(min_samples=200):
    """
    Try real data from ml_predictions first.
    Always blend with synthetic — IsolationForest needs to see anomaly
    patterns to draw the right boundary, and real data alone won't have
    enough anomaly examples.
    """
    print("  Checking for real training data in ml_predictions...")
    real_rows = _fetch_real_data()
    real_X    = _prepare_real_data(real_rows)

    if len(real_X) >= min_samples:
        print(f"  ✓ Found {len(real_X)} real samples")
        syn_X = generate_synthetic_data(max(1000, len(real_X)))
        X     = np.vstack([real_X, syn_X])
        idx   = np.random.permutation(len(X))
        print(f"  ✓ Blended: {len(real_X)} real + {len(syn_X)} synthetic = {len(X)} total")
        return X[idx]
    else:
        print(f"  ⚠ Only {len(real_X)} real samples (need {min_samples}) — using pure synthetic")
        return generate_synthetic_data()


# ─────────────────────────────────────────────────────────────────────────────
# SYNTHETIC DATA
# ─────────────────────────────────────────────────────────────────────────────

def generate_synthetic_data(n_samples=3000):
    np.random.seed(42)
    n_normal  = int(n_samples * 0.95)
    n_anomaly = n_samples - n_normal

    scenarios = {
        'open_space': int(n_normal * 0.25),
        'corridor':   int(n_normal * 0.25),
        'near_wall':  int(n_normal * 0.20),
        'crowded':    int(n_normal * 0.15),
        'outdoor':    int(n_normal * 0.15),
    }

    normal_chunks = []

    n = scenarios['open_space']
    normal_chunks.append(np.column_stack([
        np.random.uniform(150, 400, n), np.random.uniform(300,   2000,  n),
        np.random.uniform(400, 1500,n), np.random.uniform(-8,    8,     n),
        np.random.uniform(0.2, 2,   n),
    ]))

    n = scenarios['corridor']
    normal_chunks.append(np.column_stack([
        np.random.uniform(40,  150, n), np.random.uniform(3000,  12000, n),
        np.random.uniform(200, 600, n), np.random.uniform(-15,   5,     n),
        np.random.uniform(1,   5,   n),
    ]))

    n = scenarios['near_wall']
    normal_chunks.append(np.column_stack([
        np.random.uniform(20,  60,  n), np.random.uniform(10000, 19000, n),
        np.random.uniform(100, 500, n), np.random.uniform(-2,    2,     n),
        np.random.uniform(0.1, 1,   n),
    ]))

    n = scenarios['crowded']
    normal_chunks.append(np.column_stack([
        np.random.uniform(30,  120, n), np.random.uniform(5000,  15000, n),
        np.random.uniform(200, 700, n), np.random.uniform(-20,   10,    n),
        np.random.uniform(5,   15,  n),
    ]))

    n = scenarios['outdoor']
    normal_chunks.append(np.column_stack([
        np.random.uniform(200, 400, n), np.random.uniform(200,   1500,  n),
        np.random.uniform(800, 2000,n), np.random.uniform(-5,    5,     n),
        np.random.uniform(0.1, 1.5, n),
    ]))

    normal_X  = np.vstack(normal_chunks)
    normal_X += np.random.normal(0, 0.5, normal_X.shape)

    n_each = n_anomaly // 4
    anomaly_chunks = [
        np.column_stack([np.random.choice([0,401,450], n_each), np.random.choice([0,65535], n_each),
                         np.random.uniform(0,50,n_each),   np.random.uniform(-100,100,n_each), np.random.uniform(0,1,n_each)]),
        np.column_stack([np.random.uniform(350,400,n_each), np.random.uniform(100,500,n_each),
                         np.random.uniform(200,800,n_each),np.random.uniform(80,200,n_each),   np.random.uniform(0,1,n_each)]),
        np.column_stack([np.random.uniform(100,105,n_each), np.random.uniform(4990,5010,n_each),
                         np.random.uniform(390,410,n_each),np.random.uniform(-0.1,0.1,n_each), np.random.uniform(20,30,n_each)]),
        np.column_stack([np.random.uniform(10,20,n_each),   np.random.uniform(100,300,n_each),
                         np.random.uniform(200,800,n_each), np.random.uniform(-50,-40,n_each), np.random.uniform(10,20,n_each)]),
    ]

    X   = np.vstack([normal_X, np.vstack(anomaly_chunks)])
    idx = np.random.permutation(len(X))
    return X[idx]


# ─────────────────────────────────────────────────────────────────────────────
# TRAINING
# ─────────────────────────────────────────────────────────────────────────────

def train_model():
    print("=" * 60)
    print("Training Anomaly Detection Model (v3)")
    print("Features: distance_cm, proximity_value, ambient_light,")
    print("          rate_of_change, detection_count")
    print("=" * 60)

    X = load_training_data()
    print(f"✓ Total samples: {len(X)}")

    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print("✓ Scaled features")

    model = IsolationForest(contamination=0.05, n_estimators=200,
                            max_samples='auto', random_state=42, n_jobs=-1)
    model.fit(X_scaled)
    print("✓ Model trained")

    print("\n🧪 Verification tests:")
    tests = [
        ([150, 3000, 500,  -5,  2],   "Normal: walking in corridor"),
        ([250, 800,  1000, -3,  1],   "Normal: open space walking"),
        ([30,  15000, 300, -1,  0.5], "Normal: stationary near wall"),
        ([0,   65535, 10,  200, 0],   "Anomaly: sensor malfunction"),
        ([102, 5000,  400, 0,   25],  "Anomaly: stuck sensor"),
        ([15,  200,   500, -45, 15],  "Anomaly: physical impossibility"),
    ]
    for features, description in tests:
        s = np.array([features])
        p = model.predict(scaler.transform(s))[0]
        score = model.decision_function(scaler.transform(s))[0]
        print(f"  {'🔴 ANOMALY' if p == -1 else '🟢 Normal '} (score={score:.3f}) — {description}")

    models_dir = Path(__file__).parent.parent / 'ml_models' / 'saved_models'
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({'model': model, 'scaler': scaler}, models_dir / 'anomaly_detector.pkl')
    print(f"\n✓ Saved to {models_dir / 'anomaly_detector.pkl'}")
    print("=" * 60)
    print("✅ Anomaly Detection Model Training Complete!")
    print("=" * 60)


if __name__ == '__main__':
    train_model()