import React, { useState, useEffect } from "react";
import { Wrench, CheckCircle, Clock, AlertCircle } from "lucide-react";
import { mlAPI } from "../../api";

const MaintenanceStatus = ({ deviceInfo }) => {
  const [maintenanceData, setMaintenanceData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkMaintenanceStatus();
  }, [deviceInfo]);

  const checkMaintenanceStatus = async () => {
    try {
      const deviceData = deviceInfo || {
        device_age_days: 365,
        battery_cycles: 500,
        usage_intensity: 0.6,
        error_rate: 1.5,
        last_maintenance_days: 90,
      };

      // Replace fetch with:
      const response = await mlAPI.predictMaintenance(deviceData);
      const data = response.data;

      setMaintenanceData(data);

      if (data) {
        addToHistory({
          ...data,
          timestamp: new Date().toISOString(),
          message: data.needs_maintenance
            ? `Maintenance required - ${data.priority} priority`
            : `System healthy - next maintenance in ~${data.estimated_days_until_maintenance} days`,
          is_anomaly: data.needs_maintenance,
          severity: data.priority,
        });
      }

      setLoading(false);
    } catch (error) {
      console.error("Maintenance prediction error:", error);
      setLoading(false);
    }
  };

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

  if (!maintenanceData) return null;

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

      <div>
        <h4 className="font-semibold text-sm text-gray-700 mb-2">
          Recommendations:
        </h4>
        <ul className="space-y-2">
          {maintenanceData.recommendations.map((rec, index) => (
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
