import numpy as np
from app.ml_models.model_loader import model_loader
from typing import Dict, List
import math

class MLService:
    """
    ML inference service for IoT predictions
    Supports 5 models:
    1. Anomaly Detection
    2. Maintenance Prediction
    3. Object Detection
    4. Danger Prediction (NEW)
    5. Environment Classification (NEW)
    """
    
    def __init__(self):
        self._anomaly_model = None
        self._maintenance_model = None
        self._object_detection_model = None
        self._danger_prediction_model = None
        self._environment_classifier = None
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
            
            # Load maintenance prediction model
            try:
                maintenance_data = model_loader.load_model('maintenance_model')
                self._maintenance_model = maintenance_data
                print("✓ Maintenance prediction model loaded")
            except Exception as e:
                print(f"⚠ Maintenance model not loaded: {e}")
            
            # Load object detection model
            try:
                object_data = model_loader.load_model('object_detection_model')
                self._object_detection_model = object_data
                print("✓ Object detection model loaded")
            except Exception as e:
                print(f"⚠ Object detection model not loaded: {e}")
            
            # Load danger prediction model (NEW)
            try:
                danger_data = model_loader.load_model('danger_prediction_model')
                self._danger_prediction_model = danger_data
                print("✓ Danger prediction model loaded")
            except Exception as e:
                print(f"⚠ Danger prediction model not loaded: {e}")
            
            # Load environment classifier (NEW)
            try:
                env_data = model_loader.load_model('environment_classifier')
                self._environment_classifier = env_data
                print("✓ Environment classifier loaded")
            except Exception as e:
                print(f"⚠ Environment classifier not loaded: {e}")
            
            self._models_loaded = True
            
        except Exception as e:
            print(f"Error loading models: {e}")
    
    # ========== 1. ANOMALY DETECTION ==========
    
    def detect_anomaly(self, telemetry_data: dict) -> dict:
        """
        Detect anomalies in device telemetry
        
        Args:
            telemetry_data: Dict with keys: temperature, heart_rate, battery_level, 
                          signal_strength, usage_hours
        
        Returns:
            Dict with anomaly prediction results:
            {
                'is_anomaly': bool,
                'anomaly_score': float,
                'confidence': float,
                'severity': str,
                'device_health_score': float,
                'message': str
            }
        """
        self._ensure_models_loaded()
        
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
            
            # Calculate device health score (100 = perfect, 0 = critical)
            device_health_score = 100 * (1 - anomaly_score) if is_anomaly else 100.0
            
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
                'device_health_score': device_health_score,
                'message': message
            }
            
        except Exception as e:
            print(f"Anomaly detection error: {e}")
            raise
    
    # ========== 2. MAINTENANCE PREDICTION ==========
    
    def predict_maintenance(self, device_info: dict) -> dict:
        """
        Predict if device needs maintenance
        
        Args:
            device_info: Dict with keys: battery_health, charge_cycles, 
                        temperature_avg, error_count, uptime_days
        
        Returns:
            Dict with maintenance prediction results:
            {
                'needs_maintenance': bool,
                'probability': float,
                'confidence': float,
                'days_until': int,
                'priority': str,
                'recommendations': dict,
                'message': str
            }
        """
        self._ensure_models_loaded()
        
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
    
    # ========== 3. OBJECT DETECTION ==========
    
    def detect_object(self, detection_data: dict) -> dict:
        """
        Classify detected object and assess danger level
        
        Args:
            detection_data: {
                'object_detected': str,
                'distance_cm': float,
                'detection_source': str (optional),
                'detection_confidence': float (optional)
            }
        
        Returns:
            Dict with object detection results:
            {
                'object_detected': str,
                'distance_cm': float,
                'danger_level': str,
                'detection_confidence': float,
                'message': str
            }
        """
        self._ensure_models_loaded()
        
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
                return 'critical'
            elif distance_cm < 200:
                return 'high'
            elif distance_cm < 400:
                return 'medium'
            else:
                return 'low'
        
        # Medium-risk objects (people, walls, poles)
        medium_risk_objects = ['person', 'wall', 'pole', 'tree', 'building', 
                            'obstacle', 'barrier', 'door']
        
        if object_type in medium_risk_objects:
            if distance_cm < 50:
                return 'high'
            elif distance_cm < 150:
                return 'medium'
            else:
                return 'low'
        
        # Low-risk objects (furniture, small objects)
        if distance_cm < 30:
            return 'medium'
        elif distance_cm < 100:
            return 'low'
        else:
            return 'low'
    
    def _generate_detection_message(self, object_type: str, distance: float, danger: str) -> str:
        """Generate appropriate warning message"""
        
        if danger == 'critical':
            return f"⚠️ CRITICAL: {object_type.title()} very close at {distance:.0f}cm - STOP!"
        elif danger == 'high':
            return f"⚠️ WARNING: {object_type.title()} detected at {distance:.0f}cm - caution ahead"
        elif danger == 'medium':
            return f"ℹ️ {object_type.title()} detected at {distance:.0f}cm"
        else:
            return f"{object_type.title()} detected at {distance:.0f}cm - clear path"
    
    # ========== 4. DANGER PREDICTION (NEW) ==========
    
    def predict_danger(self, sensor_data: dict) -> dict:
        """
        Predict danger level and recommend action based on sensor data
        
        Args:
            sensor_data: {
                'distance_sensors': List[float],  # distances from multiple sensors
                'speed': float,  # current speed in m/s
                'acceleration': float (optional),
                'obstacles_detected': int (optional)
            }
        
        Returns:
            Dict with danger prediction results:
            {
                'danger_score': float (0-100),
                'recommended_action': str ('SAFE', 'CAUTION', 'SLOW_DOWN', 'STOP'),
                'time_to_collision': float (seconds, or None),
                'confidence': float,
                'message': str
            }
        """
        self._ensure_models_loaded()
        
        try:
            distance_sensors = sensor_data.get('distance_sensors', [500, 500, 500])
            speed = sensor_data.get('speed', 0.0)  # m/s
            acceleration = sensor_data.get('acceleration', 0.0)
            obstacles = sensor_data.get('obstacles_detected', 0)
            
            # Calculate minimum distance
            min_distance = min(distance_sensors) if distance_sensors else 500
            
            # Calculate time to collision
            if speed > 0.1 and min_distance < 1000:  # Convert cm to m
                time_to_collision = (min_distance / 100) / speed  # seconds
            else:
                time_to_collision = None
            
            # Calculate danger score (0-100)
            danger_score = self._calculate_danger_score(
                min_distance, 
                speed, 
                acceleration, 
                obstacles,
                time_to_collision
            )
            
            # Determine recommended action
            recommended_action = self._determine_action(danger_score, time_to_collision)
            
            # Calculate confidence
            confidence = self._calculate_danger_confidence(
                distance_sensors, 
                speed, 
                obstacles
            )
            
            # Generate message
            message = self._generate_danger_message(
                danger_score, 
                recommended_action, 
                time_to_collision
            )
            
            return {
                'danger_score': danger_score,
                'recommended_action': recommended_action,
                'time_to_collision': time_to_collision,
                'confidence': confidence,
                'message': message
            }
            
        except Exception as e:
            print(f"Danger prediction error: {e}")
            raise
    
    def _calculate_danger_score(self, distance: float, speed: float, 
                                accel: float, obstacles: int, 
                                ttc: float = None) -> float:
        """Calculate danger score (0-100)"""
        
        score = 0.0
        
        # Distance factor (closer = more dangerous)
        if distance < 50:
            score += 40
        elif distance < 100:
            score += 30
        elif distance < 200:
            score += 20
        elif distance < 400:
            score += 10
        
        # Speed factor (faster = more dangerous)
        if speed > 2.0:  # > 7.2 km/h
            score += 25
        elif speed > 1.0:  # > 3.6 km/h
            score += 15
        elif speed > 0.5:  # > 1.8 km/h
            score += 5
        
        # Time to collision factor
        if ttc is not None and ttc < 5:
            score += 20 * (5 - ttc) / 5  # Up to 20 points
        
        # Obstacles factor
        score += min(15, obstacles * 3)
        
        return min(100.0, score)
    
    def _determine_action(self, danger_score: float, ttc: float = None) -> str:
        """Determine recommended action"""
        
        if danger_score >= 80 or (ttc is not None and ttc < 1.0):
            return 'STOP'
        elif danger_score >= 60 or (ttc is not None and ttc < 2.0):
            return 'SLOW_DOWN'
        elif danger_score >= 30:
            return 'CAUTION'
        else:
            return 'SAFE'
    
    def _calculate_danger_confidence(self, distances: list, speed: float, 
                                     obstacles: int) -> float:
        """Calculate prediction confidence"""
        
        confidence = 0.7  # Base confidence
        
        # More sensors = higher confidence
        if len(distances) >= 3:
            confidence += 0.1
        
        # Consistent readings = higher confidence
        if len(distances) > 1:
            variance = np.var(distances)
            if variance < 100:  # Low variance
                confidence += 0.1
        
        # Speed data available = higher confidence
        if speed > 0:
            confidence += 0.1
        
        return min(0.95, confidence)
    
    def _generate_danger_message(self, score: float, action: str, 
                                 ttc: float = None) -> str:
        """Generate danger warning message"""
        
        if action == 'STOP':
            if ttc:
                return f"🚨 STOP! Collision imminent in {ttc:.1f}s (danger: {score:.0f}%)"
            return f"🚨 STOP! Critical danger detected ({score:.0f}%)"
        elif action == 'SLOW_DOWN':
            return f"⚠️ SLOW DOWN - High danger ahead ({score:.0f}%)"
        elif action == 'CAUTION':
            return f"⚠️ CAUTION - Moderate danger ({score:.0f}%)"
        else:
            return f"✅ Path clear - Low danger ({score:.0f}%)"
    
    # ========== 5. ENVIRONMENT CLASSIFICATION (NEW) ==========
    
    def classify_environment(self, sensor_data: dict) -> dict:
        """
        Classify environment type based on sensor patterns
        
        Args:
            sensor_data: {
                'ambient_light': float,  # lux
                'noise_level': float,  # decibels
                'obstacle_density': float,  # obstacles per meter
                'space_width': float (optional),  # meters
                'gps_accuracy': float (optional)  # meters
            }
        
        Returns:
            Dict with environment classification:
            {
                'environment_type': str (indoor/outdoor/crowded/open_space/narrow_corridor),
                'lighting_condition': str (bright/dim/dark),
                'complexity_level': str (simple/moderate/complex),
                'confidence': float,
                'message': str
            }
        """
        self._ensure_models_loaded()
        
        try:
            ambient_light = sensor_data.get('ambient_light', 500)  # lux
            noise_level = sensor_data.get('noise_level', 60)  # dB
            obstacle_density = sensor_data.get('obstacle_density', 0.5)  # per meter
            space_width = sensor_data.get('space_width', 3.0)  # meters
            gps_accuracy = sensor_data.get('gps_accuracy', 10.0)  # meters
            
            # Classify lighting condition
            lighting_condition = self._classify_lighting(ambient_light)
            
            # Classify environment type
            environment_type = self._classify_environment_type(
                gps_accuracy,
                space_width,
                obstacle_density,
                noise_level
            )
            
            # Classify complexity level
            complexity_level = self._classify_complexity(
                obstacle_density,
                lighting_condition,
                space_width
            )
            
            # Calculate confidence
            confidence = self._calculate_environment_confidence(
                ambient_light,
                gps_accuracy,
                obstacle_density
            )
            
            # Generate message
            message = self._generate_environment_message(
                environment_type,
                lighting_condition,
                complexity_level
            )
            
            return {
                'environment_type': environment_type,
                'lighting_condition': lighting_condition,
                'complexity_level': complexity_level,
                'confidence': confidence,
                'message': message
            }
            
        except Exception as e:
            print(f"Environment classification error: {e}")
            raise
    
    def _classify_lighting(self, lux: float) -> str:
        """Classify lighting condition"""
        
        if lux > 500:
            return 'bright'
        elif lux > 100:
            return 'dim'
        else:
            return 'dark'
    
    def _classify_environment_type(self, gps_accuracy: float, width: float,
                                   density: float, noise: float) -> str:
        """Classify environment type"""
        
        # Indoor detection (poor GPS + narrow space)
        if gps_accuracy > 20 and width < 5:
            # Narrow corridor
            if width < 2:
                return 'narrow_corridor'
            # Crowded indoor
            elif density > 1.0 or noise > 70:
                return 'crowded'
            # Regular indoor
            else:
                return 'indoor'
        
        # Outdoor detection (good GPS)
        else:
            # Crowded outdoor (high density or noise)
            if density > 1.5 or noise > 75:
                return 'crowded'
            # Open space (wide + low density)
            elif width > 10 and density < 0.3:
                return 'open_space'
            # Regular outdoor
            else:
                return 'outdoor'
    
    def _classify_complexity(self, density: float, lighting: str, 
                            width: float) -> str:
        """Classify complexity level"""
        
        complexity_score = 0
        
        # Density factor
        if density > 1.5:
            complexity_score += 2
        elif density > 0.8:
            complexity_score += 1
        
        # Lighting factor
        if lighting == 'dark':
            complexity_score += 2
        elif lighting == 'dim':
            complexity_score += 1
        
        # Space factor
        if width < 2:
            complexity_score += 2
        elif width < 5:
            complexity_score += 1
        
        # Classify based on score
        if complexity_score >= 4:
            return 'complex'
        elif complexity_score >= 2:
            return 'moderate'
        else:
            return 'simple'
    
    def _calculate_environment_confidence(self, light: float, gps: float, 
                                         density: float) -> float:
        """Calculate classification confidence"""
        
        confidence = 0.6  # Base confidence
        
        # Clear lighting reading
        if light > 10:  # Not in complete darkness
            confidence += 0.15
        
        # Good GPS signal (or very poor, indicating indoor)
        if gps < 10 or gps > 30:
            confidence += 0.15
        
        # Obstacle data available
        if density > 0:
            confidence += 0.1
        
        return min(0.95, confidence)
    
    def _generate_environment_message(self, env_type: str, lighting: str, 
                                     complexity: str) -> str:
        """Generate environment description message"""
        
        messages = {
            'indoor': f"📍 Indoor environment - {lighting} lighting, {complexity} navigation",
            'outdoor': f"🌤️ Outdoor environment - {lighting} lighting, {complexity} navigation",
            'crowded': f"👥 Crowded area - {lighting} lighting, {complexity} navigation",
            'open_space': f"🏞️ Open space - {lighting} lighting, {complexity} navigation",
            'narrow_corridor': f"🚪 Narrow corridor - {lighting} lighting, {complexity} navigation"
        }
        
        return messages.get(env_type, f"Environment detected - {lighting}, {complexity}")
    
    # ========== UTILITY METHODS ==========
    
    def reload_models(self):
        """Reload all models (useful after retraining)"""
        model_loader.clear_cache()
        self._models_loaded = False
        self._ensure_models_loaded()
    
    def get_model_status(self) -> dict:
        """Get status of all models"""
        return {
            'anomaly': self._anomaly_model is not None,
            'maintenance': self._maintenance_model is not None,
            'object_detection': self._object_detection_model is not None,
            'danger_prediction': self._danger_prediction_model is not None,
            'environment_classification': self._environment_classifier is not None,
            'all_loaded': all([
                self._anomaly_model is not None,
                self._maintenance_model is not None,
                self._object_detection_model is not None,
                self._danger_prediction_model is not None,
                self._environment_classifier is not None
            ])
        }


# Global instance
ml_service = MLService()