"""
Danger Predictor - Predicts danger level and recommends action
"""

import numpy as np


class DangerPredictor:
    def __init__(self):
        self.score_model = None
        self.action_model = None
        self.scaler = None
        
    def predict(self, danger_data):
        """
        Predict danger level and recommend action
        
        Args:
            danger_data: dict with keys:
                - distance_cm (float)
                - rate_of_change (float): cm/s, negative = approaching
                - proximity_value (int)
                - object_type (str)
                - current_speed_estimate (float): m/s
        
        Returns:
            dict with danger prediction results
        """
        if not self.score_model or not self.action_model:
            return {
                'danger_score': 0.0,
                'recommended_action': 'SAFE',
                'time_to_collision': 999.0,
                'confidence': 0.0,
                'message': 'Model not loaded'
            }
        
        try:
            # Encode object type
            object_encoding = {
                'obstacle': 0,
                'person': 1,
                'vehicle': 2,
                'wall': 3,
                'stairs': 4,
                'stairs_down': 4,
                'stairs_up': 4,
                'door': 3,
                'pole': 0,
                'unknown': 0
            }
            
            object_type = danger_data.get('object_type', 'obstacle')
            object_encoded = object_encoding.get(object_type, 0)
            
            # Extract features
            features = np.array([[
                danger_data.get('distance_cm', 100.0),
                danger_data.get('rate_of_change', 0.0),
                danger_data.get('proximity_value', 5000),
                object_encoded,
                danger_data.get('current_speed_estimate', 1.0)
            ]])
            
            # Scale if scaler available
            if self.scaler:
                features = self.scaler.transform(features)
            
            # Predict danger score
            danger_score = self.score_model.predict(features)[0]
            danger_score = max(0.0, min(100.0, danger_score))
            
            # Predict recommended action
            action_prediction = self.action_model.predict(features)[0]
            actions = ['SAFE', 'CAUTION', 'SLOW_DOWN', 'STOP']
            recommended_action = actions[action_prediction] if action_prediction < len(actions) else 'SAFE'
            
            # Calculate time to collision
            distance = danger_data.get('distance_cm', 100)
            speed = abs(danger_data.get('rate_of_change', 0))
            
            if speed > 1:
                time_to_collision = distance / speed
            else:
                time_to_collision = 999.0
            
            # Generate message
            if danger_score >= 80:
                message = f"🚨 CRITICAL: {object_type.upper()} at {distance:.0f}cm! {recommended_action} immediately!"
            elif danger_score >= 60:
                message = f"⚠️ HIGH DANGER: {object_type} approaching at {distance:.0f}cm. {recommended_action}!"
            elif danger_score >= 30:
                message = f"⚡ CAUTION: {object_type} detected at {distance:.0f}cm. {recommended_action}."
            else:
                message = f"ℹ️ Safe: {object_type} at {distance:.0f}cm. Proceed normally."
            
            # Calculate confidence
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
            print(f"Error in danger prediction: {e}")
            return {
                'danger_score': 0.0,
                'recommended_action': 'SAFE',
                'time_to_collision': 999.0,
                'confidence': 0.0,
                'message': f"Prediction error: {str(e)}"
            }