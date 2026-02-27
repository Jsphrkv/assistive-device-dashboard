import React, { useState, useEffect, useCallback } from "react";
import {
  Users,
  ChevronDown,
  ChevronRight,
  ToggleLeft,
  ToggleRight,
  X,
} from "lucide-react";
import { adminAPI } from "../../services/api";

// ✅ FIX: Normalize confidence regardless of storage format
const normalizeConfidence = (v) => {
  if (v == null) return null;
  if (v > 1) return v / 100; // stored as e.g. 87.5 → normalize to 0.875
  return v;
};

// ── Per-user detection history drawer ────────────────────────────────────────
const UserHistoryDrawer = ({ user, onClose }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    adminAPI
      .getUserDetections(user.id, 20)
      .then((res) => setHistory(res.data?.detections ?? res.data?.data ?? []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [user]);

  if (!user) return null;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-end"
      onClick={onClose}
    >
      <div
        className="bg-white w-full max-w-lg h-full overflow-y-auto shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-white border-b border-gray-200 px-5 py-4 flex items-center justify-between z-10">
          <div>
            <h3 className="font-semibold text-gray-900">{user.username}</h3>
            <p className="text-xs text-gray-500">
              {user.email} · Last 20 detections
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5">
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="h-14 bg-gray-100 animate-pulse rounded-lg"
                />
              ))}
            </div>
          ) : history.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-12">
              No detections found for this user.
            </p>
          ) : (
            <div className="space-y-2">
              {history.map((d, i) => {
                // ✅ FIX: normalize before displaying
                const confNorm = normalizeConfidence(d.detection_confidence);
                return (
                  <div
                    key={d.id ?? i}
                    className="bg-gray-50 rounded-lg p-3 text-sm"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-800">
                        {d.object_detected ?? "Unknown"}
                      </span>
                      <span
                        className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                          d.danger_level === "Critical"
                            ? "bg-red-100 text-red-800"
                            : d.danger_level === "High"
                              ? "bg-orange-100 text-orange-800"
                              : d.danger_level === "Medium"
                                ? "bg-amber-100 text-amber-800"
                                : "bg-green-100 text-green-800"
                        }`}
                      >
                        {d.danger_level ?? "—"}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-gray-500">
                      <span>
                        {d.detected_at
                          ? new Date(d.detected_at).toLocaleString()
                          : "—"}
                      </span>
                      {d.distance_cm != null && <span>{d.distance_cm} cm</span>}
                      {/* ✅ FIX: use normalized value, show N/A if null */}
                      {confNorm != null ? (
                        <span>{(confNorm * 100).toFixed(0)}%</span>
                      ) : (
                        <span className="text-gray-400">N/A</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ── Device toggle row ─────────────────────────────────────────────────────────
const DeviceRow = ({ device, onToggle, toggling }) => {
  const isActive = device.status === "active";
  return (
    <div className="flex items-center justify-between py-2.5 px-3 bg-gray-50 rounded-lg">
      <div>
        <p className="text-sm font-medium text-gray-800">
          {device.device_name}
        </p>
        <p className="text-xs text-gray-500">
          {device.device_model} · {device.status}
        </p>
      </div>
      <button
        onClick={() => onToggle(device, isActive ? "inactive" : "active")}
        disabled={toggling === device.id}
        className="flex items-center gap-1.5 text-xs font-medium transition-colors disabled:opacity-50"
        title={isActive ? "Deactivate device" : "Activate device"}
      >
        {toggling === device.id ? (
          <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
        ) : isActive ? (
          <ToggleRight className="w-6 h-6 text-green-600" />
        ) : (
          <ToggleLeft className="w-6 h-6 text-gray-400" />
        )}
        <span className={isActive ? "text-green-700" : "text-gray-500"}>
          {isActive ? "Active" : "Inactive"}
        </span>
      </button>
    </div>
  );
};

// ── User row with expand ──────────────────────────────────────────────────────
const UserRow = ({ user, onViewHistory, onToggleDevice, toggling }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
            <span className="text-sm font-bold text-purple-700">
              {(user.username?.[0] ?? "?").toUpperCase()}
            </span>
          </div>
          <div>
            <p className="font-semibold text-gray-900">{user.username}</p>
            <p className="text-xs text-gray-500">{user.email}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span
            className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
              user.role === "admin"
                ? "bg-purple-100 text-purple-800"
                : "bg-blue-100 text-blue-800"
            }`}
          >
            {user.role ?? "user"}
          </span>

          <button
            onClick={() => onViewHistory(user)}
            className="text-xs px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            History
          </button>

          {user.devices?.length > 0 && (
            <button
              onClick={() => setExpanded((p) => !p)}
              className="p-1.5 text-gray-400 hover:text-gray-600 rounded transition-colors"
            >
              {expanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>
          )}
        </div>
      </div>

      {expanded && user.devices?.length > 0 && (
        <div className="px-5 pb-4 space-y-2 border-t border-gray-100 pt-3">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Devices ({user.devices.length})
          </p>
          {user.devices.map((d) => (
            <DeviceRow
              key={d.id}
              device={d}
              onToggle={onToggleDevice}
              toggling={toggling}
            />
          ))}
        </div>
      )}

      {user.devices?.length === 0 && expanded && (
        <div className="px-5 pb-4 text-xs text-gray-400 border-t border-gray-100 pt-3">
          No devices registered.
        </div>
      )}
    </div>
  );
};

// ── Main component ────────────────────────────────────────────────────────────
const AdminUserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [historyUser, setHistoryUser] = useState(null);
  const [toggling, setToggling] = useState(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminAPI.getAllUsers();
      setUsers(res.data?.users ?? res.data?.data ?? []);
    } catch (err) {
      setError("Failed to load users.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleToggleDevice = async (device, newStatus) => {
    setToggling(device.id);
    try {
      await adminAPI.toggleDeviceStatus(device.id, newStatus);
      setUsers((prev) =>
        prev.map((u) => ({
          ...u,
          devices: u.devices?.map((d) =>
            d.id === device.id ? { ...d, status: newStatus } : d,
          ),
        })),
      );
    } catch (err) {
      console.error("Failed to toggle device status:", err);
    } finally {
      setToggling(null);
    }
  };

  const totalDevices = users.reduce(
    (sum, u) => sum + (u.devices?.length ?? 0),
    0,
  );
  const activeDevices = users.reduce(
    (sum, u) =>
      sum + (u.devices?.filter((d) => d.status === "active").length ?? 0),
    0,
  );

  return (
    <div className="space-y-6 fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Users & Devices</h2>
        <button
          onClick={fetchUsers}
          className="flex items-center gap-2 px-4 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
        >
          <Users className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Total Users", value: loading ? "—" : users.length },
          { label: "Total Devices", value: loading ? "—" : totalDevices },
          { label: "Active Devices", value: loading ? "—" : activeDevices },
        ].map(({ label, value }) => (
          <div
            key={label}
            className="bg-white rounded-lg shadow p-4 text-center"
          >
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
              {label}
            </p>
            <p className="text-2xl font-bold text-purple-700">{value}</p>
          </div>
        ))}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 text-sm">
          {error}
        </div>
      )}

      {/* User list */}
      <div className="space-y-3">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="bg-white rounded-lg shadow p-5 animate-pulse"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-gray-200" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-32" />
                  <div className="h-3 bg-gray-100 rounded w-48" />
                </div>
              </div>
            </div>
          ))
        ) : users.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
            No users found.
          </div>
        ) : (
          users.map((user) => (
            <UserRow
              key={user.id}
              user={user}
              onViewHistory={setHistoryUser}
              onToggleDevice={handleToggleDevice}
              toggling={toggling}
            />
          ))
        )}
      </div>

      {historyUser && (
        <UserHistoryDrawer
          user={historyUser}
          onClose={() => setHistoryUser(null)}
        />
      )}
    </div>
  );
};

export default AdminUserManagement;
