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
        from app.services.ml_service import ml_service
        print("🔄 Loading ML models...")
        try:
            success = ml_service.load_models()
            if success:
                print("✅ ML models loaded successfully")
                # Show which models are loaded
                loaded = []
                if ml_service.device_classifier: loaded.append("device_classifier")
                if ml_service.anomaly_detector: loaded.append("anomaly_detector")
                if ml_service.maintenance_predictor: loaded.append("maintenance_predictor")
                if ml_service.activity_recognizer: loaded.append("activity_recognizer")
                print(f"   Loaded models: {', '.join(loaded)}")
            else:
                print("⚠️  ML models failed to load")
        except Exception as e:
            print(f"⚠️  Warning: Could not load ML models: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║     Assistive Device Server API                         ║
║     Running on: http://{host}:{port}                    ║
║     Environment: {os.getenv('FLASK_ENV', 'development')}                                    ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Run application
    app.run(
        host=host,
        port=port,
        debug=debug
    )