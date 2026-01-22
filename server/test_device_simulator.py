#!/usr/bin/env python3
"""
Simulate Raspberry Pi sending data to backend
"""

import requests
import random
import time
from datetime import datetime
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

# Import app to generate token
from app import create_app
from app.utils.jwt_handler import generate_device_token

# Configuration
API_URL = "http://localhost:5000/api"

# Generate device token
print("Generating device token...")
app = create_app()
with app.app_context():
    DEVICE_TOKEN = generate_device_token("raspberry-pi-001")
    print(f"✓ Token generated: {DEVICE_TOKEN[:50]}...\n")

def simulate_detection():
    """Simulate a single detection"""
    obstacles = ['Person', 'Wall', 'Object', 'Stairs']
    
    distance = random.randint(20, 200)
    obstacle_type = random.choice(obstacles)
    
    if distance < 50:
        danger_level = 'High'
        alert_type = 'Both'
    elif distance < 100:
        danger_level = 'Medium'
        alert_type = random.choice(['Audio', 'Both'])
    else:
        danger_level = 'Low'
        alert_type = 'Audio'
    
    data = {
        'obstacle_type': obstacle_type,
        'distance_cm': distance,
        'danger_level': danger_level,
        'alert_type': alert_type
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-Device-Token': DEVICE_TOKEN
    }
    
    try:
        response = requests.post(
            f"{API_URL}/detections",
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 201:
            print(f"✓ Detection logged: {obstacle_type} at {distance}cm - {danger_level}")
            return True
        else:
            print(f"✗ Failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Error: Cannot connect to {API_URL}")
        print(f"  Make sure backend is running!")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def simulate_device_status():
    """Simulate device status update"""
    data = {
        'deviceOnline': True,
        'cameraStatus': 'Active',
        'batteryLevel': random.randint(60, 100),
        'lastDetectionTime': datetime.now().isoformat()
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-Device-Token': DEVICE_TOKEN
    }
    
    try:
        response = requests.post(
            f"{API_URL}/device/status",
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✓ Status updated: Battery {data['batteryLevel']}%")
            return True
        else:
            print(f"✗ Status update failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error updating status: {e}")
        return False

def test_backend():
    """Test if backend is running"""
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✓ Backend is running")
            return True
        else:
            print("✗ Backend returned error")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to backend at http://localhost:5000")
        print("  Start it with: python run.py")
        return False

def main():
    print("=" * 60)
    print("🤖 Device Simulator")
    print("=" * 60)
    print(f"📡 API URL: {API_URL}")
    print(f"🔑 Token: {DEVICE_TOKEN[:30]}...")
    print("=" * 60)
    print()
    
    # Test backend connection
    if not test_backend():
        return
    
    print("\nStarting simulation... (Press Ctrl+C to stop)\n")
    
    try:
        counter = 0
        while True:
            # Simulate detection
            if simulate_detection():
                counter += 1
            
            # Wait random time
            time.sleep(random.randint(3, 7))
            
            # Update status every 5 detections
            if counter > 0 and counter % 5 == 0:
                simulate_device_status()
    
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print(f"👋 Simulation stopped")
        print(f"📊 Total detections sent: {counter}")
        print("=" * 60)

if __name__ == "__main__":
    main()