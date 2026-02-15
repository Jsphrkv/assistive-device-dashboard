import React, { useState, useEffect } from "react";
import {
  Activity,
  Camera,
  Battery,
  AlertTriangle,
  Brain,
  Zap,
} from "lucide-react";
import { deviceAPI, detectionsAPI, mlAPI } from "../../services/api";
import { formatRelativeTime } from "../../utils/helpers";
import AnomalyAlert from "../ml/AnomalyAlert";
import MaintenanceStatus from "../ml/MaintenanceStatus";
import DangerMonitor from "../ml/DangerMonitor";

const DashboardTab = () => {
  const [deviceStatus, setDeviceStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hasDevice, setHasDevice] = useState(true);

  // Real data states
  const [totalDetections, setTotalDetections] = useState(0);
  const [mlStats, setMlStats] = useState(null);
  const [anomalyCount, setAnomalyCount] = useState(0);
  const [deviceUptime, setDeviceUptime] = useState(null);

  useEffect(() => {
    fetchAllData();

    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchAllData();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const fetchAllData = async () => {
    await Promise.all([
      fetchDeviceStatus(),
      fetchDetectionStats(),
      fetchMLStats(),
      fetchAnomalies(),
    ]);
  };

  const fetchDeviceStatus = async () => {
    try {
      const response = await deviceAPI.getStatus();
      const data = response.data;

      setDeviceStatus(data);
      setHasDevice(data.hasDevice !== false);

      // Check both possible field names
      const lastSeenTime = data.lastSeen || data.last_seen;
      if (lastSeenTime) {
        const uptime = calculateUptime(lastSeenTime);
        setDeviceUptime(uptime);
      }

      setLoading(false);
    } catch (error) {
      console.error("Error fetching device status:", error);

      if (error.response?.status === 404) {
        setHasDevice(false);
        setDeviceStatus(null);
      }

      setLoading(false);
    }
  };

  const fetchDetectionStats = async () => {
    try {
      const response = await detectionsAPI.getRecent();
      const detections = response.data?.detections || [];
      setTotalDetections(detections.length);
    } catch (error) {
      console.error("Error fetching detection stats:", error);
      setTotalDetections(0);
    }
  };

  const fetchMLStats = async () => {
    try {
      const response = await mlAPI.getStats(7); // Last 7 days
      setMlStats(response.data);
    } catch (error) {
      console.error("Error fetching ML stats:", error);
      setMlStats(null);
    }
  };

  const fetchAnomalies = async () => {
    try {
      const response = await mlAPI.getAnomalies(10);
      const anomalies = response.data?.data || [];
      setAnomalyCount(anomalies.length);
    } catch (error) {
      console.error("Error fetching anomalies:", error);
      setAnomalyCount(0);
    }
  };

  const calculateUptime = (lastSeen) => {
    const now = new Date();
    const lastSeenDate = new Date(lastSeen);
    const diffMs = now - lastSeenDate;
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 60) return `${diffMins}m`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d`;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!hasDevice) {
    return (
      <div className="space-y-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <Activity className="w-6 h-6 text-yellow-600 mt-1" />
            <div>
              <h3 className="text-lg font-semibold text-yellow-900 mb-2">
                No Device Registered
              </h3>
              <p className="text-yellow-800 mb-4">
                You don't have any devices registered yet. Go to the "Devices"
                tab to add your first device.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatusCard
            title="Camera Status"
            value="--"
            icon={Camera}
            color="blue"
            empty
          />
          <div className="bg-white rounded-lg shadow p-4 opacity-50">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">Battery Level</span>
              <div className="p-2 rounded-lg bg-gray-50 text-gray-400">
                <Battery className="w-5 h-5" />
              </div>
            </div>
            <div className="text-2xl font-bold text-gray-900">--</div>
            <p className="text-xs text-gray-400 mt-1">No data available</p>
          </div>
          <StatusCard
            title="Device Health"
            value="--"
            icon={Activity}
            color="blue"
            empty
          />
        </div>

        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200 opacity-50">
          <h3 className="text-lg font-semibold text-gray-700 mb-2 flex items-center">
            <Brain className="w-5 h-5 mr-2" />
            AI-Powered Analysis
          </h3>
          <p className="text-sm text-gray-600">
            Register a device to see AI-powered insights
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 opacity-50">
          <div className="bg-white rounded-lg shadow p-6">
            <h4 className="font-semibold text-gray-500 mb-2">
              Anomaly Detection
            </h4>
            <p className="text-sm text-gray-400">No data available</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h4 className="font-semibold text-gray-500 mb-2">Danger Monitor</h4>
            <p className="text-sm text-gray-400">No data available</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h4 className="font-semibold text-gray-500 mb-2">
              Maintenance Status
            </h4>
            <p className="text-sm text-gray-400">No data available</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Device Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Device Status</h2>
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                deviceStatus?.deviceOnline ? "bg-green-500" : "bg-red-500"
              } animate-pulse`}
            ></div>
            <span className="text-sm text-gray-600">
              {deviceStatus?.deviceOnline ? "Online" : "Offline"}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatusCard
            title="Device Health"
            value={deviceStatus?.batteryLevel > 50 ? "Good" : "Warning"}
            icon={Activity}
            color={deviceStatus?.batteryLevel > 50 ? "green" : "orange"}
            subtitle={
              deviceStatus?.deviceOnline ? "All systems operational" : "Offline"
            }
          />
          <StatusCard
            title="Camera Status"
            value={deviceStatus?.cameraStatus || "Unknown"}
            icon={Camera}
            color={deviceStatus?.cameraStatus === "online" ? "green" : "orange"}
            subtitle={
              totalDetections > 0
                ? `${totalDetections} detections`
                : "No detections yet"
            }
          />
          <BatteryIndicator level={deviceStatus?.batteryLevel || 0} />
        </div>
      </div>

      {/* AI Analysis Banner */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
              <Brain className="w-5 h-5 mr-2 text-blue-600" />
              AI-Powered Analysis
            </h3>
            <p className="text-sm text-gray-600">
              Real-time machine learning insights for device health, danger
              detection, and maintenance predictions
            </p>
          </div>
          {mlStats && (
            <div className="bg-white rounded-lg p-3 shadow-sm">
              <p className="text-xs text-gray-600 mb-1">ML Accuracy</p>
              <p className="text-2xl font-bold text-blue-600">
                {mlStats.avgConfidence || 0}%
              </p>
            </div>
          )}
        </div>
      </div>

      {/* ML Components Grid - 3 columns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <AnomalyAlert deviceId={deviceStatus?.deviceId || "device-001"} />
        <DangerMonitor deviceId={deviceStatus?.deviceId || "device-001"} />
        <MaintenanceStatus deviceId={deviceStatus?.deviceId || "device-001"} />
      </div>

      {/* Quick Stats - Real Data (3 cards) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Anomalies */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Anomalies Detected</p>
              <p className="text-2xl font-bold text-red-600">{anomalyCount}</p>
              {mlStats && (
                <p className="text-xs text-gray-500 mt-1">
                  {mlStats.anomalyRate}% rate
                </p>
              )}
            </div>
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
        </div>

        {/* Last Active */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Last Active</p>
              <p className="text-2xl font-bold text-gray-900">
                {deviceUptime || "N/A"}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {deviceStatus?.deviceOnline ? "Online now" : "Offline"}
              </p>
            </div>
            <Zap className="w-8 h-8 text-green-500" />
          </div>
        </div>

        {/* Last Obstacle */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Last Obstacle</p>
              <p className="text-xl font-bold text-gray-900 truncate max-w-[120px]">
                {deviceStatus?.lastObstacle || "None"}
              </p>
              {deviceStatus?.lastDetectionTime && (
                <p className="text-xs text-gray-500 mt-1">
                  {formatRelativeTime(deviceStatus?.lastDetectionTime)}
                </p>
              )}
            </div>
            <AlertTriangle className="w-8 h-8 text-orange-500" />
          </div>
        </div>
      </div>
    </div>
  );
};

const StatusCard = ({
  title,
  value,
  icon: Icon,
  color,
  subtitle,
  empty = false,
}) => {
  const colorClasses = {
    blue: "bg-blue-50 text-blue-600",
    green: "bg-green-50 text-green-600",
    red: "bg-red-50 text-red-600",
    orange: "bg-orange-50 text-orange-600",
  };

  return (
    <div
      className={`bg-white rounded-lg shadow p-4 ${empty ? "opacity-50" : ""}`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-600">{title}</span>
        <div
          className={`p-2 rounded-lg ${empty ? "bg-gray-50 text-gray-400" : colorClasses[color]}`}
        >
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
      {empty && <p className="text-xs text-gray-400 mt-1">No data available</p>}
    </div>
  );
};

const BatteryIndicator = ({ level }) => {
  const getColor = () => {
    if (level > 50) return "text-green-600 bg-green-50";
    if (level > 20) return "text-orange-600 bg-orange-50";
    return "text-red-600 bg-red-50";
  };

  const getBarColor = () => {
    if (level > 50) return "bg-green-500";
    if (level > 20) return "bg-orange-500";
    return "bg-red-500";
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-600">Battery Level</span>
        <div className={`p-2 rounded-lg ${getColor()}`}>
          <Battery className="w-5 h-5" />
        </div>
      </div>
      <div className="text-2xl font-bold text-gray-900">{level}%</div>
      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
        <div
          className={`h-2 rounded-full transition-all ${getBarColor()}`}
          style={{ width: `${level}%` }}
        />
      </div>
      <p className="text-xs text-gray-500 mt-1">
        {level > 50 ? "Good" : level > 20 ? "Low" : "Critical"}
      </p>
    </div>
  );
};

export default DashboardTab;
