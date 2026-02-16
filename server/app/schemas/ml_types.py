"""
ML Request Schemas
Pydantic schemas for ML model inputs
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

# ========== 1. ANOMALY DETECTION ==========

class AnomalyDetectionRequest(BaseModel):
    """Request schema for anomaly detection"""
    device_id: UUID
    temperature: float = Field(..., description="Temperature in Celsius")
    heart_rate: float = Field(..., description="Heart rate in BPM")
    battery_level: float = Field(..., ge=0, le=100, description="Battery percentage")
    signal_strength: float = Field(..., description="Signal strength in dBm")
    usage_hours: float = Field(..., ge=0, description="Usage hours")

# ========== 2. MAINTENANCE PREDICTION ==========

class MaintenancePredictionRequest(BaseModel):
    """Request schema for maintenance prediction"""
    device_id: UUID
    battery_health: float = Field(..., ge=0, le=100, description="Battery health percentage")
    charge_cycles: int = Field(..., ge=0, description="Number of charge cycles")
    temperature_avg: float = Field(..., description="Average temperature in Celsius")
    error_count: int = Field(..., ge=0, description="Number of errors")
    uptime_days: int = Field(..., ge=0, description="Days since last reboot")

# ========== 3. OBJECT DETECTION ==========

class ObjectDetectionRequest(BaseModel):
    """Request schema for object detection"""
    device_id: UUID
    object_detected: str = Field(..., description="Type of object detected")
    distance_cm: float = Field(..., ge=0, description="Distance in centimeters")
    detection_source: Optional[str] = Field(None, description="Source of detection (ultrasonic, camera, lidar)")
    detection_confidence: Optional[float] = Field(0.85, ge=0, le=1, description="Detection confidence")

# ========== 4. DANGER PREDICTION (NEW) ==========

class DangerPredictionRequest(BaseModel):
    """Request schema for danger prediction"""
    device_id: UUID
    distance_sensors: List[float] = Field(..., description="Array of distance readings from sensors (in cm)")
    speed: float = Field(..., ge=0, description="Current speed in m/s")
    acceleration: Optional[float] = Field(0.0, description="Current acceleration in m/s²")
    obstacles_detected: Optional[int] = Field(0, ge=0, description="Number of obstacles detected")

# ========== 5. ENVIRONMENT CLASSIFICATION (NEW) ==========

class EnvironmentClassificationRequest(BaseModel):
    """Request schema for environment classification"""
    device_id: UUID
    ambient_light: float = Field(..., ge=0, description="Ambient light in lux")
    noise_level: float = Field(..., ge=0, description="Noise level in decibels")
    obstacle_density: float = Field(..., ge=0, description="Obstacles per meter")
    space_width: Optional[float] = Field(3.0, ge=0, description="Width of space in meters")
    gps_accuracy: Optional[float] = Field(10.0, ge=0, description="GPS accuracy in meters")