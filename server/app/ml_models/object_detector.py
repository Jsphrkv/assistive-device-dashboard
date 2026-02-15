"""
Object Detector - Wrapper for object/obstacle detection model
"""

import numpy as np
from .model_loader import model_loader

class ObjectDetector:
    def __init__(self):
        self.model_name = 'object_detection_model'
        
    def detect(self, detection_data):
        """
        Detect and classify objects/obstacles
        
        Args:
            detection_data: dict with keys:
                - distance_cm (float)
                - detection_confidence (float)
                - proximity_value (int)
                - ambient_light (int)
        
        Returns:
            dict with:
                - object_detected (str)
                - distance_cm (float)
                - danger_level (str)
                - detection_confidence (float)
                - message (str)
        """
        try:
            # Extract features in correct order
            features = [
                detection_data.get('distance_cm', 100.0),
                detection_data.get('detection_confidence', 0.85),
                detection_data.get('proximity_value', 500),
                detection_data.get('ambient_light', 400)
            ]
            
            # Get prediction
            result = model_loader.predict_object(features)
            
            object_type = result['object_detected']
            distance = detection_data.get('distance_cm', 100.0)
            confidence = result['detection_confidence']
            
            # Determine danger level based on distance and object type
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
                'distance_cm': distance,
                'danger_level': danger_level,
                'detection_confidence': confidence,
                'message': message
            }
            
        except Exception as e:
            raise RuntimeError(f"Object detection failed: {e}")