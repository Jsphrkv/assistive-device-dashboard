"""
Train Danger Prediction Model
"""
import sys
import os
import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).parent.parent))

def generate_synthetic_data(n_samples=600):
    """Generate synthetic danger prediction data"""
    np.random.seed(42)
    
    # Features: distance_cm, rate_of_change, proximity_value, object_type, speed
    X = np.column_stack([
        np.random.uniform(10, 400, n_samples),      # distance_cm
        np.random.uniform(-50, 10, n_samples),      # rate_of_change (usually approaching)
        np.random.uniform(500, 20000, n_samples),   # proximity_value
        np.random.randint(0, 7, n_samples),         # object_type (0-6)
        np.random.uniform(0.5, 2.0, n_samples),     # current_speed_estimate
    ])
    
    # Calculate danger score based on distance, speed, and rate
    distance_factor = 1 - (X[:, 0] / 400)  # Closer = more dangerous
    approach_factor = np.abs(X[:, 1]) / 50  # Faster approach = more dangerous
    speed_factor = X[:, 4] / 2  # Faster speed = more dangerous
    
    danger_score = (
        distance_factor * 50 +
        approach_factor * 30 +
        speed_factor * 20
    ).clip(0, 100)
    
    # Add noise
    danger_score += np.random.normal(0, 5, n_samples)
    danger_score = danger_score.clip(0, 100)
    
    # Determine recommended action based on danger score
    # 0=SAFE, 1=CAUTION, 2=SLOW_DOWN, 3=STOP
    recommended_action = np.digitize(danger_score, bins=[0, 30, 60, 80, 100]) - 1
    recommended_action = recommended_action.clip(0, 3)
    
    return X, danger_score, recommended_action

def train_model():
    """Train and save danger prediction model"""
    print("=" * 60)
    print("Training Danger Prediction Model")
    print("=" * 60)
    
    # Generate data
    X, y_score, y_action = generate_synthetic_data()
    print(f"✓ Generated {len(X)} samples")
    
    # Split data
    X_train, X_test, y_score_train, y_score_test, y_action_train, y_action_test = train_test_split(
        X, y_score, y_action, test_size=0.2, random_state=42
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print("✓ Scaled features")
    
    # Train danger score model (regression)
    print("\n🤖 Training Danger Score Model...")
    score_model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42
    )
    score_model.fit(X_train_scaled, y_score_train)
    print("✓ Score model trained")
    
    # Evaluate score model
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    y_score_pred = score_model.predict(X_test_scaled)
    mse = mean_squared_error(y_score_test, y_score_pred)
    mae = mean_absolute_error(y_score_test, y_score_pred)
    r2 = r2_score(y_score_test, y_score_pred)
    
    print(f"\n📊 Danger Score Performance:")
    print(f"   MSE: {mse:.4f}")
    print(f"   MAE: {mae:.4f}")
    print(f"   R²: {r2:.4f}")
    
    # Train action model (classification)
    print("\n🤖 Training Action Recommender...")
    action_model = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42
    )
    action_model.fit(X_train_scaled, y_action_train)
    print("✓ Action model trained")
    
    # Evaluate action model
    from sklearn.metrics import accuracy_score
    y_action_pred = action_model.predict(X_test_scaled)
    accuracy = accuracy_score(y_action_test, y_action_pred)
    
    print(f"\n📊 Action Recommender Performance:")
    print(f"   Accuracy: {accuracy:.4f}")
    
    # Save both models
    models_dir = Path(__file__).parent.parent / 'ml_models' / 'saved_models'
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / 'danger_prediction_model.joblib'
    joblib.dump({
        'score_model': score_model,
        'action_model': action_model,
        'scaler': scaler
    }, model_path)
    print(f"\n✓ Model saved to {model_path}")
    
    # Test prediction
    test_sample = [[25, -50, 9500, 1, 3.0]]  # Close, fast approach, person
    test_scaled = scaler.transform(test_sample)
    
    danger = score_model.predict(test_scaled)[0]
    action = action_model.predict(test_scaled)[0]
    actions = ['SAFE', 'CAUTION', 'SLOW_DOWN', 'STOP']
    
    print(f"\n✓ Test prediction: Danger Score={danger:.1f}, Action={actions[action]}")
    
    print("=" * 60)
    print("✅ Danger Prediction Model Training Complete!")
    print("=" * 60)

if __name__ == '__main__':
    train_model()