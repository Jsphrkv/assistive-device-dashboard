"""
Object Detector - Detects and classifies objects/obstacles
"""

import numpy as np


class ObjectDetector:
    def __init__(self):
        self.model = None
        self.scaler = None
        
    def predict(self, detection_data):
        """
        Detect and classify objects/obstacles
        
        Args:
            detection_data: dict with keys:
                - distance_cm (float)
                - detection_confidence (float)
                - proximity_value (int)
                - ambient_light (int)
        
        Returns:
            dict with object detection results
        """
        if not self.model:
            return {
                'object_detected': 'unknown',
                'distance_cm': detection_data.get('distance_cm', 100.0),
                'danger_level': 'Low',
                'detection_confidence': 0.0,
                'message': 'Model not loaded'
            }
        
        try:
            # Extract features
            features = np.array([[
                detection_data.get('distance_cm', 100.0),
                detection_data.get('detection_confidence', 0.85),
                detection_data.get('proximity_value', 500),
                detection_data.get('ambient_light', 400)
            ]])
            
            # Scale if scaler available
            if self.scaler:
                features = self.scaler.transform(features)
            
            # Predict
            prediction = self.model.predict(features)[0]
            
            # Get confidence
            try:
                confidence = np.max(self.model.predict_proba(features)[0])
            except:
                confidence = 0.85
            
            # Map prediction to object type
            object_types = ['obstacle', 'person', 'vehicle', 'wall', 'stairs', 'door', 'pole']
            object_type = object_types[prediction] if prediction < len(object_types) else 'unknown'
            
            distance = detection_data.get('distance_cm', 100.0)
            
            # Determine danger level
            if distance < 30:
                danger_level = 'Critical'
                message = f"DANGER: {object_type.upper()} very close ({distance:.0f}cm)!"
            elif distance < 100:
                danger_level = 'High'
                message = f"Warning: {object_type} detected ahead ({distance:.0f}cm)"
            elif distance < 200:
                danger_level = 'Medium'
                message = f"Caution: {object_type} at {distance:.0f}cm"
            else:
                danger_level = 'Low'
                message = f"{object_type.capitalize()} detected at safe distance ({distance:.0f}cm)"
            
            return {
                'object_detected': object_type,
                'distance_cm': float(distance),
                'danger_level': danger_level,
                'detection_confidence': float(confidence),
                'message': message
            }
            
        except Exception as e:
            print(f"Error in object detection: {e}")
            return {
                'object_detected': 'unknown',
                'distance_cm': detection_data.get('distance_cm', 100.0),
                'danger_level': 'Low',
                'detection_confidence': 0.0,
                'message': f"Detection error: {str(e)}"
            }