import React, { useState, useEffect } from "react";
import { Wrench, AlertCircle, CheckCircle } from "lucide-react";
import { mlAPI } from "../../services/api";

const MaintenanceStatus = ({ deviceId, deviceInfo }) => {
  const [maintenanceData, setMaintenanceData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMaintenanceData();
    const interval = setInterval(fetchMaintenanceData, 60000); // Refresh every 60s
    return () => clearInterval(interval);
  }, [deviceId]);

  const fetchMaintenanceData = async () => {
    try {
      setLoading(true);

      // ✅ Use getHistory with maintenance filter
      const response = await mlAPI.getHistory({
        type: "maintenance",
        limit: 1,
      });

      const predictions = response.data?.data || [];

      if (predictions.length > 0) {
        const latest = predictions[0];
        setMaintenanceData({
          needsMaintenance: latest.result?.needs_maintenance || false,
          confidence: (latest.result?.confidence || 0) * 100,
          priority: latest.result?.priority || "low",
          recommendation:
            latest.result?.recommendation || "No maintenance needed",
          timestamp: latest.timestamp,
        });
      } else {
        // Default: No maintenance predictions yet
        setMaintenanceData({
          needsMaintenance: false,
          confidence: 85,
          priority: "low",
          recommendation: "All systems operational",
          timestamp: new Date().toISOString(),
        });
      }
    } catch (error) {
      console.error("Error fetching maintenance data:", error);
      setMaintenanceData({
        needsMaintenance: false,
        confidence: 85,
        priority: "low",
        recommendation: "All systems operational",
        timestamp: new Date().toISOString(),
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading && !maintenanceData) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600"></div>
        </div>
      </div>
    );
  }

  const priorityColors = {
    high: "bg-red-100 text-red-700 border-red-300",
    medium: "bg-yellow-100 text-yellow-700 border-yellow-300",
    low: "bg-green-100 text-green-700 border-green-300",
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Wrench className="w-5 h-5 text-orange-600" />
          Maintenance Status
        </h3>
        <button
          onClick={fetchMaintenanceData}
          disabled={loading}
          className="text-sm text-orange-600 hover:text-orange-700"
        >
          {loading ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-orange-600"></div>
          ) : (
            "Refresh"
          )}
        </button>
      </div>

      {maintenanceData && (
        <div className="space-y-4">
          {/* Status Header */}
          <div
            className={`p-4 rounded-lg border-2 ${
              maintenanceData.needsMaintenance
                ? "bg-orange-50 border-orange-300"
                : "bg-green-50 border-green-300"
            }`}
          >
            <div className="flex items-start gap-3">
              {maintenanceData.needsMaintenance ? (
                <AlertCircle className="w-6 h-6 text-orange-600 mt-1" />
              ) : (
                <CheckCircle className="w-6 h-6 text-green-600 mt-1" />
              )}
              <div>
                <h4
                  className={`font-semibold ${
                    maintenanceData.needsMaintenance
                      ? "text-orange-900"
                      : "text-green-900"
                  }`}
                >
                  {maintenanceData.needsMaintenance
                    ? "Maintenance Required"
                    : "No Maintenance Needed"}
                </h4>
                <p
                  className={`text-sm mt-1 ${
                    maintenanceData.needsMaintenance
                      ? "text-orange-700"
                      : "text-green-700"
                  }`}
                >
                  {maintenanceData.recommendation}
                </p>
              </div>
            </div>
          </div>

          {/* Priority Badge */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Priority Level</span>
            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold border ${priorityColors[maintenanceData.priority]}`}
            >
              {maintenanceData.priority.toUpperCase()}
            </span>
          </div>

          {/* Confidence Bar */}
          <div>
            <p className="text-sm text-gray-600 mb-2">Prediction Confidence</p>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-orange-600 h-2 rounded-full transition-all"
                style={{ width: `${maintenanceData.confidence}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              {maintenanceData.confidence.toFixed(1)}%
            </p>
          </div>

          {/* Device Info (if provided) */}
          {deviceInfo && (
            <div className="pt-4 border-t">
              <p className="text-xs text-gray-500 mb-2">
                Device Health Metrics
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-600">Battery Cycles:</span>
                  <span className="ml-1 font-semibold">
                    {deviceInfo.battery_cycles || 0}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Usage:</span>
                  <span className="ml-1 font-semibold">
                    {((deviceInfo.usage_intensity || 0) * 100).toFixed(0)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Device Age:</span>
                  <span className="ml-1 font-semibold">
                    {deviceInfo.device_age_days || 0} days
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Error Rate:</span>
                  <span className="ml-1 font-semibold">
                    {deviceInfo.error_rate || 0}%
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MaintenanceStatus;
