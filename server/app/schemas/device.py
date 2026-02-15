from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ========== BASIC DEVICE SCHEMAS ==========

class DeviceBase(BaseModel):
    """Base device schema"""
    name: str = Field(..., description="Device name")
    type: str = Field(..., description="Device type (smartphone, laptop, iot_device)")
    mac_address: str = Field(..., description="Device MAC address")

class DeviceCreate(DeviceBase):
    """Schema for creating a device"""
    pass

class DeviceUpdate(BaseModel):
    """Schema for updating a device"""
    name: Optional[str] = None
    status: Optional[str] = None
    battery_level: Optional[int] = None

class Device(DeviceBase):
    """Complete device schema with all fields"""
    id: str
    status: str = Field(default="offline")
    battery_level: int = Field(default=100, ge=0, le=100)
    last_seen: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

# ========== ML MODEL INPUT SCHEMAS ==========

# 1. Anomaly Detection Input
class DeviceTelemetry(BaseModel):
    """
    Device telemetry data for ML anomaly detection
    Used by: /api/ml/detect/anomaly
    """
    device_id: str
    temperature: float = Field(default=37.0, description="Temperature in Celsius")
    heart_rate: float = Field(default=75.0, description="Heart rate in BPM")
    battery_level: float = Field(default=80.0, ge=0, le=100, description="Battery percentage")
    signal_strength: float = Field(default=-50.0, description="Signal strength in dBm")
    usage_hours: float = Field(default=8.0, ge=0, description="Usage hours")

# 2. Maintenance Prediction Input
class DeviceMaintenanceInfo(BaseModel):
    """
    Device maintenance information for predictive maintenance
    Used by: /api/ml/predict/maintenance
    """
    device_id: str
    battery_health: float = Field(default=80.0, ge=0, le=100, description="Battery health percentage")
    charge_cycles: int = Field(default=100, ge=0, description="Number of charge cycles")
    temperature_avg: float = Field(default=35.0, description="Average temperature in Celsius")
    error_count: int = Field(default=0, ge=0, description="Number of errors")
    uptime_days: int = Field(default=30, ge=0, description="Days since last reboot")

# 3. Object Detection Input (handled by ml_types.py ObjectDetectionRequest)
# 4. Danger Prediction Input (handled by ml_types.py DangerPredictionRequest)
# 5. Environment Classification Input (handled by ml_types.py EnvironmentClassificationRequest)

# ========== COMPREHENSIVE ANALYSIS ==========

class DeviceAnalysisRequest(BaseModel):
    """
    Comprehensive device analysis request
    Can include multiple types of data for different ML models
    """
    device_id: str
    telemetry: Optional[DeviceTelemetry] = None  # For anomaly detection
    device_info: Optional[DeviceMaintenanceInfo] = None  # For maintenance prediction

