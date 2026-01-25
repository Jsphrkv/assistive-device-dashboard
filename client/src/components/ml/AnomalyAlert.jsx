import React, { useState, useEffect } from "react";
import { AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import { mlAPI } from "../../api";

const AnomalyAlert = ({ deviceId }) => {
  const [anomalyData, setAnomalyData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkForAnomalies();
    // Check every 30 seconds
    const interval = setInterval(checkForAnomalies, 30000);
    return () => clearInterval(interval);
  }, [deviceId]);

  const checkForAnomalies = async () => {
    try {
      const telemetry = {
        battery_level: Math.random() * 100,
        usage_duration: Math.random() * 400,
        temperature: 30 + Math.random() * 25,
        signal_strength: -90 + Math.random() * 30,
        error_count: Math.floor(Math.random() * 10),
      };

      // Replace fetch with:
      const response = await mlAPI.detectAnomaly(telemetry);
      const data = response.data; // axios returns data in response.data

      setAnomalyData(data);

      if (data) {
        addToHistory({
          ...data,
          timestamp: new Date().toISOString(),
          telemetry: telemetry,
        });
      }

      setLoading(false);
    } catch (error) {
      console.error("Anomaly detection error:", error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-4 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    );
  }

  if (!anomalyData) return null;

  const getSeverityColor = (severity) => {
    switch (severity) {
      case "high":
        return "bg-red-100 border-red-500 text-red-800";
      case "medium":
        return "bg-yellow-100 border-yellow-500 text-yellow-800";
      case "low":
        return "bg-blue-100 border-blue-500 text-blue-800";
      default:
        return "bg-green-100 border-green-500 text-green-800";
    }
  };

  const getSeverityIcon = (severity) => {
    if (anomalyData.is_anomaly) {
      return <AlertTriangle className="w-6 h-6" />;
    }
    return <CheckCircle className="w-6 h-6" />;
  };

  return (
    <div
      className={`rounded-lg border-l-4 p-4 ${getSeverityColor(anomalyData.severity)}`}
    >
      <div className="flex items-start">
        <div className="flex-shrink-0">
          {getSeverityIcon(anomalyData.severity)}
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-lg font-semibold mb-1">
            {anomalyData.is_anomaly ? "Anomaly Detected" : "System Normal"}
          </h3>
          <p className="text-sm mb-2">{anomalyData.message}</p>
          <div className="mt-2 flex items-center justify-between">
            <span className="text-xs font-medium">
              Anomaly Score: {(anomalyData.anomaly_score * 100).toFixed(0)}%
            </span>
            {anomalyData.is_anomaly && (
              <span className="text-xs font-semibold uppercase px-2 py-1 rounded bg-white bg-opacity-50">
                {anomalyData.severity} Priority
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnomalyAlert;
