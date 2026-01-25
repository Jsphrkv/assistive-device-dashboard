import React from "react";
import { AlertTriangle, CheckCircle } from "lucide-react";

const AnomalyAlert = ({ deviceId, batteryLevel, anomalyData, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-4 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    );
  }

  // Show empty state if no data
  if (!anomalyData) {
    return (
      <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 p-6">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <CheckCircle className="w-6 h-6 text-gray-400" />
          </div>
          <div className="ml-3 flex-1">
            <h3 className="text-lg font-semibold text-gray-600 mb-1">
              No Anomaly Data
            </h3>
            <p className="text-sm text-gray-500">
              Waiting for device telemetry to analyze anomalies...
            </p>
          </div>
        </div>
      </div>
    );
  }

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

          {/* Show telemetry details if available */}
          {anomalyData.telemetry && (
            <div className="mt-3 text-xs space-y-1 opacity-75">
              <div>
                Battery: {anomalyData.telemetry.battery_level?.toFixed(1)}%
              </div>
              <div>
                Temperature: {anomalyData.telemetry.temperature?.toFixed(1)}°C
              </div>
              <div>
                Signal: {anomalyData.telemetry.signal_strength?.toFixed(0)} dBm
              </div>
            </div>
          )}

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
