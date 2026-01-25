import React, { useState, useEffect } from "react";
import SystemCard from "./SystemCard";
import { deviceAPI } from "../../services/api";
import { formatDate } from "../../utils/helpers";
import { Server } from "lucide-react";

const SystemInfoTab = () => {
  const [systemInfo, setSystemInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hasDevice, setHasDevice] = useState(true);

  useEffect(() => {
    fetchSystemInfo();
  }, []);

  const fetchSystemInfo = async () => {
    setLoading(true);
    try {
      const response = await deviceAPI.getSystemInfo();
      if (response.data) {
        setSystemInfo(response.data);
        setHasDevice(true);
      }
    } catch (error) {
      console.error("Error fetching system info:", error);
      if (error.response?.status === 404) {
        setHasDevice(false);
      }
    } finally {
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

  if (!hasDevice) {
    return (
      <div className="space-y-6 fade-in">
        <h2 className="text-2xl font-bold text-gray-900">System Information</h2>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <Server className="w-6 h-6 text-yellow-600 mt-1" />
            <div>
              <h3 className="text-lg font-semibold text-yellow-900 mb-2">
                No Device Connected
              </h3>
              <p className="text-yellow-800 mb-4">
                Register a device in the "Devices" tab to view system
                information.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6 opacity-50">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <SystemCard label="Raspberry Pi Model" value="--" color="blue" />
            <SystemCard label="Software Version" value="--" color="green" />
            <SystemCard label="Last Reboot Time" value="--" color="yellow" />
            <SystemCard label="CPU Temperature" value="--°C" color="gray" />
          </div>
        </div>
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
