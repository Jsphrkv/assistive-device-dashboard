"""
Train Anomaly Detection Model
Detects abnormal sensor behavior — sensor malfunction, sudden jumps,
physically impossible readings from the HC-SR04 + VCNL4010 combo.

Improvements over v1:
  - 3x more samples (3000 vs 1000)
  - Scenario-based normal/anomaly generation matching real RPi behavior
  - Real data fallback: pulls from Supabase ml_predictions if 200+ rows exist
  - Better anomaly categories: sensor malfunction, physical impossibility,
    sudden spike, stuck sensor
"""
import sys
import os
import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Feature names (must match ml_service.py detect_anomaly input) ─────────────
# [0] distance_cm          HC-SR04 reading
# [1] proximity_value      VCNL4010 raw
# [2] ambient_light        lux
# [3] rate_of_change       cm/s
# [4] detection_count      detections per minute


# ─────────────────────────────────────────────────────────────────────────────
# REAL DATA (Supabase fallback)
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_real_data():
    """Pull real sensor readings from ml_predictions table."""
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
    """Convert Supabase rows to X array for IsolationForest."""
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


# def load_training_data(min_samples=200):
#     """Try real data first, fall back to synthetic."""
#     print("  Checking for real training data...")
#     real_rows = _fetch_real_data()
#     real_X    = _prepare_real_data(real_rows)

#     if len(real_X) >= min_samples:
#         print(f"  ✓ Using {len(real_X)} real samples from Supabase")
#         return real_X
#     else:
#         print(f"  ⚠ Only {len(real_X)} real samples (need {min_samples}) — using improved synthetic")
#         return generate_synthetic_data()
def load_training_data(min_samples=200):
    print("  Using improved synthetic data (no labeled source available)")
    return generate_synthetic_data()

# ─────────────────────────────────────────────────────────────────────────────
# IMPROVED SYNTHETIC DATA
# ─────────────────────────────────────────────────────────────────────────────

def generate_synthetic_data(n_samples=3000):
    """
    Scenario-based synthetic data matching real RPi HC-SR04 + VCNL4010 behavior.

    Normal scenarios (95%):
      - Walking in open space: distance 150-400cm, low detection frequency
      - Walking in corridor: distance 40-150cm, moderate frequency
      - Stationary near wall: distance 20-60cm, very low roc
      - Crowded area: distance 30-120cm, high frequency
      - Outdoor open: distance 200-400cm, low proximity

    Anomaly scenarios (5%):
      - Sensor malfunction: impossible values (distance=0, proximity=65535)
      - Sudden spike: distance jumps 300cm in one reading
      - Stuck sensor: same value 10+ times (low variance in roc)
      - Physical impossibility: distance 5cm + proximity 200 (contradictory)
    """
    np.random.seed(42)

    n_normal  = int(n_samples * 0.95)
    n_anomaly = n_samples - n_normal

    # ── Normal scenarios ──────────────────────────────────────────────────────
    scenarios = {
        'open_space':  int(n_normal * 0.25),
        'corridor':    int(n_normal * 0.25),
        'near_wall':   int(n_normal * 0.20),
        'crowded':     int(n_normal * 0.15),
        'outdoor':     int(n_normal * 0.15),
    }

    normal_chunks = []

    # Open space walking
    n = scenarios['open_space']
    normal_chunks.append(np.column_stack([
        np.random.uniform(150, 400, n),      # distance
        np.random.uniform(300, 2000, n),     # proximity (low — far away)
        np.random.uniform(400, 1500, n),     # ambient (bright outdoor)
        np.random.uniform(-8, 8, n),         # slow roc
        np.random.uniform(0.2, 2, n),        # low detection frequency
    ]))

    # Corridor walking
    n = scenarios['corridor']
    normal_chunks.append(np.column_stack([
        np.random.uniform(40, 150, n),
        np.random.uniform(3000, 12000, n),   # higher proximity — closer walls
        np.random.uniform(200, 600, n),      # indoor lighting
        np.random.uniform(-15, 5, n),        # moderate approach
        np.random.uniform(1, 5, n),
    ]))

    # Stationary near wall
    n = scenarios['near_wall']
    normal_chunks.append(np.column_stack([
        np.random.uniform(20, 60, n),
        np.random.uniform(10000, 19000, n),  # very high proximity — very close
        np.random.uniform(100, 500, n),
        np.random.uniform(-2, 2, n),         # nearly stationary
        np.random.uniform(0.1, 1, n),
    ]))

    # Crowded environment
    n = scenarios['crowded']
    normal_chunks.append(np.column_stack([
        np.random.uniform(30, 120, n),
        np.random.uniform(5000, 15000, n),
        np.random.uniform(200, 700, n),
        np.random.uniform(-20, 10, n),
        np.random.uniform(5, 15, n),         # high frequency
    ]))

    # Outdoor open
    n = scenarios['outdoor']
    normal_chunks.append(np.column_stack([
        np.random.uniform(200, 400, n),
        np.random.uniform(200, 1500, n),
        np.random.uniform(800, 2000, n),     # bright sunlight
        np.random.uniform(-5, 5, n),
        np.random.uniform(0.1, 1.5, n),
    ]))

    normal_X = np.vstack(normal_chunks)
    # Add realistic sensor noise
    normal_X += np.random.normal(0, 0.5, normal_X.shape)

    # ── Anomaly scenarios ─────────────────────────────────────────────────────
    n_each = n_anomaly // 4

    anomaly_chunks = [
        # Sensor malfunction: impossible raw values
        np.column_stack([
            np.random.choice([0, 401, 450], n_each),          # out of range distance
            np.random.choice([0, 65535], n_each),              # VCNL max/min
            np.random.uniform(0, 50, n_each),                  # near-zero ambient
            np.random.uniform(-100, 100, n_each),              # extreme roc
            np.random.uniform(0, 1, n_each),
        ]),
        # Sudden spike: distance jumps wildly
        np.column_stack([
            np.random.uniform(350, 400, n_each),               # suddenly very far
            np.random.uniform(100, 500, n_each),               # proximity doesn't match
            np.random.uniform(200, 800, n_each),
            np.random.uniform(80, 200, n_each),                # extreme roc
            np.random.uniform(0, 1, n_each),
        ]),
        # Stuck sensor: near-zero rate of change with high detection count
        np.column_stack([
            np.random.uniform(100, 105, n_each),               # barely changes
            np.random.uniform(4990, 5010, n_each),             # barely changes
            np.random.uniform(390, 410, n_each),               # barely changes
            np.random.uniform(-0.1, 0.1, n_each),              # stuck
            np.random.uniform(20, 30, n_each),                 # but high count
        ]),
        # Physical impossibility: distance very close but proximity very low
        np.column_stack([
            np.random.uniform(10, 20, n_each),                 # very close
            np.random.uniform(100, 300, n_each),               # but proximity says far
            np.random.uniform(200, 800, n_each),
            np.random.uniform(-50, -40, n_each),
            np.random.uniform(10, 20, n_each),
        ]),
    ]

    anomaly_X = np.vstack(anomaly_chunks)

    X = np.vstack([normal_X, anomaly_X])
    idx = np.random.permutation(len(X))
    return X[idx]


# ─────────────────────────────────────────────────────────────────────────────
# TRAINING
# ─────────────────────────────────────────────────────────────────────────────

def train_model():
    print("=" * 60)
    print("Training Anomaly Detection Model (v2)")
    print("Features: distance_cm, proximity_value, ambient_light,")
    print("          rate_of_change, detection_count")
    print("=" * 60)

    X = load_training_data()
    print(f"✓ Total samples: {len(X)}")

    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print("✓ Scaled features")

    # Increased n_estimators for better anomaly boundary detection
    model = IsolationForest(
        contamination=0.05,
        n_estimators=200,        # up from 100
        max_samples='auto',
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_scaled)
    print("✓ Model trained")

    # Verification tests
    print("\n🧪 Verification tests:")
    tests = [
        ([150, 3000, 500,  -5,  2],  "Normal: walking in corridor"),
        ([250, 800,  1000, -3,  1],  "Normal: open space walking"),
        ([30,  15000, 300, -1,  0.5],"Normal: stationary near wall"),
        ([0,   65535, 10,  200, 0],  "Anomaly: sensor malfunction"),
        ([102, 5000,  400, 0,   25], "Anomaly: stuck sensor"),
        ([15,  200,   500, -45, 15], "Anomaly: physical impossibility"),
    ]
    for features, description in tests:
        sample     = np.array([features])
        scaled     = scaler.transform(sample)
        prediction = model.predict(scaled)[0]
        score      = model.decision_function(scaled)[0]
        result     = "🔴 ANOMALY" if prediction == -1 else "🟢 Normal"
        print(f"  {result} (score={score:.3f}) — {description}")

    # Save
    models_dir = Path(__file__).parent.parent / 'ml_models' / 'saved_models'
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / 'anomaly_detector.pkl'
    joblib.dump({'model': model, 'scaler': scaler}, model_path)
    print(f"\n✓ Saved to {model_path}")

    print("=" * 60)
    print("✅ Anomaly Detection Model Training Complete!")
    print("=" * 60)


if __name__ == '__main__':
    train_model()