import React, { useState, useEffect } from "react";
import SystemCard from "./SystemCard";
import { deviceAPI } from "../../services/api";
import { formatDate } from "../../utils/helpers";

const SystemInfoTab = () => {
  const [systemInfo, setSystemInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSystemInfo();
  }, []);

  const fetchSystemInfo = async () => {
    setLoading(true);
    try {
      const response = await deviceAPI.getSystemInfo();
      if (response.data) {
        setSystemInfo(response.data);
      }
    } catch (error) {
      console.error("Error fetching system info:", error);
    } finally {
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
      <h2 className="text-2xl font-bold text-gray-900">System Information</h2>

      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SystemCard
            label="Raspberry Pi Model"
            value={systemInfo?.raspberryPiModel || "Unknown"}
            color="blue"
          />

          <SystemCard
            label="Software Version"
            value={systemInfo?.softwareVersion || "Unknown"}
            color="green"
          />

          <SystemCard
            label="Last Reboot Time"
            value={formatDate(systemInfo?.lastRebootTime) || "Unknown"}
            color="yellow"
          />

          <SystemCard
            label="CPU Temperature"
            value={`${systemInfo?.cpuTemperature || 0}°C`}
            color={
              systemInfo?.cpuTemperature > 70
                ? "red"
                : systemInfo?.cpuTemperature > 50
                  ? "yellow"
                  : "green"
            }
          />
        </div>

        <div className="mt-6 pt-6 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            Hardware Specifications
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-600">CPU</span>
              <span className="text-gray-900 font-medium">
                {systemInfo?.cpuModel || "Unknown"}
              </span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-600">RAM</span>
              <span className="text-gray-900 font-medium">
                {systemInfo?.ramSize || "Unknown"}
              </span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-600">Storage</span>
              <span className="text-gray-900 font-medium">
                {systemInfo?.storageSize || "Unknown"}
              </span>
            </div>
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-gray-600">OS</span>
              <span className="text-gray-900 font-medium">
                {systemInfo?.osVersion || "Unknown"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemInfoTab;
