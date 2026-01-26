import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, 
    f1_score, confusion_matrix, classification_report,
    roc_auc_score
)
from imblearn.over_sampling import SMOTE
import joblib
import os
from datetime import datetime

class DataPreprocessor:
    """Handle data preprocessing for ML models"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
    def prepare_features(self, df, feature_columns, target_column, handle_imbalance=True):
        """
        Prepare features for training
        
        Args:
            df: Input dataframe
            feature_columns: List of feature column names
            target_column: Target column name
            handle_imbalance: Whether to use SMOTE for imbalanced data
            
        Returns:
            X_train, X_test, y_train, y_test, scaler
        """
        # Separate features and target
        X = df[feature_columns].values
        y = df[target_column].values
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0.0)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Handle class imbalance using SMOTE
        if handle_imbalance and len(np.unique(y_train)) > 1:
            try:
                smote = SMOTE(random_state=42)
                X_train_scaled, y_train = smote.fit_resample(X_train_scaled, y_train)
                print(f"✓ Applied SMOTE - New training size: {len(X_train_scaled)}")
            except ValueError as e:
                print(f"⚠ Could not apply SMOTE: {e}")
        
        return X_train_scaled, X_test_scaled, y_train, y_test
    
    def prepare_multiclass_features(self, df, feature_columns, target_column):
        """Prepare features for multiclass classification"""
        X = df[feature_columns].values
        y = df[target_column].values
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0.0)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        return X_train_scaled, X_test_scaled, y_train, y_test


class ModelEvaluator:
    """Evaluate ML model performance"""
    
    @staticmethod
    def evaluate_binary_classifier(model, X_test, y_test, model_name="Model"):
        """Evaluate binary classification model"""
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1_score': f1_score(y_test, y_pred, zero_division=0)
        }
        
        if y_pred_proba is not None:
            metrics['roc_auc'] = roc_auc_score(y_test, y_pred_proba)
        
        print(f"\n{'='*60}")
        print(f"{model_name} Performance Metrics")
        print(f"{'='*60}")
        print(f"Accuracy:  {metrics['accuracy']:.4f}")
        print(f"Precision: {metrics['precision']:.4f}")
        print(f"Recall:    {metrics['recall']:.4f}")
        print(f"F1 Score:  {metrics['f1_score']:.4f}")
        if 'roc_auc' in metrics:
            print(f"ROC AUC:   {metrics['roc_auc']:.4f}")
        print(f"{'='*60}\n")
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        print("Confusion Matrix:")
        print(cm)
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        return metrics
    
    @staticmethod
    def evaluate_multiclass_classifier(model, X_test, y_test, label_encoder, model_name="Model"):
        """Evaluate multiclass classification model"""
        y_pred = model.predict(X_test)
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),
            'f1_score': f1_score(y_test, y_pred, average='weighted', zero_division=0)
        }
        
        print(f"\n{'='*60}")
        print(f"{model_name} Performance Metrics")
        print(f"{'='*60}")
        print(f"Accuracy:  {metrics['accuracy']:.4f}")
        print(f"Precision: {metrics['precision']:.4f}")
        print(f"Recall:    {metrics['recall']:.4f}")
        print(f"F1 Score:  {metrics['f1_score']:.4f}")
        print(f"{'='*60}\n")
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        print("Confusion Matrix:")
        print(cm)
        print("\nClassification Report:")
        target_names = label_encoder.classes_ if hasattr(label_encoder, 'classes_') else None
        print(classification_report(y_test, y_pred, target_names=target_names))
        
        return metrics


class ModelSaver:
    """Save and version trained models"""
    
    @staticmethod
    def save_model(model, scaler, model_name, metrics=None, label_encoder=None):
        """
        Save trained model with metadata
        
        Args:
            model: Trained model
            scaler: Fitted scaler
            model_name: Name for the model file
            metrics: Performance metrics dict
            label_encoder: Label encoder (for multiclass)
        """
        # Create directory if it doesn't exist
        save_dir = os.path.join('app', 'ml_models', 'saved_models')
        os.makedirs(save_dir, exist_ok=True)
        
        # Save model
        model_path = os.path.join(save_dir, f'{model_name}.pkl')
        joblib.dump(model, model_path)
        print(f"✓ Model saved to: {model_path}")
        
        # Save scaler
        scaler_path = os.path.join(save_dir, f'{model_name}_scaler.pkl')
        joblib.dump(scaler, scaler_path)
        print(f"✓ Scaler saved to: {scaler_path}")
        
        # Save label encoder if provided
        if label_encoder is not None:
            encoder_path = os.path.join(save_dir, f'{model_name}_encoder.pkl')
            joblib.dump(label_encoder, encoder_path)
            print(f"✓ Label encoder saved to: {encoder_path}")
        
        # Save metadata
        metadata = {
            'model_name': model_name,
            'trained_at': datetime.now().isoformat(),
            'metrics': metrics or {},
            'model_type': type(model).__name__
        }
        
        metadata_path = os.path.join(save_dir, f'{model_name}_metadata.pkl')
        joblib.dump(metadata, metadata_path)
        print(f"✓ Metadata saved to: {metadata_path}")
        
        print(f"\n✅ All files saved successfully for '{model_name}'\n")
        
        return model_path


def generate_synthetic_data(n_samples=1000, dataset_type='anomaly'):
    """
    Generate synthetic training data for testing
    
    Args:
        n_samples: Number of samples to generate
        dataset_type: 'anomaly', 'activity', or 'maintenance'
        
    Returns:
        DataFrame with synthetic data
    """
    np.random.seed(42)
    
    if dataset_type == 'anomaly':
        # Anomaly detection data
        normal_ratio = 0.85
        n_normal = int(n_samples * normal_ratio)
        n_anomaly = n_samples - n_normal
        
        # Normal data (tighter distributions)
        normal_data = {
            'temperature': np.random.normal(37.0, 0.5, n_normal),
            'heart_rate': np.random.normal(75, 10, n_normal),
            'battery_level': np.random.uniform(20, 100, n_normal),
            'signal_strength': np.random.uniform(-70, -30, n_normal),
            'usage_hours': np.random.uniform(0, 16, n_normal),
            'is_anomaly': np.zeros(n_normal)
        }
        
        # Anomaly data (wider distributions, extreme values)
        anomaly_data = {
            'temperature': np.random.normal(39.5, 2.0, n_anomaly),
            'heart_rate': np.random.choice([np.random.normal(50, 5, n_anomaly//2), 
                                           np.random.normal(120, 15, n_anomaly//2)]).flatten()[:n_anomaly],
            'battery_level': np.random.uniform(0, 30, n_anomaly),
            'signal_strength': np.random.uniform(-90, -70, n_anomaly),
            'usage_hours': np.random.uniform(18, 24, n_anomaly),
            'is_anomaly': np.ones(n_anomaly)
        }
        
        # Combine
        df = pd.DataFrame({
            key: np.concatenate([normal_data[key], anomaly_data[key]])
            for key in normal_data.keys()
        })
        
    elif dataset_type == 'activity':
        # Activity recognition data
        activities = ['resting', 'walking', 'using_device']
        activity_labels = np.random.choice(activities, n_samples)
        
        df = pd.DataFrame({
            'accelerometer_x': np.random.normal(0, 1, n_samples),
            'accelerometer_y': np.random.normal(0, 1, n_samples),
            'accelerometer_z': np.random.normal(0, 1, n_samples),
            'gyroscope_x': np.random.normal(0, 0.5, n_samples),
            'gyroscope_y': np.random.normal(0, 0.5, n_samples),
            'gyroscope_z': np.random.normal(0, 0.5, n_samples),
            'activity': activity_labels
        })
        
        # Adjust values based on activity
        for i, activity in enumerate(activity_labels):
            if activity == 'walking':
                df.loc[i, ['accelerometer_x', 'accelerometer_y']] *= 3
            elif activity == 'using_device':
                df.loc[i, ['gyroscope_x', 'gyroscope_y']] *= 2
                
    elif dataset_type == 'maintenance':
        # Maintenance prediction data
        needs_maintenance_ratio = 0.3
        n_needs = int(n_samples * needs_maintenance_ratio)
        n_normal = n_samples - n_needs
        
        # Normal devices
        normal_data = {
            'battery_health': np.random.uniform(80, 100, n_normal),
            'charge_cycles': np.random.uniform(0, 300, n_normal),
            'temperature_avg': np.random.normal(35, 2, n_normal),
            'error_count': np.random.poisson(1, n_normal),
            'uptime_days': np.random.uniform(0, 365, n_normal),
            'needs_maintenance': np.zeros(n_normal)
        }
        
        # Needs maintenance
        maintenance_data = {
            'battery_health': np.random.uniform(20, 70, n_needs),
            'charge_cycles': np.random.uniform(400, 800, n_needs),
            'temperature_avg': np.random.normal(40, 3, n_needs),
            'error_count': np.random.poisson(10, n_needs),
            'uptime_days': np.random.uniform(200, 730, n_needs),
            'needs_maintenance': np.ones(n_needs)
        }
        
        # Combine
        df = pd.DataFrame({
            key: np.concatenate([normal_data[key], maintenance_data[key]])
            for key in normal_data.keys()
        })
    
    # Shuffle
    df = df.sample(frac=1).reset_index(drop=True)
    
    return df