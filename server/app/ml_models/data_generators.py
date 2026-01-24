"""
Synthetic data generators for ML model training and demo
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
        - battery_level: 0-100%
        - usage_duration: minutes per day
        - temperature: device temperature in Celsius
        - signal_strength: -100 to 0 dBm
        - error_count: number of errors
        - is_anomaly: 0 (normal) or 1 (anomaly)
        """
        np.random.seed(42)
        
        n_normal = int(n_samples * (1 - anomaly_ratio))
        n_anomaly = n_samples - n_normal
        
        # Normal data
        normal_data = {
            'battery_level': np.random.normal(70, 15, n_normal).clip(20, 100),
            'usage_duration': np.random.normal(180, 45, n_normal).clip(30, 360),  # 3 hours avg
            'temperature': np.random.normal(35, 3, n_normal).clip(25, 45),
            'signal_strength': np.random.normal(-60, 10, n_normal).clip(-90, -30),
            'error_count': np.random.poisson(0.5, n_normal).clip(0, 5),
            'is_anomaly': np.zeros(n_normal)
        }
        
        # Anomaly data (unusual patterns)
        anomaly_data = {
            'battery_level': np.concatenate([
                np.random.normal(15, 5, n_anomaly // 2).clip(0, 25),  # Very low battery
                np.random.normal(95, 3, n_anomaly - n_anomaly // 2).clip(90, 100)  # Always full
            ]),
            'usage_duration': np.concatenate([
                np.random.normal(30, 10, n_anomaly // 2).clip(0, 60),  # Very low usage
                np.random.normal(350, 20, n_anomaly - n_anomaly // 2).clip(300, 400)  # Excessive usage
            ]),
            'temperature': np.concatenate([
                np.random.normal(50, 5, n_anomaly // 2).clip(45, 60),  # Overheating
                np.random.normal(20, 3, n_anomaly - n_anomaly // 2).clip(10, 25)  # Too cold
            ]),
            'signal_strength': np.random.normal(-85, 5, n_anomaly).clip(-95, -75),  # Poor signal
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
        - device_age_days: age in days
        - battery_cycles: number of charge cycles
        - usage_intensity: 0-1 (low to high usage)
        - error_rate: errors per day
        - last_maintenance_days: days since last maintenance
        - needs_maintenance: 0 (no) or 1 (yes)
        """
        np.random.seed(42)
        
        data = {
            'device_age_days': np.random.uniform(0, 730, n_samples),  # 0-2 years
            'battery_cycles': np.random.uniform(0, 800, n_samples),
            'usage_intensity': np.random.beta(2, 5, n_samples),  # Skewed toward lower usage
            'error_rate': np.random.exponential(0.5, n_samples).clip(0, 5),
            'last_maintenance_days': np.random.uniform(0, 180, n_samples),
        }
        
        df = pd.DataFrame(data)
        
        # Calculate maintenance need based on rules + some randomness
        maintenance_score = (
            (df['device_age_days'] / 365) * 0.3 +
            (df['battery_cycles'] / 500) * 0.3 +
            df['usage_intensity'] * 0.2 +
            (df['error_rate'] / 5) * 0.1 +
            (df['last_maintenance_days'] / 180) * 0.1
        )
        
        # Add some noise
        maintenance_score += np.random.normal(0, 0.1, n_samples)
        
        df['needs_maintenance'] = (maintenance_score > 0.6).astype(int)
        
        return df
    
    @staticmethod
    def generate_activity_data(n_samples: int = 1000) -> pd.DataFrame:
        """
        Generate accelerometer/gyroscope data for activity recognition
        
        Activities:
        - 0: Resting (sitting/lying)
        - 1: Walking
        - 2: Using device (active interaction)
        """
        np.random.seed(42)
        
        activities = []
        
        # Generate ~33% of each activity
        for activity in [0, 1, 2]:
            n = n_samples // 3
            
            if activity == 0:  # Resting - low movement
                acc_x = np.random.normal(0, 0.5, n)
                acc_y = np.random.normal(0, 0.5, n)
                acc_z = np.random.normal(9.8, 0.3, n)  # Gravity
                gyro_x = np.random.normal(0, 5, n)
                gyro_y = np.random.normal(0, 5, n)
                gyro_z = np.random.normal(0, 5, n)
                
            elif activity == 1:  # Walking - periodic movement
                t = np.linspace(0, 10, n)
                acc_x = 2 * np.sin(2 * np.pi * 2 * t) + np.random.normal(0, 0.5, n)
                acc_y = 1.5 * np.sin(2 * np.pi * 2 * t + np.pi/4) + np.random.normal(0, 0.5, n)
                acc_z = 9.8 + np.sin(2 * np.pi * 2 * t) + np.random.normal(0, 0.3, n)
                gyro_x = 20 * np.sin(2 * np.pi * 2 * t) + np.random.normal(0, 10, n)
                gyro_y = 15 * np.sin(2 * np.pi * 2 * t) + np.random.normal(0, 10, n)
                gyro_z = 10 * np.cos(2 * np.pi * 2 * t) + np.random.normal(0, 5, n)
                
            else:  # Using device - varied movement
                acc_x = np.random.normal(0, 1.5, n)
                acc_y = np.random.normal(0, 1.5, n)
                acc_z = np.random.normal(9.8, 1, n)
                gyro_x = np.random.normal(0, 25, n)
                gyro_y = np.random.normal(0, 25, n)
                gyro_z = np.random.normal(0, 20, n)
            
            activity_df = pd.DataFrame({
                'acc_x': acc_x,
                'acc_y': acc_y,
                'acc_z': acc_z,
                'gyro_x': gyro_x,
                'gyro_y': gyro_y,
                'gyro_z': gyro_z,
                'activity': activity
            })
            
            activities.append(activity_df)
        
        df = pd.concat(activities, ignore_index=True)
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        return df