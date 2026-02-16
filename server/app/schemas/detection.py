from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

class DetectionBase(BaseModel):
    """Base detection schema"""
    device_id: UUID
    detection_type: str = Field(..., description="Type of detection (anomaly, maintenance, object_detection, danger_prediction, environment_classification)")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    message: str

class DetectionCreate(DetectionBase):
    """Schema for creating a detection record"""
    confidence: float = Field(..., ge=0, le=1)
    metadata: Optional[dict] = None

class Detection(DetectionBase):
    """Complete detection schema"""
    id: str
    confidence: float
    metadata: Optional[dict] = None
    created_at: datetime
    acknowledged: bool = Field(default=False)
    
    class Config:
        from_attributes = True

# ========== 1. ANOMALY DETECTION ==========

class AnomalyDetectionResponse(BaseModel):
    """Response schema for anomaly detection"""
    is_anomaly: bool
    anomaly_score: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    severity: str  # 'low', 'medium', 'high'
    device_health_score: float = Field(..., ge=0, le=100)
    message: str
    timestamp: int

# ========== 2. MAINTENANCE PREDICTION ==========

class MaintenancePredictionResponse(BaseModel):
    """Response schema for maintenance prediction"""
    maintenance_needed: bool
    probability: float = Field(..., ge=0, le=1)
    priority: str  # 'low', 'medium', 'high'
    days_until: int
    recommendations: dict
    message: str
    timestamp: int

# ========== 3. OBJECT DETECTION ==========

class ObjectDetectionResponse(BaseModel):
    """Response schema for object detection"""
    object_detected: str
    distance_cm: float
    danger_level: str  # 'low', 'medium', 'high', 'critical'
    detection_confidence: float = Field(..., ge=0, le=1)
    message: str
    timestamp: int

# ========== 4. DANGER PREDICTION (NEW) ==========

class DangerPredictionResponse(BaseModel):
    """Response schema for danger prediction"""
    danger_score: float = Field(..., ge=0, le=100)
    recommended_action: str  # 'SAFE', 'CAUTION', 'SLOW_DOWN', 'STOP'
    time_to_collision: Optional[float] = None  # seconds, can be None
    confidence: float = Field(..., ge=0, le=1)
    message: str
    timestamp: int

# ========== 5. ENVIRONMENT CLASSIFICATION (NEW) ==========

class EnvironmentClassificationResponse(BaseModel):
    """Response schema for environment classification"""
    environment_type: str  # 'indoor', 'outdoor', 'crowded', 'open_space', 'narrow_corridor'
    lighting_condition: str  # 'bright', 'dim', 'dark'
    complexity_level: str  # 'simple', 'moderate', 'complex'
    confidence: float = Field(..., ge=0, le=1)
    message: str
    timestamp: int