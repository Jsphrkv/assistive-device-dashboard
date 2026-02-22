import React, { useState, useEffect } from "react";
import { Activity, Camera, Battery, AlertTriangle, Zap } from "lucide-react";
import { deviceAPI, statisticsAPI, mlAPI } from "../../services/api";
import { formatRelativeTime } from "../../utils/helpers";
import AnomalyAlert from "../ml/AnomalyAlert";
import DangerMonitor from "../ml/DangerMonitor";

const DashboardTab = () => {
  const [deviceStatus, setDeviceStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hasDevice, setHasDevice] = useState(true);
  const [totalDetections, setTotalDetections] = useState(0);
  const [mlStats, setMlStats] = useState(null);
  const [anomalyCount, setAnomalyCount] = useState(0);
  const [lastSeenTime, setLastSeenTime] = useState(null);

  // ✅ NEW: Centralized ML data state
  const [mlData, setMlData] = useState({
    anomalies: [],
    dangerData: [],
  });
  const [mlLoading, setMlLoading] = useState(true);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAllData = async () => {
    await Promise.all([
      fetchDeviceStatus(),
      fetchDetectionStats(),
      fetchMLStats(),
      fetchMLData(), // ✅ NEW: Centralized ML data fetch
    ]);
  };

  const fetchDeviceStatus = async () => {
    try {
      const response = await deviceAPI.getStatus();
      const raw = response.data;

      // Normalize all fields so every card reads the correct value
      const data = {
        ...raw,
        batteryLevel: raw.batteryLevel ?? raw.battery_level ?? 0,
        cameraStatus: raw.cameraStatus ?? raw.camera_status ?? "Unknown",
        deviceOnline: raw.deviceOnline ?? raw.device_online ?? false,
        lastObstacle: raw.lastObstacle ?? raw.last_obstacle ?? null,
        lastDetectionTime:
          raw.lastDetectionTime ?? raw.last_detection_time ?? null,
        lastSeen: raw.lastSeen ?? raw.last_seen ?? null,
        hasDevice: raw.hasDevice ?? raw.has_device ?? true,
        deviceId: raw.deviceId ?? raw.device_id ?? null,
      };

      setDeviceStatus(data);
      setHasDevice(data.hasDevice !== false);

      if (data.lastSeen) {
        setLastSeenTime(data.lastSeen);
      } else {
        setLastSeenTime(null);
      }

      setLoading(false);
    } catch (error) {
      console.error("❌ Error fetching device status:", error);

      if (error.response?.status === 404) {
        setHasDevice(false);
        setDeviceStatus(null);
      }

      setLoading(false);
    }
  };

  const fetchDetectionStats = async () => {
    try {
      const response = await statisticsAPI.getSummary();
      setTotalDetections(response.data?.totalPredictions || 0);
    } catch (error) {
      console.error("❌ Error fetching detection stats:", error);
      setTotalDetections(0);
    }
  };

  const fetchMLStats = async () => {
    try {
      const response = await mlAPI.getStats(7);
      const stats = response.data;

      setMlStats(stats);

      if (stats && stats.anomalyCount !== undefined) {
        setAnomalyCount(stats.anomalyCount);
      } else {
        setAnomalyCount(0);
      }
    } catch (error) {
      console.error("❌ Error fetching ML stats:", error);
      setMlStats(null);
      setAnomalyCount(0);
    }
  };

  // ✅ NEW: Centralized ML data fetching (replaces 2 separate component API calls)
  const fetchMLData = async () => {
    setMlLoading(true);

    try {
      // Fetch both ML data types in parallel
      const [anomaliesRes, dangerRes] = await Promise.all([
        mlAPI.getAnomalies(10).catch(() => ({ data: { data: [] } })),
        mlAPI
          .getHistory({ type: "danger_prediction", limit: 10 })
          .catch(() => ({ data: { data: [] } })),
      ]);

      // Filter by deviceId if available
      const filterByDevice = (items) => {
        const deviceId = deviceStatus?.deviceId;
        if (!deviceId || deviceId === "device-001") return items;
        return items.filter((item) => item.device_id === deviceId);
      };

      setMlData({
        anomalies: filterByDevice(anomaliesRes.data?.data || []),
        dangerData: filterByDevice(dangerRes.data?.data || []),
      });
    } catch (error) {
      console.error("❌ Error fetching ML data:", error);
      // Set empty data on error so components show empty state
      setMlData({
        anomalies: [],
        dangerData: [],
      });
    } finally {
      setMlLoading(false);
    }
  };

  const getLastActiveDisplay = () => {
    if (!lastSeenTime) return "N/A";

    try {
      const now = new Date();
      const lastSeenDate = new Date(lastSeenTime);

      if (isNaN(lastSeenDate.getTime())) return "N/A";

      const diffMs = now - lastSeenDate;
      const diffMins = Math.floor(diffMs / 60000);

      if (diffMins < 1) return "Just now";
      if (diffMins < 60) return `${diffMins}m ago`;

      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;

      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}d ago`;
    } catch (error) {
      return "N/A";
    }
  };

  const isDeviceOnline = () => {
    if (deviceStatus?.deviceOnline !== undefined) {
      return deviceStatus.deviceOnline;
    }

    if (lastSeenTime) {
      const now = new Date();
      const lastSeenDate = new Date(lastSeenTime);
      const diffMs = now - lastSeenDate;
      const diffMins = Math.floor(diffMs / 60000);
      return diffMins < 2;
    }

    return false;
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

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 opacity-50">
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
        </div>
      </div>
    );
  }

  const deviceOnline = isDeviceOnline();

  return (
    <div className="space-y-6">
      {/* Device Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Device Status</h2>
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                deviceOnline ? "bg-green-500" : "bg-red-500"
              } animate-pulse`}
            ></div>
            <span className="text-sm text-gray-600">
              {deviceOnline ? "Online" : "Offline"}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatusCard
            title="Device Health"
            value={deviceStatus?.batteryLevel > 50 ? "Good" : "Warning"}
            icon={Activity}
            color={deviceStatus?.batteryLevel > 50 ? "green" : "orange"}
            subtitle={deviceOnline ? "All systems operational" : "Offline"}
          />
          <StatusCard
            title="Camera Status"
            value={deviceStatus?.cameraStatus || "Unknown"}
            icon={Camera}
            color={
              deviceStatus?.cameraStatus === "Active" ||
              deviceStatus?.cameraStatus === "active"
                ? "green"
                : "orange"
            }
            subtitle={
              totalDetections > 0
                ? `${totalDetections.toLocaleString()} detections`
                : "No detections yet"
            }
          />
          <BatteryIndicator level={deviceStatus?.batteryLevel || 0} />
        </div>
      </div>

      {/* ✅ OPTIMIZED: Pass pre-fetched data as props */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AnomalyAlert
          deviceId={deviceStatus?.deviceId}
          anomaliesData={mlData.anomalies} // ✅ Data from parent
          loading={mlLoading}
        />
        <DangerMonitor
          deviceId={deviceStatus?.deviceId}
          dangerData={mlData.dangerData} // ✅ Data from parent
          loading={mlLoading}
        />
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Anomalies Detected</p>
              <p className="text-2xl font-bold text-red-600">{anomalyCount}</p>
              {mlStats && (
                <p className="text-xs text-gray-500 mt-1">
                  {mlStats.anomalyRate}% rate (last 7 days)
                </p>
              )}
            </div>
            <AlertTriangle className="w-8 h-8 text-red-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Last Active</p>
              <p className="text-2xl font-bold text-gray-900">
                {getLastActiveDisplay()}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {deviceOnline ? "Online now" : "Offline"}
              </p>
            </div>
            <Zap
              className={`w-8 h-8 ${deviceOnline ? "text-green-500" : "text-gray-400"}`}
            />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 mb-1">Last Obstacle</p>
              <p className="text-xl font-bold text-gray-900 truncate max-w-[120px] capitalize">
                {deviceStatus?.lastObstacle || "None"}
              </p>
              {deviceStatus?.lastDetectionTime && (
                <p className="text-xs text-gray-500 mt-1">
                  {formatRelativeTime(deviceStatus.lastDetectionTime)}
                </p>
              )}
            </div>
            <AlertTriangle
              className={`w-8 h-8 ${
                deviceStatus?.lastObstacle ? "text-orange-500" : "text-gray-300"
              }`}
            />
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
          className={`p-2 rounded-lg ${
            empty ? "bg-gray-50 text-gray-400" : colorClasses[color]
          }`}
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
