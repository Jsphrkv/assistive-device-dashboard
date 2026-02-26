"""
Train Environment Classification Model

Features (must match ml_service.py classify_environment exactly):
  [0] ambient_light_avg
  [1] ambient_light_variance
  [2] detection_frequency
  [3] average_obstacle_distance
  [4] proximity_pattern_complexity
  [5] distance_variance

Classes: indoor, outdoor, crowded, open_space, narrow_corridor

Improvements over v1:
  - 3000 samples (up from 500), 600 per environment
  - More realistic feature overlap between similar environments
  - Separate accuracy per output head
  - Real data fallback from ml_predictions
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

ENV_TYPES    = ['indoor', 'outdoor', 'crowded', 'open_space', 'narrow_corridor']
LIGHTING     = ['bright', 'dim', 'dark']
COMPLEXITY   = ['simple', 'moderate', 'complex']


# ─────────────────────────────────────────────────────────────────────────────
# REAL DATA (Supabase fallback)
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

            X.append([
                float(inp.get('ambient_light_avg',            400)),
                float(inp.get('ambient_light_variance',       50)),
                float(inp.get('detection_frequency',          2)),
                float(inp.get('average_obstacle_distance',    150)),
                float(inp.get('proximity_pattern_complexity', 5)),
                float(inp.get('distance_variance',            80)),
            ])
            # Lighting and complexity defaults when not stored
            y.append([env_map[env], 0, 1])
        except Exception:
            continue

    return np.array(X), np.array(y)


# def load_training_data(min_samples=200):
#     print("  Checking for real training data...")
#     real_rows      = _fetch_real_data()
#     real_X, real_y = _prepare_real_data(real_rows) if real_rows else (
#         np.array([]).reshape(0, 6), np.array([]).reshape(0, 3)
#     )

#     if len(real_X) >= min_samples:
#         print(f"  ✓ Using {len(real_X)} real samples from Supabase")
#         return real_X, real_y
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
    600 samples per environment, each with realistic sensor characteristics.
    Added realistic overlap between similar environments (indoor vs corridor).
    """
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
            det_freq  = np.random.uniform(6,    20,   n)   # high frequency
            avg_dist  = np.random.uniform(25,   120,  n)   # close obstacles
            complexity= np.random.uniform(7,    10,   n)   # high complexity
            dist_var  = np.random.uniform(40,   150,  n)
            lighting  = np.random.choice([0, 1, 2], n, p=[0.45, 0.40, 0.15])
            comp_lvl  = np.random.choice([1, 2], n, p=[0.30, 0.70])

        elif env_name == 'open_space':
            amb_avg   = np.random.uniform(500,  2000, n)
            amb_var   = np.random.uniform(60,   350,  n)
            det_freq  = np.random.uniform(0.1,  1.5,  n)   # very low frequency
            avg_dist  = np.random.uniform(200,  400,  n)   # far obstacles
            complexity= np.random.uniform(1,    3,    n)   # simple
            dist_var  = np.random.uniform(80,   250,  n)
            lighting  = np.random.choice([0], n)
            comp_lvl  = np.random.choice([0], n)

        else:  # narrow_corridor
            amb_avg   = np.random.uniform(100,  450,  n)
            amb_var   = np.random.uniform(5,    35,   n)   # very stable lighting
            det_freq  = np.random.uniform(2,    8,    n)
            avg_dist  = np.random.uniform(30,   110,  n)   # close walls
            complexity= np.random.uniform(4,    8,    n)
            dist_var  = np.random.uniform(15,   55,   n)   # low variance — consistent walls
            lighting  = np.random.choice([0, 1, 2], n, p=[0.30, 0.50, 0.20])
            comp_lvl  = np.random.choice([1, 2], n, p=[0.50, 0.50])

        X = np.column_stack([amb_avg, amb_var, det_freq, avg_dist, complexity, dist_var])
        y = np.column_stack([
            np.full(n, env_idx),
            lighting,
            comp_lvl,
        ])

        # Add sensor noise
        X += np.random.normal(0, 0.3, X.shape)
        X = np.clip(X, 0, None)

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
    print("Training Environment Classification Model v2")
    print("Features: ambient_light_avg, ambient_light_variance,")
    print("          detection_frequency, average_obstacle_distance,")
    print("          proximity_pattern_complexity, distance_variance")
    print("=" * 60)

    X, y = load_training_data()
    print(f"✓ Total samples: {len(X)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    scaler         = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)
    print("✓ Scaled features")

    model = MultiOutputClassifier(
        RandomForestClassifier(
            n_estimators=200,        # up from 100
            max_depth=15,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1,
        ),
        n_jobs=-1
    )
    model.fit(X_train_scaled, y_train)
    print("✓ Model trained")

    y_pred = model.predict(X_test_scaled)
    output_names = ['Environment Type', 'Lighting Condition', 'Complexity Level']
    for i, name in enumerate(output_names):
        acc = accuracy_score(y_test[:, i], y_pred[:, i])
        print(f"  📊 {name}: {acc:.4f}")

    # Verification
    print("\n🧪 Verification tests:")
    tests = [
        ([400,  30,  3,   120, 5,  80],  "indoor"),
        ([1200, 300, 1,   250, 3,  200], "outdoor"),
        ([500,  60,  12,  60,  9,  80],  "crowded"),
        ([1500, 200, 0.5, 350, 2,  200], "open_space"),
        ([250,  15,  4,   60,  6,  30],  "narrow_corridor"),
    ]
    for features, expected in tests:
        sample   = np.array([features])
        scaled   = scaler.transform(sample)
        pred     = model.predict(scaled)[0]
        env_pred = ENV_TYPES[int(pred[0])]
        match    = "✅" if env_pred == expected else "⚠️ "
        print(f"  {match} Expected={expected:16s} Got={env_pred}")

    # Save
    models_dir = Path(__file__).parent.parent / 'ml_models' / 'saved_models'
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / 'environment_classifier.pkl'
    joblib.dump({'model': model, 'scaler': scaler,
                 'env_types': ENV_TYPES, 'lighting': LIGHTING,
                 'complexity': COMPLEXITY}, model_path)
    print(f"\n✓ Saved to {model_path}")

    print("=" * 60)
    print("✅ Environment Classification Model Training Complete!")
    print("=" * 60)


if __name__ == '__main__':
    train_model()