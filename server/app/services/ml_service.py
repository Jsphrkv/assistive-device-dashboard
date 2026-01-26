import numpy as np
from app.ml_models.model_loader import model_loader

class MLService:
    """ML inference service for IoT predictions"""
    
    def __init__(self):
        self._anomaly_model = None
        self._activity_model = None
        self._maintenance_model = None
        self._load_models()
    
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


# Global instance
ml_service = MLService()