"""
Train Environment Classification Model  (v3)

Features (must match ml_service.py classify_environment exactly):
  [0] ambient_light_avg
  [1] ambient_light_variance
  [2] detection_frequency
  [3] average_obstacle_distance
  [4] proximity_pattern_complexity
  [5] distance_variance

Classes: indoor, outdoor, crowded, open_space, narrow_corridor

v3 changes vs v2:
  - Real data fetch ENABLED (was commented out)
  - Blends real + synthetic proportionally
  - Why ml_predictions, NOT detection_logs?
      detection_logs stores raw per-detection rows. Environment classification
      needs AGGREGATED features: ambient_light_avg, detection_frequency,
      distance_variance — computed over many detections, not per-detection.
      These live as input_data JSON in ml_predictions.
      Use inject_training_data.py to populate them.
"""
import sys
import os
import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

sys.path.insert(0, str(Path(__file__).parent.parent))

ENV_TYPES  = ['indoor', 'outdoor', 'crowded', 'open_space', 'narrow_corridor']
LIGHTING   = ['bright', 'dim', 'dark']
COMPLEXITY = ['simple', 'moderate', 'complex']


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
            .eq('prediction_type', 'environment') \
            .order('created_at', desc=True) \
            .limit(5000) \
            .execute()
        return rows.data or []
    except Exception as e:
        print(f"  ⚠ Real data fetch failed: {e}")
        return []


def _prepare_real_data(rows):
    env_map = {e: i for i, e in enumerate(ENV_TYPES)}
    X, y = [], []
    for row in rows:
        try:
            inp    = row.get('input_data', {})
            result = row.get('prediction_result', {})
            env    = str(result.get('environment', 'indoor')).lower()
            if env not in env_map:
                continue
            # Derive lighting/complexity from stored result if available
            lighting_str   = str(result.get('lighting', 'bright')).lower()
            complexity_str = str(result.get('complexity', 'moderate')).lower()
            lighting_idx   = LIGHTING.index(lighting_str)   if lighting_str   in LIGHTING   else 0
            complexity_idx = COMPLEXITY.index(complexity_str) if complexity_str in COMPLEXITY else 1
            X.append([
                float(inp.get('ambient_light_avg',            400)),
                float(inp.get('ambient_light_variance',       50)),
                float(inp.get('detection_frequency',          2)),
                float(inp.get('average_obstacle_distance',    150)),
                float(inp.get('proximity_pattern_complexity', 5)),
                float(inp.get('distance_variance',            80)),
            ])
            y.append([env_map[env], lighting_idx, complexity_idx])
        except Exception:
            continue
    if not X:
        return np.array([]).reshape(0, 6), np.array([]).reshape(0, 3)
    return np.array(X), np.array(y)


def load_training_data(min_samples=200):
    """
    Try real data from ml_predictions first, blend with synthetic.
    """
    print("  Checking for real training data in ml_predictions...")
    real_rows      = _fetch_real_data()
    real_X, real_y = _prepare_real_data(real_rows)

    if len(real_X) >= min_samples:
        print(f"  ✓ Found {len(real_X)} real samples")
        syn_X, syn_y = generate_synthetic_data(max(1500, len(real_X)))
        X   = np.vstack([real_X, syn_X])
        y   = np.vstack([real_y, syn_y])
        idx = np.random.permutation(len(X))
        print(f"  ✓ Blended: {len(real_X)} real + {len(syn_X)} synthetic = {len(X)} total")
        return X[idx], y[idx]
    else:
        print(f"  ⚠ Only {len(real_X)} real samples (need {min_samples}) — using pure synthetic")
        return generate_synthetic_data()


# ─────────────────────────────────────────────────────────────────────────────
# SYNTHETIC DATA
# ─────────────────────────────────────────────────────────────────────────────

def generate_synthetic_data(n_samples=3000):
    np.random.seed(42)
    n_per_env = n_samples // len(ENV_TYPES)
    all_X, all_y = [], []

    for env_idx, env_name in enumerate(ENV_TYPES):
        n = n_per_env

        if env_name == 'indoor':
            amb_avg   = np.random.uniform(200,  700,  n)
            amb_var   = np.random.uniform(10,   80,   n)
            det_freq  = np.random.uniform(1,    6,    n)
            avg_dist  = np.random.uniform(60,   250,  n)
            complexity= np.random.uniform(3,    7,    n)
            dist_var  = np.random.uniform(30,   120,  n)
            lighting  = np.random.choice([0, 1], n, p=[0.65, 0.35])
            comp_lvl  = np.random.choice([0, 1, 2], n, p=[0.2, 0.6, 0.2])

        elif env_name == 'outdoor':
            amb_avg   = np.random.uniform(600,  2500, n)
            amb_var   = np.random.uniform(100,  600,  n)
            det_freq  = np.random.uniform(0.3,  3,    n)
            avg_dist  = np.random.uniform(100,  400,  n)
            complexity= np.random.uniform(1,    5,    n)
            dist_var  = np.random.uniform(80,   300,  n)
            lighting  = np.random.choice([0, 1], n, p=[0.85, 0.15])
            comp_lvl  = np.random.choice([0, 1], n, p=[0.65, 0.35])

        elif env_name == 'crowded':
            amb_avg   = np.random.uniform(150,  800,  n)
            amb_var   = np.random.uniform(20,   100,  n)
            det_freq  = np.random.uniform(6,    20,   n)
            avg_dist  = np.random.uniform(25,   120,  n)
            complexity= np.random.uniform(7,    10,   n)
            dist_var  = np.random.uniform(40,   150,  n)
            lighting  = np.random.choice([0, 1, 2], n, p=[0.45, 0.40, 0.15])
            comp_lvl  = np.random.choice([1, 2], n, p=[0.30, 0.70])

        elif env_name == 'open_space':
            amb_avg   = np.random.uniform(500,  2000, n)
            amb_var   = np.random.uniform(60,   350,  n)
            det_freq  = np.random.uniform(0.1,  1.5,  n)
            avg_dist  = np.random.uniform(200,  400,  n)
            complexity= np.random.uniform(1,    3,    n)
            dist_var  = np.random.uniform(80,   250,  n)
            lighting  = np.random.choice([0], n)
            comp_lvl  = np.random.choice([0], n)

        else:  # narrow_corridor
            amb_avg   = np.random.uniform(100,  450,  n)
            amb_var   = np.random.uniform(5,    35,   n)
            det_freq  = np.random.uniform(2,    8,    n)
            avg_dist  = np.random.uniform(30,   110,  n)
            complexity= np.random.uniform(4,    8,    n)
            dist_var  = np.random.uniform(15,   55,   n)
            lighting  = np.random.choice([0, 1, 2], n, p=[0.30, 0.50, 0.20])
            comp_lvl  = np.random.choice([1, 2], n, p=[0.50, 0.50])

        X = np.column_stack([amb_avg, amb_var, det_freq, avg_dist, complexity, dist_var])
        y = np.column_stack([np.full(n, env_idx), lighting, comp_lvl])
        X += np.random.normal(0, 0.3, X.shape)
        X  = np.clip(X, 0, None)
        all_X.append(X)
        all_y.append(y)

    X   = np.vstack(all_X)
    y   = np.vstack(all_y)
    idx = np.random.permutation(len(X))
    return X[idx], y[idx]


# ─────────────────────────────────────────────────────────────────────────────
# TRAINING
# ─────────────────────────────────────────────────────────────────────────────

def train_model():
    print("=" * 60)
    print("Training Environment Classification Model v3")
    print("Features: ambient_light_avg, ambient_light_variance,")
    print("          detection_frequency, average_obstacle_distance,")
    print("          proximity_pattern_complexity, distance_variance")
    print("=" * 60)

    X, y = load_training_data()
    print(f"✓ Total samples: {len(X)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    scaler         = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)
    print("✓ Scaled features")

    model = MultiOutputClassifier(
        RandomForestClassifier(n_estimators=200, max_depth=15,
                               class_weight='balanced', random_state=42, n_jobs=-1),
        n_jobs=-1
    )
    model.fit(X_train_scaled, y_train)
    print("✓ Model trained")

    y_pred = model.predict(X_test_scaled)
    for i, name in enumerate(['Environment Type', 'Lighting Condition', 'Complexity Level']):
        acc = accuracy_score(y_test[:, i], y_pred[:, i])
        print(f"  📊 {name}: {acc:.4f}")

    print("\n🧪 Verification tests:")
    tests = [
        ([400,  30,  3,   120, 5,  80],  "indoor"),
        ([1200, 300, 1,   250, 3,  200], "outdoor"),
        ([500,  60,  12,  60,  9,  80],  "crowded"),
        ([1500, 200, 0.5, 350, 2,  200], "open_space"),
        ([250,  15,  4,   60,  6,  30],  "narrow_corridor"),
    ]
    for features, expected in tests:
        pred     = model.predict(scaler.transform(np.array([features])))[0]
        env_pred = ENV_TYPES[int(pred[0])]
        match    = "✅" if env_pred == expected else "⚠️ "
        print(f"  {match} Expected={expected:16s} Got={env_pred}")

    models_dir = Path(__file__).parent.parent / 'ml_models' / 'saved_models'
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({'model': model, 'scaler': scaler,
                 'env_types': ENV_TYPES, 'lighting': LIGHTING,
                 'complexity': COMPLEXITY},
                models_dir / 'environment_classifier.pkl')
    print(f"\n✓ Saved to {models_dir / 'environment_classifier.pkl'}")
    print("=" * 60)
    print("✅ Environment Classification Model Training Complete!")
    print("=" * 60)


if __name__ == '__main__':
    train_model()