from pydantic import BaseModel, Field
from typing import Optional


class YOLODetectionRequest(BaseModel):
    device_id: str
    image_data: str
    distance_cm: Optional[float] = 0
    detection_source: Optional[str] = 'camera'


class ObjectDetectionRequest(BaseModel):
    device_id: str
    distance_cm: float
    detection_confidence: float = Field(default=0.65, ge=0.0, le=1.0)
    proximity_value: Optional[float] = 0
    ambient_light: Optional[float] = 0
    detection_source: Optional[str] = 'ultrasonic'


class DangerPredictionRequest(BaseModel):
    device_id: str
    distance_cm: float
    rate_of_change: Optional[float] = 0
    proximity_value: Optional[float] = 0
    object_type: Optional[str] = 'obstacle'
    current_speed_estimate: Optional[float] = 1.0


class EnvironmentClassificationRequest(BaseModel):
    device_id: str
    ambient_light_avg: Optional[float] = 500
    ambient_light_variance: Optional[float] = 100
    detection_frequency: Optional[float] = 2
    average_obstacle_distance: Optional[float] = 150
    proximity_pattern_complexity: Optional[float] = 5
    distance_variance: Optional[float] = 50