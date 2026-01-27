# import os
# import joblib
# from datetime import datetime

# class ModelLoader:
#     """Load and cache trained ML models"""
    
#     def __init__(self):
#         self.models_dir = os.path.join(
#             os.path.dirname(__file__), 'saved_models'
#         )
#         self._models_cache = {}
#         self._scalers_cache = {}
#         self._encoders_cache = {}
#         self._metadata_cache = {}
        
#     def load_model(self, model_name, force_reload=False):
#         """
#         Load a trained model from disk
        
#         Args:
#             model_name: Name of the model (e.g., 'anomaly_model')
#             force_reload: Force reload even if cached
            
#         Returns:
#             dict with 'model', 'scaler', 'metadata', 'encoder' (if available)
#         """
#         # Return cached if available
#         if not force_reload and model_name in self._models_cache:
#             return {
#                 'model': self._models_cache[model_name],
#                 'scaler': self._scalers_cache.get(model_name),
#                 'encoder': self._encoders_cache.get(model_name),
#                 'metadata': self._metadata_cache.get(model_name)
#             }
        
#         # Load model
#         model_path = os.path.join(self.models_dir, f'{model_name}.pkl')
#         if not os.path.exists(model_path):
#             raise FileNotFoundError(
#                 f"Model '{model_name}' not found. "
#                 f"Please train the model first using train_{model_name.split('_')[0]}.py"
#             )
        
#         model = joblib.load(model_path)
#         self._models_cache[model_name] = model
        
#         # Load scaler
#         scaler_path = os.path.join(self.models_dir, f'{model_name}_scaler.pkl')
#         if os.path.exists(scaler_path):
#             scaler = joblib.load(scaler_path)
#             self._scalers_cache[model_name] = scaler
#         else:
#             scaler = None
        
#         # Load encoder (for multiclass models)
#         encoder_path = os.path.join(self.models_dir, f'{model_name}_encoder.pkl')
#         if os.path.exists(encoder_path):
#             encoder = joblib.load(encoder_path)
#             self._encoders_cache[model_name] = encoder
#         else:
#             encoder = None
        
#         # Load metadata
#         metadata_path = os.path.join(self.models_dir, f'{model_name}_metadata.pkl')
#         if os.path.exists(metadata_path):
#             metadata = joblib.load(metadata_path)
#             self._metadata_cache[model_name] = metadata
#         else:
#             metadata = {}
        
#         print(f"✓ Loaded model: {model_name}")
#         if metadata:
#             print(f"  Trained: {metadata.get('trained_at', 'Unknown')}")
#             print(f"  Type: {metadata.get('model_type', 'Unknown')}")
#             if 'metrics' in metadata:
#                 print(f"  Accuracy: {metadata['metrics'].get('accuracy', 'N/A'):.4f}")
        
#         return {
#             'model': model,
#             'scaler': scaler,
#             'encoder': encoder,
#             'metadata': metadata
#         }
    
#     def get_model_info(self, model_name):
#         """Get metadata about a model without loading it"""
#         metadata_path = os.path.join(self.models_dir, f'{model_name}_metadata.pkl')
#         if os.path.exists(metadata_path):
#             return joblib.load(metadata_path)
#         return None
    
#     def list_available_models(self):
#         """List all available trained models"""
#         if not os.path.exists(self.models_dir):
#             return []
        
#         models = []
#         for filename in os.listdir(self.models_dir):
#             if filename.endswith('.pkl') and not any(
#                 x in filename for x in ['scaler', 'encoder', 'metadata']
#             ):
#                 model_name = filename.replace('.pkl', '')
#                 models.append(model_name)
        
#         return models
    
#     def clear_cache(self):
#         """Clear all cached models"""
#         self._models_cache.clear()
#         self._scalers_cache.clear()
#         self._encoders_cache.clear()
#         self._metadata_cache.clear()
#         print("✓ Model cache cleared")


# # Global instance
# model_loader = ModelLoader()


# # Convenience functions
# def load_anomaly_model():
#     """Load anomaly detection model"""
#     return model_loader.load_model('anomaly_model')


# def load_activity_model():
#     """Load activity recognition model"""
#     return model_loader.load_model('activity_model')


# def load_maintenance_model():
#     """Load maintenance prediction model"""
#     return model_loader.load_model('maintenance_model')

import os
import pickle, joblib
import traceback

class ModelLoader:
    def load_model(self, model_name, force_reload=False):
        """Load a trained model from disk"""
        # Return cached if available
        if not force_reload and model_name in self._models_cache:
            return {
                'model': self._models_cache[model_name],
                'scaler': self._scalers_cache.get(model_name),
                'encoder': self._encoders_cache.get(model_name),
                'metadata': self._metadata_cache.get(model_name)
            }
        
        # Load model
        model_path = os.path.join(self.models_dir, f'{model_name}.pkl')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model '{model_name}' not found")
        
        model = joblib.load(model_path)
        self._models_cache[model_name] = model
        
        # Load scaler
        scaler_path = os.path.join(self.models_dir, f'{model_name}_scaler.pkl')
        if os.path.exists(scaler_path):
            scaler = joblib.load(scaler_path)
            self._scalers_cache[model_name] = scaler
        else:
            scaler = None
        
        # Load encoder (for multiclass models)
        encoder_path = os.path.join(self.models_dir, f'{model_name}_encoder.pkl')
        if os.path.exists(encoder_path):
            encoder = joblib.load(encoder_path)
            self._encoders_cache[model_name] = encoder
        else:
            encoder = None
        
        # Load metadata
        metadata_path = os.path.join(self.models_dir, f'{model_name}_metadata.pkl')
        if os.path.exists(metadata_path):
            metadata = joblib.load(metadata_path)
            self._metadata_cache[model_name] = metadata
        else:
            metadata = {}
        
        print(f"✓ Loaded {model_name}")
        
        # RETURN A DICT, NOT JUST THE MODEL
        return {
            'model': model,
            'scaler': scaler,
            'encoder': encoder,
            'metadata': metadata
        }

# Global instance
model_loader = ModelLoader()

# Try to load models on import
try:
    models_loaded = model_loader.load_all_models()
    if not models_loaded:
        print("⚠ WARNING: No ML models loaded. Using fallback mode.")
except Exception as e:
    print(f"⚠ ERROR loading models: {e}")
    print("  API will use fallback predictions")