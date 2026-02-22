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
  Wifi,
  WifiOff,
} from "lucide-react";
import { deviceAPI } from "../../services/api";
import { formatDate } from "../../utils/helpers";
import SystemCard from "./SystemCard";

const MODALS = {
  ADD: "add",
  PAIRING_CODE: "pairingCode",
  PAIRING_INPUT: "pairingInput",
  DELETE: "delete",
  REGENERATE: "regenerate",
};

// FIX: Online/offline threshold — if last_seen is older than this the
// Pi is considered offline regardless of its registration `status` field.
// `device.status` = "active/pending/inactive" is purely a registration
// state stored in the DB. It does NOT reflect whether the Pi is currently
// powered on and connected. We derive real-time connection state from how
// recently the device last communicated with the backend.
// 2 minutes = 4 missed heartbeat cycles at a typical 30s ping interval.
const ONLINE_THRESHOLD_MS = 2 * 60 * 1000;

const DeviceSystemTab = () => {
  const [device, setDevice] = useState(null);
  const [systemInfo, setSystemInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeModal, setActiveModal] = useState(null);

  const [pairingCode, setPairingCode] = useState(null);
  const [currentDeviceId, setCurrentDeviceId] = useState(null);
  const [userInputCode, setUserInputCode] = useState("");
  const [pairingError, setPairingError] = useState("");
  const [newToken, setNewToken] = useState(null);

  const [newDevice, setNewDevice] = useState({
    deviceName: "",
    deviceModel: "Raspberry Pi 3 B",
  });
  const [copiedCode, setCopiedCode] = useState(false);
  const [copiedToken, setCopiedToken] = useState(false);
  const [notify, setNotify] = useState(null);

  // FIX: Single isSubmitting flag for all destructive async actions.
  // Since modals are mutually exclusive (one activeModal at a time),
  // one flag covers delete, regenerate, and pair without conflicts.
  const [isSubmitting, setIsSubmitting] = useState(false);

  const showNotify = (type, text, autoDismissMs = 5000) => {
    setNotify({ type, text });
    if (autoDismissMs) {
      setTimeout(() => setNotify(null), autoDismissMs);
    }
  };

  const closeModal = () => {
    setActiveModal(null);
    setIsSubmitting(false);
  };

  useEffect(() => {
    refreshAll();
  }, []);

  // FIX: Split into two functions so callers only trigger the API calls
  // they actually need, instead of always chaining both fetches together.

  // refreshAll — used on mount and after pairing completes, where we
  // need both device data and fresh system info simultaneously.
  const refreshAll = async () => {
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

  // refreshDeviceOnly — used after token regeneration and cancel pairing,
  // where system info hasn't changed and a second call would be wasteful.
  const refreshDeviceOnly = async () => {
    try {
      const response = await deviceAPI.getAll();
      const devices = response.data.data || [];
      setDevice(devices.length > 0 ? devices[0] : null);
    } catch (error) {
      console.error("Error fetching device:", error);
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

  // FIX: Derive online/offline from last_seen freshness, NOT device.status.
  // Returns true only if the Pi has communicated within ONLINE_THRESHOLD_MS.
  const getIsOnline = (dev) => {
    if (!dev?.last_seen) return false;
    return Date.now() - new Date(dev.last_seen).getTime() < ONLINE_THRESHOLD_MS;
  };

  const handleAddDevice = async () => {
    try {
      const response = await deviceAPI.create(newDevice);
      console.log("Device creation response:", response);

      const createdDevice = response.data.device || response.data;

      const code =
        createdDevice.pairing_code ||
        response.data.pairing_code ||
        createdDevice.pairingCode ||
        response.data.pairingCode;

      const deviceId =
        createdDevice.id ||
        response.data.id ||
        createdDevice.device_id ||
        response.data.device_id;

      console.log("Extracted pairing code:", code);
      console.log("Extracted device ID:", deviceId);

      if (code && deviceId) {
        setPairingCode(code);
        setCurrentDeviceId(deviceId);
        setNewDevice({ deviceName: "", deviceModel: "Raspberry Pi 3 B" });
        setActiveModal(MODALS.PAIRING_CODE);
      } else {
        await refreshDeviceOnly();
        if (!code) {
          console.error("No pairing code found in response:", response);
          showNotify(
            "error",
            "Device created but no pairing code received. Check Supabase database.",
          );
        }
        if (!deviceId) {
          console.error("No device ID found in response:", response);
          showNotify("error", "Device created but no device ID received.");
        }
      }
    } catch (error) {
      console.error("Error adding device:", error);
      showNotify(
        "error",
        error.response?.data?.error || "Failed to add device.",
      );
    }
  };

  const handleDeleteDevice = async () => {
    setIsSubmitting(true);
    try {
      await deviceAPI.delete(device.id);
      setDevice(null);
      setSystemInfo(null);
      closeModal();
    } catch (error) {
      console.error("Error deleting device:", error);
      closeModal();
      showNotify("error", "Failed to delete device. Please try again.");
    }
  };

  const handleRegenerateToken = async () => {
    setIsSubmitting(true);
    try {
      const response = await deviceAPI.regenerateToken(device.id);
      const token = response.data.token;
      closeModal();

      // FIX: Update device_token locally — no need for a network round-trip
      // since we already have the new token value from the response.
      setDevice((prev) => ({ ...prev, device_token: token }));
      setNewToken(token);
    } catch (error) {
      console.error("Error regenerating token:", error);
      closeModal();
      showNotify("error", "Failed to regenerate token. Please try again.");
    }
  };

  const copyPairingCode = () => {
    if (!pairingCode) return;
    navigator.clipboard.writeText(pairingCode);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  const copyToClipboard = (text) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedToken(true);
    setTimeout(() => setCopiedToken(false), 2000);
  };

  const closePairingCodeModal = () => {
    setActiveModal(MODALS.PAIRING_INPUT);
    setCopiedCode(false);
  };

  const handlePairDevice = async () => {
    if (!userInputCode.trim()) {
      setPairingError("Please enter the pairing code");
      return;
    }
    if (userInputCode.toUpperCase() !== pairingCode.toUpperCase()) {
      setPairingError("Code doesn't match! Please check and try again.");
      return;
    }

    setIsSubmitting(true);
    try {
      console.log("Pairing with device ID:", currentDeviceId);

      const response = await deviceAPI.completePairing({
        deviceId: currentDeviceId,
        pairingCode: userInputCode.toUpperCase(),
      });

      if (response.data.success) {
        closeModal();
        setPairingCode(null);
        setCurrentDeviceId(null);
        setUserInputCode("");
        setPairingError("");
        // After successful pairing we need fresh device + system info
        await refreshAll();
        showNotify(
          "success",
          "✅ Device paired successfully! You can now run python main.py on your Raspberry Pi.",
          8000,
        );
      }
    } catch (error) {
      console.error("Pairing error:", error);
      setIsSubmitting(false);
      setPairingError(
        error.response?.data?.error ||
          "Failed to pair device. Please try again.",
      );
    }
  };

  const cancelPairing = () => {
    closeModal();
    setPairingCode(null);
    setCurrentDeviceId(null);
    setUserInputCode("");
    setPairingError("");
    // FIX: Was calling refreshAll() (2 API calls) just to check device
    // state. Only the device row needs checking here — system info hasn't
    // changed during a cancelled pairing flow.
    refreshDeviceOnly();
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

  // ── Shared inline notification banner ─────────────────────────────────────
  const NotifyBanner = () =>
    notify ? (
      <div
        className={`p-4 rounded-lg border flex items-start justify-between gap-3 ${
          notify.type === "success"
            ? "bg-green-50 border-green-200 text-green-800"
            : "bg-red-50 border-red-200 text-red-800"
        }`}
      >
        <p className="text-sm">{notify.text}</p>
        <button onClick={() => setNotify(null)} className="flex-shrink-0">
          <X className="w-4 h-4 opacity-60 hover:opacity-100" />
        </button>
      </div>
    ) : null;

  // ── Pairing modals — rendered outside the !device branch to avoid the
  // race condition where fetchDevice() completing mid-flow collapses them ──
  const PairingModals = () => (
    <>
      {activeModal === MODALS.PAIRING_CODE && pairingCode && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg">
            <h3 className="text-xl font-bold mb-4 text-center">
              🎉 Device Created Successfully!
            </h3>

            <div className="bg-blue-50 p-8 rounded-lg mb-6">
              <p className="text-center text-sm text-gray-600 mb-2">
                Your 6-Digit Pairing Code:
              </p>
              <div className="flex items-center justify-center gap-3">
                <p className="text-center text-5xl font-mono font-bold tracking-widest text-blue-600">
                  {pairingCode}
                </p>
                <button
                  onClick={copyPairingCode}
                  className="p-2 hover:bg-blue-100 rounded transition-colors"
                  title="Copy code"
                >
                  {copiedCode ? (
                    <Check className="w-6 h-6 text-green-600" />
                  ) : (
                    <Copy className="w-6 h-6 text-blue-600" />
                  )}
                </button>
              </div>
              <p className="text-center text-xs text-gray-500 mt-2">
                ⏰ Expires in 1 hour
              </p>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-yellow-900">
                  <p className="font-semibold mb-1">⚠️ Important:</p>
                  <p>
                    This code will only be shown ONCE. Make sure to copy it
                    before closing this window!
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg mb-4">
              <p className="font-semibold mb-3 flex items-center gap-2">
                <Server className="w-5 h-5 text-blue-600" />
                Setup Instructions:
              </p>
              <ol className="space-y-2 text-sm">
                <li className="flex gap-2">
                  <span className="font-bold text-blue-600 min-w-[20px]">
                    1.
                  </span>
                  <span>
                    On your Raspberry Pi, run:{" "}
                    <code className="bg-gray-200 px-2 py-1 rounded font-mono text-xs">
                      sudo python pair_device.py
                    </code>
                  </span>
                </li>
                <li className="flex gap-2">
                  <span className="font-bold text-blue-600 min-w-[20px]">
                    2.
                  </span>
                  <span>
                    Enter the 6-digit code: <strong>{pairingCode}</strong>
                  </span>
                </li>
                <li className="flex gap-2">
                  <span className="font-bold text-blue-600 min-w-[20px]">
                    3.
                  </span>
                  <span>
                    After pairing, run:{" "}
                    <code className="bg-gray-200 px-2 py-1 rounded font-mono text-xs">
                      python main.py
                    </code>
                  </span>
                </li>
              </ol>
            </div>

            <button
              onClick={closePairingCodeModal}
              className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              I've Saved the Code - Close Window
            </button>
          </div>
        </div>
      )}

      {activeModal === MODALS.PAIRING_INPUT && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-xl font-bold mb-4 text-center">
              📱 Pair Your Device
            </h3>

            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
              <p className="text-sm text-gray-700 mb-3">
                To complete pairing, enter the 6-digit code that was shown in
                the previous step.
              </p>
              <p className="text-xs text-gray-600">
                💡 This step verifies you have the code before your Raspberry Pi
                connects.
              </p>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Enter 6-Digit Pairing Code:
              </label>
              <input
                type="text"
                value={userInputCode}
                onChange={(e) => {
                  setUserInputCode(e.target.value.toUpperCase());
                  setPairingError("");
                }}
                maxLength={6}
                placeholder="LFU46J"
                className={`w-full px-4 py-3 text-center text-2xl font-mono font-bold tracking-widest border-2 rounded-lg focus:ring-2 focus:ring-blue-500 ${
                  pairingError
                    ? "border-red-300 bg-red-50"
                    : "border-gray-300 bg-white"
                }`}
              />
              {pairingError && (
                <p className="mt-2 text-sm text-red-600 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  {pairingError}
                </p>
              )}
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
              <p className="text-xs text-blue-800">
                <strong>Next Steps:</strong> After pairing, run{" "}
                <code className="bg-blue-100 px-1 rounded">python main.py</code>{" "}
                on your Raspberry Pi to start the assistive device system.
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={cancelPairing}
                disabled={isSubmitting}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handlePairDevice}
                disabled={
                  isSubmitting ||
                  !userInputCode.trim() ||
                  userInputCode.length !== 6
                }
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {isSubmitting ? "Pairing..." : "Pair Device"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );

  // ── Empty state — no device registered ────────────────────────────────────
  if (!device) {
    return (
      <div className="space-y-6 fade-in">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">My Device</h2>
        </div>

        <NotifyBanner />

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
            onClick={() => setActiveModal(MODALS.ADD)}
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Register Your Raspberry Pi
          </button>
        </div>

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
        {activeModal === MODALS.ADD && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold">Register Raspberry Pi</h3>
                <button
                  onClick={closeModal}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

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
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
              </div>

              <div className="flex gap-2 mt-6">
                <button
                  onClick={closeModal}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddDevice}
                  disabled={!newDevice.deviceName.trim()}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Generate Pairing Code
                </button>
              </div>
            </div>
          </div>
        )}

        <PairingModals />
      </div>
    );
  }

  // ── Device registered — show device info + system info ───────────────────

  // FIX: Compute real-time online/offline separately from device.status.
  // device.status ("active") = registration state — it does NOT change
  // when the Pi powers off. isOnline = whether the Pi is currently live.
  const isOnline = getIsOnline(device);

  return (
    <div className="space-y-6 fade-in">
      {/* Header — registration status badge + live connection indicator */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">My Device</h2>
        <div className="flex items-center gap-2">
          {/* FIX: Separate online/offline pill based on last_seen freshness.
              This is what actually tells you if the Pi is powered on now. */}
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 text-sm font-semibold rounded-full ${
              isOnline
                ? "bg-green-100 text-green-800"
                : "bg-gray-100 text-gray-600"
            }`}
          >
            {isOnline ? (
              <Wifi className="w-3.5 h-3.5" />
            ) : (
              <WifiOff className="w-3.5 h-3.5" />
            )}
            {isOnline ? "Online" : "Offline"}
          </span>

          {/* Registration status badge — unchanged, still useful to show
              whether the device is active/pending/inactive in the DB */}
          <span
            className={`px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(device.status)}`}
          >
            {device.status}
          </span>
        </div>
      </div>

      <NotifyBanner />

      {/* System Information */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          System Information
        </h3>

        {!systemInfo ? (
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
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 opacity-50">
              <SystemCard label="Raspberry Pi Model" value="--" color="blue" />
              <SystemCard label="Software Version" value="--" color="green" />
              <SystemCard label="Last Reboot Time" value="--" color="yellow" />
              <SystemCard label="CPU Temperature" value="--°C" color="gray" />
            </div>
          </>
        ) : (
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
              value={
                device.device_token
                  ? device.device_token.substring(0, 40) + "..."
                  : "No token available"
              }
              className="text-xs font-mono text-gray-800 flex-1 bg-white px-3 py-2 rounded border border-gray-200"
            />
            <button
              onClick={() => copyToClipboard(device.device_token)}
              className="p-2 hover:bg-gray-200 rounded transition-colors"
              title="Copy token"
              aria-label="Copy device token"
              disabled={!device.device_token}
            >
              {copiedToken ? (
                <Check className="w-4 h-4 text-green-600" />
              ) : (
                <Copy className="w-4 h-4 text-gray-600" />
              )}
            </button>
          </div>
        </div>

        {/* New token reveal — shown after successful regeneration */}
        {newToken && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
            <p className="text-xs font-medium text-green-800 mb-2">
              ✅ New token generated — copy it now and update your Raspberry Pi:
            </p>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={newToken}
                className="text-xs font-mono text-gray-800 flex-1 bg-white px-3 py-2 rounded border border-green-300"
              />
              <button
                onClick={() => copyToClipboard(newToken)}
                className="p-2 hover:bg-green-100 rounded transition-colors"
                title="Copy new token"
              >
                {copiedToken ? (
                  <Check className="w-4 h-4 text-green-600" />
                ) : (
                  <Copy className="w-4 h-4 text-green-700" />
                )}
              </button>
            </div>
            <button
              onClick={() => setNewToken(null)}
              className="mt-2 text-xs text-green-700 underline hover:no-underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={() => setActiveModal(MODALS.REGENERATE)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 text-sm bg-yellow-50 text-yellow-700 rounded-lg hover:bg-yellow-100 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Regenerate Token
          </button>
          <button
            onClick={() => setActiveModal(MODALS.DELETE)}
            className="flex items-center justify-center gap-2 px-4 py-2 text-sm bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Delete Device
          </button>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {activeModal === MODALS.DELETE && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-lg w-full max-w-md shadow-xl animate-slideIn overflow-hidden">
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
                onClick={closeModal}
                disabled={isSubmitting}
                className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

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

              <div className="flex gap-3">
                <button
                  onClick={closeModal}
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium disabled:opacity-50"
                >
                  Cancel
                </button>
                {/* FIX: Button disabled + shows feedback while request is in flight
                    — prevents double-clicks from firing duplicate delete requests */}
                <button
                  onClick={handleDeleteDevice}
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? "Deleting..." : "Delete Device"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Regenerate Token Confirmation Modal */}
      {activeModal === MODALS.REGENERATE && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-lg w-full max-w-md shadow-xl animate-slideIn overflow-hidden">
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
                onClick={closeModal}
                disabled={isSubmitting}
                className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

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

              <div className="flex gap-3">
                <button
                  onClick={closeModal}
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium disabled:opacity-50"
                >
                  Cancel
                </button>
                {/* FIX: Disabled + spinner during request */}
                <button
                  onClick={handleRegenerateToken}
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? "Regenerating..." : "Regenerate Token"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <PairingModals />
    </div>
  );
};

export default DeviceSystemTab;
