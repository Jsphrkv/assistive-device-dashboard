import React, { useState, useEffect } from "react";
import { Activity, Camera, AlertTriangle } from "lucide-react";
import StatusCard from "./StatusCard";
import BatteryIndicator from "./BatteryIndicator";
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
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in">
      <h2 className="text-2xl font-bold text-gray-900">Device Status</h2>

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
    </div>
  );
};

export default DashboardTab;
