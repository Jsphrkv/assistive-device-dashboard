from pydantic import BaseModel, Field
from typing import Optional, List

# ========== DETECTION (Obstacle/Object Detection) ==========

class ObjectDetectionRequest(BaseModel):
    """Request schema for object/obstacle detection"""
    device_id: str
    object_detected: str = Field(..., description="Type of object (person, wall, vehicle, etc.)")
    distance_cm: float = Field(..., ge=0, description="Distance to object in centimeters")
    detection_source: str = Field(..., description="Source: camera, ultrasonic, lidar, combined")
    detection_confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence score 0-1")
    image_data: Optional[str] = Field(None, description="Base64 encoded image (optional)")

class ObjectDetectionResponse(BaseModel):
    """Response schema for object detection"""
    object_detected: str
    distance_cm: float
    danger_level: str  # Low, Medium, High, Critical
    detection_confidence: float
    message: str
    timestamp: int


# ========== FALL DETECTION ==========

class FallDetectionRequest(BaseModel):
    """Request schema for fall detection"""
    device_id: str
    accelerometer_x: float = Field(..., description="X-axis acceleration (g)")
    accelerometer_y: float = Field(..., description="Y-axis acceleration (g)")
    accelerometer_z: float = Field(..., description="Z-axis acceleration (g)")
    gyroscope_x: Optional[float] = Field(None, description="X-axis rotation (deg/s)")
    gyroscope_y: Optional[float] = Field(None, description="Y-axis rotation (deg/s)")
    gyroscope_z: Optional[float] = Field(None, description="Z-axis rotation (deg/s)")
    time_since_last_movement: Optional[int] = Field(None, description="Seconds since last movement")

class FallDetectionResponse(BaseModel):
    """Response schema for fall detection"""
    fall_detected: bool
    confidence: float
    severity: str  # low, medium, high, critical
    post_fall_movement: bool
    impact_magnitude: float
    message: str
    emergency_alert: bool
    timestamp: int


# ========== ROUTE PREDICTION ==========

class LocationPoint(BaseModel):
    """GPS coordinate point"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class RoutePredictionRequest(BaseModel):
    """Request schema for route prediction"""
    device_id: str
    current_location: LocationPoint
    destination: LocationPoint
    time_of_day: str = Field(..., description="morning, afternoon, evening, night")
    avoid_obstacles: Optional[List[str]] = Field(None, description="Obstacle types to avoid")
    max_detour_meters: Optional[int] = Field(500, description="Max acceptable detour distance")

class RoutePredictionResponse(BaseModel):
    """Response schema for route prediction"""
    predicted_route: List[LocationPoint]
    route_confidence: float
    estimated_obstacles: int
    difficulty_score: float  # 0-1 (0=easy, 1=very difficult)
    estimated_time_minutes: int
    recommendation: str
    alternative_routes: Optional[int] = None
    timestamp: int