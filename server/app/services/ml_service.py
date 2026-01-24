import numpy as np
import logging
from app.ml_models.model_loader import model_loader

logger = logging.getLogger(__name__)

class MLService:
    def __init__(self):
        self.device_classifier = None
        self.anomaly_detector = None
        self.maintenance_predictor = None
        self.activity_recognizer = None
    
    def load_models(self):
        """Load all required models on startup"""
        success_count = 0
        total_models = 4
        
        try:
            # Original device classifier
            self.device_classifier = model_loader.load_model("device_classifier", "pkl")
            logger.info("✅ Device classifier loaded")
            success_count += 1
        except Exception as e:
            logger.warning(f"⚠️  Device classifier not loaded: {str(e)}")
        
        try:
            # Anomaly detector
            self.anomaly_detector = model_loader.load_model("anomaly_detector", "pkl")
            logger.info("✅ Anomaly detector loaded")
            success_count += 1
        except Exception as e:
            logger.warning(f"⚠️  Anomaly detector not loaded: {str(e)}")
        
        try:
            # Maintenance predictor
            self.maintenance_predictor = model_loader.load_model("maintenance_predictor", "pkl")
            logger.info("✅ Maintenance predictor loaded")
            success_count += 1
        except Exception as e:
            logger.warning(f"⚠️  Maintenance predictor not loaded: {str(e)}")
        
        try:
            # Activity recognizer
            self.activity_recognizer = model_loader.load_model("activity_recognizer", "pkl")
            logger.info("✅ Activity recognizer loaded")
            success_count += 1
        except Exception as e:
            logger.warning(f"⚠️  Activity recognizer not loaded: {str(e)}")
        
        logger.info(f"ML models loaded: {success_count}/{total_models}")
        return success_count > 0
    
    # ========== Device Classification ==========
    
    def predict_device_type(self, features: list) -> dict:
        """
        Predict device type based on features
        
        Args:
            features: List of 5 numerical features
        
        Returns:
            Dictionary with prediction and confidence
        """
        if self.device_classifier is None:
            raise RuntimeError("Device classifier not loaded")
        
        input_array = np.array(features).reshape(1, -1)
        
        prediction = self.device_classifier.predict(input_array)[0]
        probabilities = self.device_classifier.predict_proba(input_array)[0]
        
        device_types = {0: "smartphone", 1: "laptop", 2: "iot_device"}
        
        return {
            "device_type": device_types.get(prediction, "unknown"),
            "confidence": float(probabilities.max()),
            "all_probabilities": {
                device_types[i]: float(prob) 
                for i, prob in enumerate(probabilities)
            }
        }
    
    # ========== Anomaly Detection ==========
    
    def detect_anomaly(self, telemetry: dict) -> dict:
        """
        Detect if device behavior is anomalous
        
        Args:
            telemetry: {
                'battery_level': float (0-100),
                'usage_duration': float (minutes),
                'temperature': float (Celsius),
                'signal_strength': float (dBm),
                'error_count': int
            }
        
        Returns:
            Dictionary with anomaly detection results
        """
        if self.anomaly_detector is None:
            raise RuntimeError("Anomaly detector not loaded")
        
        # Extract features in correct order
        features = [
            telemetry.get('battery_level', 70),
            telemetry.get('usage_duration', 180),
            telemetry.get('temperature', 35),
            telemetry.get('signal_strength', -60),
            telemetry.get('error_count', 0)
        ]
        
        input_array = np.array(features).reshape(1, -1)
        
        # Predict: -1 = anomaly, 1 = normal
        prediction = self.anomaly_detector.predict(input_array)[0]
        
        # Get anomaly score (lower = more anomalous)
        anomaly_score = self.anomaly_detector.score_samples(input_array)[0]
        
        is_anomaly = prediction == -1
        
        # Normalize score to 0-1 (0 = normal, 1 = highly anomalous)
        # Typically scores range from -0.5 to 0.5, we'll map this
        normalized_score = max(0, min(1, (-anomaly_score + 0.5)))
        
        # Determine severity
        if normalized_score < 0.3:
            severity = "low"
        elif normalized_score < 0.6:
            severity = "medium"
        else:
            severity = "high"
        
        return {
            "is_anomaly": bool(is_anomaly),
            "anomaly_score": float(normalized_score),
            "severity": severity if is_anomaly else "none",
            "message": self._get_anomaly_message(telemetry, is_anomaly)
        }
    
    def _get_anomaly_message(self, telemetry: dict, is_anomaly: bool) -> str:
        """Generate human-readable anomaly message"""
        if not is_anomaly:
            return "Device behavior is normal"
        
        messages = []
        
        if telemetry.get('battery_level', 100) < 20:
            messages.append("critically low battery")
        if telemetry.get('temperature', 0) > 45:
            messages.append("device overheating")
        if telemetry.get('signal_strength', 0) < -80:
            messages.append("poor signal strength")
        if telemetry.get('error_count', 0) > 3:
            messages.append("high error rate")
        if telemetry.get('usage_duration', 180) > 300:
            messages.append("excessive usage")
        
        if messages:
            return "Detected: " + ", ".join(messages)
        return "Unusual device behavior detected"
    
    # ========== Predictive Maintenance ==========
    
    def predict_maintenance(self, device_data: dict) -> dict:
        """
        Predict if device needs maintenance
        
        Args:
            device_data: {
                'device_age_days': int,
                'battery_cycles': int,
                'usage_intensity': float (0-1),
                'error_rate': float,
                'last_maintenance_days': int
            }
        
        Returns:
            Dictionary with maintenance prediction
        """
        if self.maintenance_predictor is None:
            raise RuntimeError("Maintenance predictor not loaded")
        
        # Extract features in correct order
        features = [
            device_data.get('device_age_days', 0),
            device_data.get('battery_cycles', 0),
            device_data.get('usage_intensity', 0.5),
            device_data.get('error_rate', 0),
            device_data.get('last_maintenance_days', 0)
        ]
        
        input_array = np.array(features).reshape(1, -1)
        
        # Predict
        prediction = self.maintenance_predictor.predict(input_array)[0]
        probabilities = self.maintenance_predictor.predict_proba(input_array)[0]
        
        needs_maintenance = bool(prediction == 1)
        confidence = float(probabilities[1])  # Probability of needing maintenance
        
        # Calculate estimated days until maintenance
        if needs_maintenance:
            days_until_maintenance = 0
        else:
            # Estimate based on confidence (higher confidence = sooner)
            days_until_maintenance = int((1 - confidence) * 90)  # 0-90 days
        
        # Determine priority
        if confidence > 0.8:
            priority = "high"
        elif confidence > 0.5:
            priority = "medium"
        else:
            priority = "low"
        
        return {
            "needs_maintenance": needs_maintenance,
            "confidence": confidence,
            "priority": priority,
            "estimated_days_until_maintenance": days_until_maintenance,
            "recommendations": self._get_maintenance_recommendations(device_data, needs_maintenance, confidence)
        }
    
    def _get_maintenance_recommendations(self, device_data: dict, needs_maintenance: bool, confidence: float) -> list:
        """Generate maintenance recommendations"""
        recommendations = []
        
        if device_data.get('battery_cycles', 0) > 500:
            recommendations.append("Consider battery replacement")
        
        if device_data.get('device_age_days', 0) > 365:
            recommendations.append("Schedule annual inspection")
        
        if device_data.get('error_rate', 0) > 2:
            recommendations.append("Check for software updates")
        
        if device_data.get('last_maintenance_days', 0) > 90:
            recommendations.append("Overdue for routine maintenance")
        
        if not recommendations and needs_maintenance:
            recommendations.append("General maintenance check recommended")
        
        if not recommendations:
            recommendations.append("Device is in good condition")
        
        return recommendations
    
    # ========== Activity Recognition ==========
    
    def recognize_activity(self, sensor_data: dict) -> dict:
        """
        Recognize user activity from sensor data
        
        Args:
            sensor_data: {
                'acc_x': float,
                'acc_y': float,
                'acc_z': float,
                'gyro_x': float,
                'gyro_y': float,
                'gyro_z': float
            }
        
        Returns:
            Dictionary with activity recognition results
        """
        if self.activity_recognizer is None:
            raise RuntimeError("Activity recognizer not loaded")
        
        # Extract features in correct order
        features = [
            sensor_data.get('acc_x', 0),
            sensor_data.get('acc_y', 0),
            sensor_data.get('acc_z', 9.8),  # Default to gravity
            sensor_data.get('gyro_x', 0),
            sensor_data.get('gyro_y', 0),
            sensor_data.get('gyro_z', 0)
        ]
        
        input_array = np.array(features).reshape(1, -1)
        
        # Predict
        prediction = self.activity_recognizer.predict(input_array)[0]
        probabilities = self.activity_recognizer.predict_proba(input_array)[0]
        
        activity_names = {
            0: "resting",
            1: "walking",
            2: "using_device"
        }
        
        activity_descriptions = {
            0: "User is resting (sitting or lying down)",
            1: "User is walking",
            2: "User is actively using the device"
        }
        
        activity = activity_names.get(prediction, "unknown")
        confidence = float(probabilities.max())
        
        return {
            "activity": activity,
            "description": activity_descriptions.get(prediction, "Unknown activity"),
            "confidence": confidence,
            "all_probabilities": {
                activity_names[i]: float(prob) 
                for i, prob in enumerate(probabilities)
            },
            "intensity": self._calculate_activity_intensity(features)
        }
    
    def _calculate_activity_intensity(self, features: list) -> str:
        """Calculate activity intensity based on sensor magnitudes"""
        acc_magnitude = np.sqrt(features[0]**2 + features[1]**2 + features[2]**2)
        gyro_magnitude = np.sqrt(features[3]**2 + features[4]**2 + features[5]**2)
        
        total_intensity = acc_magnitude + (gyro_magnitude / 10)  # Scale gyro
        
        if total_intensity < 12:
            return "low"
        elif total_intensity < 18:
            return "moderate"
        else:
            return "high"

# Create singleton instance
ml_service = MLService()