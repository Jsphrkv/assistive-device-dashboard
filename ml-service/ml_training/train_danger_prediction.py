"""
Train Danger Prediction Model — 4 features version

Features (must match ml_service.py predict_danger exactly):
  [0] distance_cm           — how far the obstacle is
  [1] rate_of_change        — cm/s, negative = approaching
  [2] proximity_value       — VCNL4010 raw reading
  [3] current_speed_estimate — estimated walking speed m/s

NOTE: object_type is intentionally excluded from training.
      It is applied as a risk_mult AFTER inference in ml_service.py
      so the scaler does not need to be retrained when new object
      types are added. This keeps the feature count stable at 4.
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


def generate_synthetic_data(n_samples=800):
    """
    Generate realistic synthetic sensor readings and danger scores.

    Feature ranges match what the Pi actually sends:
      distance_cm          : 10–400 cm  (ultrasonic range)
      rate_of_change       : -50 to +10 cm/s (negative = approaching)
      proximity_value      : 500–20000  (VCNL4010 raw)
      current_speed_estimate: 0.5–2.0  m/s (slow walk to fast walk)
    """
    np.random.seed(42)

    distance  = np.random.uniform(10,  400,   n_samples)   # cm
    roc       = np.random.uniform(-50, 10,    n_samples)   # cm/s
    proximity = np.random.uniform(500, 20000, n_samples)   # VCNL raw
    speed     = np.random.uniform(0.5, 2.0,   n_samples)   # m/s

    X = np.column_stack([distance, roc, proximity, speed])

    # Danger score formula — mirrors _danger_score() fallback in ml_service.py
    # so the model learns the same signal the fallback would produce, but
    # with the added nuance of rate_of_change and speed contributions.
    distance_factor  = np.clip(1 - (distance / 400), 0, 1)  # closer = more danger
    approach_factor  = np.clip(np.abs(np.minimum(roc, 0)) / 50, 0, 1)  # faster approach = more danger
    proximity_factor = np.clip(proximity / 20000, 0, 1)  # higher proximity = closer object
    speed_factor     = np.clip(speed / 2.0, 0, 1)  # faster walk = more danger

    danger_score = (
        distance_factor  * 50 +
        approach_factor  * 30 +
        proximity_factor * 10 +
        speed_factor     * 10
    ).clip(0, 100)

    # Add realistic noise
    danger_score += np.random.normal(0, 3, n_samples)
    danger_score  = danger_score.clip(0, 100)

    return X, danger_score


def train_model():
    print("=" * 60)
    print("Training Danger Prediction Model (4 features)")
    print("Features: distance_cm, rate_of_change, proximity_value,")
    print("          current_speed_estimate")
    print("=" * 60)

    X, y = generate_synthetic_data()
    print(f"✓ Generated {len(X)} samples")
    print(f"  Feature shape: {X.shape}  ← must be (N, 4)")
    print(f"  Danger score range: {y.min():.1f} – {y.max():.1f}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Scaler fitted on exactly 4 features — this is what ml_service.py sends
    scaler         = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)
    print(f"✓ Scaler fitted on {scaler.n_features_in_} features")  # should print 4

    model = GradientBoostingRegressor(
        n_estimators=150,
        learning_rate=0.08,
        max_depth=5,
        subsample=0.8,
        random_state=42
    )
    model.fit(X_train_scaled, y_train)
    print("✓ Model trained")

    y_pred = model.predict(X_test_scaled)
    print(f"\n📊 Performance:")
    print(f"   MSE : {mean_squared_error(y_test, y_pred):.4f}")
    print(f"   MAE : {mean_absolute_error(y_test, y_pred):.4f}")
    print(f"   R²  : {r2_score(y_test, y_pred):.4f}")

    # Save
    models_dir = Path(__file__).parent.parent / 'ml_models' / 'saved_models'
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / 'danger_predictor.pkl'
    joblib.dump({'model': model, 'scaler': scaler}, model_path)
    print(f"\n✓ Saved to {model_path}")

    # Verify — simulate what ml_service.py sends
    print("\n🧪 Verification tests:")
    tests = [
        ([25,  -30, 15000, 1.5], "Very close + approaching fast → should be HIGH"),
        ([250, -5,  3000,  1.0], "Medium distance, slow approach → should be MEDIUM"),
        ([380, 0,   800,   0.8], "Far away, not approaching → should be LOW/SAFE"),
        ([15,  -50, 19000, 2.0], "Critical: very close, fast approach → should be STOP"),
    ]
    for features, description in tests:
        sample  = np.array([features])
        scaled  = scaler.transform(sample)
        score   = model.predict(scaled)[0]
        action  = ('STOP' if score > 80 else 'SLOW_DOWN' if score > 60
                   else 'CAUTION' if score > 30 else 'SAFE')
        print(f"   {description}")
        print(f"   → score={score:.1f}, action={action}")
        print()

    print("=" * 60)
    print("✅ Danger Prediction Model Training Complete!")
    print(f"   Scaler expects: {scaler.n_features_in_} features")
    print(f"   ml_service.py sends: 4 features")
    print(f"   Match: {'✅ YES' if scaler.n_features_in_ == 4 else '❌ NO — something is wrong'}")
    print("=" * 60)


if __name__ == '__main__':
    train_model()