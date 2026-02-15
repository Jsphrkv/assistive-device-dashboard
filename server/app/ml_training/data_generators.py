"""
Synthetic data generators for ML model training and demo
Generates data for the 5 working models (no IMU or GPS required)
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import random


class SyntheticDataGenerator:
    """Generate realistic synthetic data for assistive devices"""
    
    @staticmethod
    def generate_device_telemetry(n_samples: int = 1000, anomaly_ratio: float = 0.05) -> pd.DataFrame:
        """
        Generate device telemetry data for anomaly detection
        
        Features:
        - temperature_c: device temperature in Celsius
        - battery_level: 0-100%
        - cpu_usage: 0-100%
        - rssi: signal strength -100 to 0 dBm
        - error_count: number of errors
        - is_anomaly: 0 (normal) or 1 (anomaly)
        """
        np.random.seed(42)
        
        n_normal = int(n_samples * (1 - anomaly_ratio))
        n_anomaly = n_samples - n_normal
        
        # Normal data
        normal_data = {
            'temperature_c': np.random.normal(30, 5, n_normal).clip(20, 40),
            'battery_level': np.random.normal(70, 15, n_normal).clip(20, 100),
            'cpu_usage': np.random.normal(40, 10, n_normal).clip(10, 70),
            'rssi': np.random.normal(-50, 10, n_normal).clip(-80, -30),
            'error_count': np.random.poisson(0.5, n_normal).clip(0, 5),
            'is_anomaly': np.zeros(n_normal)
        }
        
        # Anomaly data (unusual patterns)
        anomaly_data = {
            'temperature_c': np.concatenate([
                np.random.normal(50, 5, n_anomaly // 2).clip(45, 60),  # Overheating
                np.random.normal(15, 3, n_anomaly - n_anomaly // 2).clip(5, 20)  # Too cold
            ]),
            'battery_level': np.concatenate([
                np.random.normal(10, 5, n_anomaly // 2).clip(0, 20),  # Very low battery
                np.random.normal(95, 3, n_anomaly - n_anomaly // 2).clip(90, 100)  # Always full
            ]),
            'cpu_usage': np.concatenate([
                np.random.normal(85, 5, n_anomaly // 2).clip(75, 100),  # High CPU
                np.random.normal(5, 2, n_anomaly - n_anomaly // 2).clip(0, 10)  # Suspiciously low
            ]),
            'rssi': np.random.normal(-85, 5, n_anomaly).clip(-95, -75),  # Poor signal
            'error_count': np.random.poisson(5, n_anomaly).clip(3, 15),  # Many errors
            'is_anomaly': np.ones(n_anomaly)
        }
        
        # Combine and shuffle
        df_normal = pd.DataFrame(normal_data)
        df_anomaly = pd.DataFrame(anomaly_data)
        df = pd.concat([df_normal, df_anomaly], ignore_index=True)
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        return df
    
    @staticmethod
    def generate_maintenance_data(n_samples: int = 500) -> pd.DataFrame:
        """
        Generate device maintenance data for predictive maintenance
        
        Features:
        - battery_health: 0-100%
        - usage_hours: total usage hours
        - temperature_avg: average temperature
        - error_count: cumulative errors
        - days_since_last_maintenance: days since last service
        - needs_maintenance: 0 (no) or 1 (yes)
        """
        np.random.seed(42)
        
        data = {
            'battery_health': np.random.uniform(30, 100, n_samples),
            'usage_hours': np.random.uniform(0, 2000, n_samples),
            'temperature_avg': np.random.uniform(20, 50, n_samples),
            'error_count': np.random.poisson(2, n_samples).clip(0, 20),
            'days_since_last_maintenance': np.random.uniform(0, 180, n_samples),
        }
        
        df = pd.DataFrame(data)
        
        # Calculate maintenance need based on rules + some randomness
        maintenance_score = (
            (100 - df['battery_health']) / 100 * 0.3 +
            (df['usage_hours'] / 2000) * 0.3 +
            ((df['temperature_avg'] - 25) / 25) * 0.2 +
            (df['error_count'] / 10) * 0.1 +
            (df['days_since_last_maintenance'] / 180) * 0.1
        )
        
        # Add some noise
        maintenance_score += np.random.normal(0, 0.1, n_samples)
        
        df['needs_maintenance'] = (maintenance_score > 0.5).astype(int)
        
        return df
    
    @staticmethod
    def generate_object_detection_data(n_samples: int = 800) -> pd.DataFrame:
        """
        Generate object detection data from ultrasonic + proximity sensors
        
        Features:
        - distance_cm: ultrasonic distance (HC-SR04)
        - detection_confidence: confidence score
        - proximity_value: VCNL4010 proximity reading
        - ambient_light: VCNL4010 light sensor
        - object_type: 0=obstacle, 1=person, 2=vehicle, 3=wall, 4=stairs, 5=door, 6=pole
        """
        np.random.seed(42)
        
        object_types = {
            0: 'obstacle',   # Random objects
            1: 'person',     # People (higher proximity, medium distance)
            2: 'vehicle',    # Vehicles (low proximity, medium-far distance)
            3: 'wall',       # Walls (very high proximity, close distance)
            4: 'stairs',     # Stairs (varying distance)
            5: 'door',       # Doors (like walls but specific distance)
            6: 'pole'        # Poles (low proximity, close distance)
        }
        
        samples_per_type = n_samples // len(object_types)
        all_data = []
        
        for obj_type in range(len(object_types)):
            if obj_type == 0:  # obstacle
                distance = np.random.uniform(10, 300, samples_per_type)
                confidence = np.random.uniform(0.6, 0.95, samples_per_type)
                proximity = np.random.uniform(500, 8000, samples_per_type)
                ambient = np.random.uniform(100, 1000, samples_per_type)
            elif obj_type == 1:  # person
                distance = np.random.uniform(50, 250, samples_per_type)
                confidence = np.random.uniform(0.75, 0.98, samples_per_type)
                proximity = np.random.uniform(3000, 12000, samples_per_type)
                ambient = np.random.uniform(200, 800, samples_per_type)
            elif obj_type == 2:  # vehicle
                distance = np.random.uniform(100, 400, samples_per_type)
                confidence = np.random.uniform(0.7, 0.95, samples_per_type)
                proximity = np.random.uniform(1000, 5000, samples_per_type)
                ambient = np.random.uniform(300, 1200, samples_per_type)
            elif obj_type == 3:  # wall
                distance = np.random.uniform(20, 150, samples_per_type)
                confidence = np.random.uniform(0.85, 0.99, samples_per_type)
                proximity = np.random.uniform(10000, 20000, samples_per_type)
                ambient = np.random.uniform(100, 600, samples_per_type)
            elif obj_type == 4:  # stairs
                distance = np.random.uniform(30, 200, samples_per_type)
                confidence = np.random.uniform(0.65, 0.90, samples_per_type)
                proximity = np.random.uniform(5000, 15000, samples_per_type)
                ambient = np.random.uniform(150, 700, samples_per_type)
            elif obj_type == 5:  # door
                distance = np.random.uniform(50, 180, samples_per_type)
                confidence = np.random.uniform(0.75, 0.95, samples_per_type)
                proximity = np.random.uniform(8000, 18000, samples_per_type)
                ambient = np.random.uniform(200, 800, samples_per_type)
            else:  # pole
                distance = np.random.uniform(20, 120, samples_per_type)
                confidence = np.random.uniform(0.70, 0.92, samples_per_type)
                proximity = np.random.uniform(2000, 8000, samples_per_type)
                ambient = np.random.uniform(250, 900, samples_per_type)
            
            obj_data = pd.DataFrame({
                'distance_cm': distance,
                'detection_confidence': confidence,
                'proximity_value': proximity,
                'ambient_light': ambient,
                'object_type': obj_type
            })
            all_data.append(obj_data)
        
        df = pd.concat(all_data, ignore_index=True)
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        return df
    
    @staticmethod
    def generate_danger_prediction_data(n_samples: int = 600) -> pd.DataFrame:
        """
        Generate danger prediction data based on distance and rate of change
        
        Features:
        - distance_cm: current distance
        - rate_of_change: cm/s (negative = approaching)
        - proximity_value: sensor reading
        - object_type: encoded (0-6)
        - current_speed_estimate: m/s
        - danger_score: 0-100
        - recommended_action: 0=SAFE, 1=CAUTION, 2=SLOW_DOWN, 3=STOP
        """
        np.random.seed(42)
        
        data = {
            'distance_cm': np.random.uniform(10, 400, n_samples),
            'rate_of_change': np.random.uniform(-50, 10, n_samples),  # Usually approaching
            'proximity_value': np.random.uniform(500, 20000, n_samples),
            'object_type': np.random.randint(0, 7, n_samples),
            'current_speed_estimate': np.random.uniform(0.5, 2.0, n_samples),
        }
        
        df = pd.DataFrame(data)
        
        # Calculate danger score based on distance, speed, and rate of change
        # Closer = more dangerous, approaching faster = more dangerous
        distance_factor = 1 - (df['distance_cm'] / 400)  # 0-1
        approach_factor = np.abs(df['rate_of_change']) / 50  # 0-1
        speed_factor = df['current_speed_estimate'] / 2  # 0-1
        
        df['danger_score'] = (
            distance_factor * 50 +
            approach_factor * 30 +
            speed_factor * 20
        ).clip(0, 100)
        
        # Add noise
        df['danger_score'] += np.random.normal(0, 5, n_samples)
        df['danger_score'] = df['danger_score'].clip(0, 100)
        
        # Determine recommended action based on danger score
        df['recommended_action'] = pd.cut(
            df['danger_score'],
            bins=[-1, 30, 60, 80, 100],
            labels=[0, 1, 2, 3]  # SAFE, CAUTION, SLOW_DOWN, STOP
        ).astype(int)
        
        return df
    
    @staticmethod
    def generate_environment_classification_data(n_samples: int = 500) -> pd.DataFrame:
        """
        Generate environment classification data from sensor patterns
        
        Features:
        - ambient_light_avg: average light level
        - ambient_light_variance: light variance
        - detection_frequency: detections per minute
        - average_obstacle_distance: average distance
        - proximity_pattern_complexity: 0-10 score
        - distance_variance: variance in distances
        - environment_type: 0=indoor, 1=outdoor, 2=crowded, 3=open_space, 4=narrow_corridor
        - lighting_condition: 0=bright, 1=dim, 2=dark
        - complexity_level: 0=simple, 1=moderate, 2=complex
        """
        np.random.seed(42)
        
        # Generate for each environment type
        samples_per_env = n_samples // 5
        all_data = []
        
        for env_type in range(5):
            if env_type == 0:  # indoor
                ambient_light = np.random.uniform(200, 600, samples_per_env)
                light_variance = np.random.uniform(10, 50, samples_per_env)
                detection_freq = np.random.uniform(1, 5, samples_per_env)
                avg_distance = np.random.uniform(50, 200, samples_per_env)
                complexity = np.random.uniform(3, 7, samples_per_env)
                distance_var = np.random.uniform(30, 100, samples_per_env)
                lighting = np.random.choice([0, 1], samples_per_env, p=[0.7, 0.3])  # mostly bright
                complex_level = np.random.choice([0, 1, 2], samples_per_env, p=[0.2, 0.6, 0.2])
                
            elif env_type == 1:  # outdoor
                ambient_light = np.random.uniform(500, 2000, samples_per_env)
                light_variance = np.random.uniform(100, 500, samples_per_env)
                detection_freq = np.random.uniform(0.5, 3, samples_per_env)
                avg_distance = np.random.uniform(100, 400, samples_per_env)
                complexity = np.random.uniform(2, 5, samples_per_env)
                distance_var = np.random.uniform(100, 300, samples_per_env)
                lighting = np.random.choice([0, 1], samples_per_env, p=[0.8, 0.2])  # very bright
                complex_level = np.random.choice([0, 1], samples_per_env, p=[0.6, 0.4])
                
            elif env_type == 2:  # crowded
                ambient_light = np.random.uniform(150, 700, samples_per_env)
                light_variance = np.random.uniform(20, 80, samples_per_env)
                detection_freq = np.random.uniform(5, 15, samples_per_env)
                avg_distance = np.random.uniform(30, 150, samples_per_env)
                complexity = np.random.uniform(7, 10, samples_per_env)
                distance_var = np.random.uniform(50, 150, samples_per_env)
                lighting = np.random.choice([0, 1, 2], samples_per_env, p=[0.4, 0.4, 0.2])
                complex_level = np.random.choice([1, 2], samples_per_env, p=[0.3, 0.7])  # mostly complex
                
            elif env_type == 3:  # open_space
                ambient_light = np.random.uniform(400, 1500, samples_per_env)
                light_variance = np.random.uniform(80, 300, samples_per_env)
                detection_freq = np.random.uniform(0.2, 2, samples_per_env)
                avg_distance = np.random.uniform(150, 400, samples_per_env)
                complexity = np.random.uniform(1, 4, samples_per_env)
                distance_var = np.random.uniform(100, 250, samples_per_env)
                lighting = np.random.choice([0, 1], samples_per_env, p=[0.9, 0.1])
                complex_level = np.random.choice([0], samples_per_env)  # always simple
                
            else:  # narrow_corridor
                ambient_light = np.random.uniform(100, 400, samples_per_env)
                light_variance = np.random.uniform(5, 30, samples_per_env)
                detection_freq = np.random.uniform(2, 8, samples_per_env)
                avg_distance = np.random.uniform(40, 120, samples_per_env)
                complexity = np.random.uniform(4, 8, samples_per_env)
                distance_var = np.random.uniform(20, 60, samples_per_env)
                lighting = np.random.choice([0, 1, 2], samples_per_env, p=[0.3, 0.5, 0.2])
                complex_level = np.random.choice([1, 2], samples_per_env, p=[0.5, 0.5])
            
            env_data = pd.DataFrame({
                'ambient_light_avg': ambient_light,
                'ambient_light_variance': light_variance,
                'detection_frequency': detection_freq,
                'average_obstacle_distance': avg_distance,
                'proximity_pattern_complexity': complexity,
                'distance_variance': distance_var,
                'environment_type': env_type,
                'lighting_condition': lighting,
                'complexity_level': complex_level
            })
            all_data.append(env_data)
        
        df = pd.concat(all_data, ignore_index=True)
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        return df


# Convenience function for backward compatibility
def generate_device_telemetry(*args, **kwargs):
    return SyntheticDataGenerator.generate_device_telemetry(*args, **kwargs)

def generate_maintenance_data(*args, **kwargs):
    return SyntheticDataGenerator.generate_maintenance_data(*args, **kwargs)

def generate_object_detection_data(*args, **kwargs):
    return SyntheticDataGenerator.generate_object_detection_data(*args, **kwargs)

def generate_danger_prediction_data(*args, **kwargs):
    return SyntheticDataGenerator.generate_danger_prediction_data(*args, **kwargs)

def generate_environment_classification_data(*args, **kwargs):
    return SyntheticDataGenerator.generate_environment_classification_data(*args, **kwargs)