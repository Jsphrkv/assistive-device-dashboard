import React, { useState, useEffect } from "react";
import { Heart, Activity, RefreshCw } from "lucide-react";
import { mlAPI } from "../../services/api";

const DeviceHealthMonitor = ({
  deviceId,
  healthData: propHealthData,
  loading: propLoading,
}) => {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);

  const usingProps = propHealthData !== undefined;

  useEffect(() => {
    if (usingProps) {
      processHealthData(propHealthData);
      setLoading(propLoading || false);
    } else {
      fetchHealthData();
      const interval = setInterval(fetchHealthData, 30000);
      return () => clearInterval(interval);
    }
  }, [deviceId, propHealthData, propLoading, usingProps]);

  const processHealthData = (data) => {
    if (!data || data.length === 0) {
      setHealthData(null);
      return;
    }

    const latest = data[0];
    const result = latest.result || {};

    const rawScore = result.score ?? 0;
    const anomalyScorePct = rawScore > 1 ? rawScore : rawScore * 100;

    const deviceHealthScore = result.device_health_score ?? 100;
    const severity = result.severity || "low";

    // FIX: The anomaly model sometimes returns is_anomaly=False but
    // device_health_score=0 and severity='critical' — contradictory.
    // Derive isAnomaly from health score as a fallback so the widget
    // shows a consistent state instead of "Normal Operation" with score=0.
    const isAnomalyFromModel = latest.is_anomaly ?? false;
    const isAnomaly = isAnomalyFromModel || deviceHealthScore < 30;

    // FIX: Use message from result if available, otherwise derive from state
    const message =
      result.message &&
      result.message !== `Device anomaly detected (health: 0.0%)`
        ? result.message
        : isAnomaly
          ? `Device health is low (${deviceHealthScore.toFixed(0)}%)`
          : "Device operating normally";

    setHealthData({
      isAnomaly,
      anomalyScore: anomalyScorePct,
      severity,
      deviceHealthScore,
      message,
      timestamp: latest.timestamp,
    });
  };

  const fetchHealthData = async () => {
    try {
      setLoading(true);
      const response = await mlAPI.getHistory({ type: "anomaly", limit: 10 });
      const predictions = response.data?.data || [];
      const filtered =
        deviceId && deviceId !== "device-001"
          ? predictions.filter((p) => p.device_id === deviceId)
          : predictions;
      processHealthData(filtered);
    } catch (error) {
      console.error("Error fetching health data:", error);
      setHealthData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    if (!usingProps) fetchHealthData();
  };

  if (loading && !healthData) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
        </div>
      </div>
    );
  }

  const severityConfig = {
    low: { color: "bg-green-100 text-green-700 border-green-300", icon: "✓" },
    medium: {
      color: "bg-yellow-100 text-yellow-700 border-yellow-300",
      icon: "⚠️",
    },
    high: { color: "bg-red-100 text-red-700 border-red-300", icon: "🚨" },
    critical: { color: "bg-red-100 text-red-700 border-red-300", icon: "🚨" },
  };

  const getHealthStatus = (score) => {
    if (score >= 90) return { label: "Excellent", color: "text-green-600" };
    if (score >= 70) return { label: "Good", color: "text-blue-600" };
    if (score >= 50) return { label: "Fair", color: "text-yellow-600" };
    return { label: "Poor", color: "text-red-600" };
  };

  const getHealthBarColor = (score) => {
    if (score >= 90) return "text-green-600";
    if (score >= 70) return "text-blue-600";
    if (score >= 50) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Heart className="w-5 h-5 text-green-600" />
          Device Health
        </h3>
        {!usingProps && (
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="text-sm text-green-600 hover:text-green-700"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        )}
      </div>

      {!healthData ? (
        <div className="text-center py-8">
          <Activity className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-gray-500 text-sm">No health data yet</p>
          <p className="text-gray-400 text-xs mt-1">
            Monitoring device status...
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Health Score Circle */}
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
                  strokeDasharray={`${2 * Math.PI * 56}`}
                  strokeDashoffset={`${2 * Math.PI * 56 * (1 - healthData.deviceHealthScore / 100)}`}
                  className={getHealthBarColor(healthData.deviceHealthScore)}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute">
                <div
                  className={`text-3xl font-bold ${getHealthStatus(healthData.deviceHealthScore).color}`}
                >
                  {healthData.deviceHealthScore.toFixed(0)}
                </div>
                <div className="text-xs text-gray-500">Health Score</div>
              </div>
            </div>
            <p
              className={`mt-2 font-semibold ${getHealthStatus(healthData.deviceHealthScore).color}`}
            >
              {getHealthStatus(healthData.deviceHealthScore).label}
            </p>
          </div>

          {/* Anomaly Status — now consistent with health score */}
          <div
            className={`p-4 rounded-lg border-2 ${
              healthData.isAnomaly
                ? "bg-red-50 border-red-300"
                : "bg-green-50 border-green-300"
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">
                {healthData.isAnomaly ? "⚠️" : "✓"}
              </span>
              <h4
                className={`font-semibold ${healthData.isAnomaly ? "text-red-900" : "text-green-900"}`}
              >
                {healthData.isAnomaly ? "Anomaly Detected" : "Normal Operation"}
              </h4>
            </div>
            <p
              className={`text-sm ${healthData.isAnomaly ? "text-red-700" : "text-green-700"}`}
            >
              {healthData.message}
            </p>
          </div>

          {/* Severity Badge */}
          <div className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
            <span className="text-sm text-gray-600">Severity Level</span>
            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold border ${
                severityConfig[healthData.severity]?.color ||
                severityConfig.low.color
              }`}
            >
              {severityConfig[healthData.severity]?.icon}{" "}
              {healthData.severity.toUpperCase()}
            </span>
          </div>

          {/* Anomaly Score */}
          {healthData.isAnomaly && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs text-gray-600">Anomaly Score</p>
                <p className="text-xs text-gray-600">
                  {healthData.anomalyScore.toFixed(0)}%
                </p>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-red-600 h-2 rounded-full transition-all"
                  style={{
                    width: `${Math.min(100, healthData.anomalyScore)}%`,
                  }}
                />
              </div>
            </div>
          )}

          <div className="pt-2 border-t text-xs text-gray-500 text-center">
            Updated{" "}
            {new Date(healthData.timestamp).toLocaleTimeString("en-PH", {
              timeZone: "Asia/Manila",
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default DeviceHealthMonitor;
