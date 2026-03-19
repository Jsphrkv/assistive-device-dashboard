import React, { useState, useEffect, useCallback } from "react";
import {
  AlertTriangle,
  Shield,
  RefreshCw,
  TrendingUp,
  Zap,
  BarChart2,
} from "lucide-react";
import { mlAPI } from "../../services/api";

// ── signal config ─────────────────────────────────────────────────────────────

const SIGNAL_META = {
  critical_spike: {
    icon: <Zap className="w-4 h-4" />,
    label: "Critical Spike",
    color: { high: "text-red-600", medium: "text-orange-500" },
    bg: {
      high: "bg-red-50 border-red-200",
      medium: "bg-orange-50 border-orange-200",
    },
  },
  confidence_drop: {
    icon: <TrendingUp className="w-4 h-4 rotate-180" />,
    label: "Confidence Drop",
    color: { high: "text-red-600", medium: "text-orange-500" },
    bg: {
      high: "bg-red-50 border-red-200",
      medium: "bg-orange-50 border-orange-200",
    },
  },
  detection_flood: {
    icon: <BarChart2 className="w-4 h-4" />,
    label: "Detection Flood",
    color: { medium: "text-yellow-600", low: "text-yellow-500" },
    bg: {
      medium: "bg-yellow-50 border-yellow-200",
      low: "bg-yellow-50 border-yellow-100",
    },
  },
  pattern_shift: {
    icon: <TrendingUp className="w-4 h-4" />,
    label: "Pattern Shift",
    color: { low: "text-blue-500" },
    bg: { low: "bg-blue-50 border-blue-200" },
  },
};

const SEVERITY_BADGE = {
  high: "bg-red-100    text-red-800    border-red-300",
  medium: "bg-orange-100 text-orange-800 border-orange-300",
  low: "bg-yellow-100 text-yellow-800 border-yellow-300",
  normal: "bg-green-100  text-green-800  border-green-300",
};

// ── component ─────────────────────────────────────────────────────────────────

const AnomalyAlert = ({
  deviceId,
  anomaliesData: _ignored,
  loading: _propLoading,
}) => {
  // NOTE: prop anomaliesData (hardware-based) intentionally ignored.
  // Anomaly is now derived from detection patterns — not device telemetry.

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnomalies = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await mlAPI.getDetectionAnomalies();
      setData(res.data);
    } catch (err) {
      console.error("AnomalyAlert fetch error:", err);
      setError("Could not load anomaly data");
    } finally {
      setLoading(false);
    }
  }, [deviceId]);

  useEffect(() => {
    fetchAnomalies();
    const id = setInterval(fetchAnomalies, 30000);
    return () => clearInterval(id);
  }, [fetchAnomalies]);

  // ── loading ────────────────────────────────────────────────────────────────
  if (loading && !data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600" />
        </div>
      </div>
    );
  }

  // ── error ──────────────────────────────────────────────────────────────────
  if (error && !data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-5 h-5 text-red-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Anomaly Detection
          </h3>
        </div>
        <div className="text-center py-8">
          <p className="text-red-500 text-sm">{error}</p>
          <button
            onClick={fetchAnomalies}
            className="mt-3 text-sm text-blue-600 underline"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const isAnomaly = data?.is_anomaly ?? false;
  const severity = data?.overall_severity ?? "normal";
  const summary = data?.summary ?? "Analyzing...";
  const anomalies = data?.anomalies ?? [];
  const stats = data?.stats ?? {};

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          {isAnomaly ? (
            <AlertTriangle className="w-5 h-5 text-red-600" />
          ) : (
            <Shield className="w-5 h-5 text-green-600" />
          )}
          Anomaly Detection
        </h3>
        <div className="flex items-center gap-2">
          <span
            className={`px-2 py-0.5 text-xs font-semibold rounded-full border ${SEVERITY_BADGE[severity]}`}
          >
            {severity.toUpperCase()}
          </span>
          <button
            onClick={fetchAnomalies}
            disabled={loading}
            className="text-gray-400 hover:text-gray-600"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {/* status banner */}
        <div
          className={`p-4 rounded-lg border-2 ${
            isAnomaly
              ? "bg-red-50 border-red-300"
              : "bg-green-50 border-green-300"
          }`}
        >
          <div className="flex items-start gap-3">
            {isAnomaly ? (
              <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
            ) : (
              <Shield className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
            )}
            <div>
              <p
                className={`font-semibold text-sm ${isAnomaly ? "text-red-900" : "text-green-900"}`}
              >
                {isAnomaly ? "Anomaly Detected" : "Detection Patterns Normal"}
              </p>
              <p
                className={`text-xs mt-0.5 ${isAnomaly ? "text-red-700" : "text-green-700"}`}
              >
                {summary}
              </p>
            </div>
          </div>
        </div>

        {/* quick stats row */}
        {stats.total_analyzed > 0 && (
          <div className="grid grid-cols-3 gap-2">
            <div className="bg-gray-50 rounded-lg p-2 text-center">
              <p className="text-xs text-gray-500">Analyzed</p>
              <p className="text-lg font-bold text-gray-900">
                {stats.total_analyzed}
              </p>
            </div>
            <div className="bg-red-50 rounded-lg p-2 text-center">
              <p className="text-xs text-red-500">Critical %</p>
              <p className="text-lg font-bold text-red-600">
                {stats.critical_rate_pct ?? 0}%
              </p>
            </div>
            <div className="bg-blue-50 rounded-lg p-2 text-center">
              <p className="text-xs text-blue-500">Avg Conf</p>
              <p className="text-lg font-bold text-blue-600">
                {stats.avg_confidence_pct != null
                  ? `${stats.avg_confidence_pct.toFixed(0)}%`
                  : "—"}
              </p>
            </div>
          </div>
        )}

        {/* active anomaly signals */}
        {anomalies.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              Active Signals
            </p>
            {anomalies.map((anomaly, idx) => {
              const meta = SIGNAL_META[anomaly.type] || {};
              const sevColor =
                (meta.color || {})[anomaly.severity] || "text-gray-700";
              const sevBg =
                (meta.bg || {})[anomaly.severity] ||
                "bg-gray-50 border-gray-200";
              return (
                <div
                  key={idx}
                  className={`flex items-start gap-3 p-3 rounded-lg border ${sevBg}`}
                >
                  <span className={`mt-0.5 flex-shrink-0 ${sevColor}`}>
                    {meta.icon || <AlertTriangle className="w-4 h-4" />}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className={`text-xs font-semibold ${sevColor}`}>
                      {meta.label || anomaly.type}
                    </p>
                    <p className="text-xs text-gray-600 mt-0.5 leading-tight">
                      {anomaly.message}
                    </p>
                  </div>
                  <span
                    className={`px-2 py-0.5 text-xs font-semibold rounded-full border flex-shrink-0 ${SEVERITY_BADGE[anomaly.severity]}`}
                  >
                    {anomaly.severity}
                  </span>
                </div>
              );
            })}
          </div>
        )}

        {/* dominant object context */}
        {stats.dominant_object && (
          <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t">
            <span>Most detected recently</span>
            <span className="font-medium text-gray-700 capitalize">
              {stats.dominant_object}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnomalyAlert;
