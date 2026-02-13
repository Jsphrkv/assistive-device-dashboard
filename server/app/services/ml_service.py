import numpy as np
from app.ml_models.model_loader import model_loader
from typing import Dict, List, Tuple
import math

class MLService:
    """ML inference service for IoT predictions"""
    
    def __init__(self):
        self._anomaly_model = None
        self._activity_model = None
        self._maintenance_model = None
        self._models_loaded = False
        print("ML service initialized (models load on first use)")

    def _ensure_models_loaded(self):
        """Load models if not already loaded"""
        if self._models_loaded:
            return
        
        print("Loading ML models...")
        try:
            # Load anomaly detection model
            try:
                anomaly_data = model_loader.load_model('anomaly_model')
                self._anomaly_model = anomaly_data
                print("✓ Anomaly detection model loaded")
            except Exception as e:
                print(f"⚠ Anomaly model not loaded: {e}")
            
            # Load activity recognition model
            try:
                activity_data = model_loader.load_model('activity_model')
                self._activity_model = activity_data
                print("✓ Activity recognition model loaded")
            except Exception as e:
                print(f"⚠ Activity model not loaded: {e}")
            
            # Load maintenance prediction model
            try:
                maintenance_data = model_loader.load_model('maintenance_model')
                self._maintenance_model = maintenance_data
                print("✓ Maintenance prediction model loaded")
            except Exception as e:
                print(f"⚠ Maintenance model not loaded: {e}")
            
            self._models_loaded = True
            
        except Exception as e:
            print(f"Error loading models: {e}")

    def _load_models(self):
        """Load all trained models on initialization"""
        try:
            print("Loading ML models...")
            
            # Load anomaly detection model
            try:
                anomaly_data = model_loader.load_model('anomaly_model')
                self._anomaly_model = anomaly_data
                print("✓ Anomaly detection model loaded")
            except FileNotFoundError:
                print("⚠ Anomaly model not found - train it first with train_anomaly.py")
            
            # Load activity recognition model
            try:
                activity_data = model_loader.load_model('activity_model')
                self._activity_model = activity_data
                print("✓ Activity recognition model loaded")
            except FileNotFoundError:
                print("⚠ Activity model not found - train it first with train_activity.py")
            
            # Load maintenance prediction model
            try:
                maintenance_data = model_loader.load_model('maintenance_model')
                self._maintenance_model = maintenance_data
                print("✓ Maintenance prediction model loaded")
            except FileNotFoundError:
                print("⚠ Maintenance model not found - train it first with train_maintenance.py")
                
        except Exception as e:
            print(f"Error loading models: {e}")
    
    def detect_anomaly(self, telemetry_data):

        self._ensure_models_loaded()
        """
        Detect anomalies in device telemetry
        
        Args:
            telemetry_data: Dict with keys: temperature, heart_rate, battery_level, 
                          signal_strength, usage_hours
        
        Returns:
            Dict with anomaly prediction results
        """
        if self._anomaly_model is None:
            raise RuntimeError("Anomaly model not loaded. Please train the model first.")
        
        try:
            # Extract features in correct order
            features = np.array([[
                telemetry_data.get('temperature', 37.0),
                telemetry_data.get('heart_rate', 75.0),
                telemetry_data.get('battery_level', 80.0),
                telemetry_data.get('signal_strength', -50.0),
                telemetry_data.get('usage_hours', 8.0)
            ]])
            
            # Scale features
            scaler = self._anomaly_model['scaler']
            features_scaled = scaler.transform(features)
            
            # Predict
            model = self._anomaly_model['model']
            prediction = model.predict(features_scaled)[0]
            probabilities = model.predict_proba(features_scaled)[0]
            
            is_anomaly = bool(prediction == 1)
            anomaly_score = float(probabilities[1])
            
            # Determine severity
            if anomaly_score > 0.8:
                severity = 'high'
            elif anomaly_score > 0.5:
                severity = 'medium'
            else:
                severity = 'low'
            
            message = (
                f'Unusual pattern detected (score: {anomaly_score:.2f})' 
                if is_anomaly 
                else 'Normal operation'
            )
            
            return {
                'is_anomaly': is_anomaly,
                'anomaly_score': anomaly_score,
                'confidence': anomaly_score if is_anomaly else (1 - anomaly_score),
                'severity': severity,
                'message': message
            }
            
        except Exception as e:
            print(f"Anomaly detection error: {e}")
            raise
    
    def recognize_activity(self, sensor_data):

        self._ensure_models_loaded()
        """
        Recognize user activity from sensor data
        
        Args:
            sensor_data: Dict with keys: accelerometer_x/y/z, gyroscope_x/y/z
        
        Returns:
            Dict with activity prediction results
        """
        if self._activity_model is None:
            raise RuntimeError("Activity model not loaded. Please train the model first.")
        
        try:
            # Extract features
            features = np.array([[
                sensor_data.get('accelerometer_x', 0.0),
                sensor_data.get('accelerometer_y', 0.0),
                sensor_data.get('accelerometer_z', 0.0),
                sensor_data.get('gyroscope_x', 0.0),
                sensor_data.get('gyroscope_y', 0.0),
                sensor_data.get('gyroscope_z', 0.0)
            ]])
            
            # Scale features
            scaler = self._activity_model['scaler']
            features_scaled = scaler.transform(features)
            
            # Predict
            model = self._activity_model['model']
            encoder = self._activity_model['encoder']
            
            prediction_encoded = model.predict(features_scaled)[0]
            probabilities = model.predict_proba(features_scaled)[0]
            
            # Decode prediction
            activity = encoder.inverse_transform([prediction_encoded])[0]
            confidence = float(probabilities[prediction_encoded])
            
            # Get all probabilities
            activity_probabilities = {
                encoder.inverse_transform([i])[0]: float(prob)
                for i, prob in enumerate(probabilities)
            }
            
            # Determine intensity based on sensor magnitudes
            acc_magnitude = np.sqrt(
                sensor_data.get('accelerometer_x', 0)**2 +
                sensor_data.get('accelerometer_y', 0)**2 +
                sensor_data.get('accelerometer_z', 0)**2
            )
            
            if acc_magnitude > 2.0:
                intensity = 'high'
            elif acc_magnitude > 1.0:
                intensity = 'medium'
            else:
                intensity = 'low'
            
            return {
                'activity': activity,
                'confidence': confidence,
                'intensity': intensity,
                'probabilities': activity_probabilities,
                'message': f'User is {activity}'
            }
            
        except Exception as e:
            print(f"Activity recognition error: {e}")
            raise
    
    def predict_maintenance(self, device_info):

        self._ensure_models_loaded()
        """
        Predict if device needs maintenance
        
        Args:
            device_info: Dict with keys: battery_health, charge_cycles, 
                        temperature_avg, error_count, uptime_days
        
        Returns:
            Dict with maintenance prediction results
        """
        if self._maintenance_model is None:
            raise RuntimeError("Maintenance model not loaded. Please train the model first.")
        
        try:
            # Extract features
            features = np.array([[
                device_info.get('battery_health', 80.0),
                device_info.get('charge_cycles', 100),
                device_info.get('temperature_avg', 35.0),
                device_info.get('error_count', 0),
                device_info.get('uptime_days', 30)
            ]])
            
            # Scale features
            scaler = self._maintenance_model['scaler']
            features_scaled = scaler.transform(features)
            
            # Predict
            model = self._maintenance_model['model']
            prediction = model.predict(features_scaled)[0]
            probabilities = model.predict_proba(features_scaled)[0]
            
            needs_maintenance = bool(prediction == 1)
            maintenance_confidence = float(probabilities[1])
            
            # Calculate days until maintenance
            days_until = int((1 - maintenance_confidence) * 30)
            
            # Determine priority
            if maintenance_confidence > 0.8:
                priority = 'high'
            elif maintenance_confidence > 0.6:
                priority = 'medium'
            else:
                priority = 'low'
            
            # Generate recommendations
            recommendations = {
                'check_battery': device_info.get('battery_health', 100) < 70,
                'clean_sensors': device_info.get('error_count', 0) > 5,
                'update_software': device_info.get('uptime_days', 0) > 180
            }
            
            message = (
                f'Maintenance predicted in {days_until} days'
                if needs_maintenance
                else 'No maintenance needed'
            )
            
            return {
                'needs_maintenance': needs_maintenance,
                'probability': maintenance_confidence,
                'confidence': maintenance_confidence,
                'days_until': days_until,
                'priority': priority,
                'recommendations': recommendations,
                'message': message
            }
            
        except Exception as e:
            print(f"Maintenance prediction error: {e}")
            raise
    
    def reload_models(self):
        """Reload all models (useful after retraining)"""
        model_loader.clear_cache()
        self._load_models()

    def _ensure_models_loaded(self):
        """Lazy load models on first use"""
        if self._models_loaded:
            return
        
        self._load_models()
        self._models_loaded = True

    def detect_object(self, detection_data: Dict) -> Dict:
            """
            Classify detected object and assess danger level
            
            Args:
                detection_data: {
                    object_detected: str,
                    distance_cm: float,
                    detection_source: str,
                    detection_confidence: float
                }
            
            Returns:
                {
                    object_detected: str,
                    distance_cm: float,
                    danger_level: str,
                    detection_confidence: float,
                    message: str
                }
            """
            object_type = detection_data.get('object_detected', 'unknown').lower()
            distance = detection_data.get('distance_cm', 999)
            confidence = detection_data.get('detection_confidence', 0.85)
            
            # Define danger levels based on distance and object type
            danger_level = self._calculate_danger_level(object_type, distance)
            
            # Generate message
            message = self._generate_detection_message(object_type, distance, danger_level)
            
            return {
                'object_detected': object_type,
                'distance_cm': distance,
                'danger_level': danger_level,
                'detection_confidence': confidence,
                'message': message
            }
        
    def _calculate_danger_level(self, object_type: str, distance_cm: float) -> str:
            """Calculate danger level based on object type and distance"""
            
            # High-risk objects (vehicles, stairs, potholes)
            high_risk_objects = ['vehicle', 'car', 'motorcycle', 'bicycle', 'stairs', 
                                'stairs_down', 'pothole', 'cliff', 'traffic']
            
            if object_type in high_risk_objects:
                if distance_cm < 100:
                    return 'Critical'
                elif distance_cm < 200:
                    return 'High'
                elif distance_cm < 400:
                    return 'Medium'
                else:
                    return 'Low'
            
            # Medium-risk objects (people, walls, poles)
            medium_risk_objects = ['person', 'wall', 'pole', 'tree', 'building', 
                                'obstacle', 'barrier', 'door']
            
            if object_type in medium_risk_objects:
                if distance_cm < 50:
                    return 'High'
                elif distance_cm < 150:
                    return 'Medium'
                else:
                    return 'Low'
            
            # Low-risk objects (furniture, small objects)
            if distance_cm < 30:
                return 'Medium'
            elif distance_cm < 100:
                return 'Low'
            else:
                return 'Low'
        
    def _generate_detection_message(self, object_type: str, distance: float, danger: str) -> str:
            """Generate appropriate warning message"""
            
            if danger == 'Critical':
                return f"⚠️ CRITICAL: {object_type.title()} very close at {distance:.0f}cm - STOP!"
            elif danger == 'High':
                return f"⚠️ WARNING: {object_type.title()} detected at {distance:.0f}cm - caution ahead"
            elif danger == 'Medium':
                return f"ℹ️ {object_type.title()} detected at {distance:.0f}cm"
            else:
                return f"{object_type.title()} detected at {distance:.0f}cm - clear path"
        
        # ========== FALL DETECTION ==========
        
    def detect_fall(self, sensor_data: Dict) -> Dict:
            """
            Detect if user has fallen based on accelerometer/gyroscope data
            
            Args:
                sensor_data: {
                    accelerometer_x: float,
                    accelerometer_y: float,
                    accelerometer_z: float,
                    gyroscope_x: float (optional),
                    gyroscope_y: float (optional),
                    gyroscope_z: float (optional),
                    time_since_last_movement: int (optional)
                }
            
            Returns:
                {
                    fall_detected: bool,
                    confidence: float,
                    severity: str,
                    post_fall_movement: bool,
                    impact_magnitude: float,
                    message: str,
                    emergency_alert: bool
                }
            """
            
            # Calculate acceleration magnitude
            acc_x = sensor_data.get('accelerometer_x', 0)
            acc_y = sensor_data.get('accelerometer_y', 0)
            acc_z = sensor_data.get('accelerometer_z', 0)
            
            magnitude = math.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
            
            # Fall detection thresholds
            FALL_THRESHOLD = 2.5  # g (sudden impact)
            FREE_FALL_THRESHOLD = 0.5  # g (free fall before impact)
            
            # Check for sudden impact (high acceleration)
            impact_detected = magnitude > FALL_THRESHOLD
            
            # Check for free fall before impact (low acceleration)
            free_fall = magnitude < FREE_FALL_THRESHOLD
            
            # Check if user moved after potential fall
            time_stationary = sensor_data.get('time_since_last_movement', 0)
            post_fall_movement = time_stationary < 3  # User moved within 3 seconds
            
            # Determine if it's a fall
            fall_detected = impact_detected and not post_fall_movement
            
            # Calculate confidence
            confidence = 0.0
            if impact_detected:
                confidence += 0.5
            if not post_fall_movement and time_stationary > 5:
                confidence += 0.3
            if free_fall:
                confidence += 0.2
            
            confidence = min(confidence, 0.95)
            
            # Determine severity
            severity = self._calculate_fall_severity(magnitude, time_stationary)
            
            # Emergency alert for critical falls
            emergency_alert = fall_detected and severity in ['high', 'critical']
            
            # Generate message
            if fall_detected:
                if emergency_alert:
                    message = f"🚨 FALL DETECTED! User unresponsive for {time_stationary}s - Emergency alert sent"
                else:
                    message = f"⚠️ Possible fall detected - checking user status..."
            else:
                message = "No fall detected - normal movement"
            
            return {
                'fall_detected': fall_detected,
                'confidence': confidence,
                'severity': severity,
                'post_fall_movement': post_fall_movement,
                'impact_magnitude': magnitude,
                'message': message,
                'emergency_alert': emergency_alert
            }
        
    def _calculate_fall_severity(self, impact_magnitude: float, time_stationary: int) -> str:
            """Calculate fall severity based on impact and lack of movement"""
            
            if impact_magnitude > 4.0 and time_stationary > 10:
                return 'critical'
            elif impact_magnitude > 3.0 and time_stationary > 5:
                return 'high'
            elif impact_magnitude > 2.5 or time_stationary > 3:
                return 'medium'
            else:
                return 'low'
        
        # ========== ROUTE PREDICTION ==========
        
    def predict_route(self, route_data: Dict) -> Dict:
            """
            Predict best route from current location to destination
            
            Args:
                route_data: {
                    current_location: {latitude: float, longitude: float},
                    destination: {latitude: float, longitude: float},
                    time_of_day: str,
                    avoid_obstacles: List[str] (optional),
                    max_detour_meters: int (optional)
                }
            
            Returns:
                {
                    predicted_route: List[{lat, lng}],
                    route_confidence: float,
                    estimated_obstacles: int,
                    difficulty_score: float,
                    estimated_time_minutes: int,
                    recommendation: str
                }
            """
            
            current = route_data['current_location']
            destination = route_data['destination']
            time_of_day = route_data.get('time_of_day', 'afternoon')
            
            # Calculate straight-line distance
            distance_km = self._calculate_distance(
                current['latitude'], current['longitude'],
                destination['latitude'], destination['longitude']
            )
            
            # For now, predict simple waypoints (in production, use pathfinding algorithm)
            # This is a simplified version - you'd integrate with Google Maps API or similar
            waypoints = self._generate_simple_route(current, destination)
            
            # Estimate obstacles based on distance and time of day
            estimated_obstacles = self._estimate_obstacles(distance_km, time_of_day)
            
            # Calculate difficulty (0-1 scale)
            difficulty_score = self._calculate_route_difficulty(
                distance_km, 
                estimated_obstacles, 
                time_of_day
            )
            
            # Estimate time (walking speed ~5 km/h)
            walking_speed_kmh = 5.0
            estimated_time_minutes = int((distance_km / walking_speed_kmh) * 60)
            
            # Add buffer for obstacles
            estimated_time_minutes += estimated_obstacles * 2  # 2 min per obstacle
            
            # Route confidence (higher for shorter routes)
            route_confidence = max(0.6, 1.0 - (distance_km / 10.0))
            
            # Generate recommendation
            recommendation = self._generate_route_recommendation(
                difficulty_score, 
                estimated_obstacles, 
                time_of_day
            )
            
            return {
                'predicted_route': waypoints,
                'route_confidence': route_confidence,
                'estimated_obstacles': estimated_obstacles,
                'difficulty_score': difficulty_score,
                'estimated_time_minutes': estimated_time_minutes,
                'recommendation': recommendation
            }
        
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            """Calculate distance between two GPS coordinates using Haversine formula"""
            
            R = 6371  # Earth's radius in kilometers
            
            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            
            a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            
            return R * c
        
    def _generate_simple_route(self, start: Dict, end: Dict) -> List[Dict]:
            """Generate simple waypoints (in production, use real routing API)"""
            
            # Simple linear interpolation for demo
            waypoints = [
                start,  # Starting point
                {
                    'latitude': (start['latitude'] + end['latitude']) / 2,
                    'longitude': (start['longitude'] + end['longitude']) / 2
                },  # Midpoint
                end  # Destination
            ]
            
            return waypoints
        
    def _estimate_obstacles(self, distance_km: float, time_of_day: str) -> int:
            """Estimate number of obstacles based on distance and time"""
            
            # Base obstacles per km
            obstacles_per_km = 3
            
            # Adjust for time of day
            if time_of_day in ['morning', 'evening']:
                obstacles_per_km += 2  # Rush hour, more people
            elif time_of_day == 'night':
                obstacles_per_km -= 1  # Less people, but reduced visibility
            
            return int(distance_km * obstacles_per_km)
        
    def _calculate_route_difficulty(self, distance_km: float, obstacles: int, time: str) -> float:
            """Calculate route difficulty score (0-1)"""
            
            difficulty = 0.0
            
            # Distance factor
            difficulty += min(0.3, distance_km / 10.0)
            
            # Obstacles factor
            difficulty += min(0.4, obstacles / 20.0)
            
            # Time of day factor
            if time == 'night':
                difficulty += 0.2
            elif time in ['morning', 'evening']:
                difficulty += 0.1
            
            return min(1.0, difficulty)
        
    def _generate_route_recommendation(self, difficulty: float, obstacles: int, time: str) -> str:
            """Generate route recommendation text"""
            
            if difficulty > 0.7:
                return f"⚠️ Challenging route with {obstacles} estimated obstacles. Consider alternative route or companion."
            elif difficulty > 0.5:
                return f"ℹ️ Moderate difficulty route. {obstacles} obstacles expected. Stay alert."
            else:
                return f"✅ Easy route. Clear path with minimal obstacles expected."


# Global instance
ml_service = MLService()