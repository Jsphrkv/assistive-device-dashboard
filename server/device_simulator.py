import requests
import time
import random
from datetime import datetime

# API Configuration
API_URL = "https://assistive-device-dashboard.onrender.com/api/device/telemetry"
DEVICE_IDS = [
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002",
    "550e8400-e29b-41d4-a716-446655440003"
]
SEND_INTERVAL = 30  # seconds

def generate_telemetry(anomaly_mode=False):
    """Generate realistic telemetry data"""
    
    if anomaly_mode:
        # Abnormal readings (20% chance)
        temperature = random.uniform(38.5, 40.5)
        heart_rate = random.choice([
            random.uniform(45, 55),   # Too low
            random.uniform(110, 130)  # Too high
        ])
        battery_level = random.uniform(5, 20)
        signal_strength = random.uniform(-90, -70)
        
        # High activity
        accel_magnitude = random.uniform(2.0, 4.0)
        gyro_magnitude = random.uniform(1.0, 2.0)
    else:
        # Normal readings (80% chance)
        temperature = random.uniform(36.0, 37.8)
        heart_rate = random.uniform(60, 90)
        battery_level = random.uniform(40, 100)
        signal_strength = random.uniform(-70, -30)
        
        # Normal activity
        accel_magnitude = random.uniform(0.1, 1.0)
        gyro_magnitude = random.uniform(0.05, 0.5)
    
    # Generate accelerometer data
    accel_x = random.uniform(-accel_magnitude, accel_magnitude)
    accel_y = random.uniform(-accel_magnitude, accel_magnitude)
    accel_z = random.uniform(-accel_magnitude, accel_magnitude)
    
    # Generate gyroscope data
    gyro_x = random.uniform(-gyro_magnitude, gyro_magnitude)
    gyro_y = random.uniform(-gyro_magnitude, gyro_magnitude)
    gyro_z = random.uniform(-gyro_magnitude, gyro_magnitude)
    
    # Maintenance info (send every 10th reading)
    battery_health = random.uniform(40, 100)
    charge_cycles = random.randint(50, 500)
    error_count = random.randint(0, 20)
    uptime_days = random.randint(1, 365)
    
    return {
        'device_id': random.choice(DEVICE_IDS),
        'temperature': round(temperature, 2),
        'heart_rate': round(heart_rate, 1),
        'battery_level': round(battery_level, 1),
        'signal_strength': round(signal_strength, 1),
        'usage_hours': round(random.uniform(0, 16), 2),
        'accel_x': round(accel_x, 3),
        'accel_y': round(accel_y, 3),
        'accel_z': round(accel_z, 3),
        'gyro_x': round(gyro_x, 3),
        'gyro_y': round(gyro_y, 3),
        'gyro_z': round(gyro_z, 3),
        # Maintenance data
        'battery_health': round(battery_health, 1),
        'charge_cycles': charge_cycles,
        'error_count': error_count,
        'uptime_days': uptime_days,
        'check_maintenance': False  # Will be set to True periodically
    }

def send_telemetry(data):
    """Send telemetry data to the backend"""
    try:
        response = requests.post(API_URL, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Telemetry sent successfully")
            
            # Show prediction results
            predictions = result.get('predictions', {})
            
            if 'anomaly' in predictions and 'error' not in predictions['anomaly']:
                anomaly = predictions['anomaly']
                status = "🚨 ANOMALY" if anomaly.get('is_anomaly') else "✓ Normal"
                score = anomaly.get('anomaly_score', 0) * 100
                print(f"   Anomaly: {status} (score: {score:.1f}%)")
            
            if 'activity' in predictions and 'error' not in predictions['activity']:
                activity = predictions['activity']
                act = activity.get('activity', 'unknown')
                conf = activity.get('confidence', 0) * 100
                print(f"   Activity: {act} (confidence: {conf:.1f}%)")
            
            if 'maintenance' in predictions and 'error' not in predictions['maintenance']:
                maintenance = predictions['maintenance']
                needed = "⚠️ YES" if maintenance.get('needs_maintenance') else "✓ No"
                prob = maintenance.get('probability', 0) * 100
                print(f"   Maintenance: {needed} (probability: {prob:.1f}%)")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main simulation loop"""
    print("="*70)
    print("🤖 IoT DEVICE SIMULATOR")
    print("="*70)
    print(f"Device ID: {DEVICE_IDS}")
    print(f"API URL: {API_URL}")
    print(f"Send Interval: {SEND_INTERVAL} seconds")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print("\nPress Ctrl+C to stop\n")
    
    reading_count = 0
    
    try:
        while True:
            reading_count += 1
            
            # 20% chance of anomaly
            is_anomaly = random.random() < 0.2
            
            # Generate telemetry
            telemetry = generate_telemetry(anomaly_mode=is_anomaly)
            
            # Check maintenance every 10th reading
            if reading_count % 10 == 0:
                telemetry['check_maintenance'] = True
            
            # Print header
            print(f"\n📊 Reading #{reading_count} - {datetime.now().strftime('%H:%M:%S')}")
            print(f"   Temp: {telemetry['temperature']}°C | HR: {telemetry['heart_rate']} bpm")
            print(f"   Battery: {telemetry['battery_level']}% | Signal: {telemetry['signal_strength']} dBm")
            print(f"   Mode: {'🚨 Anomaly Simulation' if is_anomaly else '✓ Normal'}")
            
            # Send to backend
            success = send_telemetry(telemetry)
            
            if not success:
                print("   ⚠️ Will retry next interval...")
            
            # Wait before next reading
            print(f"\n⏳ Waiting {SEND_INTERVAL} seconds...")
            time.sleep(SEND_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("🛑 Simulator stopped")
        print(f"Total readings sent: {reading_count}")
        print(f"Stopped: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

if __name__ == "__main__":
    main()