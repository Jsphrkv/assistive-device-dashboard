from .device import (
    Device,
    DeviceCreate,
    DeviceUpdate,
    DeviceTelemetry,
    DeviceMaintenanceInfo,
    DeviceSensorData,
    DeviceAnalysisRequest,
    ActivityRecognitionResponse,
    MaintenancePredictionResponse
)

from .detection import (
    Detection,
    DetectionCreate,
    AnomalyDetectionResponse,
    MaintenancePredictionResponse,
    ActivityRecognitionResponse
)

from .user import (
    User,
    UserCreate,
    UserLogin,
    UserUpdate,
    UserInDB
)

__all__ = [
    # Device schemas
    'Device',
    'DeviceCreate',
    'DeviceUpdate',
    'DeviceTelemetry',
    'DeviceMaintenanceInfo',
    'DeviceSensorData',
    'DeviceAnalysisRequest',
    'ActivityRecognitionResponse',
    'MaintenancePredictionResponse',

    # Detection schemas
    'Detection',
    'DetectionCreate',
    'AnomalyDetectionResponse',
    'MaintenancePredictionResponse',
    'ActivityRecognitionResponse',
    
    # User schemas
    'User',
    'UserCreate',
    'UserLogin',
    'UserUpdate',
    'UserInDB',
]