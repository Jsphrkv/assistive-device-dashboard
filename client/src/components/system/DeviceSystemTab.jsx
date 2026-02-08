import React, { useState, useEffect } from "react";
import {
  Plus,
  Trash2,
  RefreshCw,
  Copy,
  Check,
  Server,
  AlertCircle,
  X,
} from "lucide-react";
import { deviceAPI } from "../../services/api";
import { formatDate } from "../../utils/helpers";
import SystemCard from "./SystemCard";

const DeviceSystemTab = () => {
  const [device, setDevice] = useState(null);
  const [systemInfo, setSystemInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [newDevice, setNewDevice] = useState({
    deviceName: "",
    deviceModel: "Raspberry Pi 4",
  });
  const [copiedToken, setCopiedToken] = useState(false);

  useEffect(() => {
    fetchDevice();
  }, []);

  const fetchDevice = async () => {
    setLoading(true);
    try {
      const response = await deviceAPI.getAll();
      const devices = response.data.data || [];

      if (devices.length > 0) {
        setDevice(devices[0]);
        await fetchSystemInfo();
      } else {
        setDevice(null);
        setSystemInfo(null);
      }
    } catch (error) {
      console.error("Error fetching device:", error);
      setDevice(null);
      setSystemInfo(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemInfo = async () => {
    try {
      const response = await deviceAPI.getSystemInfo();
      if (response.data) {
        setSystemInfo(response.data);
      }
    } catch (error) {
      console.error("Error fetching system info:", error);
      if (error.response?.status === 404) {
        setSystemInfo(null);
      }
    }
  };

  const handleAddDevice = async () => {
    try {
      const response = await deviceAPI.create(newDevice);
      setDevice(response.data.device);
      setShowAddModal(false);
      setNewDevice({ deviceName: "", deviceModel: "Raspberry Pi 4" });
      copyToClipboard(response.data.device.token);
    } catch (error) {
      console.error("Error adding device:", error);
      alert(error.response?.data?.error || "Failed to add device");
    }
  };

  const handleDeleteDevice = async () => {
    try {
      await deviceAPI.delete(device.id);
      setDevice(null);
      setSystemInfo(null);
      setShowDeleteModal(false);
    } catch (error) {
      console.error("Error deleting device:", error);
      alert("Failed to delete device");
    }
  };

  const handleRegenerateToken = async () => {
    try {
      const response = await deviceAPI.regenerateToken(device.id);
      copyToClipboard(response.data.token);
      setShowRegenerateModal(false);
      fetchDevice();
    } catch (error) {
      console.error("Error regenerating token:", error);
      alert("Failed to regenerate token");
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedToken(true);
    setTimeout(() => setCopiedToken(false), 2000);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "active":
        return "bg-green-100 text-green-800";
      case "pending":
        return "bg-yellow-100 text-yellow-800";
      case "inactive":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Empty State - No Device Registered
  if (!device) {
    return (
      <div className="space-y-6 fade-in">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">My Device</h2>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-12 text-center">
          <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Server className="w-10 h-10 text-blue-600" />
          </div>

          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            No Device Registered
          </h3>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Register your Raspberry Pi to start monitoring system information
            and managing your assistive device.
          </p>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 max-w-lg mx-auto">
            <div className="flex items-start gap-3 text-left">
              <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-blue-900">
                <p className="font-medium mb-1">One Device Per Account</p>
                <p className="text-blue-800">
                  Each account can register one Raspberry Pi device. You can
                  replace it anytime by deleting the current device first.
                </p>
              </div>
            </div>
          </div>

          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Register Your Raspberry Pi
          </button>
        </div>

        {/* Preview of what they'll see */}
        <div className="bg-gray-50 rounded-lg p-6 opacity-50">
          <h3 className="text-sm font-medium text-gray-500 mb-4">
            Preview: System Information (Available after registration)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <SystemCard label="Raspberry Pi Model" value="--" color="blue" />
            <SystemCard label="Software Version" value="--" color="green" />
            <SystemCard label="Last Reboot Time" value="--" color="yellow" />
            <SystemCard label="CPU Temperature" value="--°C" color="gray" />
          </div>
        </div>

        {/* Add Device Modal */}
        {showAddModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h3 className="text-lg font-bold mb-4">Register Raspberry Pi</h3>

              <div className="space-y-4">
                <div>
                  <label
                    htmlFor="deviceName"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Device Name
                  </label>
                  <input
                    id="deviceName"
                    name="deviceName"
                    type="text"
                    value={newDevice.deviceName}
                    onChange={(e) =>
                      setNewDevice({ ...newDevice, deviceName: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="My Assistive Device"
                  />
                </div>

                <div>
                  <label
                    htmlFor="deviceModel"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Raspberry Pi Model
                  </label>
                  <select
                    id="deviceModel"
                    name="deviceModel"
                    value={newDevice.deviceModel}
                    onChange={(e) =>
                      setNewDevice({
                        ...newDevice,
                        deviceModel: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option>Raspberry Pi 5</option>
                    <option>Raspberry Pi 4</option>
                    <option>Raspberry Pi 3 B+</option>
                    <option>Raspberry Pi 3 B</option>
                    <option>Raspberry Pi Zero W</option>
                  </select>
                </div>

                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-blue-800">
                    📋 After registration, you'll receive a device token. Copy
                    it to your Raspberry Pi's .env file to connect.
                  </p>
                </div>
              </div>

              <div className="flex gap-2 mt-6">
                <button
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddDevice}
                  disabled={!newDevice.deviceName.trim()}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Register Device
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Device Registered - Show Device Info + System Info
  return (
    <div className="space-y-6 fade-in">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">My Device</h2>
        <span
          className={`px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(device.status)}`}
        >
          {device.status}
        </span>
      </div>

      {/* Device Information Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="text-xl font-semibold text-gray-900 mb-1">
              {device.device_name}
            </h3>
            <p className="text-gray-600">{device.device_model}</p>
          </div>
          <Server className="w-8 h-8 text-blue-600" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="text-sm">
            <span className="text-gray-600">Registered:</span>
            <p className="text-gray-900 font-medium">
              {new Date(device.created_at).toLocaleDateString()}
            </p>
          </div>
          {device.last_seen && (
            <div className="text-sm">
              <span className="text-gray-600">Last Seen:</span>
              <p className="text-gray-900 font-medium">
                {new Date(device.last_seen).toLocaleString()}
              </p>
            </div>
          )}
        </div>

        {/* Device Token */}
        <div className="bg-gray-50 p-4 rounded-lg mb-4">
          <label
            htmlFor="deviceToken"
            className="text-xs font-medium text-gray-700 mb-2 block"
          >
            Device Token:
          </label>
          <div className="flex items-center gap-2">
            <input
              id="deviceToken"
              name="deviceToken"
              type="text"
              readOnly
              value={device.device_token.substring(0, 40) + "..."}
              className="text-xs font-mono text-gray-800 flex-1 bg-white px-3 py-2 rounded border border-gray-200"
            />
            <button
              onClick={() => copyToClipboard(device.device_token)}
              className="p-2 hover:bg-gray-200 rounded transition-colors"
              title="Copy token"
              aria-label="Copy device token"
            >
              {copiedToken ? (
                <Check className="w-4 h-4 text-green-600" />
              ) : (
                <Copy className="w-4 h-4 text-gray-600" />
              )}
            </button>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={() => setShowRegenerateModal(true)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 text-sm bg-yellow-50 text-yellow-700 rounded-lg hover:bg-yellow-100 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Regenerate Token
          </button>
          <button
            onClick={() => setShowDeleteModal(true)}
            className="flex items-center justify-center gap-2 px-4 py-2 text-sm bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Delete Device
          </button>
        </div>
      </div>

      {/* System Information Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          System Information
        </h3>

        {!systemInfo ? (
          // Show waiting message with preview cards
          <>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-yellow-900 mb-1">
                    Waiting for Device Connection
                  </p>
                  <p className="text-yellow-800">
                    System information will appear once your Raspberry Pi
                    connects and sends its first update.
                  </p>
                </div>
              </div>
            </div>

            {/* Preview cards while waiting */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 opacity-50">
              <SystemCard label="Raspberry Pi Model" value="--" color="blue" />
              <SystemCard label="Software Version" value="--" color="green" />
              <SystemCard label="Last Reboot Time" value="--" color="yellow" />
              <SystemCard label="CPU Temperature" value="--°C" color="gray" />
            </div>
          </>
        ) : (
          // Show actual system information
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <SystemCard
                label="Raspberry Pi Model"
                value={systemInfo.raspberryPiModel || "Unknown"}
                color="blue"
              />
              <SystemCard
                label="Software Version"
                value={systemInfo.softwareVersion || "Unknown"}
                color="green"
              />
              <SystemCard
                label="Last Reboot Time"
                value={formatDate(systemInfo.lastRebootTime) || "Unknown"}
                color="yellow"
              />
              <SystemCard
                label="CPU Temperature"
                value={`${systemInfo.cpuTemperature || 0}°C`}
                color={
                  systemInfo.cpuTemperature > 70
                    ? "red"
                    : systemInfo.cpuTemperature > 50
                      ? "yellow"
                      : "green"
                }
              />
            </div>

            {/* Hardware Specifications */}
            <div className="pt-6 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-700 mb-3">
                Hardware Specifications
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div className="flex justify-between py-2 border-b border-gray-100">
                  <span className="text-gray-600">CPU</span>
                  <span className="text-gray-900 font-medium">
                    {systemInfo.cpuModel || "Unknown"}
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-100">
                  <span className="text-gray-600">RAM</span>
                  <span className="text-gray-900 font-medium">
                    {systemInfo.ramSize || "Unknown"}
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-100">
                  <span className="text-gray-600">Storage</span>
                  <span className="text-gray-900 font-medium">
                    {systemInfo.storageSize || "Unknown"}
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b border-gray-100">
                  <span className="text-gray-600">OS</span>
                  <span className="text-gray-900 font-medium">
                    {systemInfo.osVersion || "Unknown"}
                  </span>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-lg w-full max-w-md shadow-xl animate-slideIn overflow-hidden">
            {/* Header with close button */}
            <div className="flex items-start justify-between px-6 pt-5 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <AlertCircle className="w-6 h-6 text-red-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">
                    Delete Device
                  </h3>
                  <p className="text-sm text-gray-600">
                    This action cannot be undone
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowDeleteModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="px-6 pb-6">
              <p className="text-gray-700 mb-3">
                Are you sure you want to delete{" "}
                <strong>{device.device_name}</strong>?
              </p>
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-6">
                <p className="text-sm text-red-800">
                  <strong>Warning:</strong> All detection logs, system data, and
                  settings associated with this device will be permanently
                  removed.
                </p>
              </div>

              {/* Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={() => setShowDeleteModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteDevice}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
                >
                  Delete Device
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Regenerate Token Confirmation Modal */}
      {showRegenerateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-lg w-full max-w-md shadow-xl animate-slideIn overflow-hidden">
            {/* Header with close button */}
            <div className="flex items-start justify-between px-6 pt-5 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <RefreshCw className="w-6 h-6 text-yellow-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">
                    Regenerate Token
                  </h3>
                  <p className="text-sm text-gray-600">
                    Security confirmation required
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowRegenerateModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="px-6 pb-6">
              <p className="text-gray-700 mb-3">
                This will invalidate the current device token.
              </p>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-6">
                <p className="text-sm text-yellow-800">
                  <strong>Important:</strong> Your Raspberry Pi will need to be
                  reconfigured with the new token to continue working.
                </p>
              </div>

              {/* Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={() => setShowRegenerateModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={handleRegenerateToken}
                  className="flex-1 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors font-medium"
                >
                  Regenerate Token
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DeviceSystemTab;
