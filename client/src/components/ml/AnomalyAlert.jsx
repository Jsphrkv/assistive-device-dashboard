import React, { useState, useEffect } from "react";
import { AlertTriangle, Shield, RefreshCw } from "lucide-react";
import { mlAPI } from "../../services/api";

const AnomalyAlert = ({
  deviceId,
  anomaliesData: propAnomaliesData,
  loading: propLoading,
}) => {
  const [anomalyData, setAnomalyData] = useState(null);
  const [recentAnomalies, setRecentAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);

  const usingProps = propAnomaliesData !== undefined;

  useEffect(() => {
    if (usingProps) {
      processAnomalyData(propAnomaliesData);
      setLoading(propLoading || false);
    } else {
      fetchAnomalyData();
      const interval = setInterval(fetchAnomalyData, 30000);
      return () => clearInterval(interval);
    }
  }, [deviceId, propAnomaliesData, propLoading, usingProps]);

  const processAnomalyData = (anomalies) => {
    // /api/ml-history/anomalies returns flat items (different shape from /api/ml-history):
    // {
    //   id, device_id, type, severity, message,
    //   score: number | null    ← already 0-1 normalized by backend
    //   timestamp, source
    // }
    // Note: no nested `result` object — anomalies endpoint is flat by design.

    const normalised = (anomalies || []).map((item) => {
      const rawScore = item.score ?? 0;
      const scorePct = rawScore > 1 ? rawScore : rawScore * 100;
      return {
        id: item.id,
        isAnomaly: true,
        severity: item.severity || "low",
        score: scorePct,
        message: item.message || "Anomaly detected",
        type: item.type || "anomaly",
        timestamp: item.timestamp,
      };
    });

    setRecentAnomalies(normalised);

    if (normalised.length > 0) {
      const latest = normalised[0];
      setAnomalyData({
        isAnomaly: true,
        severity: latest.severity,
        message: latest.message,
        score: latest.score,
        timestamp: latest.timestamp,
        type: latest.type,
      });
    } else {
      setAnomalyData({
        isAnomaly: false,
        severity: "low",
        message: "All systems normal",
        score: 0,
        timestamp: new Date().toISOString(),
        type: "normal",
      });
    }
  };

  const fetchAnomalyData = async () => {
    try {
      setLoading(true);
      const response = await mlAPI.getAnomalies(10);
      const allAnomalies = response.data?.data || [];
      const anomalies =
        deviceId && deviceId !== "device-001"
          ? allAnomalies.filter((a) => a.device_id === deviceId)
          : allAnomalies;
      processAnomalyData(anomalies);
    } catch (error) {
      console.error("Error fetching anomaly data:", error);
      setAnomalyData({
        isAnomaly: false,
        severity: "low",
        message: "All systems normal",
        score: 0,
        timestamp: new Date().toISOString(),
        type: "normal",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    if (!usingProps) fetchAnomalyData();
  };

  if (loading && !anomalyData) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
        </div>
      </div>
    );
  }

  const severityColors = {
    high: "bg-red-100 text-red-700 border-red-300",
    critical: "bg-red-100 text-red-700 border-red-300",
    medium: "bg-yellow-100 text-yellow-700 border-yellow-300",
    low: "bg-green-100 text-green-700 border-green-300",
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          {anomalyData?.isAnomaly ? (
            <AlertTriangle className="w-5 h-5 text-red-600" />
          ) : (
            <Shield className="w-5 h-5 text-green-600" />
          )}
          Anomaly Detection
        </h3>
        {!usingProps && (
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="text-sm text-gray-600 hover:text-gray-700"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        )}
      </div>

      {anomalyData && (
        <div className="space-y-4">
          {/* Status Card */}
          <div
            className={`p-4 rounded-lg border-2 ${
              anomalyData.isAnomaly
                ? "bg-red-50 border-red-300"
                : "bg-green-50 border-green-300"
            }`}
          >
            <div className="flex items-start gap-3">
              {anomalyData.isAnomaly ? (
                <AlertTriangle className="w-6 h-6 text-red-600 mt-1" />
              ) : (
                <Shield className="w-6 h-6 text-green-600 mt-1" />
              )}
              <div>
                <h4
                  className={`font-semibold ${anomalyData.isAnomaly ? "text-red-900" : "text-green-900"}`}
                >
                  {anomalyData.isAnomaly ? "Anomaly Detected" : "No Anomalies"}
                </h4>
                <p
                  className={`text-sm mt-1 ${anomalyData.isAnomaly ? "text-red-700" : "text-green-700"}`}
                >
                  {anomalyData.message}
                </p>
              </div>
            </div>
          </div>

          {/* Severity Badge */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Severity Level</span>
            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold border ${
                severityColors[anomalyData.severity] || severityColors.low
              }`}
            >
              {anomalyData.severity.toUpperCase()}
            </span>
          </div>

          {/* Anomaly Score */}
          {anomalyData.isAnomaly && anomalyData.score > 0 && (
            <div>
              <p className="text-sm text-gray-600 mb-2">Anomaly Score</p>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-red-600 h-2 rounded-full transition-all"
                  style={{ width: `${Math.min(100, anomalyData.score)}%` }}
                />
              </div>
              <p className="text-sm text-gray-600 mt-1">
                {anomalyData.score.toFixed(1)}%
              </p>
            </div>
          )}

          {/* Recent Anomalies List */}
          {recentAnomalies.length > 0 && (
            <div className="pt-4 border-t">
              <p className="text-xs text-gray-500 mb-2">Recent Anomalies</p>
              <div className="space-y-2">
                {recentAnomalies.slice(0, 3).map((anomaly, index) => (
                  <div
                    key={anomaly.id || index}
                    className="flex items-center justify-between text-xs p-2 bg-gray-50 rounded"
                  >
                    <div>
                      <p className="font-medium text-gray-900 capitalize">
                        {anomaly.type?.replace(/_/g, " ") || "anomaly"}
                      </p>
                      <p className="text-gray-600 text-xs">
                        {new Date(anomaly.timestamp).toLocaleTimeString(
                          "en-PH",
                          {
                            timeZone: "Asia/Manila",
                          },
                        )}
                      </p>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                        severityColors[anomaly.severity] || severityColors.low
                      }`}
                    >
                      {anomaly.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AnomalyAlert;
