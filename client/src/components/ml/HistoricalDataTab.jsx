import React, { useState, useEffect, useMemo } from "react";
import {
  Calendar,
  Download,
  TrendingUp,
  BarChart3,
  RefreshCw,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useMLHistory } from "../../contexts/MLHistoryContext";

const HistoricalDataTab = ({ deviceId }) => {
  const [dateRange, setDateRange] = useState("7days");

  // Get real ML history from the hook
  const { history, loading, refresh } = useMLHistory(
    deviceId || "default",
    500,
  );

  // Helper to detect log type
  const detectLogType = (item) => {
    const msg = item.message?.toLowerCase() || "";
    const source = item.source?.toLowerCase() || "";

    if (source === "ml_statistics" || msg.includes("statistical analysis")) {
      return "statistics";
    }
    if (
      msg.includes("maintenance") ||
      msg.includes("repair") ||
      msg.includes("service")
    ) {
      return "maintenance";
    }
    if (
      msg.includes("activity") ||
      msg.includes("walking") ||
      msg.includes("resting") ||
      msg.includes("using")
    ) {
      return "activity";
    }
    return "anomaly";
  };

  // Process real historical data
  const historicalData = useMemo(() => {
    if (!history || history.length === 0) return [];

    const days = dateRange === "7days" ? 7 : dateRange === "30days" ? 30 : 90;

    // Create array of dates
    const dateArray = Array.from({ length: days }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (days - i - 1));
      date.setHours(0, 0, 0, 0);
      return date;
    });

    // Group history by date
    const groupedData = dateArray.map((date) => {
      const nextDay = new Date(date);
      nextDay.setDate(nextDay.getDate() + 1);

      // Filter logs for this day
      const dayLogs = history.filter((item) => {
        const itemDate = new Date(item.timestamp);
        return itemDate >= date && itemDate < nextDay;
      });

      // Count by type
      const anomalies = dayLogs.filter(
        (item) => detectLogType(item) === "anomaly",
      ).length;
      const maintenance = dayLogs.filter(
        (item) => detectLogType(item) === "maintenance",
      ).length;
      const activities = dayLogs.filter(
        (item) => detectLogType(item) === "activity",
      ).length;

      // Calculate average confidence for the day
      const confidences = dayLogs.map(
        (item) => item.confidence || item.anomaly_score || 0.85,
      );
      const avgConfidence =
        confidences.length > 0
          ? (confidences.reduce((sum, c) => sum + c, 0) / confidences.length) *
            100
          : 0;

      return {
        date: date.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
        }),
        fullDate: date,
        anomalies,
        maintenance_alerts: maintenance,
        activity_changes: activities,
        avg_confidence: avgConfidence,
        total_logs: dayLogs.length,
      };
    });

    return groupedData;
  }, [history, dateRange]);

  // Calculate summary statistics
  const stats = useMemo(() => {
    const totalAnomalies = historicalData.reduce(
      (sum, d) => sum + d.anomalies,
      0,
    );
    const totalMaintenance = historicalData.reduce(
      (sum, d) => sum + d.maintenance_alerts,
      0,
    );
    const totalActivity = historicalData.reduce(
      (sum, d) => sum + d.activity_changes,
      0,
    );
    const avgConfidence =
      historicalData.length > 0
        ? historicalData.reduce((sum, d) => sum + d.avg_confidence, 0) /
          historicalData.length
        : 0;

    return {
      totalAnomalies,
      totalMaintenance,
      totalActivity,
      avgConfidence,
    };
  }, [historicalData]);

  const exportData = () => {
    if (historicalData.length === 0) return;

    const csv = [
      [
        "Date",
        "Anomalies",
        "Maintenance Alerts",
        "Activity Changes",
        "Avg Confidence",
        "Total Logs",
      ],
      ...historicalData.map((row) => [
        row.date,
        row.anomalies,
        row.maintenance_alerts,
        row.activity_changes,
        row.avg_confidence.toFixed(2),
        row.total_logs,
      ]),
    ]
      .map((row) => row.join(","))
      .join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ml-history-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            Historical ML Data
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Track ML predictions over time
            {history.length > 0 && (
              <span className="ml-2 text-blue-600 font-semibold">
                • {history.length} total entries
              </span>
            )}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* Date Range Filter */}
          <div className="flex items-center space-x-2">
            <Calendar className="w-5 h-5 text-gray-600" />
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="7days">Last 7 Days</option>
              <option value="30days">Last 30 Days</option>
              <option value="90days">Last 90 Days</option>
            </select>
          </div>

          {/* Refresh Button */}
          <button
            onClick={refresh}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span className="text-sm">Refresh</span>
          </button>

          {/* Export Button */}
          <button
            onClick={exportData}
            disabled={historicalData.length === 0}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="w-4 h-4" />
            <span className="text-sm">Export</span>
          </button>
        </div>
      </div>

      {/* Empty State */}
      {history.length === 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <BarChart3 className="w-6 h-6 text-blue-600 mt-1" />
            <div>
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                No Historical Data Yet
              </h3>
              <p className="text-blue-800">
                Historical data will appear here automatically as ML components
                collect predictions over time. Visit the Dashboard tab to see ML
                components in action.
              </p>
            </div>
          </div>
        </div>
      )}

      {history.length > 0 && (
        <>
          {/* ML Predictions Over Time */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              ML Predictions Timeline
            </h3>
            {historicalData.some((d) => d.total_logs > 0) ? (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={historicalData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="anomalies"
                    stroke="#EF4444"
                    strokeWidth={2}
                    name="Anomalies"
                    dot={{ fill: "#EF4444", r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="maintenance_alerts"
                    stroke="#F59E0B"
                    strokeWidth={2}
                    name="Maintenance Alerts"
                    dot={{ fill: "#F59E0B", r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="activity_changes"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    name="Activity Changes"
                    dot={{ fill: "#3B82F6", r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-96 flex items-center justify-center text-gray-400">
                <div className="text-center">
                  <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <p>No data in selected date range</p>
                  <p className="text-sm mt-2">
                    Try selecting a different time period
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Summary Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">Total Anomalies</p>
              <p className="text-2xl font-bold text-red-600">
                {stats.totalAnomalies}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {dateRange === "7days"
                  ? "Last 7 days"
                  : dateRange === "30days"
                    ? "Last 30 days"
                    : "Last 90 days"}
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">Maintenance Alerts</p>
              <p className="text-2xl font-bold text-orange-600">
                {stats.totalMaintenance}
              </p>
              <p className="text-xs text-gray-500 mt-1">Total predictions</p>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">Activity Changes</p>
              <p className="text-2xl font-bold text-blue-600">
                {stats.totalActivity}
              </p>
              <p className="text-xs text-gray-500 mt-1">State transitions</p>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">Avg Confidence</p>
              <p className="text-2xl font-bold text-green-600">
                {stats.avgConfidence.toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500 mt-1">Model accuracy</p>
            </div>
          </div>

          {/* Data Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">
                Detailed Records
              </h3>
            </div>
            <div className="overflow-x-auto">
              {historicalData.some((d) => d.total_logs > 0) ? (
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Anomalies
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Maintenance
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Activity
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Confidence
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Total Logs
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {historicalData
                      .filter((row) => row.total_logs > 0)
                      .slice(0, 10)
                      .map((row, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {row.date}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                              {row.anomalies}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-800">
                              {row.maintenance_alerts}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                              {row.activity_changes}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <div className="flex items-center">
                              <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                                <div
                                  className="bg-green-600 h-2 rounded-full"
                                  style={{ width: `${row.avg_confidence}%` }}
                                ></div>
                              </div>
                              <span className="text-xs">
                                {row.avg_confidence.toFixed(1)}%
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                            {row.total_logs}
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              ) : (
                <div className="py-12 text-center text-gray-400">
                  <TrendingUp className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <p>No records to display</p>
                  <p className="text-sm mt-2">
                    Try selecting a different time period
                  </p>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default HistoricalDataTab;
