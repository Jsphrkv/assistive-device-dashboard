"""
Danger Predictor - Wrapper for danger prediction model
Predicts danger level and recommends action
"""

import numpy as np
from .model_loader import model_loader

class DangerPredictor:
    def __init__(self):
        self.model_name = 'danger_prediction_model'
        
    def predict(self, danger_data):
        """
        Predict danger level and recommend action
        
        Args:
            danger_data: dict with keys:
                - distance_cm (float)
                - rate_of_change (float): cm/s, negative = approaching
                - proximity_value (int)
                - object_type (str): 'obstacle', 'person', 'vehicle', etc.
                - current_speed_estimate (float): m/s
        
        Returns:
            dict with:
                - danger_score (float): 0-100
                - recommended_action (str): STOP/SLOW_DOWN/CAUTION/SAFE
                - time_to_collision (float): seconds
                - confidence (float)
                - message (str)
        """
        try:
            # Encode object type
            object_encoding = {
                'obstacle': 0,
                'person': 1,
                'vehicle': 2,
                'wall': 3,
                'stairs_down': 4,
                'stairs_up': 4,
                'door': 3,
                'pole': 0
            }
            
            object_type = danger_data.get('object_type', 'obstacle')
            object_encoded = object_encoding.get(object_type, 0)
            
            # Extract features in correct order
            features = [
                danger_data.get('distance_cm', 100.0),
                danger_data.get('rate_of_change', 0.0),
                danger_data.get('proximity_value', 5000),
                object_encoded,
                danger_data.get('current_speed_estimate', 1.0)
            ]
            
            # Get prediction from model_loader
            result = model_loader.predict_danger(features)
            
            danger_score = result['danger_score']
            recommended_action = result['recommended_action']
            
            # Calculate time to collision
            distance = danger_data.get('distance_cm', 100)
            speed = abs(danger_data.get('rate_of_change', 0))
            
            if speed > 1:  # Moving
                time_to_collision = distance / speed
            else:
                time_to_collision = 999  # Stationary
            
            # Generate message based on danger level
            if danger_score >= 80:
                message = f"🚨 CRITICAL: {object_type.upper()} at {distance:.0f}cm! {recommended_action} immediately!"
            elif danger_score >= 60:
                message = f"⚠️ HIGH DANGER: {object_type} approaching at {distance:.0f}cm. {recommended_action}!"
            elif danger_score >= 30:
                message = f"⚡ CAUTION: {object_type} detected at {distance:.0f}cm. {recommended_action}."
            else:
                message = f"ℹ️ Safe: {object_type} at {distance:.0f}cm. Proceed normally."
            
            # Confidence based on data quality
            if speed > 0:
                confidence = min(0.95, 0.7 + (speed / 100))
            else:
                confidence = 0.75
            
            return {
                'danger_score': float(danger_score),
                'recommended_action': recommended_action,
                'time_to_collision': float(time_to_collision),
                'confidence': float(confidence),
                'message': message
            }
            
        except Exception as e:
            raise RuntimeError(f"Danger prediction failed: {e}")