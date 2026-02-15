import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from app.ml_training.utils import (
    DataPreprocessor, ModelEvaluator, ModelSaver, generate_synthetic_data
)

def train_environment_classifier_model(data_path=None, use_synthetic=True):
    """
    Train environment classification model
    Classifies environment type, lighting, and complexity from sensor patterns
    
    Args:
        data_path: Path to CSV file with training data
        use_synthetic: Generate synthetic data if no file provided
    """
    print("="*60)
    print("ENVIRONMENT CLASSIFICATION MODEL TRAINING")
    print("="*60)
    
    # Load or generate data
    if use_synthetic or data_path is None:
        print("\n📊 Generating synthetic training data...")
        df = generate_synthetic_data(n_samples=5000, dataset_type='environment_classification')
        print(f"✓ Generated {len(df)} samples")
    else:
        print(f"\n📊 Loading data from: {data_path}")
        df = pd.read_csv(data_path)
        print(f"✓ Loaded {len(df)} samples")
    
    # Display data info
    print(f"\n📋 Dataset Info:")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Shape: {df.shape}")
    
    # Define features
    feature_columns = [
        'ambient_light_avg',
        'ambient_light_variance',
        'detection_frequency',
        'average_obstacle_distance',
        'proximity_pattern_complexity',
        'distance_variance'
    ]
    
    # Three target columns (multi-output classification)
    target_columns = [
        'environment_type',     # indoor/outdoor/crowded/open/corridor
        'lighting_condition',   # bright/dim/dark
        'complexity_level'      # simple/moderate/complex
    ]
    
    print(f"\n🔧 Feature columns: {feature_columns}")
    print(f"🎯 Target columns: {target_columns}")
    
    # Prepare data
    print("\n⚙️  Preprocessing data...")
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    
    preprocessor = DataPreprocessor()
    
    X = df[feature_columns]
    
    # Encode each target separately
    encoders = {}
    y_encoded = {}
    
    for target in target_columns:
        encoder = LabelEncoder()
        y_encoded[target] = encoder.fit_transform(df[target])
        encoders[target] = encoder
        print(f"   {target} classes: {encoder.classes_}")
    
    # Combine targets into matrix
    y = np.column_stack([y_encoded[target] for target in target_columns])
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Scale features
    X_train_scaled = preprocessor.scaler.fit_transform(X_train)
    X_test_scaled = preprocessor.scaler.transform(X_test)
    
    print(f"\n✓ Training set: {X_train_scaled.shape}")
    print(f"✓ Test set: {X_test_scaled.shape}")
    print(f"✓ Targets: {y.shape}")
    
    # Train Multi-Output Random Forest
    print("\n🤖 Training Multi-Output Random Forest Classifier...")
    base_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    model = MultiOutputClassifier(base_model, n_jobs=-1)
    model.fit(X_train_scaled, y_train)
    print("✓ Model training complete!")
    
    # Evaluate model
    print("\n📊 Evaluating model performance...")
    y_pred = model.predict(X_test_scaled)
    
    from sklearn.metrics import accuracy_score, classification_report
    
    for i, target in enumerate(target_columns):
        accuracy = accuracy_score(y_test[:, i], y_pred[:, i])
        print(f"\n📈 {target.upper()} Performance:")
        print(f"   Accuracy: {accuracy:.4f}")
        print(f"\n   Classification Report:")
        print(classification_report(
            y_test[:, i],
            y_pred[:, i],
            target_names=encoders[target].classes_,
            zero_division=0
        ))
    
    # Overall accuracy
    overall_accuracy = np.mean([
        accuracy_score(y_test[:, i], y_pred[:, i]) 
        for i in range(len(target_columns))
    ])
    print(f"\n📊 Overall Average Accuracy: {overall_accuracy:.4f}")
    
    # Feature importance (from first output)
    print("\n📈 Feature Importance:")
    first_estimator = model.estimators_[0]
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': first_estimator.feature_importances_
    }).sort_values('importance', ascending=False)
    print(feature_importance.to_string(index=False))
    
    # Save model with encoders
    print("\n💾 Saving model...")
    
    model_with_encoders = {
        'model': model,
        'encoders': encoders
    }
    
    metrics = {
        'overall_accuracy': overall_accuracy,
        'individual_accuracies': {
            target: accuracy_score(y_test[:, i], y_pred[:, i])
            for i, target in enumerate(target_columns)
        }
    }
    
    ModelSaver.save_model(
        model=model_with_encoders,
        scaler=preprocessor.scaler,
        model_name='environment_classifier_model',
        metrics=metrics
    )
    
    print("\n✅ Environment classification model training complete!")
    print("="*60)
    
    return model_with_encoders, preprocessor.scaler, metrics


if __name__ == "__main__":
    # Train the model
    model, scaler, metrics = train_environment_classifier_model(use_synthetic=True)
    
    # Test prediction
    print("\n🧪 Testing prediction on sample data...")
    
    # Test cases
    test_cases = [
        {
            'name': 'Bright outdoor open space',
            'data': np.array([[800, 100, 0.5, 500, 2, 200]])  # High light, low variance, few detections
        },
        {
            'name': 'Dark indoor corridor',
            'data': np.array([[150, 50, 5.0, 100, 8, 50]])  # Low light, high detection freq, narrow
        },
        {
            'name': 'Crowded indoor area',
            'data': np.array([[400, 200, 10.0, 80, 15, 30]])  # Medium light, very high detection freq
        },
        {
            'name': 'Dim outdoor area',
            'data': np.array([[250, 150, 2.0, 300, 5, 100]])  # Medium-low light, moderate detections
        }
    ]
    
    for test_case in test_cases:
        test_sample = test_case['data']
        test_sample_scaled = scaler.transform(test_sample.reshape(1, -1))
        
        # Get predictions
        predictions = model['model'].predict(test_sample_scaled)[0]
        
        # Decode predictions
        environment_type = model['encoders']['environment_type'].inverse_transform([predictions[0]])[0]
        lighting = model['encoders']['lighting_condition'].inverse_transform([predictions[1]])[0]
        complexity = model['encoders']['complexity_level'].inverse_transform([predictions[2]])[0]
        
        # Get probabilities (average across all estimators)
        env_probs = np.mean([est.predict_proba(test_sample_scaled)[0] for est in model['model'].estimators_[0].estimators_], axis=0)
        confidence = float(np.max(env_probs))
        
        print(f"\n{test_case['name']}:")
        print(f"  Ambient light avg: {test_sample[0]:.0f}")
        print(f"  Detection frequency: {test_sample[2]:.1f}/min")
        print(f"  Average distance: {test_sample[3]:.0f}cm")
        print(f"\n  Predictions:")
        print(f"    Environment: {environment_type}")
        print(f"    Lighting: {lighting}")
        print(f"    Complexity: {complexity}")
        print(f"    Confidence: {confidence:.2%}")