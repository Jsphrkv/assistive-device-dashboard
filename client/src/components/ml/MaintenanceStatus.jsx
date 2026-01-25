import React from "react";
import { Wrench, CheckCircle, Clock, AlertCircle } from "lucide-react";

const MaintenanceStatus = ({ deviceInfo, maintenanceData, loading }) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="space-y-2">
          <div className="h-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  // Show empty state if no data
  if (!maintenanceData) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center">
            <Wrench className="w-6 h-6 text-gray-400 mr-2" />
            <h3 className="text-lg font-semibold text-gray-600">
              Maintenance Status
            </h3>
          </div>
          <CheckCircle className="w-8 h-8 text-gray-300" />
        </div>

        <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 p-4">
          <p className="text-sm text-gray-500 text-center">
            No maintenance data available yet. Connect your device to start
            monitoring.
          </p>
        </div>
      </div>
    );
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case "high":
        return "text-red-600 bg-red-50";
      case "medium":
        return "text-yellow-600 bg-yellow-50";
      default:
        return "text-green-600 bg-green-50";
    }
  };

  const getPriorityIcon = () => {
    if (maintenanceData.needs_maintenance) {
      return maintenanceData.priority === "high" ? (
        <AlertCircle className="w-8 h-8 text-red-600" />
      ) : (
        <Clock className="w-8 h-8 text-yellow-600" />
      );
    }
    return <CheckCircle className="w-8 h-8 text-green-600" />;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center">
          <Wrench className="w-6 h-6 text-gray-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">
            Maintenance Status
          </h3>
        </div>
        {getPriorityIcon()}
      </div>

      <div
        className={`rounded-lg p-4 mb-4 ${getPriorityColor(maintenanceData.priority)}`}
      >
        <div className="flex items-center justify-between mb-2">
          <span className="font-semibold">
            {maintenanceData.needs_maintenance
              ? "Maintenance Required"
              : "System Healthy"}
          </span>
          <span className="text-sm font-medium">
            {(maintenanceData.confidence * 100).toFixed(0)}% confidence
          </span>
        </div>

        {!maintenanceData.needs_maintenance && (
          <p className="text-sm">
            Next maintenance recommended in ~
            {maintenanceData.estimated_days_until_maintenance} days
          </p>
        )}
      </div>

      {/* Device Info Summary */}
      {deviceInfo && (
        <div className="bg-gray-50 rounded-lg p-3 mb-4">
          <h4 className="font-semibold text-xs text-gray-600 mb-2 uppercase">
            Device Health Metrics
          </h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-gray-500">Age:</span>{" "}
              <span className="font-medium">
                {deviceInfo.device_age_days} days
              </span>
            </div>
            <div>
              <span className="text-gray-500">Battery Cycles:</span>{" "}
              <span className="font-medium">{deviceInfo.battery_cycles}</span>
            </div>
            <div>
              <span className="text-gray-500">Usage:</span>{" "}
              <span className="font-medium">
                {(deviceInfo.usage_intensity * 100).toFixed(0)}%
              </span>
            </div>
            <div>
              <span className="text-gray-500">Last Service:</span>{" "}
              <span className="font-medium">
                {deviceInfo.last_maintenance_days} days ago
              </span>
            </div>
          </div>
        </div>
      )}

      <div>
        <h4 className="font-semibold text-sm text-gray-700 mb-2">
          Recommendations:
        </h4>
        <ul className="space-y-2">
          {maintenanceData.recommendations?.map((rec, index) => (
            <li key={index} className="flex items-start text-sm text-gray-600">
              <span className="text-blue-500 mr-2">•</span>
              <span>{rec}</span>
            </li>
          ))}
        </ul>
      </div>

      {maintenanceData.needs_maintenance && (
        <button className="mt-4 w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors">
          Schedule Maintenance
        </button>
      )}
    </div>
  );
};

export default MaintenanceStatus;
