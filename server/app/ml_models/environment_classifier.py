"""
Environment Classifier - Wrapper for environment classification model
Classifies environment type, lighting, and complexity
"""

import numpy as np
from .model_loader import model_loader

class EnvironmentClassifier:
    def __init__(self):
        self.model_name = 'environment_classifier_model'
        
    def classify(self, environment_data):
        """
        Classify environment type from sensor patterns
        
        Args:
            environment_data: dict with keys:
                - ambient_light_avg (float): Average ambient light
                - ambient_light_variance (float): Light variance
                - detection_frequency (float): Detections per minute
                - average_obstacle_distance (float): Average distance
                - proximity_pattern_complexity (float): Complexity score
                - distance_variance (float): Distance variance
        
        Returns:
            dict with:
                - environment_type (str): indoor/outdoor/crowded/open_space/narrow_corridor
                - lighting_condition (str): bright/dim/dark
                - complexity_level (str): simple/moderate/complex
                - confidence (float)
                - message (str)
        """
        try:
            # Extract features in correct order
            features = [
                environment_data.get('ambient_light_avg', 400),
                environment_data.get('ambient_light_variance', 100),
                environment_data.get('detection_frequency', 2.0),
                environment_data.get('average_obstacle_distance', 200),
                environment_data.get('proximity_pattern_complexity', 5),
                environment_data.get('distance_variance', 100)
            ]
            
            # Get prediction from model_loader
            result = model_loader.classify_environment(features)
            
            environment_type = result['environment_type']
            lighting_condition = result['lighting_condition']
            complexity_level = result['complexity_level']
            confidence = result['confidence']
            
            # Generate adaptive message based on classification
            env_descriptions = {
                'indoor': 'indoor space',
                'outdoor': 'outdoor area',
                'crowded': 'crowded area with many obstacles',
                'open_space': 'open space with few obstacles',
                'narrow_corridor': 'narrow corridor or pathway'
            }
            
            light_descriptions = {
                'bright': 'well-lit',
                'dim': 'dimly lit',
                'dark': 'poorly lit'
            }
            
            complexity_descriptions = {
                'simple': 'Simple navigation - few obstacles',
                'moderate': 'Moderate navigation complexity',
                'complex': 'Complex environment - high obstacle density'
            }
            
            env_desc = env_descriptions.get(environment_type, environment_type)
            light_desc = light_descriptions.get(lighting_condition, lighting_condition)
            complex_desc = complexity_descriptions.get(complexity_level, complexity_level)
            
            message = f"Environment: {env_desc.capitalize()}, {light_desc}. {complex_desc}."
            
            # Add recommendations based on environment
            if environment_type == 'crowded':
                message += " Reduce speed and stay alert."
            elif environment_type == 'narrow_corridor':
                message += " Proceed carefully - limited space."
            elif lighting_condition == 'dark':
                message += " Low visibility - use extra caution."
            elif complexity_level == 'complex':
                message += " Multiple obstacles detected."
            
            return {
                'environment_type': environment_type,
                'lighting_condition': lighting_condition,
                'complexity_level': complexity_level,
                'confidence': confidence,
                'message': message
            }
            
        except Exception as e:
            raise RuntimeError(f"Environment classification failed: {e}")