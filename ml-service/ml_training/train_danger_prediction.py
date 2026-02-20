"""
Train Danger Prediction Model
"""
import sys
import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_synthetic_data(n_samples=600):
    np.random.seed(42)

    X = np.column_stack([
        np.random.uniform(10, 400,   n_samples),   # distance_cm
        np.random.uniform(-50, 10,   n_samples),   # rate_of_change
        np.random.uniform(500, 20000, n_samples),  # proximity_value
        np.random.randint(0, 7,      n_samples),   # object_type
        np.random.uniform(0.5, 2.0,  n_samples),   # current_speed_estimate
    ])

    distance_factor = 1 - (X[:, 0] / 400)
    approach_factor = np.abs(X[:, 1]) / 50
    speed_factor    = X[:, 4] / 2

    danger_score  = (distance_factor * 50 + approach_factor * 30 + speed_factor * 20).clip(0, 100)
    danger_score += np.random.normal(0, 5, n_samples)
    danger_score  = danger_score.clip(0, 100)

    return X, danger_score


def train_model():
    print("=" * 60)
    print("Training Danger Prediction Model")
    print("=" * 60)

    X, y_score = generate_synthetic_data()
    print(f"✓ Generated {len(X)} samples")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_score, test_size=0.2, random_state=42
    )

    scaler         = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)
    print("✓ Scaled features")

    # ── Only score model needed — ml_service derives action from score ────────
    model = GradientBoostingRegressor(
        n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42
    )
    model.fit(X_train_scaled, y_train)
    print("✓ Model trained")

    y_pred = model.predict(X_test_scaled)
    print(f"\n📊 Performance:")
    print(f"   MSE: {mean_squared_error(y_test, y_pred):.4f}")
    print(f"   MAE: {mean_absolute_error(y_test, y_pred):.4f}")
    print(f"   R²:  {r2_score(y_test, y_pred):.4f}")

    # ── Fix: correct filename + save as dict with scaler ─────────────────────
    models_dir = Path(__file__).parent.parent / 'ml_models' / 'saved_models'
    models_dir.mkdir(parents=True, exist_ok=True)

    model_path = models_dir / 'danger_predictor.pkl'           # ← fixed name
    joblib.dump({'model': model, 'scaler': scaler}, model_path)
    print(f"\n✓ Model saved to {model_path}")

    # Test
    test_sample = np.array([[25, -50, 9500, 1, 2.0]])
    test_scaled = scaler.transform(test_sample)
    danger      = model.predict(test_scaled)[0]
    action      = 'STOP' if danger > 80 else 'SLOW_DOWN' if danger > 60 else 'CAUTION' if danger > 30 else 'SAFE'
    print(f"✓ Test prediction: Danger Score={danger:.1f}, Action={action}")

    print("=" * 60)
    print("✅ Danger Prediction Model Training Complete!")
    print("=" * 60)


if __name__ == '__main__':
    train_model()