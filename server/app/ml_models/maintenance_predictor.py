"""
Maintenance Predictor - Predicts device maintenance needs
"""

import numpy as np


class MaintenancePredictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        
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
            dict with maintenance prediction results
        """
        if not self.model:
            return {
                'needs_maintenance': False,
                'probability': 0.0,
                'priority': 'low',
                'days_until': 90,
                'message': 'Model not loaded',
                'recommendations': {}
            }
        
        try:
            # Extract features
            features = np.array([[
                device_data.get('battery_health', 100),
                device_data.get('usage_hours', 0),
                device_data.get('temperature_avg', 25.0),
                device_data.get('error_count', 0),
                device_data.get('days_since_last_maintenance', 0)
            ]])
            
            # Scale if scaler available
            if self.scaler:
                features = self.scaler.transform(features)
            
            # Predict
            prediction = self.model.predict(features)[0]
            
            # Get probability
            try:
                probability = self.model.predict_proba(features)[0][1]
            except:
                probability = 0.5 if prediction == 1 else 0.1
            
            needs_maintenance = bool(prediction == 1)
            
            # Determine priority and days
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
                'probability': float(probability),
                'priority': priority,
                'days_until': int(days_until),
                'message': message,
                'recommendations': recommendations
            }
            
        except Exception as e:
            print(f"Error in maintenance prediction: {e}")
            return {
                'needs_maintenance': False,
                'probability': 0.0,
                'priority': 'low',
                'days_until': 90,
                'message': f"Prediction error: {str(e)}",
                'recommendations': {}
            }