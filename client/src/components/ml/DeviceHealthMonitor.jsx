import React, { useState, useEffect, useCallback } from "react";
import { Activity, RefreshCw, Wifi, Clock, Shield } from "lucide-react";
import { mlAPI } from "../../services/api";

// ── helpers ──────────────────────────────────────────────────────────────────

const getHealthColor = (score) => {
  if (score >= 80)
    return {
      text: "text-green-600",
      bg: "bg-green-600",
      ring: "text-green-600",
    };
  if (score >= 60)
    return { text: "text-blue-600", bg: "bg-blue-600", ring: "text-blue-600" };
  if (score >= 40)
    return {
      text: "text-yellow-600",
      bg: "bg-yellow-600",
      ring: "text-yellow-600",
    };
  return { text: "text-red-600", bg: "bg-red-600", ring: "text-red-600" };
};

const getStatusBadge = (color) => {
  const map = {
    green: "bg-green-100  text-green-800  border-green-300",
    yellow: "bg-yellow-100 text-yellow-800 border-yellow-300",
    orange: "bg-orange-100 text-orange-800 border-orange-300",
    red: "bg-red-100    text-red-800    border-red-300",
  };
  return map[color] || map.green;
};

const formatLastSeen = (ts) => {
  if (!ts) return "Unknown";
  try {
    const d = new Date(ts);
    const diff = Math.floor((Date.now() - d.getTime()) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return d.toLocaleTimeString("en-PH", { timeZone: "Asia/Manila" });
  } catch {
    return "Unknown";
  }
};

// ── component ─────────────────────────────────────────────────────────────────

const DeviceHealthMonitor = ({
  deviceId,
  healthData: _ignored,
  loading: propLoading,
}) => {
  // NOTE: propHealthData (anomaly-based) is intentionally ignored.
  // This component now fetches detection-pattern health from /device-health.
  // The powerbank-based battery health was always 0% / "Poor" on the Pi
  // because powerbank battery level is unreadable via software.

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHealth = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await mlAPI.getDeviceHealth(); // GET /api/ml-history/device-health
      setData(res.data);
    } catch (err) {
      console.error("DeviceHealthMonitor fetch error:", err);
      setError("Could not load device health");
    } finally {
      setLoading(false);
    }
  }, [deviceId]);

  useEffect(() => {
    fetchHealth();
    const id = setInterval(fetchHealth, 30000);
    return () => clearInterval(id);
  }, [fetchHealth]);

  // ── loading ────────────────────────────────────────────────────────────────
  if (loading && !data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600" />
        </div>
      </div>
    );
  }

  // ── error ──────────────────────────────────────────────────────────────────
  if (error && !data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-green-600" />
          <h3 className="text-lg font-semibold text-gray-900">Device Health</h3>
        </div>
        <div className="text-center py-8">
          <p className="text-red-500 text-sm">{error}</p>
          <button
            onClick={fetchHealth}
            className="mt-3 text-sm text-blue-600 underline"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const score = data?.health_score ?? 85;
  const status = data?.status ?? "Idle";
  const color = data?.status_color ?? "green";
  const details = data?.details ?? {};
  const lastSeen = data?.last_seen;

  const { text: scoreText, ring: ringColor } = getHealthColor(score);
  const circumference = 2 * Math.PI * 56;
  const dashOffset = circumference * (1 - score / 100);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Activity className="w-5 h-5 text-green-600" />
          Device Health
        </h3>
        <button
          onClick={fetchHealth}
          disabled={loading}
          className="text-gray-400 hover:text-gray-600"
          title="Refresh"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      <div className="space-y-4">
        {/* circular score */}
        <div className="text-center">
          <div className="relative inline-flex items-center justify-center w-32 h-32">
            <svg className="transform -rotate-90 w-32 h-32">
              <circle
                cx="64"
                cy="64"
                r="56"
                stroke="currentColor"
                strokeWidth="8"
                fill="transparent"
                className="text-gray-200"
              />
              <circle
                cx="64"
                cy="64"
                r="56"
                stroke="currentColor"
                strokeWidth="8"
                fill="transparent"
                strokeDasharray={circumference}
                strokeDashoffset={dashOffset}
                className={ringColor}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute text-center">
              <div className={`text-3xl font-bold ${scoreText}`}>
                {Math.round(score)}
              </div>
              <div className="text-xs text-gray-500">Health</div>
            </div>
          </div>

          {/* status badge */}
          <div className="mt-2">
            <span
              className={`inline-block px-3 py-1 rounded-full text-xs font-semibold border ${getStatusBadge(color)}`}
            >
              {status}
            </span>
          </div>
        </div>

        {/* stats grid */}
        {details.total_detections_24h !== undefined && (
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 mb-1">Detections (24h)</p>
              <p className="text-xl font-bold text-gray-900">
                {details.total_detections_24h.toLocaleString()}
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 mb-1">Avg Confidence</p>
              <p className="text-xl font-bold text-gray-900">
                {details.avg_confidence_pct > 0
                  ? `${details.avg_confidence_pct.toFixed(0)}%`
                  : "—"}
              </p>
            </div>
            <div className="bg-red-50 rounded-lg p-3 text-center">
              <p className="text-xs text-red-500 mb-1">Critical</p>
              <p className="text-xl font-bold text-red-600">
                {details.critical_count ?? 0}
              </p>
            </div>
            <div className="bg-yellow-50 rounded-lg p-3 text-center">
              <p className="text-xs text-yellow-500 mb-1">High</p>
              <p className="text-xl font-bold text-yellow-600">
                {details.high_count ?? 0}
              </p>
            </div>
          </div>
        )}

        {/* message */}
        {details.message && (
          <div className="flex items-start gap-2 bg-blue-50 rounded-lg p-3">
            <Shield className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-blue-700">{details.message}</p>
          </div>
        )}

        {/* last seen */}
        <div className="flex items-center justify-between pt-2 border-t text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <Wifi className="w-3 h-3" />
            Last active: {formatLastSeen(lastSeen)}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {new Date().toLocaleTimeString("en-PH", {
              timeZone: "Asia/Manila",
            })}
          </span>
        </div>
      </div>
    </div>
  );
};

export default DeviceHealthMonitor;
