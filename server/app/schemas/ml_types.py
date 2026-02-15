from pydantic import BaseModel, Field
from typing import Optional, Dict, List


# ========== Object Detection ==========

class ObjectDetectionRequest(BaseModel):
    """Request schema for object detection"""
    device_id: str
    distance_cm: float = Field(..., description="Distance to object in centimeters")
    detection_confidence: float = Field(default=0.85, description="Detection confidence 0-1")
    proximity_value: int = Field(default=0, description="Proximity sensor reading")
    ambient_light: int = Field(default=400, description="Ambient light level")
    detection_source: str = Field(default="ultrasonic", description="Detection source")


# ========== Danger Prediction (NEW) ==========

class DangerPredictionRequest(BaseModel):
    """Request schema for danger prediction"""
    device_id: str
    distance_cm: float = Field(..., description="Current distance to obstacle in cm")
    rate_of_change: float = Field(..., description="Rate of distance change in cm/s (negative = approaching)")
    proximity_value: int = Field(default=5000, description="Proximity sensor reading")
    object_type: str = Field(default="obstacle", description="Type of detected object")
    current_speed_estimate: float = Field(default=1.0, description="Estimated speed in m/s")


# ========== Environment Classification (NEW) ==========

class EnvironmentClassificationRequest(BaseModel):
    """Request schema for environment classification"""
    device_id: str
    ambient_light_avg: float = Field(..., description="Average ambient light over time")
    ambient_light_variance: float = Field(..., description="Variance in ambient light")
    detection_frequency: float = Field(..., description="Detections per minute")
    average_obstacle_distance: float = Field(..., description="Average distance to obstacles")
    proximity_pattern_complexity: float = Field(..., description="Complexity score of proximity patterns")
    distance_variance: float = Field(..., description="Variance in measured distances")