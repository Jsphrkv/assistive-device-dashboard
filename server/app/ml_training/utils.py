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
        # Device anomaly detection data
        df = pd.DataFrame({
            'temperature_c': np.random.normal(37, 8, n_samples),  # CPU temp
            'battery_level': np.random.randint(10, 100, n_samples),
            'cpu_usage': np.random.randint(20, 100, n_samples),
            'rssi': np.random.randint(-90, -30, n_samples),  # WiFi signal
            'error_count': np.random.randint(0, 20, n_samples),
            'is_anomaly': np.random.choice([0, 1], n_samples, p=[0.85, 0.15])
        })
        return df
    
    elif dataset_type == 'maintenance':
        # Predictive maintenance data
        df = pd.DataFrame({
            'battery_health': np.random.randint(40, 100, n_samples),
            'usage_hours': np.random.randint(0, 1000, n_samples),
            'temperature_avg': np.random.normal(35, 5, n_samples),
            'error_count': np.random.randint(0, 30, n_samples),
            'days_since_last_maintenance': np.random.randint(0, 180, n_samples),
            'needs_maintenance': np.random.choice([0, 1], n_samples, p=[0.75, 0.25])
        })
        return df
    
    elif dataset_type == 'object_detection':
        # Object/obstacle detection and classification
        df = pd.DataFrame({
            'distance_cm': np.random.uniform(10, 500, n_samples),
            'detection_confidence': np.random.uniform(0.5, 1.0, n_samples),
            'proximity_value': np.random.randint(50, 10000, n_samples),
            'ambient_light': np.random.randint(100, 800, n_samples),
            'object_detected': np.random.choice(
                ['obstacle', 'person', 'vehicle', 'wall', 'stairs_down', 
                 'stairs_up', 'curb', 'door', 'pole'],
                n_samples
            )
        })
        return df
    
    elif dataset_type == 'danger_prediction':
        # Danger prediction (NEW)
        # Features: distance, rate_of_change, proximity, object_type, speed
        # Targets: danger_score (0-100), recommended_action
        
        distances = np.random.uniform(10, 400, n_samples)
        rates_of_change = np.random.normal(-10, 30, n_samples)  # negative = approaching
        
        # Generate danger scores based on distance and rate
        danger_scores = []
        actions = []
        
        for dist, rate in zip(distances, rates_of_change):
            # Calculate danger based on distance and approach rate
            if dist < 30 and rate < -20:
                danger = np.random.uniform(80, 100)
                action = 'STOP'
            elif dist < 100 and rate < -10:
                danger = np.random.uniform(60, 85)
                action = np.random.choice(['STOP', 'SLOW_DOWN'])
            elif dist < 200:
                danger = np.random.uniform(30, 65)
                action = np.random.choice(['SLOW_DOWN', 'CAUTION'])
            else:
                danger = np.random.uniform(0, 35)
                action = 'SAFE'
            
            danger_scores.append(danger)
            actions.append(action)
        
        df = pd.DataFrame({
            'distance_cm': distances,
            'rate_of_change': rates_of_change,  # cm/s (negative = approaching)
            'proximity_value': np.random.randint(1000, 10000, n_samples),
            'object_type_encoded': np.random.randint(0, 5, n_samples),  # 0=obstacle, 1=person, 2=vehicle, etc.
            'current_speed_estimate': np.random.uniform(0, 5, n_samples),  # m/s
            'danger_score': danger_scores,
            'recommended_action': actions
        })
        return df
    
    elif dataset_type == 'environment_classification':
        # Environment classification (NEW)
        # Features: light patterns, detection frequency, distances
        # Targets: environment_type, lighting, complexity
        
        environments = []
        lightings = []
        complexities = []
        
        ambient_lights = []
        light_variances = []
        detection_freqs = []
        avg_distances = []
        complexities_score = []
        distance_vars = []
        
        for _ in range(n_samples):
            # Generate correlated environment features
            env_type = np.random.choice(['indoor', 'outdoor', 'crowded', 'open_space', 'narrow_corridor'])
            
            if env_type == 'indoor':
                ambient = np.random.uniform(200, 500)
                light_var = np.random.uniform(50, 150)
                det_freq = np.random.uniform(2, 8)
                avg_dist = np.random.uniform(100, 300)
                complexity = np.random.uniform(5, 12)
                dist_var = np.random.uniform(30, 100)
                lighting = np.random.choice(['dim', 'bright'], p=[0.6, 0.4])
                complex_level = np.random.choice(['moderate', 'complex'], p=[0.6, 0.4])
                
            elif env_type == 'outdoor':
                ambient = np.random.uniform(500, 900)
                light_var = np.random.uniform(100, 300)
                det_freq = np.random.uniform(0.5, 3)
                avg_dist = np.random.uniform(200, 600)
                complexity = np.random.uniform(2, 8)
                dist_var = np.random.uniform(50, 200)
                lighting = np.random.choice(['bright', 'dim'], p=[0.7, 0.3])
                complex_level = np.random.choice(['simple', 'moderate'], p=[0.6, 0.4])
                
            elif env_type == 'crowded':
                ambient = np.random.uniform(300, 600)
                light_var = np.random.uniform(100, 250)
                det_freq = np.random.uniform(8, 15)
                avg_dist = np.random.uniform(50, 150)
                complexity = np.random.uniform(12, 20)
                dist_var = np.random.uniform(20, 60)
                lighting = np.random.choice(['bright', 'dim'], p=[0.5, 0.5])
                complex_level = 'complex'
                
            elif env_type == 'open_space':
                ambient = np.random.uniform(600, 900)
                light_var = np.random.uniform(80, 200)
                det_freq = np.random.uniform(0.2, 1.5)
                avg_dist = np.random.uniform(400, 800)
                complexity = np.random.uniform(1, 5)
                dist_var = np.random.uniform(100, 300)
                lighting = 'bright'
                complex_level = 'simple'
                
            else:  # narrow_corridor
                ambient = np.random.uniform(150, 400)
                light_var = np.random.uniform(30, 100)
                det_freq = np.random.uniform(4, 10)
                avg_dist = np.random.uniform(80, 200)
                complexity = np.random.uniform(8, 15)
                dist_var = np.random.uniform(20, 50)
                lighting = np.random.choice(['dim', 'dark'], p=[0.6, 0.4])
                complex_level = 'complex'
            
            ambient_lights.append(ambient)
            light_variances.append(light_var)
            detection_freqs.append(det_freq)
            avg_distances.append(avg_dist)
            complexities_score.append(complexity)
            distance_vars.append(dist_var)
            environments.append(env_type)
            lightings.append(lighting)
            complexities.append(complex_level)
        
        df = pd.DataFrame({
            'ambient_light_avg': ambient_lights,
            'ambient_light_variance': light_variances,
            'detection_frequency': detection_freqs,  # detections per minute
            'average_obstacle_distance': avg_distances,
            'proximity_pattern_complexity': complexities_score,
            'distance_variance': distance_vars,
            'environment_type': environments,
            'lighting_condition': lightings,
            'complexity_level': complexities
        })
        return df
    
    else:
        raise ValueError(f"Unknown dataset_type: {dataset_type}")

    return df