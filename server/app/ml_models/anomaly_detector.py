"""
Anomaly Detector - Wrapper for anomaly detection model
"""

import numpy as np
from .model_loader import model_loader

class AnomalyDetector:
    def __init__(self):
        self.model_name = 'anomaly_model'
        
    def detect(self, telemetry_data):
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
            dict with:
                - is_anomaly (bool)
                - anomaly_score (float)
                - severity (str)
                - message (str)
        """
        try:
            # Extract features in correct order
            features = [
                telemetry_data.get('temperature_c', 25.0),
                telemetry_data.get('battery_level', 100),
                telemetry_data.get('cpu_usage', 50),
                telemetry_data.get('rssi', -50),
                telemetry_data.get('error_count', 0)
            ]
            
            # Get prediction
            result = model_loader.predict_anomaly(features)
            
            # Determine severity
            score = result['anomaly_score']
            if score >= 0.8:
                severity = 'high'
                message = 'Critical anomaly detected - immediate attention required'
            elif score >= 0.5:
                severity = 'medium'
                message = 'Moderate anomaly detected - check device status'
            else:
                severity = 'low'
                message = 'Device operating normally'
            
            return {
                'is_anomaly': result['is_anomaly'],
                'anomaly_score': score,
                'confidence': result['confidence'],
                'severity': severity,
                'message': message
            }
            
        except Exception as e:
            raise RuntimeError(f"Anomaly detection failed: {e}")