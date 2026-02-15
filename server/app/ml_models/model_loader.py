"""
ML Model Loader
Handles loading and management of all ML models
"""
import os
import joblib
from pathlib import Path
from typing import Optional


class ModelLoader:
    """Singleton class to load and manage ML models"""
    
    def __init__(self):
        self.models_dir = Path(__file__).parent / 'saved_models'
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize model instances to None - will be set during loading
        self.anomaly_detector = None
        self.maintenance_predictor = None
        self.object_detector = None
        self.danger_predictor = None
        self.environment_classifier = None
        
        self.models_loaded = False
        self.load_count = 0
        
    def load_all_models(self):
        """Load all available ML models"""
        # Import here to avoid circular imports
        from .anomaly_detector import AnomalyDetector
        from .maintenance_predictor import MaintenancePredictor
        from .object_detector import ObjectDetector
        from .danger_predictor import DangerPredictor
        from .environment_classifier import EnvironmentClassifier
        
        print("\n" + "="*60)
        print("LOADING ML MODELS")
        print("="*60)
        
        self.load_count = 0
        total_models = 5  # We have 5 models now
        
        # Load each model
        self._load_anomaly_model(AnomalyDetector)
        self._load_maintenance_model(MaintenancePredictor)
        self._load_object_detection_model(ObjectDetector)
        self._load_danger_prediction_model(DangerPredictor)
        self._load_environment_classification_model(EnvironmentClassifier)
        
        print("="*60)
        print(f"✅ Loaded {self.load_count}/{total_models} models successfully")
        print("="*60 + "\n")
        
        self.models_loaded = True
        return self.load_count == total_models
    
    def _load_anomaly_model(self, AnomalyDetector):
        """Load anomaly detection model"""
        model_path = self.models_dir / 'anomaly_model.joblib'
        try:
            if model_path.exists():
                model_data = joblib.load(model_path)
                self.anomaly_detector = AnomalyDetector()
                self.anomaly_detector.model = model_data['model']
                self.anomaly_detector.scaler = model_data.get('scaler')
                print(f"✅ Loaded: Anomaly Detection Model")
                self.load_count += 1
            else:
                print(f"⚠️  Model not found: {model_path}")
        except Exception as e:
            print(f"❌ Failed to load anomaly model: {e}")
    
    def _load_maintenance_model(self, MaintenancePredictor):
        """Load maintenance prediction model"""
        model_path = self.models_dir / 'maintenance_model.joblib'
        try:
            if model_path.exists():
                model_data = joblib.load(model_path)
                self.maintenance_predictor = MaintenancePredictor()
                self.maintenance_predictor.model = model_data['model']
                self.maintenance_predictor.scaler = model_data.get('scaler')
                print(f"✅ Loaded: Maintenance Prediction Model")
                self.load_count += 1
            else:
                print(f"⚠️  Model not found: {model_path}")
        except Exception as e:
            print(f"❌ Failed to load maintenance model: {e}")
    
    def _load_object_detection_model(self, ObjectDetector):
        """Load object detection model"""
        model_path = self.models_dir / 'object_detection_model.joblib'
        try:
            if model_path.exists():
                model_data = joblib.load(model_path)
                self.object_detector = ObjectDetector()
                self.object_detector.model = model_data['model']
                self.object_detector.scaler = model_data.get('scaler')
                print(f"✅ Loaded: Object Detection Model")
                self.load_count += 1
            else:
                print(f"⚠️  Model not found: {model_path}")
        except Exception as e:
            print(f"❌ Failed to load object detection model: {e}")
    
    def _load_danger_prediction_model(self, DangerPredictor):
        """Load danger prediction model"""
        model_path = self.models_dir / 'danger_prediction_model.joblib'
        try:
            if model_path.exists():
                model_data = joblib.load(model_path)
                self.danger_predictor = DangerPredictor()
                self.danger_predictor.score_model = model_data['score_model']
                self.danger_predictor.action_model = model_data['action_model']
                self.danger_predictor.scaler = model_data.get('scaler')
                print(f"✅ Loaded: Danger Prediction Model")
                self.load_count += 1
            else:
                print(f"⚠️  Model not found: {model_path}")
        except Exception as e:
            print(f"❌ Failed to load danger prediction model: {e}")
    
    def _load_environment_classification_model(self, EnvironmentClassifier):
        """Load environment classification model"""
        model_path = self.models_dir / 'environment_classification_model.joblib'
        try:
            if model_path.exists():
                model_data = joblib.load(model_path)
                self.environment_classifier = EnvironmentClassifier()
                self.environment_classifier.model = model_data['model']
                self.environment_classifier.scaler = model_data.get('scaler')
                print(f"✅ Loaded: Environment Classification Model")
                self.load_count += 1
            else:
                print(f"⚠️  Model not found: {model_path}")
        except Exception as e:
            print(f"❌ Failed to load environment classification model: {e}")
    
    # Prediction methods
    def predict_anomaly(self, telemetry_data):
        """Detect anomalies in device telemetry"""
        if not self.anomaly_detector:
            raise ValueError("Anomaly detection model not loaded")
        return self.anomaly_detector.predict(telemetry_data)
    
    def predict_maintenance(self, device_data):
        """Predict maintenance needs"""
        if not self.maintenance_predictor:
            raise ValueError("Maintenance prediction model not loaded")
        return self.maintenance_predictor.predict(device_data)
    
    def detect_object(self, detection_data):
        """Detect and classify objects"""
        if not self.object_detector:
            raise ValueError("Object detection model not loaded")
        return self.object_detector.predict(detection_data)
    
    def predict_danger(self, danger_data):
        """Predict danger level and recommended action"""
        if not self.danger_predictor:
            raise ValueError("Danger prediction model not loaded")
        return self.danger_predictor.predict(danger_data)
    
    def classify_environment(self, environment_data):
        """Classify environment type, lighting, and complexity"""
        if not self.environment_classifier:
            raise ValueError("Environment classification model not loaded")
        return self.environment_classifier.predict(environment_data)


# Global singleton instance
model_loader = ModelLoader()