import React, { useState, useEffect } from "react";
import { Activity, Camera, AlertTriangle, Brain } from "lucide-react";
import StatusCard from "./StatusCard";
import BatteryIndicator from "./BatteryIndicator";
import AnomalyAlert from "../ml/AnomalyAlert";
import MaintenanceStatus from "../ml/MaintenanceStatus";
import ActivityMonitor from "../ml/ActivityMonitor";
import { deviceAPI } from "../../services/api";
import { formatRelativeTime } from "../../utils/helpers";

const DashboardTab = () => {
  const [deviceStatus, setDeviceStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDeviceStatus();
    const interval = setInterval(fetchDeviceStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchDeviceStatus = async () => {
    try {
      const response = await deviceAPI.getStatus();
      if (response.data) {
        setDeviceStatus(response.data);
        setLoading(false);
      }
    } catch (error) {
      console.error("Error fetching device status:", error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in">
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <Brain className="w-5 h-5 text-blue-600" />
          <span className="font-medium">AI-Powered Insights</span>
        </div>
      </div>

      {/* Device Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatusCard
          title="Device Status"
          value={deviceStatus?.deviceOnline ? "Online" : "Offline"}
          icon={Activity}
          color={deviceStatus?.deviceOnline ? "green" : "red"}
        />

        <StatusCard
          title="Camera Status"
          value={deviceStatus?.cameraStatus || "Unknown"}
          icon={Camera}
          color="blue"
        />

        <BatteryIndicator level={deviceStatus?.batteryLevel || 0} />

        <StatusCard
          title="Last Obstacle"
          value={deviceStatus?.lastObstacle || "None"}
          icon={AlertTriangle}
          color="red"
          subtitle={formatRelativeTime(deviceStatus?.lastDetectionTime)}
        />
      </div>

      {/* ML Insights Section */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
          <Brain className="w-5 h-5 mr-2 text-blue-600" />
          AI-Powered Analysis
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          Real-time machine learning insights for device health, anomalies, and
          user activity
        </p>
      </div>

      {/* ML Components Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Anomaly Detection Alert */}
        <AnomalyAlert
          deviceId={deviceStatus?.deviceId || "device-001"}
          batteryLevel={deviceStatus?.batteryLevel}
        />

        {/* Activity Monitor */}
        <ActivityMonitor />
      </div>

      {/* Maintenance Status - Full Width */}
      <div className="grid grid-cols-1">
        <MaintenanceStatus
          deviceInfo={{
            device_age_days: deviceStatus?.deviceAgeDays || 365,
            battery_cycles: deviceStatus?.batteryCycles || 500,
            usage_intensity: deviceStatus?.usageIntensity || 0.6,
            error_rate: deviceStatus?.errorRate || 1.5,
            last_maintenance_days: deviceStatus?.lastMaintenanceDays || 90,
          }}
        />
      </div>

      {/* Optional: Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Detections</p>
              <p className="text-2xl font-bold text-gray-900">
                {deviceStatus?.totalDetections || 0}
              </p>
            </div>
            <AlertTriangle className="w-8 h-8 text-orange-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Uptime</p>
              <p className="text-2xl font-bold text-gray-900">
                {deviceStatus?.uptime || "0h"}
              </p>
            </div>
            <Activity className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">System Health</p>
              <p className="text-2xl font-bold text-gray-900">
                {deviceStatus?.systemHealth || "Good"}
              </p>
            </div>
            <Brain className="w-8 h-8 text-blue-500" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardTab;
