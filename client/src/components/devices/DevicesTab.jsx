import React, { useState, useEffect } from "react";
import { Plus, Trash2, RefreshCw, Copy, Check } from "lucide-react";
import { deviceAPI } from "../../services/api";

const DevicesTab = () => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newDevice, setNewDevice] = useState({
    deviceName: "",
    deviceModel: "Raspberry Pi 4",
  });
  const [copiedToken, setCopiedToken] = useState(null);

  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    try {
      const response = await deviceAPI.getAll();
      setDevices(response.data.data || []);
    } catch (error) {
      console.error("Error fetching devices:", error);
      setDevices([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddDevice = async () => {
    try {
      const response = await deviceAPI.create(newDevice);
      setDevices([response.data.device, ...devices]);
      setShowAddModal(false);
      setNewDevice({ deviceName: "", deviceModel: "Raspberry Pi 4" });
      copyToClipboard(response.data.device.token);
    } catch (error) {
      console.error("Error adding device:", error);
      alert(error.response?.data?.error || "Failed to add device");
    }
  };

  const handleDeleteDevice = async (deviceId) => {
    if (!window.confirm("Are you sure you want to delete this device?")) return;

    try {
      await deviceAPI.delete(deviceId);
      setDevices(devices.filter((d) => d.id !== deviceId));
    } catch (error) {
      console.error("Error deleting device:", error);
      alert("Failed to delete device");
    }
  };

  const handleRegenerateToken = async (deviceId) => {
    if (!window.confirm("This will invalidate the old token. Continue?"))
      return;

    try {
      const response = await deviceAPI.regenerateToken(deviceId);
      copyToClipboard(response.data.token);
      fetchDevices();
    } catch (error) {
      console.error("Error regenerating token:", error);
      alert("Failed to regenerate token");
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedToken(text);
    setTimeout(() => setCopiedToken(null), 2000);
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

  return (
    <div className="space-y-6 fade-in">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">My Devices</h2>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Add Device
        </button>
      </div>

      {devices.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <Plus className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-600 mb-4">No devices registered yet</p>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Add Your First Device
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {devices.map((device) => (
            <div key={device.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="font-semibold text-gray-900">
                    {device.device_name}
                  </h3>
                  <p className="text-sm text-gray-600">{device.device_model}</p>
                </div>
                <span
                  className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(device.status)}`}
                >
                  {device.status}
                </span>
              </div>

              <div className="space-y-2 text-sm text-gray-600 mb-4">
                <p>
                  Created: {new Date(device.created_at).toLocaleDateString()}
                </p>
                {device.last_seen && (
                  <p>
                    Last seen: {new Date(device.last_seen).toLocaleString()}
                  </p>
                )}
              </div>

              <div className="bg-gray-50 p-3 rounded mb-4">
                <p className="text-xs text-gray-500 mb-1">Device Token:</p>
                <div className="flex items-center gap-2">
                  <code className="text-xs font-mono truncate flex-1">
                    {device.device_token.substring(0, 30)}...
                  </code>
                  <button
                    onClick={() => copyToClipboard(device.device_token)}
                    className="p-1 hover:bg-gray-200 rounded"
                  >
                    {copiedToken === device.device_token ? (
                      <Check className="w-4 h-4 text-green-600" />
                    ) : (
                      <Copy className="w-4 h-4 text-gray-600" />
                    )}
                  </button>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleRegenerateToken(device.id)}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm bg-yellow-50 text-yellow-700 rounded hover:bg-yellow-100"
                >
                  <RefreshCw className="w-4 h-4" />
                  New Token
                </button>
                <button
                  onClick={() => handleDeleteDevice(device.id)}
                  className="flex items-center justify-center gap-2 px-3 py-2 text-sm bg-red-50 text-red-700 rounded hover:bg-red-100"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Device Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4">Add New Device</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Device Name
                </label>
                <input
                  type="text"
                  value={newDevice.deviceName}
                  onChange={(e) =>
                    setNewDevice({ ...newDevice, deviceName: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  placeholder="My Assistive Device"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Raspberry Pi Model
                </label>
                <select
                  value={newDevice.deviceModel}
                  onChange={(e) =>
                    setNewDevice({ ...newDevice, deviceModel: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option>Raspberry Pi 4</option>
                  <option>Raspberry Pi 3 B+</option>
                  <option>Raspberry Pi Zero W</option>
                  <option>Raspberry Pi 5</option>
                </select>
              </div>

              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-blue-800">
                  📋 After adding, you'll receive a token. Copy it to your
                  Raspberry Pi's .env file.
                </p>
              </div>
            </div>

            <div className="flex gap-2 mt-6">
              <button
                onClick={() => setShowAddModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAddDevice}
                disabled={!newDevice.deviceName}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Add Device
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DevicesTab;
