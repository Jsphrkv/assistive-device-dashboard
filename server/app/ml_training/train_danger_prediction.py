import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.multioutput import MultiOutputRegressor
from app.ml_training.utils import (
    DataPreprocessor, ModelEvaluator, ModelSaver, generate_synthetic_data
)

def train_danger_prediction_model(data_path=None, use_synthetic=True):
    """
    Train danger prediction model
    Predicts danger score and recommended action based on sensor data
    
    Args:
        data_path: Path to CSV file with training data
        use_synthetic: Generate synthetic data if no file provided
    """
    print("="*60)
    print("DANGER PREDICTION MODEL TRAINING")
    print("="*60)
    
    # Load or generate data
    if use_synthetic or data_path is None:
        print("\n📊 Generating synthetic training data...")
        df = generate_synthetic_data(n_samples=5000, dataset_type='danger_prediction')
        print(f"✓ Generated {len(df)} samples")
    else:
        print(f"\n📊 Loading data from: {data_path}")
        df = pd.read_csv(data_path)
        print(f"✓ Loaded {len(df)} samples")
    
    # Display data info
    print(f"\n📋 Dataset Info:")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Shape: {df.shape}")
    
    # Define features and target
    feature_columns = [
        'distance_cm',
        'rate_of_change',
        'proximity_value',
        'object_type_encoded',
        'current_speed_estimate'
    ]
    
    # We'll train two models: one for danger_score (regression), one for recommended_action (classification)
    target_danger_score = 'danger_score'
    target_action = 'recommended_action'
    
    print(f"\n🔧 Feature columns: {feature_columns}")
    print(f"🎯 Targets: {target_danger_score}, {target_action}")
    
    # Prepare data for danger score (regression)
    print("\n⚙️  Preprocessing data...")
    preprocessor = DataPreprocessor()
    
    from sklearn.model_selection import train_test_split
    X = df[feature_columns]
    y_score = df[target_danger_score]
    y_action = df[target_action]
    
    X_train, X_test, y_score_train, y_score_test, y_action_train, y_action_test = train_test_split(
        X, y_score, y_action, test_size=0.2, random_state=42
    )
    
    # Scale features
    X_train_scaled = preprocessor.scaler.fit_transform(X_train)
    X_test_scaled = preprocessor.scaler.transform(X_test)
    
    print(f"✓ Training set: {X_train_scaled.shape}")
    print(f"✓ Test set: {X_test_scaled.shape}")
    
    # Train Danger Score Model (Regression)
    print("\n🤖 Training Danger Score Predictor (Gradient Boosting Regressor)...")
    score_model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        subsample=0.8,
        random_state=42
    )
    
    score_model.fit(X_train_scaled, y_score_train)
    print("✓ Danger score model training complete!")
    
    # Evaluate regression model
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    
    y_score_pred = score_model.predict(X_test_scaled)
    mse = mean_squared_error(y_score_test, y_score_pred)
    mae = mean_absolute_error(y_score_test, y_score_pred)
    r2 = r2_score(y_score_test, y_score_pred)
    
    print(f"\n📊 Danger Score Model Performance:")
    print(f"   MSE: {mse:.4f}")
    print(f"   MAE: {mae:.4f}")
    print(f"   R²: {r2:.4f}")
    
    # Train Recommended Action Model (Classification)
    print("\n🤖 Training Action Recommender (Gradient Boosting Classifier)...")
    
    # Encode actions
    from sklearn.preprocessing import LabelEncoder
    action_encoder = LabelEncoder()
    y_action_encoded_train = action_encoder.fit_transform(y_action_train)
    y_action_encoded_test = action_encoder.transform(y_action_test)
    
    action_model = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        subsample=0.8,
        random_state=42
    )
    
    action_model.fit(X_train_scaled, y_action_encoded_train)
    print("✓ Action model training complete!")
    
    # Evaluate classification model
    from sklearn.metrics import accuracy_score, classification_report
    
    y_action_pred = action_model.predict(X_test_scaled)
    accuracy = accuracy_score(y_action_encoded_test, y_action_pred)
    
    print(f"\n📊 Action Recommender Performance:")
    print(f"   Accuracy: {accuracy:.4f}")
    print(f"\n   Classification Report:")
    print(classification_report(
        y_action_encoded_test, 
        y_action_pred,
        target_names=action_encoder.classes_
    ))
    
    # Feature importance (from score model)
    print("\n📈 Feature Importance (Danger Score):")
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': score_model.feature_importances_
    }).sort_values('importance', ascending=False)
    print(feature_importance.to_string(index=False))
    
    # Combine both models into a single object
    combined_model = {
        'score_model': score_model,
        'action_model': action_model,
        'action_encoder': action_encoder
    }
    
    # Save both models
    print("\n💾 Saving models...")
    
    metrics = {
        'score_mse': mse,
        'score_mae': mae,
        'score_r2': r2,
        'action_accuracy': accuracy
    }
    
    ModelSaver.save_model(
        model=combined_model,
        scaler=preprocessor.scaler,
        model_name='danger_prediction_model',
        metrics=metrics
    )
    
    print("\n✅ Danger prediction model training complete!")
    print("="*60)
    
    return combined_model, preprocessor.scaler, metrics


if __name__ == "__main__":
    # Train the model
    model, scaler, metrics = train_danger_prediction_model(use_synthetic=True)
    
    # Test prediction
    print("\n🧪 Testing prediction on sample data...")
    
    # Test cases
    test_cases = [
        {
            'name': 'CRITICAL: Very close obstacle approaching fast',
            'data': np.array([[25.0, -50.0, 9500, 1, 3.0]])  # 25cm, closing fast, person, moving
        },
        {
            'name': 'HIGH: Close obstacle, moderate approach',
            'data': np.array([[80.0, -20.0, 8000, 0, 1.5]])  # 80cm, closing, obstacle, slow
        },
        {
            'name': 'MEDIUM: Medium distance, slow approach',
            'data': np.array([[150.0, -5.0, 5000, 2, 1.0]])  # 150cm, slow closing, vehicle
        },
        {
            'name': 'LOW: Far obstacle, moving away',
            'data': np.array([[300.0, 10.0, 2000, 0, 0.5]])  # 300cm, moving away
        }
    ]
    
    for test_case in test_cases:
        test_sample = test_case['data']
        test_sample_scaled = scaler.transform(test_sample)
        
        # Get danger score
        danger_score = model['score_model'].predict(test_sample_scaled)[0]
        
        # Get recommended action
        action_encoded = model['action_model'].predict(test_sample_scaled)[0]
        recommended_action = model['action_encoder'].inverse_transform([action_encoded])[0]
        
        # Calculate time to collision (simple estimate)
        distance = test_sample[0][0]
        speed = abs(test_sample[0][1])  # rate of change
        if speed > 0:
            time_to_collision = distance / speed
        else:
            time_to_collision = 999
        
        print(f"\n{test_case['name']}:")
        print(f"  Distance: {test_sample[0][0]:.0f}cm")
        print(f"  Rate of change: {test_sample[0][1]:.1f}cm/s")
        print(f"  Danger Score: {danger_score:.1f}/100")
        print(f"  Recommended Action: {recommended_action}")
        print(f"  Time to collision: {time_to_collision:.1f}s")