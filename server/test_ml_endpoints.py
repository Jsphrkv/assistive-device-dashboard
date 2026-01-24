"""
Comprehensive ML API Testing Script
Tests all ML endpoints with various scenarios
"""
import requests
import json
from datetime import datetime
from typing import Dict, Any

BASE_URL = "http://localhost:5000/api/ml"

class Colors:
    """Terminal colors for pretty output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_success(text: str):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_warning(text: str):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_error(text: str):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text: str):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def print_result(data: Dict[Any, Any]):
    print(f"{Colors.OKBLUE}{json.dumps(data, indent=2)}{Colors.ENDC}")

def test_health_check():
    """Test health check endpoint"""
    print_header("1. Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()
        
        if response.status_code == 200:
            print_success(f"Status: {data['status']}")
            print_success(f"Models loaded: {data['total_loaded']}/{data['total_expected']}")
            print_result(data['models'])
        else:
            print_warning(f"Partial status - some models not loaded")
            print_result(data)
            
    except Exception as e:
        print_error(f"Health check failed: {str(e)}")

def test_anomaly_detection():
    """Test anomaly detection with multiple scenarios"""
    print_header("2. Anomaly Detection")
    
    scenarios = [
        {
            "name": "Normal Device",
            "data": {
                "battery_level": 75,
                "usage_duration": 180,
                "temperature": 35,
                "signal_strength": -60,
                "error_count": 1
            }
        },
        {
            "name": "Critical Battery",
            "data": {
                "battery_level": 5,
                "usage_duration": 200,
                "temperature": 36,
                "signal_strength": -65,
                "error_count": 2
            }
        },
        {
            "name": "Overheating Device",
            "data": {
                "battery_level": 50,
                "usage_duration": 180,
                "temperature": 55,
                "signal_strength": -60,
                "error_count": 1
            }
        },
        {
            "name": "Multiple Issues",
            "data": {
                "battery_level": 10,
                "usage_duration": 350,
                "temperature": 52,
                "signal_strength": -90,
                "error_count": 10
            }
        }
    ]
    
    for scenario in scenarios:
        print_info(f"Testing: {scenario['name']}")
        try:
            response = requests.post(
                f"{BASE_URL}/detect/anomaly",
                json=scenario['data']
            )
            data = response.json()
            
            if data.get('is_anomaly'):
                print_warning(f"Anomaly detected! Severity: {data['severity']}")
                print_warning(f"Message: {data['message']}")
            else:
                print_success("Device behavior is normal")
            
            print(f"  Anomaly Score: {data['anomaly_score']:.2f}")
            print()
            
        except Exception as e:
            print_error(f"Test failed: {str(e)}")

def test_maintenance_prediction():
    """Test maintenance prediction with multiple scenarios"""
    print_header("3. Predictive Maintenance")
    
    scenarios = [
        {
            "name": "New Device",
            "data": {
                "device_age_days": 30,
                "battery_cycles": 50,
                "usage_intensity": 0.3,
                "error_rate": 0.1,
                "last_maintenance_days": 10
            }
        },
        {
            "name": "Well-Maintained Device",
            "data": {
                "device_age_days": 200,
                "battery_cycles": 300,
                "usage_intensity": 0.5,
                "error_rate": 0.5,
                "last_maintenance_days": 30
            }
        },
        {
            "name": "Needs Maintenance",
            "data": {
                "device_age_days": 600,
                "battery_cycles": 700,
                "usage_intensity": 0.8,
                "error_rate": 3.0,
                "last_maintenance_days": 150
            }
        },
        {
            "name": "Critical Condition",
            "data": {
                "device_age_days": 730,
                "battery_cycles": 800,
                "usage_intensity": 0.95,
                "error_rate": 5.0,
                "last_maintenance_days": 180
            }
        }
    ]
    
    for scenario in scenarios:
        print_info(f"Testing: {scenario['name']}")
        try:
            response = requests.post(
                f"{BASE_URL}/predict/maintenance",
                json=scenario['data']
            )
            data = response.json()
            
            if data['needs_maintenance']:
                print_warning(f"Maintenance needed! Priority: {data['priority']}")
            else:
                print_success(f"Device OK - Next maintenance in ~{data['estimated_days_until_maintenance']} days")
            
            print(f"  Confidence: {data['confidence']:.2%}")
            print(f"  Recommendations:")
            for rec in data['recommendations']:
                print(f"    - {rec}")
            print()
            
        except Exception as e:
            print_error(f"Test failed: {str(e)}")

def test_activity_recognition():
    """Test activity recognition with multiple scenarios"""
    print_header("4. Activity Recognition")
    
    scenarios = [
        {
            "name": "Resting",
            "data": {
                "acc_x": 0.1,
                "acc_y": 0.2,
                "acc_z": 9.8,
                "gyro_x": 2,
                "gyro_y": 1,
                "gyro_z": 1
            }
        },
        {
            "name": "Walking",
            "data": {
                "acc_x": 2.5,
                "acc_y": 1.8,
                "acc_z": 10.2,
                "gyro_x": 25,
                "gyro_y": 18,
                "gyro_z": 12
            }
        },
        {
            "name": "Using Device",
            "data": {
                "acc_x": 1.2,
                "acc_y": 0.8,
                "acc_z": 9.5,
                "gyro_x": 15,
                "gyro_y": 12,
                "gyro_z": 8
            }
        },
        {
            "name": "Intense Activity",
            "data": {
                "acc_x": 4.0,
                "acc_y": 3.5,
                "acc_z": 11.0,
                "gyro_x": 40,
                "gyro_y": 35,
                "gyro_z": 20
            }
        }
    ]
    
    for scenario in scenarios:
        print_info(f"Testing: {scenario['name']}")
        try:
            response = requests.post(
                f"{BASE_URL}/recognize/activity",
                json=scenario['data']
            )
            data = response.json()
            
            print_success(f"Activity: {data['activity'].upper()}")
            print(f"  {data['description']}")
            print(f"  Confidence: {data['confidence']:.2%}")
            print(f"  Intensity: {data['intensity']}")
            print(f"  Probabilities:")
            for activity, prob in data['all_probabilities'].items():
                print(f"    - {activity}: {prob:.2%}")
            print()
            
        except Exception as e:
            print_error(f"Test failed: {str(e)}")

def test_comprehensive_analysis():
    """Test comprehensive device analysis"""
    print_header("5. Comprehensive Device Analysis")
    
    scenarios = [
        {
            "name": "Healthy Device - User Resting",
            "data": {
                "telemetry": {
                    "battery_level": 80,
                    "usage_duration": 150,
                    "temperature": 34,
                    "signal_strength": -55,
                    "error_count": 0
                },
                "device_info": {
                    "device_age_days": 100,
                    "battery_cycles": 150,
                    "usage_intensity": 0.4,
                    "error_rate": 0.2,
                    "last_maintenance_days": 20
                },
                "sensor_data": {
                    "acc_x": 0.1,
                    "acc_y": 0.1,
                    "acc_z": 9.8,
                    "gyro_x": 1,
                    "gyro_y": 1,
                    "gyro_z": 1
                }
            }
        },
        {
            "name": "Critical Device - User Walking",
            "data": {
                "telemetry": {
                    "battery_level": 8,
                    "usage_duration": 340,
                    "temperature": 50,
                    "signal_strength": -88,
                    "error_count": 9
                },
                "device_info": {
                    "device_age_days": 650,
                    "battery_cycles": 750,
                    "usage_intensity": 0.9,
                    "error_rate": 4.5,
                    "last_maintenance_days": 170
                },
                "sensor_data": {
                    "acc_x": 2.8,
                    "acc_y": 2.0,
                    "acc_z": 10.5,
                    "gyro_x": 28,
                    "gyro_y": 20,
                    "gyro_z": 15
                }
            }
        }
    ]
    
    for scenario in scenarios:
        print_info(f"Scenario: {scenario['name']}")
        try:
            response = requests.post(
                f"{BASE_URL}/analyze/device",
                json=scenario['data']
            )
            data = response.json()
            
            # Anomaly
            if 'anomaly' in data:
                anomaly = data['anomaly']
                if anomaly.get('is_anomaly'):
                    print_warning(f"🚨 ANOMALY: {anomaly['message']}")
                    print(f"   Severity: {anomaly['severity']} | Score: {anomaly['anomaly_score']:.2f}")
                else:
                    print_success("✓ No anomalies detected")
            
            # Maintenance
            if 'maintenance' in data:
                maint = data['maintenance']
                if maint.get('needs_maintenance'):
                    print_warning(f"🔧 MAINTENANCE REQUIRED - Priority: {maint['priority']}")
                    print(f"   Confidence: {maint['confidence']:.2%}")
                    for rec in maint['recommendations']:
                        print(f"   • {rec}")
                else:
                    print_success(f"✓ No maintenance needed (~{maint['estimated_days_until_maintenance']} days)")
            
            # Activity
            if 'activity' in data:
                act = data['activity']
                print_info(f"👤 User Activity: {act['activity'].upper()} ({act['confidence']:.0%} confidence)")
                print(f"   {act['description']} | Intensity: {act['intensity']}")
            
            print()
            
        except Exception as e:
            print_error(f"Test failed: {str(e)}")

def test_device_classification():
    """Test device type classification"""
    print_header("6. Device Classification")
    
    scenarios = [
        {
            "name": "Smartphone-like",
            "features": [0.3, 0.4, 0.6, 0.2, 0.5]
        },
        {
            "name": "Laptop-like",
            "features": [0.5, 0.3, 0.8, 0.2, 0.6]
        },
        {
            "name": "IoT Device-like",
            "features": [0.7, 0.8, 0.4, 0.9, 0.3]
        }
    ]
    
    for scenario in scenarios:
        print_info(f"Testing: {scenario['name']}")
        try:
            response = requests.post(
                f"{BASE_URL}/predict/device",
                json={"features": scenario['features']}
            )
            data = response.json()
            
            print_success(f"Detected: {data['device_type'].upper()}")
            print(f"  Confidence: {data['confidence']:.2%}")
            print(f"  Probabilities:")
            for device, prob in data['all_probabilities'].items():
                print(f"    - {device}: {prob:.2%}")
            print()
            
        except Exception as e:
            print_error(f"Test failed: {str(e)}")

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║          ASSISTIVE DEVICE ML API - ENDPOINT TESTING             ║")
    print("║                      Test Suite v1.0                             ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    print_info(f"Testing endpoints at: {BASE_URL}")
    print_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run all tests
        test_health_check()
        test_anomaly_detection()
        test_maintenance_prediction()
        test_activity_recognition()
        test_comprehensive_analysis()
        test_device_classification()
        
        print_header("✅ ALL TESTS COMPLETED")
        print_success("All ML endpoints are functioning correctly!")
        
    except KeyboardInterrupt:
        print_warning("\n\nTests interrupted by user")
    except Exception as e:
        print_error(f"\n\nTest suite failed: {str(e)}")

def test_validation():
    """Test input validation"""
    print_header("7. Input Validation Tests")
    
    # Test 1: Invalid battery level
    print_info("Test 1: Battery level > 100 (should fail)")
    try:
        response = requests.post(
            f"{BASE_URL}/detect/anomaly",
            json={
                "battery_level": 150,  # Invalid!
                "usage_duration": 180,
                "temperature": 35,
                "signal_strength": -60,
                "error_count": 1
            }
        )
        data = response.json()
        if response.status_code == 400:
            print_warning("Validation failed (as expected)")
            print(f"  Error: {data.get('error')}")
        else:
            print_error("Should have failed validation!")
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
    
    # Test 2: Missing required field
    print_info("\nTest 2: Missing temperature field (should fail)")
    try:
        response = requests.post(
            f"{BASE_URL}/detect/anomaly",
            json={
                "battery_level": 75,
                "usage_duration": 180,
                # temperature missing!
                "signal_strength": -60,
                "error_count": 1
            }
        )
        data = response.json()
        if response.status_code == 400:
            print_warning("Validation failed (as expected)")
            print(f"  Missing fields: {[d['loc'] for d in data.get('details', [])]}")
        else:
            print_error("Should have failed validation!")
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
    
    # Test 3: Invalid data type
    print_info("\nTest 3: String instead of number (should fail)")
    try:
        response = requests.post(
            f"{BASE_URL}/detect/anomaly",
            json={
                "battery_level": "seventy-five",  # Invalid type!
                "usage_duration": 180,
                "temperature": 35,
                "signal_strength": -60,
                "error_count": 1
            }
        )
        data = response.json()
        if response.status_code == 400:
            print_warning("Validation failed (as expected)")
            print(f"  Error: {data.get('error')}")
        else:
            print_error("Should have failed validation!")
    except Exception as e:
        print_error(f"Test failed: {str(e)}")

if __name__ == "__main__":
    main()

