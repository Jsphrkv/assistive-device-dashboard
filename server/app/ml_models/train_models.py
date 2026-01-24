"""
Train all ML models for the assistive device dashboard
"""
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import IsolationForest, RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from data_generators import SyntheticDataGenerator

def train_anomaly_detector():
    """Train anomaly detection model using Isolation Forest"""
    print("\n" + "="*60)
    print("Training Anomaly Detection Model")
    print("="*60)
    
    # Generate data
    df = SyntheticDataGenerator.generate_device_telemetry(n_samples=2000, anomaly_ratio=0.05)
    
    # Features for training
    features = ['battery_level', 'usage_duration', 'temperature', 'signal_strength', 'error_count']
    X = df[features]
    y = df['is_anomaly']
    
    print(f"Training data: {len(df)} samples")
    print(f"Normal: {(y == 0).sum()}, Anomalies: {(y == 1).sum()}")
    
    # Train Isolation Forest (unsupervised, but we'll use contamination based on our ratio)
    model = IsolationForest(
        contamination=0.05,
        random_state=42,
        n_estimators=100
    )
    
    model.fit(X)
    
    # Test predictions
    predictions = model.predict(X)
    # Convert: -1 (anomaly) to 1, 1 (normal) to 0
    predictions = (predictions == -1).astype(int)
    
    accuracy = accuracy_score(y, predictions)
    print(f"Training accuracy: {accuracy:.2%}")
    
    # Save model
    models_dir = Path(__file__).parent / "trained_models"
    model_path = models_dir / "anomaly_detector.pkl"
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"✅ Model saved: {model_path}")
    print(f"   File size: {model_path.stat().st_size:,} bytes")
    
    return model

def train_maintenance_predictor():
    """Train predictive maintenance model"""
    print("\n" + "="*60)
    print("Training Predictive Maintenance Model")
    print("="*60)
    
    # Generate data
    df = SyntheticDataGenerator.generate_maintenance_data(n_samples=1000)
    
    features = ['device_age_days', 'battery_cycles', 'usage_intensity', 'error_rate', 'last_maintenance_days']
    X = df[features]
    y = df['needs_maintenance']
    
    print(f"Training data: {len(df)} samples")
    print(f"No maintenance needed: {(y == 0).sum()}, Needs maintenance: {(y == 1).sum()}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train Gradient Boosting Classifier
    model = GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=4,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    train_acc = model.score(X_train, y_train)
    test_acc = model.score(X_test, y_test)
    
    print(f"Training accuracy: {train_acc:.2%}")
    print(f"Testing accuracy: {test_acc:.2%}")
    
    y_pred = model.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['No Maintenance', 'Needs Maintenance']))
    
    # Save model
    models_dir = Path(__file__).parent / "trained_models"
    model_path = models_dir / "maintenance_predictor.pkl"
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"✅ Model saved: {model_path}")
    print(f"   File size: {model_path.stat().st_size:,} bytes")
    
    return model

def train_activity_recognizer():
    """Train user activity recognition model"""
    print("\n" + "="*60)
    print("Training Activity Recognition Model")
    print("="*60)
    
    # Generate data
    df = SyntheticDataGenerator.generate_activity_data(n_samples=1500)
    
    features = ['acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z']
    X = df[features]
    y = df['activity']
    
    activity_names = {0: 'Resting', 1: 'Walking', 2: 'Using Device'}
    
    print(f"Training data: {len(df)} samples")
    for activity_id, name in activity_names.items():
        count = (y == activity_id).sum()
        print(f"  {name}: {count}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train Random Forest Classifier
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    train_acc = model.score(X_train, y_train)
    test_acc = model.score(X_test, y_test)
    
    print(f"Training accuracy: {train_acc:.2%}")
    print(f"Testing accuracy: {test_acc:.2%}")
    
    y_pred = model.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=list(activity_names.values())))
    
    # Save model
    models_dir = Path(__file__).parent / "trained_models"
    model_path = models_dir / "activity_recognizer.pkl"
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"✅ Model saved: {model_path}")
    print(f"   File size: {model_path.stat().st_size:,} bytes")
    
    return model

if __name__ == "__main__":
    print("🚀 Starting ML Model Training Pipeline")
    print("=" * 60)
    
    # Train all models
    anomaly_model = train_anomaly_detector()
    maintenance_model = train_maintenance_predictor()
    activity_model = train_activity_recognizer()
    
    print("\n" + "="*60)
    print("✅ All models trained successfully!")
    print("="*60)
    print("\nTrained models:")
    print("  1. anomaly_detector.pkl - Detects unusual device behavior")
    print("  2. maintenance_predictor.pkl - Predicts maintenance needs")
    print("  3. activity_recognizer.pkl - Recognizes user activities")