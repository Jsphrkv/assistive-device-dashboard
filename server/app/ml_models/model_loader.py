"""
Model Loader - Centralized ML model management
Loads and manages all trained models
"""

import os
import joblib
from pathlib import Path

class ModelLoader:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.label_encoders = {}
        self.models_dir = Path(__file__).parent / 'saved_models'
        
        # Ensure models directory exists
        self.models_dir.mkdir(exist_ok=True)
        
    def load_model(self, model_name):
        """Load a specific model by name"""
        try:
            model_path = self.models_dir / f'{model_name}.joblib'
            scaler_path = self.models_dir / f'{model_name}_scaler.joblib'
            encoder_path = self.models_dir / f'{model_name}_label_encoder.joblib'
            
            if not model_path.exists():
                print(f"⚠️  Model not found: {model_path}")
                return False
            
            # Load model
            self.models[model_name] = joblib.load(model_path)
            print(f"✅ Loaded model: {model_name}")
            
            # Load scaler if exists
            if scaler_path.exists():
                self.scalers[model_name] = joblib.load(scaler_path)
                print(f"✅ Loaded scaler for: {model_name}")
            
            # Load label encoder if exists (for classification models)
            if encoder_path.exists():
                self.label_encoders[model_name] = joblib.load(encoder_path)
                print(f"✅ Loaded label encoder for: {model_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading {model_name}: {e}")
            return False
    
    def load_all_models(self):
        """Load all available models"""
        model_names = [
            'anomaly_model',
            'maintenance_model',
            'activity_model',
            'object_detection_model',
            'fall_detection_model',
            'route_prediction_model'
        ]
        
        print("="*60)
        print("LOADING ML MODELS")
        print("="*60)
        
        loaded_count = 0
        for model_name in model_names:
            if self.load_model(model_name):
                loaded_count += 1
        
        print("="*60)
        print(f"✅ Loaded {loaded_count}/{len(model_names)} models successfully")
        print("="*60)
        
        return loaded_count > 0
    
    def get_model(self, model_name):
        """Get a loaded model"""
        return self.models.get(model_name)
    
    def get_scaler(self, model_name):
        """Get a model's scaler"""
        return self.scalers.get(model_name)
    
    def get_label_encoder(self, model_name):
        """Get a model's label encoder"""
        return self.label_encoders.get(model_name)
    
    def is_loaded(self, model_name):
        """Check if a model is loaded"""
        return model_name in self.models
    
    def predict_anomaly(self, features):
        """Predict anomaly using loaded model"""
        if not self.is_loaded('anomaly_model'):
            raise RuntimeError("Anomaly model not loaded")
        
        model = self.get_model('anomaly_model')
        scaler = self.get_scaler('anomaly_model')
        
        # Scale features
        if scaler:
            features_scaled = scaler.transform([features])
        else:
            features_scaled = [features]
        
        # Predict
        prediction = model.predict(features_scaled)[0]
        probability = model.predict_proba(features_scaled)[0]
        
        return {
            'is_anomaly': bool(prediction),
            'anomaly_score': float(probability[1]),
            'confidence': float(max(probability))
        }
    
    def predict_maintenance(self, features):
        """Predict maintenance using loaded model"""
        if not self.is_loaded('maintenance_model'):
            raise RuntimeError("Maintenance model not loaded")
        
        model = self.get_model('maintenance_model')
        scaler = self.get_scaler('maintenance_model')
        
        # Scale features
        if scaler:
            features_scaled = scaler.transform([features])
        else:
            features_scaled = [features]
        
        # Predict
        prediction = model.predict(features_scaled)[0]
        probability = model.predict_proba(features_scaled)[0]
        
        return {
            'needs_maintenance': bool(prediction),
            'probability': float(probability[1]),
            'confidence': float(max(probability))
        }
    
    def predict_activity(self, features):
        """Predict activity using loaded model"""
        if not self.is_loaded('activity_model'):
            raise RuntimeError("Activity model not loaded")
        
        model = self.get_model('activity_model')
        scaler = self.get_scaler('activity_model')
        encoder = self.get_label_encoder('activity_model')
        
        # Scale features
        if scaler:
            features_scaled = scaler.transform([features])
        else:
            features_scaled = [features]
        
        # Predict
        prediction_encoded = model.predict(features_scaled)[0]
        probabilities = model.predict_proba(features_scaled)[0]
        
        # Decode activity
        if encoder:
            activity = encoder.inverse_transform([prediction_encoded])[0]
            activity_probs = {
                encoder.inverse_transform([i])[0]: float(prob)
                for i, prob in enumerate(probabilities)
            }
        else:
            activity = str(prediction_encoded)
            activity_probs = {}
        
        return {
            'activity': activity,
            'confidence': float(max(probabilities)),
            'probabilities': activity_probs
        }
    
    def predict_object(self, features):
        """Predict object/obstacle using loaded model"""
        if not self.is_loaded('object_detection_model'):
            raise RuntimeError("Object detection model not loaded")
        
        model = self.get_model('object_detection_model')
        scaler = self.get_scaler('object_detection_model')
        encoder = self.get_label_encoder('object_detection_model')
        
        # Scale features
        if scaler:
            features_scaled = scaler.transform([features])
        else:
            features_scaled = [features]
        
        # Predict
        prediction_encoded = model.predict(features_scaled)[0]
        probabilities = model.predict_proba(features_scaled)[0]
        
        # Decode object
        if encoder:
            object_type = encoder.inverse_transform([prediction_encoded])[0]
        else:
            object_type = str(prediction_encoded)
        
        return {
            'object_detected': object_type,
            'confidence': float(max(probabilities)),
            'detection_confidence': float(max(probabilities))
        }
    
    def predict_fall(self, features):
        """Predict fall using loaded model"""
        if not self.is_loaded('fall_detection_model'):
            raise RuntimeError("Fall detection model not loaded")
        
        model = self.get_model('fall_detection_model')
        scaler = self.get_scaler('fall_detection_model')
        
        # Scale features
        if scaler:
            features_scaled = scaler.transform([features])
        else:
            features_scaled = [features]
        
        # Predict
        prediction = model.predict(features_scaled)[0]
        probability = model.predict_proba(features_scaled)[0]
        
        return {
            'fall_detected': bool(prediction),
            'confidence': float(probability[1]),
            'probability': float(probability[1])
        }
    
    def predict_route(self, features):
        """Predict route metrics using loaded model"""
        if not self.is_loaded('route_prediction_model'):
            raise RuntimeError("Route prediction model not loaded")
        
        model = self.get_model('route_prediction_model')
        scaler = self.get_scaler('route_prediction_model')
        
        # Scale features
        if scaler:
            features_scaled = scaler.transform([features])
        else:
            features_scaled = [features]
        
        # Predict (multi-output: difficulty, time, obstacles)
        prediction = model.predict(features_scaled)[0]
        
        return {
            'difficulty_score': float(prediction[0]),
            'estimated_time_minutes': int(prediction[1]),
            'estimated_obstacles': int(prediction[2])
        }


# Global singleton instance
model_loader = ModelLoader()

# Auto-load models on import
try:
    model_loader.load_all_models()
except Exception as e:
    print(f"⚠️  Could not auto-load models: {e}")
    print("   Models will need to be loaded manually")