import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from app.ml_training.utils import (
    DataPreprocessor, ModelEvaluator, ModelSaver, generate_synthetic_data
)
# from app.ml_training.data_generators import SyntheticDataGenerator

def train_anomaly_model(data_path=None, use_synthetic=True):
    """
    Train anomaly detection model
    
    Args:
        data_path: Path to CSV file with training data
        use_synthetic: Generate synthetic data if no file provided
    """
    print("="*60)
    print("ANOMALY DETECTION MODEL TRAINING")
    print("="*60)
    
    # Load or generate data
    if use_synthetic or data_path is None:
        print("\n📊 Generating synthetic training data...")
        df = generate_synthetic_data(n_samples=5000, dataset_type='anomaly')
        print(f"✓ Generated {len(df)} samples")
    else:
        print(f"\n📊 Loading data from: {data_path}")
        df = pd.read_csv(data_path)
        print(f"✓ Loaded {len(df)} samples")
    
    # Display data info
    print(f"\n📋 Dataset Info:")
    print(f"   Columns: {list(df.columns)}")
    print(f"   Shape: {df.shape}")
    print(f"\n   Anomaly distribution:")
    print(df['is_anomaly'].value_counts())
    print(f"   Anomaly rate: {df['is_anomaly'].mean()*100:.2f}%")
    
    # Define features
    feature_columns = [col for col in df.columns if col != 'is_anomaly']
    target_column = 'is_anomaly'
    
    print(f"\n🔧 Feature columns: {feature_columns}")
    
    # Prepare data
    print("\n⚙️  Preprocessing data...")
    preprocessor = DataPreprocessor()
    X_train, X_test, y_train, y_test = preprocessor.prepare_features(
        df, feature_columns, target_column, handle_imbalance=True
    )
    
    print(f"✓ Training set: {X_train.shape}")
    print(f"✓ Test set: {X_test.shape}")
    
    # Train XGBoost model
    print("\n🤖 Training XGBoost model...")
    model = XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss',
        scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum()  # Handle imbalance
    )
    
    model.fit(X_train, y_train, verbose=False)
    print("✓ Model training complete!")
    
    # Evaluate model
    print("\n📊 Evaluating model performance...")
    evaluator = ModelEvaluator()
    metrics = evaluator.evaluate_binary_classifier(
        model, X_test, y_test, model_name="Anomaly Detection XGBoost"
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
        model_name='anomaly_model',
        metrics=metrics
    )
    
    print("\n✅ Anomaly detection model training complete!")
    print("="*60)
    
    return model, preprocessor.scaler, metrics


if __name__ == "__main__":
    # Train the model
    model, scaler, metrics = train_anomaly_model(use_synthetic=True)
    
    # Test prediction
    print("\n🧪 Testing prediction on sample data...")
    test_sample = np.array([[37.2, 78, 85, -50, 8]])  # Normal values
    test_sample_scaled = scaler.transform(test_sample)
    prediction = model.predict(test_sample_scaled)[0]
    probability = model.predict_proba(test_sample_scaled)[0]
    
    print(f"Sample: {test_sample[0]}")
    print(f"Prediction: {'ANOMALY' if prediction == 1 else 'NORMAL'}")
    print(f"Probability: {probability}")