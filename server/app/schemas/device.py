from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

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
