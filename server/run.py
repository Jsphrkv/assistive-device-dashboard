#!/usr/bin/env python3
"""
Flask application entry point
"""

import os
from app import create_app

# Create Flask app
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Load ML models only in the reloader process
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not debug:
        from app.ml_models.model_loader import model_loader
        print("🔄 Loading ML models...")
        try:
            success = model_loader.load_all_models()
            if success:
                print("✅ All ML models loaded successfully")
                # Show which models are loaded
                loaded = []
                if model_loader.anomaly_detector: 
                    loaded.append("anomaly_detector")
                if model_loader.object_detector: 
                    loaded.append("object_detector")
                if model_loader.danger_predictor: 
                    loaded.append("danger_predictor")
                if model_loader.environment_classifier: 
                    loaded.append("environment_classifier")
                
                if loaded:
                    print(f"   Loaded models: {', '.join(loaded)}")
                else:
                    print("   ⚠️  No model files found (will use fallback predictions)")
            else:
                print("⚠️  ML models failed to load (will use fallback predictions)")
        except Exception as e:
            print(f"⚠️  Warning: Could not load ML models: {str(e)}")
            print("   The API will continue with fallback predictions")
            import traceback
            traceback.print_exc()
    
    print(f"""
╔════════════════════════════════════════════════════════════════════╗
║     Assistive Device Server API                                    ║
║     Running on: http://{host}:{port}{''.ljust(25 - len(str(port)))}║
║     Environment: {os.getenv('FLASK_ENV', 'development').ljust(40)} ║
║                                                                    ║
║     Available Models (4):                                          ║
║       • Anomaly Detection                                          ║
║       • Object Detection                                           ║
║       • Danger Prediction                                          ║
║       • Environment Classification                                 ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Run application
    app.run(
        host=host,
        port=port,
        debug=debug
    )