"""
Maintenance Predictor - Wrapper for maintenance prediction model
"""

import numpy as np
from .model_loader import model_loader

class MaintenancePredictor:
    def __init__(self):
        self.model_name = 'maintenance_model'
        
    def predict(self, device_data):
        """
        Predict if device needs maintenance
        
        Args:
            device_data: dict with keys:
                - battery_health (int): 0-100
                - usage_hours (int)
                - temperature_avg (float)
                - error_count (int)
                - days_since_last_maintenance (int)
        
        Returns:
            dict with:
                - needs_maintenance (bool)
                - probability (float)
                - priority (str)
                - days_until (int)
                - message (str)
                - recommendations (dict)
        """
        try:
            # Extract features in correct order
            features = [
                device_data.get('battery_health', 100),
                device_data.get('usage_hours', 0),
                device_data.get('temperature_avg', 25.0),
                device_data.get('error_count', 0),
                device_data.get('days_since_last_maintenance', 0)
            ]
            
            # Get prediction
            result = model_loader.predict_maintenance(features)
            
            probability = result['probability']
            needs_maintenance = result['needs_maintenance']
            
            # Determine priority
            if probability >= 0.8:
                priority = 'high'
                days_until = 7
                message = 'Urgent: Schedule maintenance within 7 days'
            elif probability >= 0.5:
                priority = 'medium'
                days_until = 30
                message = 'Maintenance recommended within 30 days'
            else:
                priority = 'low'
                days_until = 90
                message = 'Device in good condition'
            
            # Generate recommendations
            recommendations = {}
            if device_data.get('battery_health', 100) < 70:
                recommendations['battery'] = 'Consider battery replacement'
            if device_data.get('temperature_avg', 25) > 35:
                recommendations['cooling'] = 'Check cooling system'
            if device_data.get('error_count', 0) > 10:
                recommendations['errors'] = 'Investigate error logs'
            
            return {
                'needs_maintenance': needs_maintenance,
                'probability': probability,
                'confidence': result['confidence'],
                'priority': priority,
                'days_until': days_until,
                'message': message,
                'recommendations': recommendations
            }
            
        except Exception as e:
            raise RuntimeError(f"Maintenance prediction failed: {e}")