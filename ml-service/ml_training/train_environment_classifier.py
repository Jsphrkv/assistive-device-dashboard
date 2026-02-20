"""
Train Environment Classification Model
"""
import sys
import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_synthetic_data(n_samples=500):
    np.random.seed(42)
    samples_per_env = n_samples // 5
    all_X, all_y   = [], []

    for env_type in range(5):
        if env_type == 0:   # indoor
            ambient_light = np.random.uniform(200, 600,  samples_per_env)
            light_var     = np.random.uniform(10,  50,   samples_per_env)
            detect_freq   = np.random.uniform(1,   5,    samples_per_env)
            avg_dist      = np.random.uniform(50,  200,  samples_per_env)
            complexity    = np.random.uniform(3,   7,    samples_per_env)
            dist_var      = np.random.uniform(30,  100,  samples_per_env)
            lighting      = np.random.choice([0, 1], samples_per_env, p=[0.7, 0.3])
            complex_level = np.random.choice([0, 1, 2], samples_per_env, p=[0.2, 0.6, 0.2])
        elif env_type == 1: # outdoor
            ambient_light = np.random.uniform(500, 2000, samples_per_env)
            light_var     = np.random.uniform(100, 500,  samples_per_env)
            detect_freq   = np.random.uniform(0.5, 3,    samples_per_env)
            avg_dist      = np.random.uniform(100, 400,  samples_per_env)
            complexity    = np.random.uniform(2,   5,    samples_per_env)
            dist_var      = np.random.uniform(100, 300,  samples_per_env)
            lighting      = np.random.choice([0, 1], samples_per_env, p=[0.8, 0.2])
            complex_level = np.random.choice([0, 1], samples_per_env, p=[0.6, 0.4])
        elif env_type == 2: # crowded
            ambient_light = np.random.uniform(150, 700,  samples_per_env)
            light_var     = np.random.uniform(20,  80,   samples_per_env)
            detect_freq   = np.random.uniform(5,   15,   samples_per_env)
            avg_dist      = np.random.uniform(30,  150,  samples_per_env)
            complexity    = np.random.uniform(7,   10,   samples_per_env)
            dist_var      = np.random.uniform(50,  150,  samples_per_env)
            lighting      = np.random.choice([0, 1, 2], samples_per_env, p=[0.4, 0.4, 0.2])
            complex_level = np.random.choice([1, 2], samples_per_env, p=[0.3, 0.7])
        elif env_type == 3: # open_space
            ambient_light = np.random.uniform(400, 1500, samples_per_env)
            light_var     = np.random.uniform(80,  300,  samples_per_env)
            detect_freq   = np.random.uniform(0.2, 2,    samples_per_env)
            avg_dist      = np.random.uniform(150, 400,  samples_per_env)
            complexity    = np.random.uniform(1,   4,    samples_per_env)
            dist_var      = np.random.uniform(100, 250,  samples_per_env)
            lighting      = np.random.choice([0], samples_per_env)
            complex_level = np.random.choice([0], samples_per_env)
        else:               # narrow_corridor
            ambient_light = np.random.uniform(100, 400,  samples_per_env)
            light_var     = np.random.uniform(5,   30,   samples_per_env)
            detect_freq   = np.random.uniform(2,   8,    samples_per_env)
            avg_dist      = np.random.uniform(40,  120,  samples_per_env)
            complexity    = np.random.uniform(4,   8,    samples_per_env)
            dist_var      = np.random.uniform(20,  60,   samples_per_env)
            lighting      = np.random.choice([0, 1, 2], samples_per_env, p=[0.3, 0.5, 0.2])
            complex_level = np.random.choice([1, 2], samples_per_env, p=[0.5, 0.5])

        all_X.append(np.column_stack([ambient_light, light_var, detect_freq, avg_dist, complexity, dist_var]))
        all_y.append(np.column_stack([np.full(samples_per_env, env_type), lighting, complex_level]))

    X = np.vstack(all_X)
    y = np.vstack(all_y)
    idx = np.random.permutation(len(X))
    return X[idx], y[idx]


def train_model():
    print("=" * 60)
    print("Training Environment Classification Model")
    print("=" * 60)

    X, y = generate_synthetic_data()
    print(f"✓ Generated {len(X)} samples")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler         = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)
    print("✓ Scaled features")

    model = MultiOutputClassifier(
        RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1),
        n_jobs=-1
    )
    model.fit(X_train_scaled, y_train)
    print("✓ Model trained")

    y_pred = model.predict(X_test_scaled)
    for i, name in enumerate(['Environment Type', 'Lighting Condition', 'Complexity Level']):
        print(f"✓ {name} Accuracy: {accuracy_score(y_test[:, i], y_pred[:, i]):.4f}")

    # ── Fix: correct filename + save as dict with scaler ─────────────────────
    models_dir = Path(__file__).parent.parent / 'ml_models' / 'saved_models'
    models_dir.mkdir(parents=True, exist_ok=True)

    model_path = models_dir / 'environment_classifier.pkl'    # ← fixed name
    joblib.dump({'model': model, 'scaler': scaler}, model_path)
    print(f"\n✓ Model saved to {model_path}")

    print("=" * 60)
    print("✅ Environment Classification Model Training Complete!")
    print("=" * 60)


if __name__ == '__main__':
    train_model()