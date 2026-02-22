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

  // ✅ OPTIMIZED: Use props if provided, otherwise fetch independently
  const usingProps = propHealthData !== undefined;

  useEffect(() => {
    if (usingProps) {
      // Use data passed from parent
      processHealthData(propHealthData);
      setLoading(propLoading || false);
    } else {
      // Fetch independently (fallback for standalone usage)
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

    // ✅ FIXED: Correct field paths from backend
    // Backend: { is_anomaly, anomaly_severity, confidence_score, result: { score, severity, device_health_score, message } }
    setHealthData({
      isAnomaly: latest.is_anomaly || false,
      anomalyScore: (latest.result?.score || latest.anomaly_score || 0) * 100, // ✅ result.score (not anomaly_score)
      severity: latest.result?.severity || latest.anomaly_severity || "low",
      deviceHealthScore: latest.result?.device_health_score || 100,
      message: latest.result?.message || "Device operating normally",
      timestamp: latest.timestamp,
    });
  };

  const fetchHealthData = async () => {
    try {
      setLoading(true);

      const response = await mlAPI.getHistory({
        type: "anomaly",
        limit: 10,
      });

      const predictions = response.data?.data || [];

      // Filter by deviceId
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
    if (!usingProps) {
      fetchHealthData();
    }
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
  };

  const getHealthStatus = (score) => {
    if (score >= 90) return { label: "Excellent", color: "text-green-600" };
    if (score >= 70) return { label: "Good", color: "text-blue-600" };
    if (score >= 50) return { label: "Fair", color: "text-yellow-600" };
    return { label: "Poor", color: "text-red-600" };
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
                  className={`${
                    healthData.deviceHealthScore >= 90
                      ? "text-green-600"
                      : healthData.deviceHealthScore >= 70
                        ? "text-blue-600"
                        : healthData.deviceHealthScore >= 50
                          ? "text-yellow-600"
                          : "text-red-600"
                  }`}
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

          {/* Anomaly Status */}
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
                className={`font-semibold ${
                  healthData.isAnomaly ? "text-red-900" : "text-green-900"
                }`}
              >
                {healthData.isAnomaly ? "Anomaly Detected" : "Normal Operation"}
              </h4>
            </div>
            <p
              className={`text-sm ${
                healthData.isAnomaly ? "text-red-700" : "text-green-700"
              }`}
            >
              {healthData.message}
            </p>
          </div>

          {/* Severity Badge */}
          <div className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
            <span className="text-sm text-gray-600">Severity Level</span>
            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold border ${severityConfig[healthData.severity]?.color || "bg-gray-100 text-gray-700 border-gray-300"}`}
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
                ></div>
              </div>
            </div>
          )}

          {/* Last Updated */}
          <div className="pt-2 border-t text-xs text-gray-500 text-center">
            Updated {new Date(healthData.timestamp).toLocaleTimeString()}
          </div>
        </div>
      )}
    </div>
  );
};

export default DeviceHealthMonitor;
