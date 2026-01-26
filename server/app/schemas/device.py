from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

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

# class DeviceTelemetry(BaseModel):
#     """Device telemetry data for ML anomaly detection"""
#     battery_level: float = Field(..., ge=0, le=100, description="Battery percentage")
#     usage_duration: float = Field(..., ge=0, description="Usage duration in minutes")
#     temperature: float = Field(..., description="Device temperature in Celsius")
#     signal_strength: float = Field(..., ge=-100, le=0, description="Signal strength in dBm")
#     error_count: int = Field(..., ge=0, description="Number of errors")

# class DeviceMaintenanceInfo(BaseModel):
#     """Device information for maintenance prediction"""
#     device_age_days: int = Field(..., ge=0, description="Device age in days")
#     battery_cycles: int = Field(..., ge=0, description="Number of battery charge cycles")
#     usage_intensity: float = Field(..., ge=0, le=1, description="Usage intensity (0-1)")
#     error_rate: float = Field(..., ge=0, description="Average errors per day")
#     last_maintenance_days: int = Field(..., ge=0, description="Days since last maintenance")

# class DeviceSensorData(BaseModel):
#     """Device sensor data for activity recognition"""
#     acc_x: float = Field(..., description="Accelerometer X-axis")
#     acc_y: float = Field(..., description="Accelerometer Y-axis")
#     acc_z: float = Field(..., description="Accelerometer Z-axis")
#     gyro_x: float = Field(..., description="Gyroscope X-axis")
#     gyro_y: float = Field(..., description="Gyroscope Y-axis")
#     gyro_z: float = Field(..., description="Gyroscope Z-axis")

class DeviceTelemetry(BaseModel):
    temperature: float = Field(default=37.0)
    heart_rate: float = Field(default=75.0)
    battery_level: float = Field(default=80.0)
    signal_strength: float = Field(default=-50.0)
    usage_hours: float = Field(default=8.0)

class DeviceSensorData(BaseModel):
    accelerometer_x: float = Field(default=0.0)
    accelerometer_y: float = Field(default=0.0)
    accelerometer_z: float = Field(default=0.0)
    gyroscope_x: float = Field(default=0.0)
    gyroscope_y: float = Field(default=0.0)
    gyroscope_z: float = Field(default=0.0)

class DeviceMaintenanceInfo(BaseModel):
    battery_health: float = Field(default=80.0)
    charge_cycles: int = Field(default=100)
    temperature_avg: float = Field(default=35.0)
    error_count: int = Field(default=0)
    uptime_days: int = Field(default=30)

class DeviceAnalysisRequest(BaseModel):
    """Comprehensive device analysis request"""
    telemetry: Optional[DeviceTelemetry] = None
    device_info: Optional[DeviceMaintenanceInfo] = None
    sensor_data: Optional[DeviceSensorData] = None

