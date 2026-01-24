from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class DetectionBase(BaseModel):
    """Base detection schema"""
    device_id: str
    detection_type: str = Field(..., description="Type of detection (anomaly, maintenance, activity)")
    severity: str = Field(..., description="Severity level (low, medium, high)")
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

class AnomalyDetectionResponse(BaseModel):
    """Response schema for anomaly detection"""
    is_anomaly: bool
    anomaly_score: float = Field(..., ge=0, le=1)
    severity: str
    message: str

class MaintenancePredictionResponse(BaseModel):
    """Response schema for maintenance prediction"""
    needs_maintenance: bool
    confidence: float = Field(..., ge=0, le=1)
    priority: str
    estimated_days_until_maintenance: int
    recommendations: list[str]

class ActivityRecognitionResponse(BaseModel):
    """Response schema for activity recognition"""
    activity: str
    description: str
    confidence: float = Field(..., ge=0, le=1)
    all_probabilities: dict[str, float]
    intensity: str