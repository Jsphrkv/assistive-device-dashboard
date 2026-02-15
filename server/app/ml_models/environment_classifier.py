"""
Environment Classifier - Classifies environment type, lighting, and complexity
"""

import numpy as np


class EnvironmentClassifier:
    def __init__(self):
        self.model = None
        self.scaler = None
        
    def predict(self, environment_data):
        """
        Classify environment type from sensor patterns
        
        Args:
            environment_data: dict with keys:
                - ambient_light_avg (float)
                - ambient_light_variance (float)
                - detection_frequency (float)
                - average_obstacle_distance (float)
                - proximity_pattern_complexity (float)
                - distance_variance (float)
        
        Returns:
            dict with environment classification results
        """
        if not self.model:
            return {
                'environment_type': 'unknown',
                'lighting_condition': 'unknown',
                'complexity_level': 'unknown',
                'confidence': 0.0,
                'message': 'Model not loaded'
            }
        
        try:
            # Extract features
            features = np.array([[
                environment_data.get('ambient_light_avg', 400),
                environment_data.get('ambient_light_variance', 100),
                environment_data.get('detection_frequency', 2.0),
                environment_data.get('average_obstacle_distance', 200),
                environment_data.get('proximity_pattern_complexity', 5),
                environment_data.get('distance_variance', 100)
            ]])
            
            # Scale if scaler available
            if self.scaler:
                features = self.scaler.transform(features)
            
            # Predict (MultiOutputClassifier returns array of predictions)
            predictions = self.model.predict(features)[0]
            
            # Get confidence
            try:
                # For MultiOutputClassifier, get confidence from first estimator
                confidence = np.max(self.model.estimators_[0].predict_proba(features)[0])
            except:
                confidence = 0.75
            
            # Map predictions to labels
            environment_types = ['indoor', 'outdoor', 'crowded', 'open_space', 'narrow_corridor']
            lighting_conditions = ['bright', 'dim', 'dark']
            complexity_levels = ['simple', 'moderate', 'complex']
            
            environment_type = environment_types[predictions[0]] if predictions[0] < len(environment_types) else 'unknown'
            lighting_condition = lighting_conditions[predictions[1]] if predictions[1] < len(lighting_conditions) else 'unknown'
            complexity_level = complexity_levels[predictions[2]] if predictions[2] < len(complexity_levels) else 'unknown'
            
            # Generate message
            env_descriptions = {
                'indoor': 'indoor space',
                'outdoor': 'outdoor area',
                'crowded': 'crowded area with many obstacles',
                'open_space': 'open space with few obstacles',
                'narrow_corridor': 'narrow corridor or pathway',
                'unknown': 'unknown environment'
            }
            
            light_descriptions = {
                'bright': 'well-lit',
                'dim': 'dimly lit',
                'dark': 'poorly lit',
                'unknown': 'unknown lighting'
            }
            
            complexity_descriptions = {
                'simple': 'Simple navigation - few obstacles',
                'moderate': 'Moderate navigation complexity',
                'complex': 'Complex environment - high obstacle density',
                'unknown': 'Unknown complexity'
            }
            
            env_desc = env_descriptions[environment_type]
            light_desc = light_descriptions[lighting_condition]
            complex_desc = complexity_descriptions[complexity_level]
            
            message = f"Environment: {env_desc.capitalize()}, {light_desc}. {complex_desc}."
            
            # Add recommendations
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
                'confidence': float(confidence),
                'message': message
            }
            
        except Exception as e:
            print(f"Error in environment classification: {e}")
            return {
                'environment_type': 'unknown',
                'lighting_condition': 'unknown',
                'complexity_level': 'unknown',
                'confidence': 0.0,
                'message': f"Classification error: {str(e)}"
            }