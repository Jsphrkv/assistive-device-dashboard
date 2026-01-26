import numpy as np
import pandas as pd
import pickle, os
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

MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),  # Go up to server/app/
    'ml_models',
    'saved_models'
)


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
        
        # ✅ FIX 1: Ensure y is 1D (THIS IS THE KEY FIX!)
        if y.ndim > 1:
            y = y.ravel()
        
        # ✅ FIX 2: Convert to int for binary classification
        y = y.astype(int)
        
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
        
        # ✅ FIX 3: Ensure outputs are 1D after SMOTE
        if y_train.ndim > 1:
            y_train = y_train.ravel()
        if y_test.ndim > 1:
            y_test = y_test.ravel()
        
        return X_train_scaled, X_test_scaled, y_train, y_test
    
    def prepare_multiclass_features(self, df, feature_columns, target_column):
        """Prepare features for multiclass classification"""
        X = df[feature_columns].values
        y = df[target_column].values
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # ✅ FIX: Ensure y_encoded is 1D
        if y_encoded.ndim > 1:
            y_encoded = y_encoded.ravel()
        
        # Handle missing values
        X = np.nan_to_num(X, nan=0.0)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # ✅ FIX: Ensure outputs are 1D
        if y_train.ndim > 1:
            y_train = y_train.ravel()
        if y_test.ndim > 1:
            y_test = y_test.ravel()
        
        return X_train_scaled, X_test_scaled, y_train, y_test


class ModelSaver:
    """Save trained models to disk"""
    
    @staticmethod
    def save_model(model, scaler, model_name, metrics=None, label_encoder=None):
        """
        Save model with protocol 4 for better compatibility
        
        Args:
            model: Trained model
            scaler: Fitted scaler
            model_name: Name for the model files
            metrics: Optional dict of metrics
            label_encoder: Optional label encoder (for multiclass models)
        """
        model_path = f"{MODEL_DIR}/{model_name}.pkl"
        scaler_path = f"{MODEL_DIR}/{model_name}_scaler.pkl"
        metadata_path = f"{MODEL_DIR}/{model_name}_metadata.pkl"
        
        try:
            # Save model with protocol 4
            with open(model_path, 'wb') as f:
                pickle.dump(model, f, protocol=4)
            print(f"✓ Model saved to: {model_path}")
            
            # Save scaler
            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler, f, protocol=4)
            print(f"✓ Scaler saved to: {scaler_path}")
            
            # Save label encoder if provided
            if label_encoder is not None:
                encoder_path = f"{MODEL_DIR}/{model_name}_encoder.pkl"
                with open(encoder_path, 'wb') as f:
                    pickle.dump(label_encoder, f, protocol=4)
                print(f"✓ Label encoder saved to: {encoder_path}")
            
            # Save metrics
            if metrics:
                with open(metadata_path, 'wb') as f:
                    pickle.dump(metrics, f, protocol=4)
                print(f"✓ Metadata saved to: {metadata_path}")
            
            print(f"\n✅ All files saved successfully for '{model_name}'")
            
            return {
                'model_path': model_path,
                'scaler_path': scaler_path,
                'metadata_path': metadata_path if metrics else None
            }
            
        except Exception as e:
            print(f"❌ Error saving model: {e}")
            import traceback
            traceback.print_exc()
            raise


class ModelEvaluator:
    """Evaluate model performance"""
    
    @staticmethod
    def evaluate_binary_classifier(model, X_test, y_test, model_name="Model"):
        """Evaluate binary classification model"""
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        print(f"\n{'='*60}")
        print(f"{model_name} Performance Metrics")
        print(f"{'='*60}")
        print(f"Accuracy:  {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall:    {recall:.4f}")
        print(f"F1 Score:  {f1:.4f}")
        
        if y_pred_proba is not None:
            try:
                roc_auc = roc_auc_score(y_test, y_pred_proba)
                print(f"ROC AUC:   {roc_auc:.4f}")
            except:
                pass
        
        print(f"{'='*60}\n")
        
        print("Confusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
        }
    
    @staticmethod
    def evaluate_multiclass_classifier(model, X_test, y_test, label_encoder, model_name="Model"):
        """Evaluate multiclass classification model"""
        y_pred = model.predict(X_test)
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        print(f"\n{'='*60}")
        print(f"{model_name} Performance Metrics")
        print(f"{'='*60}")
        print(f"Accuracy:  {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall:    {recall:.4f}")
        print(f"F1 Score:  {f1:.4f}")
        print(f"{'='*60}\n")
        
        print("Confusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        
        print("\nClassification Report:")
        target_names = label_encoder.classes_ if hasattr(label_encoder, 'classes_') else None
        print(classification_report(y_test, y_pred, target_names=target_names))
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
        }


def generate_synthetic_data(n_samples=1000, dataset_type='anomaly'):
    """
    Generate synthetic data for ML training
    
    Args:
        n_samples: Number of samples to generate
        dataset_type: Type of dataset ('anomaly', 'activity', 'maintenance')
    
    Returns:
        pandas DataFrame with synthetic data
    """
    np.random.seed(42)
    
    if dataset_type == 'anomaly':
        # Generate anomaly detection data
        n_normal = int(n_samples * 0.85)  # 85% normal
        n_anomaly = n_samples - n_normal   # 15% anomalies
        
        # ❌ WRONG: This creates 2D array
        # 'heart_rate': np.random.choice([
        #     np.random.normal(50, 5, n_anomaly//2),
        #     np.random.normal(120, 15, n_anomaly//2)
        # ]).flatten()[:n_anomaly],
        
        # ✅ CORRECT: Generate data properly
        
        # Normal samples
        normal_data = {
            'temperature': np.random.normal(37, 0.5, n_normal),
            'humidity': np.random.normal(65, 10, n_normal),
            'battery_level': np.random.normal(85, 10, n_normal),
            'signal_strength': np.random.normal(-60, 10, n_normal),
            'error_count': np.random.poisson(2, n_normal),
            'is_anomaly': np.zeros(n_normal, dtype=int)  # 0 = normal
        }
        
        # Anomaly samples (split between two types)
        n_anomaly_high = n_anomaly // 2
        n_anomaly_low = n_anomaly - n_anomaly_high
        
        # Type 1: High temperature anomalies
        anomaly_high = {
            'temperature': np.random.normal(42, 2, n_anomaly_high),  # High temp
            'humidity': np.random.normal(65, 10, n_anomaly_high),
            'battery_level': np.random.normal(85, 10, n_anomaly_high),
            'signal_strength': np.random.normal(-60, 10, n_anomaly_high),
            'error_count': np.random.poisson(15, n_anomaly_high),  # High errors
            'is_anomaly': np.ones(n_anomaly_high, dtype=int)
        }
        
        # Type 2: Low battery + weak signal anomalies
        anomaly_low = {
            'temperature': np.random.normal(37, 0.5, n_anomaly_low),
            'humidity': np.random.normal(65, 10, n_anomaly_low),
            'battery_level': np.random.normal(20, 10, n_anomaly_low),  # Low battery
            'signal_strength': np.random.normal(-95, 5, n_anomaly_low),  # Weak signal
            'error_count': np.random.poisson(20, n_anomaly_low),  # High errors
            'is_anomaly': np.ones(n_anomaly_low, dtype=int)
        }
        
        # Combine all samples
        df = pd.DataFrame({
            col: np.concatenate([
                normal_data[col],
                anomaly_high[col],
                anomaly_low[col]
            ])
            for col in normal_data.keys()
        })
        
        # Shuffle the data
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
    elif dataset_type == 'activity':
        # Generate activity recognition data
        activities = ['resting', 'walking', 'using_device']
        n_per_activity = n_samples // 3
        
        activity_data = []
        
        for activity in activities:
            if activity == 'resting':
                data = {
                    'accel_x': np.random.normal(0, 0.1, n_per_activity),
                    'accel_y': np.random.normal(0, 0.1, n_per_activity),
                    'accel_z': np.random.normal(9.8, 0.2, n_per_activity),
                    'gyro_x': np.random.normal(0, 0.05, n_per_activity),
                    'gyro_y': np.random.normal(0, 0.05, n_per_activity),
                    'gyro_z': np.random.normal(0, 0.05, n_per_activity),
                    'activity': [activity] * n_per_activity
                }
            elif activity == 'walking':
                data = {
                    'accel_x': np.random.normal(2, 1, n_per_activity),
                    'accel_y': np.random.normal(1, 0.5, n_per_activity),
                    'accel_z': np.random.normal(9.8, 2, n_per_activity),
                    'gyro_x': np.random.normal(0.5, 0.3, n_per_activity),
                    'gyro_y': np.random.normal(0.5, 0.3, n_per_activity),
                    'gyro_z': np.random.normal(0.2, 0.2, n_per_activity),
                    'activity': [activity] * n_per_activity
                }
            else:  # using_device
                data = {
                    'accel_x': np.random.normal(0.5, 0.3, n_per_activity),
                    'accel_y': np.random.normal(0.5, 0.3, n_per_activity),
                    'accel_z': np.random.normal(9.8, 0.5, n_per_activity),
                    'gyro_x': np.random.normal(0.1, 0.1, n_per_activity),
                    'gyro_y': np.random.normal(0.1, 0.1, n_per_activity),
                    'gyro_z': np.random.normal(0.1, 0.1, n_per_activity),
                    'activity': [activity] * n_per_activity
                }
            
            activity_data.append(pd.DataFrame(data))
        
        df = pd.concat(activity_data, ignore_index=True)
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
    elif dataset_type == 'maintenance':
        # Generate maintenance prediction data
        n_no_maintenance = int(n_samples * 0.7)  # 70% don't need maintenance
        n_needs_maintenance = n_samples - n_no_maintenance
        
        # Devices that don't need maintenance
        no_maintenance = {
            'battery_health': np.random.uniform(80, 100, n_no_maintenance),
            'charge_cycles': np.random.randint(0, 300, n_no_maintenance),
            'temperature_avg': np.random.normal(37, 2, n_no_maintenance),
            'error_count': np.random.poisson(1, n_no_maintenance),
            'uptime_days': np.random.randint(1, 100, n_no_maintenance),
            'needs_maintenance': np.zeros(n_no_maintenance, dtype=int)
        }
        
        # Devices that need maintenance
        needs_maintenance = {
            'battery_health': np.random.uniform(10, 60, n_needs_maintenance),
            'charge_cycles': np.random.randint(500, 2000, n_needs_maintenance),
            'temperature_avg': np.random.normal(42, 3, n_needs_maintenance),
            'error_count': np.random.poisson(10, n_needs_maintenance),
            'uptime_days': np.random.randint(100, 365, n_needs_maintenance),
            'needs_maintenance': np.ones(n_needs_maintenance, dtype=int)
        }
        
        # Combine
        df = pd.DataFrame({
            col: np.concatenate([no_maintenance[col], needs_maintenance[col]])
            for col in no_maintenance.keys()
        })
        
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    else:
        raise ValueError(f"Unknown dataset_type: {dataset_type}")
    
    return df