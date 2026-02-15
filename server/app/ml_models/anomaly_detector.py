"""
Anomaly Detector - Detects anomalies in device telemetry
"""

import numpy as np


class AnomalyDetector:
    def __init__(self):
        self.model = None
        self.scaler = None
        
    def predict(self, telemetry_data):
        """
        Detect anomalies in device telemetry
        
        Args:
            telemetry_data: dict with keys:
                - temperature_c (float)
                - battery_level (int)
                - cpu_usage (int)
                - rssi (int)
                - error_count (int)
        
        Returns:
            dict with anomaly detection results
        """
        if not self.model:
            return {
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "severity": "low",
                "device_health_score": 100.0,
                "message": "Model not loaded"
            }
        
        try:
            # Extract features
            features = np.array([[
                telemetry_data.get('temperature_c', 25.0),
                telemetry_data.get('battery_level', 100),
                telemetry_data.get('cpu_usage', 50),
                telemetry_data.get('rssi', -50),
                telemetry_data.get('error_count', 0)
            ]])
            
            # Scale if scaler available
            if self.scaler:
                features = self.scaler.transform(features)
            
            # Predict
            prediction = self.model.predict(features)[0]
            
            # Get anomaly score
            try:
                anomaly_score = abs(self.model.decision_function(features)[0])
            except:
                anomaly_score = 0.5 if prediction == -1 else 0.0
            
            is_anomaly = (prediction == -1)
            
            # Determine severity
            if anomaly_score >= 0.8:
                severity = 'high'
                message = 'Critical anomaly detected - immediate attention required'
            elif anomaly_score >= 0.5:
                severity = 'medium'
                message = 'Moderate anomaly detected - check device status'
            else:
                severity = 'low'
                message = 'Device operating normally'
            
            # Calculate device health
            device_health_score = max(0.0, min(100.0, 100.0 - (anomaly_score * 100)))
            
            return {
                'is_anomaly': bool(is_anomaly),
                'anomaly_score': float(anomaly_score),
                'severity': severity,
                'device_health_score': float(device_health_score),
                'message': message
            }
            
        except Exception as e:
            print(f"Error in anomaly prediction: {e}")
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'severity': 'low',
                'device_health_score': 100.0,
                'message': f"Prediction error: {str(e)}"
            }