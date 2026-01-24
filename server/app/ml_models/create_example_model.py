"""
Run this script once to create an example model for testing
"""
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
from pathlib import Path
import sys

def create_example_model():
    """Create a simple example model for device detection"""
    
    print("Generating training data...")
    # Generate sample data
    X, y = make_classification(
        n_samples=1000,
        n_features=5,
        n_informative=3,
        n_classes=3,
        random_state=42
    )
    
    print("Training model...")
    # Train a simple Random Forest
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # Save the model
    models_dir = Path(__file__).parent / "trained_models"
    models_dir.mkdir(exist_ok=True)
    
    model_path = models_dir / "device_classifier.pkl"
    
    print(f"Saving model to: {model_path}")
    
    # Use standard pickle with binary write mode
    try:
        with open(model_path, 'wb') as f:
            pickle.dump(model, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        print(f"✅ Model saved successfully")
        print(f"   File size: {model_path.stat().st_size} bytes")
        
    except Exception as e:
        print(f"❌ Error saving model: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print(f"\nModel details:")
    print(f"   Model expects 5 features")
    print(f"   Model predicts 3 classes (0, 1, 2)")
    
    # Test loading with pickle
    print("\nTesting model loading with pickle...")
    try:
        with open(model_path, 'rb') as f:
            loaded_model = pickle.load(f)
        
        test_input = np.array([[0.5, 0.3, 0.8, 0.2, 0.6]])
        prediction = loaded_model.predict(test_input)
        probabilities = loaded_model.predict_proba(test_input)
        
        print(f"✅ Test prediction successful: {prediction[0]}")
        print(f"   Probabilities: {probabilities[0]}")
        
    except Exception as e:
        print(f"❌ Error loading/testing model: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    create_example_model()