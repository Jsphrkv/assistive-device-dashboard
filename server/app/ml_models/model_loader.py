import pickle
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ModelLoader:
    """Singleton class to load and cache ML models"""
    
    _instance = None
    _models: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def models_dir(self) -> Path:
        """Get the trained_models directory path"""
        return Path(__file__).parent / "trained_models"
    
    def load_model(self, model_name: str, file_extension: str = "pkl") -> Any:
        """
        Load a model from the trained_models directory using pickle
        """
        cache_key = f"{model_name}.{file_extension}"
        
        # Return cached model if already loaded
        if cache_key in self._models:
            logger.info(f"Using cached model: {cache_key}")
            print(f"Using cached model: {cache_key}")
            return self._models[cache_key]
        
        # Build file path
        model_path = self.models_dir / cache_key
        
        # Check if file exists
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {model_path}\n"
                f"Available models: {self.list_available_models()}"
            )
        
        # Load with pickle
        try:
            print(f"Loading model from: {model_path}")
            print(f"File size: {model_path.stat().st_size} bytes")
            
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            # Cache the loaded model
            self._models[cache_key] = model
            logger.info(f"Successfully loaded model: {cache_key}")
            print(f"Successfully loaded model: {cache_key}")
            return model
            
        except Exception as e:
            logger.error(f"Error loading model {cache_key}: {str(e)}")
            print(f"Error loading model {cache_key}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def list_available_models(self) -> list:
        """List all model files in the trained_models directory"""
        if not self.models_dir.exists():
            return []
        return [f.name for f in self.models_dir.iterdir() if f.is_file() and not f.name.startswith('.')]
    
    def unload_model(self, model_name: str, file_extension: str = "pkl"):
        """Remove a model from cache to free memory"""
        cache_key = f"{model_name}.{file_extension}"
        if cache_key in self._models:
            del self._models[cache_key]
            logger.info(f"Unloaded model: {cache_key}")
    
    def clear_cache(self):
        """Clear all cached models"""
        self._models.clear()
        logger.info("Cleared all cached models")

# Create singleton instance
model_loader = ModelLoader()