from .device import (
    Device,
    DeviceCreate,
    DeviceUpdate,
    DeviceTelemetry,
    DeviceMaintenanceInfo,
    DeviceSensorData,
    DeviceAnalysisRequest
)

from .detection import (
    Detection,
    DetectionCreate,
    AnomalyDetectionResponse,
    MaintenancePredictionResponse,
    ObjectDetectionResponse,
    DangerPredictionResponse,
    EnvironmentClassificationResponse
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

    # Detection schemas (5 models)
    'Detection',
    'DetectionCreate',
    'AnomalyDetectionResponse',
    'MaintenancePredictionResponse',
    'ObjectDetectionResponse',
    'DangerPredictionResponse',
    'EnvironmentClassificationResponse',
    
    # User schemas
    'User',
    'UserCreate',
    'UserLogin',
    'UserUpdate',
    'UserInDB',
]