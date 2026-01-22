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