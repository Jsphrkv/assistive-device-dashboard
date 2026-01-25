import React, { useState, useEffect } from "react";
import { Activity, Cpu, HardDrive, Thermometer, Zap } from "lucide-react";
import { deviceAPI } from "../../services/api";
import { formatRelativeTime } from "../../utils/helpers";

const DashboardTab = () => {
  const [deviceStatus, setDeviceStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hasDevice, setHasDevice] = useState(true);

  useEffect(() => {
    fetchDeviceStatus();
    const interval = setInterval(fetchDeviceStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDeviceStatus = async () => {
    try {
      const response = await deviceAPI.getStatus();
      setDeviceStatus(response.data);

      // Check if the response indicates no device
      if (response.data.hasDevice === false) {
        setHasDevice(false);
      } else {
        setHasDevice(true);
      }

      setLoading(false);
    } catch (error) {
      console.error("Error fetching device status:", error);

      // Handle 404 - No device registered
      if (error.response?.status === 404) {
        setHasDevice(false);
        setDeviceStatus(null);
      }

      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // No device registered - show empty state
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

        {/* Empty State Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="CPU Usage"
            value="--"
            icon={Cpu}
            color="blue"
            empty
          />
          <StatCard
            title="Memory"
            value="--"
            icon={HardDrive}
            color="green"
            empty
          />
          <StatCard
            title="Temperature"
            value="--"
            icon={Thermometer}
            color="orange"
            empty
          />
          <StatCard title="Power" value="--" icon={Zap} color="purple" empty />
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Device Status
          </h3>
          <div className="text-center py-8 text-gray-500">
            <Activity className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p>No device data available</p>
            <p className="text-sm mt-2">
              Register a device to see real-time status
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Device exists - show real data
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Device Overview</h2>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            <span className="text-sm text-gray-600">
              Last updated:{" "}
              {deviceStatus?.lastUpdate
                ? formatRelativeTime(deviceStatus.lastUpdate)
                : "Never"}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="CPU Usage"
            value={`${deviceStatus?.cpu_usage || 0}%`}
            icon={Cpu}
            color="blue"
          />
          <StatCard
            title="Memory"
            value={`${deviceStatus?.memory_usage || 0}%`}
            icon={HardDrive}
            color="green"
          />
          <StatCard
            title="Temperature"
            value={`${deviceStatus?.temperature || 0}°C`}
            icon={Thermometer}
            color="orange"
          />
          <StatCard
            title="Power"
            value={deviceStatus?.power_status || "Unknown"}
            icon={Zap}
            color="purple"
          />
        </div>
      </div>

      {/* Additional device info */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          System Information
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <InfoRow
            label="Device Name"
            value={deviceStatus?.device_name || "Unknown"}
          />
          <InfoRow
            label="Model"
            value={deviceStatus?.device_model || "Unknown"}
          />
          <InfoRow label="Status" value={deviceStatus?.status || "Unknown"} />
          <InfoRow label="Uptime" value={deviceStatus?.uptime || "Unknown"} />
        </div>
      </div>
    </div>
  );
};

// StatCard Component
const StatCard = ({ title, value, icon: Icon, color, empty = false }) => {
  const colorClasses = {
    blue: "bg-blue-50 text-blue-600",
    green: "bg-green-50 text-green-600",
    orange: "bg-orange-50 text-orange-600",
    purple: "bg-purple-50 text-purple-600",
  };

  return (
    <div
      className={`bg-white rounded-lg shadow p-6 ${empty ? "opacity-50" : ""}`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-600">{title}</span>
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      {empty && <p className="text-xs text-gray-400 mt-1">No data available</p>}
    </div>
  );
};

// InfoRow Component
const InfoRow = ({ label, value }) => (
  <div className="flex justify-between py-2 border-b border-gray-100">
    <span className="text-sm text-gray-600">{label}:</span>
    <span className="text-sm font-medium text-gray-900">{value}</span>
  </div>
);

export default DashboardTab;
