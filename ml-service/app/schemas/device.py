from pydantic import BaseModel
from typing import Optional


class DeviceTelemetry(BaseModel):
    device_id: str
    temperature_c: Optional[float] = 35
    battery_level: Optional[float] = 80
    cpu_usage: Optional[float] = 40
    rssi: Optional[float] = -50
    error_count: Optional[int] = 0