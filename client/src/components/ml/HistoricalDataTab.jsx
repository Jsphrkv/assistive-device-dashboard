import React, { useState, useEffect, useMemo } from "react";
import {
  Calendar,
  Download,
  TrendingUp,
  BarChart3,
  RefreshCw,
  Filter,
  Search,
  Clock,
  Brain,
  AlertTriangle,
  Activity,
  Package,
  Camera,
  Eye,
  ChevronLeft,
  ChevronRight,
  FileText,
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
import { useMLHistory } from "../../hooks/ml/useMLHistory";

// Type icons mapping
const TYPE_ICONS = {
  anomaly: AlertTriangle,
  activity: Activity,
  maintenance: Package,
  detection: Camera,
};

const TYPE_COLORS = {
  anomaly: "bg-red-50 text-red-700 border-red-200",
  activity: "bg-blue-50 text-blue-700 border-blue-200",
  maintenance: "bg-orange-50 text-orange-700 border-orange-200",
  detection: "bg-purple-50 text-purple-700 border-purple-200",
};

const HistoricalDataTab = () => {
  const [dateRange, setDateRange] = useState("7days");
  const [viewMode, setViewMode] = useState("charts"); // 'charts' or 'logs'

  // ✅ Pagination state for logs
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);

  // ✅ Filter states for logs view
  const [filterType, setFilterType] = useState("all");
  const [filterSource, setFilterSource] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [showAnomaliesOnly, setShowAnomaliesOnly] = useState(false);

  // Get ML history
  const { history, stats, loading, error, refresh, fetchStats } = useMLHistory({
    limit: 500,
    autoFetch: true,
    cacheDuration: 30000,
  });

  // Fetch stats on mount
  useEffect(() => {
    fetchStats(7);
  }, [fetchStats]);

  // Helper to detect log type
  const detectLogType = (item) => {
    if (item.prediction_type) {
      return item.prediction_type;
    }
    return "unknown";
  };

  // ✅ Filter logs for table view (individual entries, not aggregated)
  const filteredLogs = useMemo(() => {
    let filtered = [...history];

    // Anomalies filter
    if (showAnomaliesOnly) {
      filtered = filtered.filter((item) => item.is_anomaly);
    }

    // Type filter
    if (filterType !== "all") {
      filtered = filtered.filter((item) => {
        const type = item.prediction_type || detectLogType(item);
        return type === filterType;
      });
    }

    // Source filter
    if (filterSource !== "all") {
      filtered = filtered.filter((item) => item.source === filterSource);
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((item) => {
        const type = (item.prediction_type || "").toLowerCase();
        const deviceName = (item.device_name || "").toLowerCase();
        const resultStr = JSON.stringify(item.result || {}).toLowerCase();
        return (
          type.includes(query) ||
          deviceName.includes(query) ||
          resultStr.includes(query)
        );
      });
    }

    return filtered;
  }, [history, filterType, filterSource, searchQuery, showAnomaliesOnly]);

  // ✅ Paginate filtered logs
  const paginatedLogs = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filteredLogs.slice(startIndex, endIndex);
  }, [filteredLogs, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [filterType, filterSource, searchQuery, showAnomaliesOnly]);

  // ========== CHARTS VIEW DATA (keep existing logic) ==========
  const historicalData = useMemo(() => {
    if (!history || history.length === 0) return [];

    const days = dateRange === "7days" ? 7 : dateRange === "30days" ? 30 : 90;

    const dateArray = Array.from({ length: days }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (days - i - 1));
      date.setHours(0, 0, 0, 0);
      return date;
    });

    const groupedData = dateArray.map((date) => {
      const nextDay = new Date(date);
      nextDay.setDate(nextDay.getDate() + 1);

      const dayLogs = history.filter((item) => {
        const itemDate = new Date(item.timestamp);
        return itemDate >= date && itemDate < nextDay;
      });

      const anomalies = dayLogs.filter((item) => item.is_anomaly).length;
      const maintenance = dayLogs.filter(
        (item) => item.prediction_type === "maintenance",
      ).length;
      const activities = dayLogs.filter(
        (item) => item.prediction_type === "activity",
      ).length;
      const detections = dayLogs.filter(
        (item) => item.prediction_type === "detection",
      ).length;

      const confidences = dayLogs.map((item) => item.confidence_score || 0.85);
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
        anomalies,
        maintenance_alerts: maintenance,
        activity_changes: activities,
        detections,
        avg_confidence: avgConfidence,
        total_logs: dayLogs.length,
      };
    });

    return groupedData;
  }, [history, dateRange]);

  const summaryStats = useMemo(() => {
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

  // ✅ Export function
  const exportData = () => {
    if (viewMode === "charts") {
      // Export aggregated chart data
      if (historicalData.length === 0) return;

      const csv = [
        [
          "Date",
          "Anomalies",
          "Maintenance",
          "Activity",
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
    } else {
      // Export individual filtered logs
      if (filteredLogs.length === 0) return;

      const csv = [
        [
          "Timestamp",
          "Type",
          "Source",
          "Device",
          "Confidence",
          "Anomaly",
          "Details",
        ],
        ...filteredLogs.map((log) => [
          new Date(log.timestamp).toISOString(),
          log.prediction_type || "unknown",
          log.source || "N/A",
          log.device_name || "Unknown",
          ((log.confidence_score || 0.85) * 100).toFixed(1) + "%",
          log.is_anomaly ? "Yes" : "No",
          JSON.stringify(log.result || {}).replace(/,/g, ";"),
        ]),
      ]
        .map((row) => row.join(","))
        .join("\n");

      const blob = new Blob([csv], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ml-logs-${new Date().toISOString().split("T")[0]}.csv`;
      a.click();
    }
  };

  // ✅ Render result details
  const renderResult = (item) => {
    const result = item.result || {};
    const type = item.prediction_type || "unknown";

    switch (type) {
      case "anomaly":
        return (
          <div className="text-sm">
            <p className="text-gray-700">
              {result.message || "Anomaly detected"}
            </p>
            {result.score && (
              <span className="text-xs text-red-600">
                Score: {(result.score * 100).toFixed(1)}%
              </span>
            )}
            {result.severity && (
              <span className="ml-2 text-xs text-red-600">
                Severity: {result.severity}
              </span>
            )}
          </div>
        );

      case "activity":
        return (
          <div className="text-sm">
            <p className="text-gray-700 font-medium">
              {result.activity || "Activity detected"}
            </p>
            {result.confidence && (
              <span className="text-xs text-blue-600">
                {(result.confidence * 100).toFixed(1)}% confident
              </span>
            )}
            {result.intensity && (
              <span className="ml-2 text-xs text-blue-600">
                Intensity: {result.intensity}
              </span>
            )}
          </div>
        );

      case "maintenance":
        return (
          <div className="text-sm">
            <p className="text-gray-700">
              {result.recommendation || "Maintenance check"}
            </p>
            {result.needs_maintenance !== undefined && (
              <span
                className={`text-xs ${result.needs_maintenance ? "text-orange-600" : "text-green-600"}`}
              >
                {result.needs_maintenance ? "Required" : "Not required"}
              </span>
            )}
            {result.priority && (
              <span className="ml-2 text-xs text-orange-600">
                Priority: {result.priority}
              </span>
            )}
          </div>
        );

      case "detection":
        return (
          <div className="text-sm">
            <p className="text-gray-700">
              {result.obstacle_type || "Object detected"}
            </p>
            {result.distance && (
              <span className="text-xs text-purple-600">
                {result.distance.toFixed(1)} cm
              </span>
            )}
            {result.danger_level && (
              <span className="ml-2 text-xs text-purple-600">
                {result.danger_level} danger
              </span>
            )}
          </div>
        );

      default:
        return <p className="text-sm text-gray-600">No details available</p>;
    }
  };

  // ✅ Error state
  if (error) {
    return (
      <div className="flex flex-col justify-center items-center h-64">
        <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
        <p className="text-red-600 font-medium">{error}</p>
        <button
          onClick={() => {
            refresh();
            fetchStats(7);
          }}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  // ✅ Loading state
  if (loading && history.length === 0) {
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
            ML History & Analytics
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
          {/* View Mode Toggle */}
          <div className="flex items-center bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode("charts")}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                viewMode === "charts"
                  ? "bg-white text-blue-600 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              <BarChart3 className="w-4 h-4 inline mr-1" />
              Charts
            </button>
            <button
              onClick={() => setViewMode("logs")}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                viewMode === "logs"
                  ? "bg-white text-blue-600 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              <Eye className="w-4 h-4 inline mr-1" />
              Logs
            </button>
          </div>

          {/* Date Range Filter (for charts view only) */}
          {viewMode === "charts" && (
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
          )}

          {/* Refresh Button */}
          <button
            onClick={() => {
              refresh();
              fetchStats(7);
            }}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            <span className="text-sm">Refresh</span>
          </button>

          {/* Export Button */}
          <button
            onClick={exportData}
            disabled={
              viewMode === "charts"
                ? historicalData.length === 0
                : filteredLogs.length === 0
            }
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
            <Brain className="w-6 h-6 text-blue-600 mt-1" />
            <div>
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                No ML History Yet
              </h3>
              <p className="text-blue-800">
                ML predictions will appear here as they're generated by the
                system.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ========== CHARTS VIEW (unchanged) ========== */}
      {history.length > 0 && viewMode === "charts" && (
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
                    name="Maintenance"
                    dot={{ fill: "#F59E0B", r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="activity_changes"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    name="Activities"
                    dot={{ fill: "#3B82F6", r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-96 flex items-center justify-center text-gray-400">
                <div className="text-center">
                  <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                  <p>No data in selected date range</p>
                </div>
              </div>
            )}
          </div>

          {/* Summary Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">Total Anomalies</p>
              <p className="text-2xl font-bold text-red-600">
                {summaryStats.totalAnomalies}
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
                {summaryStats.totalMaintenance}
              </p>
              <p className="text-xs text-gray-500 mt-1">Total predictions</p>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">Activity Changes</p>
              <p className="text-2xl font-bold text-blue-600">
                {summaryStats.totalActivity}
              </p>
              <p className="text-xs text-gray-500 mt-1">State transitions</p>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">Avg Confidence</p>
              <p className="text-2xl font-bold text-green-600">
                {summaryStats.avgConfidence.toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500 mt-1">Model accuracy</p>
            </div>
          </div>

          {/* Aggregated Summary Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">
                Daily Summary
              </h3>
            </div>
            <div className="overflow-x-auto">
              {historicalData.some((d) => d.total_logs > 0) ? (
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Anomalies
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Maintenance
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Activity
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Confidence
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Total
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
                          <td className="px-6 py-4 whitespace-nowrap">
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
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* ========== LOGS VIEW (Individual Entries with Pagination) ========== */}
      {history.length > 0 && viewMode === "logs" && (
        <>
          {/* Statistics Cards */}
          {stats && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-white rounded-lg shadow p-4">
                <p className="text-xs text-gray-600 mb-1">Total Entries</p>
                <p className="text-2xl font-bold text-gray-900">
                  {filteredLogs.length}
                </p>
              </div>
              <div className="bg-red-50 rounded-lg shadow p-4">
                <p className="text-xs text-red-600 mb-1">Anomalies</p>
                <p className="text-2xl font-bold text-red-600">
                  {stats.anomalyCount}
                </p>
                <p className="text-xs text-red-500 mt-1">
                  {stats.anomalyRate}% rate
                </p>
              </div>
              <div className="bg-blue-50 rounded-lg shadow p-4">
                <p className="text-xs text-blue-600 mb-1">Activities</p>
                <p className="text-2xl font-bold text-blue-600">
                  {stats.byType?.activity || 0}
                </p>
              </div>
              <div className="bg-orange-50 rounded-lg shadow p-4">
                <p className="text-xs text-orange-600 mb-1">Maintenance</p>
                <p className="text-2xl font-bold text-orange-600">
                  {stats.byType?.maintenance || 0}
                </p>
              </div>
              <div className="bg-purple-50 rounded-lg shadow p-4">
                <p className="text-xs text-purple-600 mb-1">Avg Confidence</p>
                <p className="text-2xl font-bold text-purple-600">
                  {stats.avgConfidence}%
                </p>
              </div>
            </div>
          )}

          {/* Filters */}
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center mb-4">
              <Filter className="w-5 h-5 text-gray-600 mr-2" />
              <h3 className="text-sm font-semibold text-gray-900">Filters</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search logs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Types</option>
                <option value="anomaly">Anomalies</option>
                <option value="activity">Activities</option>
                <option value="maintenance">Maintenance</option>
                <option value="detection">Detections</option>
              </select>

              <select
                value={filterSource}
                onChange={(e) => setFilterSource(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Sources</option>
                <option value="ml_prediction">ML Predictions</option>
                <option value="detection_log">Detection Logs</option>
              </select>

              <button
                onClick={() => setShowAnomaliesOnly(!showAnomaliesOnly)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  showAnomaliesOnly
                    ? "bg-red-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                <AlertTriangle className="w-4 h-4 inline mr-1" />
                {showAnomaliesOnly ? "Anomalies Only" : "Show Anomalies"}
              </button>
            </div>
          </div>

          {/* Logs Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <div className="max-h-[600px] overflow-y-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 sticky top-0 z-10">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Timestamp
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Source
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Device
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Details
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Confidence
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {paginatedLogs.length === 0 ? (
                      <tr>
                        <td colSpan="6" className="px-6 py-12 text-center">
                          <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                          <p className="text-gray-500 font-medium">
                            No logs found
                          </p>
                          <p className="text-sm text-gray-400 mt-1">
                            {history.length === 0
                              ? "Logs will appear as ML predictions are generated"
                              : "Try adjusting your filters"}
                          </p>
                        </td>
                      </tr>
                    ) : (
                      paginatedLogs.map((log) => {
                        const type = log.prediction_type || "unknown";
                        const TypeIcon = TYPE_ICONS[type] || Brain;

                        return (
                          <tr key={log.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              <div className="flex items-center gap-2">
                                <Clock className="w-4 h-4 text-gray-400" />
                                {new Date(log.timestamp).toLocaleString()}
                                {log.is_anomaly && (
                                  <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full font-semibold">
                                    ANOMALY
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center gap-2">
                                <div
                                  className={`p-2 rounded-lg ${TYPE_COLORS[type] || TYPE_COLORS.anomaly}`}
                                >
                                  <TypeIcon className="w-4 h-4" />
                                </div>
                                <span className="text-sm font-medium text-gray-900 capitalize">
                                  {type}
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                                {log.source === "ml_prediction"
                                  ? "ML Prediction"
                                  : "Detection Log"}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {log.device_name || "Unknown"}
                            </td>
                            <td className="px-6 py-4 text-sm max-w-md">
                              {renderResult(log)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                  <div
                                    className="bg-green-600 h-2 rounded-full"
                                    style={{
                                      width: `${(log.confidence_score || 0.85) * 100}%`,
                                    }}
                                  ></div>
                                </div>
                                <span className="text-xs">
                                  {(
                                    (log.confidence_score || 0.85) * 100
                                  ).toFixed(0)}
                                  %
                                </span>
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Pagination */}
          {filteredLogs.length > 0 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">
                Showing {(currentPage - 1) * itemsPerPage + 1} to{" "}
                {Math.min(currentPage * itemsPerPage, filteredLogs.length)} of{" "}
                {filteredLogs.length} logs
              </p>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>

                <span className="text-sm text-gray-700">
                  Page {currentPage} of {totalPages}
                </span>

                <button
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default HistoricalDataTab;
