import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from app.ml_training.utils import (
    DataPreprocessor, ModelEvaluator, ModelSaver, generate_synthetic_data
)

def train_activity_model(data_path=None, use_synthetic=True):
    """
    Train activity recognition model
    
    Args:
        data_path: Path to CSV file with training data
        use_synthetic: Generate synthetic data if no file provided
    """
    print("="*60)
    print("ACTIVITY RECOGNITION MODEL TRAINING")
    print("="*60)
    
    # Load or generate data
    if use_synthetic or data_path is None:
        print("\n📊 Generating synthetic training data...")
        df = generate_synthetic_data(n_samples=5000, dataset_type='activity')
        print(f"✓ Generated {len(df)} samples")
    else:
        print(f"\n📊 Loading data from: {data_path}")
        df = pd.read_csv(data_path)
        print(f"✓ Loaded {len(df)} samples")
    
    # Display data info
    print(f"\n📋 Dataset Info:")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Shape: {df.shape}")
    print(f"\n   Activity distribution:")
    print(df['activity'].value_counts())
    
    # Define features
    feature_columns = [col for col in df.columns if col != 'activity']
    target_column = 'activity'
    
    print(f"\n🔧 Feature columns: {feature_columns}")
    
    # Prepare data
    print("\n⚙️  Preprocessing data...")
    preprocessor = DataPreprocessor()
    X_train, X_test, y_train, y_test = preprocessor.prepare_multiclass_features(
        df, feature_columns, target_column
    )
    
    print(f"✓ Training set: {X_train.shape}")
    print(f"✓ Test set: {X_test.shape}")
    print(f"✓ Classes: {preprocessor.label_encoder.classes_}")
    
    # Train Random Forest model
    print("\n🤖 Training Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    print("✓ Model training complete!")
    
    # Evaluate model
    print("\n📊 Evaluating model performance...")
    evaluator = ModelEvaluator()
    metrics = evaluator.evaluate_multiclass_classifier(
        model, X_test, y_test, 
        preprocessor.label_encoder,
        model_name="Activity Recognition Random Forest"
    )
    
    # Feature importance
    print("\n📈 Feature Importance:")
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    print(feature_importance.to_string(index=False))
    
    # Save model
    print("\n💾 Saving model...")
    ModelSaver.save_model(
        model=model,
        scaler=preprocessor.scaler,
        model_name='activity_model',
        metrics=metrics,
        label_encoder=preprocessor.label_encoder
    )
    
    print("\n✅ Activity recognition model training complete!")
    print("="*60)
    
    return model, preprocessor.scaler, preprocessor.label_encoder, metrics


if __name__ == "__main__":
    # Train the model
    model, scaler, label_encoder, metrics = train_activity_model(use_synthetic=True)
    
    # Test prediction
    print("\n🧪 Testing prediction on sample data...")
    test_sample = np.array([[0.2, 0.3, 0.1, 0.05, 0.02, 0.01]])  # Resting pattern
    test_sample_scaled = scaler.transform(test_sample)
    prediction_encoded = model.predict(test_sample_scaled)[0]
    prediction = label_encoder.inverse_transform([prediction_encoded])[0]
    probabilities = model.predict_proba(test_sample_scaled)[0]
    
    print(f"Sample: {test_sample[0]}")
    print(f"Predicted Activity: {prediction}")
    print(f"Probabilities:")
    for i, activity in enumerate(label_encoder.classes_):
        print(f"  {activity}: {probabilities[i]:.3f}")