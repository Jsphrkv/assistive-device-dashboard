import React, { useState, useEffect } from "react";
import { Wrench, AlertCircle, CheckCircle, RefreshCw } from "lucide-react";
import { mlAPI } from "../../services/api";

const MaintenanceStatus = ({ deviceId }) => {
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

      // Get latest maintenance predictions
      const response = await mlAPI.getHistory({
        type: "maintenance",
        limit: 1,
      });

      const predictions = response.data?.data || [];

      if (predictions.length > 0) {
        const latest = predictions[0];
        setMaintenanceData({
          needsMaintenance: latest.result?.needs_maintenance || false,
          confidence: (latest.result?.probability || 0) * 100,
          priority: latest.result?.priority || "low",
          daysUntil: latest.result?.days_until || 90,
          recommendations: latest.result?.recommendations || {},
          message: latest.result?.message || "All systems operational",
          timestamp: latest.timestamp,
        });
      } else {
        setMaintenanceData(null);
      }
    } catch (error) {
      console.error("Error fetching maintenance data:", error);
      setMaintenanceData(null);
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
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {!maintenanceData ? (
        <div className="text-center py-8">
          <Wrench className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-gray-500 text-sm">
            No maintenance predictions yet
          </p>
          <p className="text-gray-400 text-xs mt-1">
            Collecting device health data...
          </p>
        </div>
      ) : (
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
                  {maintenanceData.message}
                </p>
              </div>
            </div>
          </div>

          {/* Priority & Days Until Grid */}
          <div className="grid grid-cols-2 gap-4">
            {/* Priority */}
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-600 mb-2">Priority Level</p>
              <span
                className={`inline-block px-3 py-1 rounded-full text-xs font-semibold border ${priorityColors[maintenanceData.priority]}`}
              >
                {maintenanceData.priority.toUpperCase()}
              </span>
            </div>

            {/* Days Until Maintenance */}
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-600 mb-2">Days Until Service</p>
              <p className="text-2xl font-bold text-gray-900">
                {maintenanceData.daysUntil}
              </p>
            </div>
          </div>

          {/* Recommendations */}
          {maintenanceData.recommendations &&
            Object.keys(maintenanceData.recommendations).length > 0 && (
              <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <p className="text-xs text-blue-600 font-medium mb-2">
                  🔧 Recommendations
                </p>
                <ul className="text-xs text-blue-700 space-y-1">
                  {Object.entries(maintenanceData.recommendations).map(
                    ([key, value]) => (
                      <li key={key}>• {value}</li>
                    ),
                  )}
                </ul>
              </div>
            )}

          {/* Confidence Bar */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs text-gray-600">Prediction Confidence</p>
              <p className="text-xs text-gray-600">
                {maintenanceData.confidence.toFixed(0)}%
              </p>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-orange-600 h-2 rounded-full transition-all"
                style={{ width: `${maintenanceData.confidence}%` }}
              ></div>
            </div>
          </div>

          {/* Last Updated */}
          <div className="pt-2 border-t text-xs text-gray-500 text-center">
            Updated {new Date(maintenanceData.timestamp).toLocaleTimeString()}
          </div>
        </div>
      )}
    </div>
  );
};

export default MaintenanceStatus;
