import React, { useState, useEffect, useMemo, useCallback } from "react";
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
  Camera,
  Eye,
  ChevronLeft,
  ChevronRight,
  FileText,
  Shield,
  MapPin,
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
import { mlAPI } from "../../services/api";

const TYPE_ICONS = {
  anomaly: AlertTriangle,
  detection: Camera,
  object_detection: Camera,
  danger_prediction: Shield,
  danger: Shield,
  environment_classification: MapPin,
  environment: MapPin,
};

const TYPE_COLORS = {
  anomaly: "bg-red-50 text-red-700 border-red-200",
  detection: "bg-purple-50 text-purple-700 border-purple-200",
  object_detection: "bg-purple-50 text-purple-700 border-purple-200",
  danger_prediction: "bg-red-50 text-red-700 border-red-200",
  danger: "bg-red-50 text-red-700 border-red-200",
  environment_classification: "bg-blue-50 text-blue-700 border-blue-200",
  environment: "bg-blue-50 text-blue-700 border-blue-200",
};

const HistoricalDataTab = () => {
  const [dateRange, setDateRange] = useState("7days");
  const [viewMode, setViewMode] = useState("charts");
  const [logsDateRange, setLogsDateRange] = useState("all");

  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);

  const [filterType, setFilterType] = useState("all");
  const [filterSource, setFilterSource] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [showAnomaliesOnly, setShowAnomaliesOnly] = useState(false);

  const [dailySummary, setDailySummary] = useState([]);
  const [dailyLoading, setDailyLoading] = useState(false);

  const { history, totalCount, stats, loading, error, refresh, fetchStats } =
    useMLHistory({
      limit: 10000,
      autoFetch: true,
      cacheDuration: 30000,
    });

  const getDays = useCallback(
    (range = dateRange) =>
      range === "7days" ? 7 : range === "30days" ? 30 : 90,
    [dateRange],
  );

  const fetchDailySummary = useCallback(async (days) => {
    setDailyLoading(true);
    try {
      const response = await mlAPI.getDailySummary(days);
      setDailySummary(response.data.data || []);
    } catch (err) {
      console.error("Failed to fetch daily summary:", err);
      setDailySummary([]);
    } finally {
      setDailyLoading(false);
    }
  }, []);

  useEffect(() => {
    const days = getDays(dateRange);
    fetchDailySummary(days);
    fetchStats(days, true);
  }, [dateRange]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Logs filtering ────────────────────────────────────────────────────────
  const filteredLogs = useMemo(() => {
    let filtered = [...history];

    if (logsDateRange !== "all") {
      const days = getDays(logsDateRange);
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - days);
      filtered = filtered.filter(
        (item) => new Date(item.timestamp) >= cutoffDate,
      );
    }

    if (showAnomaliesOnly) {
      filtered = filtered.filter((item) => item.is_anomaly);
    }

    if (filterType !== "all") {
      filtered = filtered.filter((item) => {
        const type = item.prediction_type;
        if (
          filterType === "detection" &&
          (type === "detection" || type === "object_detection")
        )
          return true;
        if (filterType === "danger" && type === "danger_prediction")
          return true;
        if (
          filterType === "environment" &&
          type === "environment_classification"
        )
          return true;
        return type === filterType;
      });
    }

    if (filterSource !== "all") {
      filtered = filtered.filter((item) => item.source === filterSource);
    }

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
  }, [
    history,
    logsDateRange,
    filterType,
    filterSource,
    searchQuery,
    showAnomaliesOnly,
    getDays,
  ]);

  const paginatedLogs = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredLogs.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredLogs, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage);

  useEffect(() => {
    setCurrentPage(1);
  }, [filterType, filterSource, searchQuery, showAnomaliesOnly]);

  const exportData = () => {
    if (viewMode === "charts") {
      if (dailySummary.length === 0) return;
      const csv = [
        [
          "Date",
          "Anomalies",
          "Detections",
          "Dangers",
          "Avg Confidence",
          "Total Logs",
        ],
        ...dailySummary.map((row) => [
          row.date,
          row.anomalies,
          row.detections,
          row.danger_predictions,
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
      case "detection":
      case "object_detection":
        return (
          <div className="text-sm">
            <p className="text-gray-700">
              {result.obstacle_type || result.object || "Object detected"}
            </p>
            {(result.distance || result.distance_cm) && (
              <span className="text-xs text-purple-600">
                {(result.distance || result.distance_cm).toFixed(1)} cm
              </span>
            )}
            {result.danger_level && (
              <span className="ml-2 text-xs text-purple-600">
                {result.danger_level} danger
              </span>
            )}
          </div>
        );
      case "danger_prediction":
        return (
          <div className="text-sm">
            <p className="text-gray-700 font-medium">
              {result.message ||
                `Action: ${result.recommended_action || "Unknown"}`}
            </p>
            {result.danger_score !== undefined && (
              <span className="text-xs text-red-600">
                Danger: {result.danger_score.toFixed(1)}/100
              </span>
            )}
            {result.time_to_collision && (
              <span className="ml-2 text-xs text-red-600">
                TTC: {result.time_to_collision.toFixed(1)}s
              </span>
            )}
          </div>
        );
      case "environment_classification":
        return (
          <div className="text-sm">
            <p className="text-gray-700">
              {result.message ||
                `${result.environment_type || "Unknown"} environment`}
            </p>
            {result.lighting_condition && (
              <span className="text-xs text-blue-600">
                {result.lighting_condition} lighting
              </span>
            )}
            {result.complexity_level && (
              <span className="ml-2 text-xs text-blue-600">
                {result.complexity_level} complexity
              </span>
            )}
          </div>
        );
      default:
        return <p className="text-sm text-gray-600">No details available</p>;
    }
  };

  // ── Error state ───────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className="flex flex-col justify-center items-center h-64">
        <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
        <p className="text-red-600 font-medium">{error}</p>
        <button
          onClick={() => {
            const days = getDays();
            refresh();
            fetchStats(days, true);
            fetchDailySummary(days);
          }}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  // ── Initial loading state ─────────────────────────────────────────────────
  if ((loading || dailyLoading) && history.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const daysLabel =
    dateRange === "7days"
      ? "Last 7 days"
      : dateRange === "30days"
        ? "Last 30 days"
        : "Last 90 days";

  return (
    <div className="space-y-6">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            ML History & Analytics
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Track ML predictions over time
            {totalCount > 0 && (
              <span className="ml-2 text-blue-600 font-semibold">
                • {totalCount.toLocaleString()} total entries
                {history.length < totalCount && (
                  <span className="text-gray-400 font-normal ml-1">
                    (showing {history.length.toLocaleString()})
                  </span>
                )}
              </span>
            )}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* Charts / Logs toggle */}
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

          {/* Date range picker (charts mode only) */}
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

          <button
            onClick={() => {
              const days = getDays();
              refresh();
              fetchStats(days, true);
              fetchDailySummary(days);
            }}
            disabled={loading || dailyLoading}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw
              className={`w-4 h-4 ${loading || dailyLoading ? "animate-spin" : ""}`}
            />
            <span className="text-sm">Refresh</span>
          </button>

          <button
            onClick={exportData}
            disabled={
              viewMode === "charts"
                ? dailySummary.length === 0
                : filteredLogs.length === 0
            }
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="w-4 h-4" />
            <span className="text-sm">Export</span>
          </button>
        </div>
      </div>

      {/* Date range picker for Logs mode */}
      {viewMode === "logs" && (
        <div className="flex items-center space-x-2">
          <Calendar className="w-5 h-5 text-gray-600" />
          <select
            value={logsDateRange}
            onChange={(e) => setLogsDateRange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Time</option>
            <option value="7days">Last 7 Days</option>
            <option value="30days">Last 30 Days</option>
            <option value="90days">Last 90 Days</option>
          </select>
        </div>
      )}

      {/* Empty state */}
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

      {/* ══════════════════════════════════════════════════════════════════════
          CHARTS VIEW
      ══════════════════════════════════════════════════════════════════════ */}
      {history.length > 0 && viewMode === "charts" && (
        <>
          {/* Timeline chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              ML Predictions Timeline
            </h3>
            {dailyLoading ? (
              <div className="h-96 flex items-center justify-center">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
              </div>
            ) : dailySummary.some((d) => d.total_logs > 0) ? (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={dailySummary}>
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
                    dataKey="detections"
                    stroke="#8B5CF6"
                    strokeWidth={2}
                    name="Detections"
                    dot={{ fill: "#8B5CF6", r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="danger_predictions"
                    stroke="#DC2626"
                    strokeWidth={2}
                    name="Danger Predictions"
                    dot={{ fill: "#DC2626", r: 4 }}
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

          {/* Summary cards — 4 columns (maintenance removed) */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">Total Anomalies</p>
              <p className="text-2xl font-bold text-red-600">
                {stats?.anomalyCount ?? 0}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {daysLabel} • ML + Sensor
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">Detections</p>
              <p className="text-2xl font-bold text-purple-600">
                {stats
                  ? (stats.byType?.object_detection ?? 0) +
                    (stats.byType?.detection ?? 0)
                  : 0}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Object detections only
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">Danger Predictions</p>
              <p className="text-2xl font-bold text-red-600">
                {stats?.byType?.danger_prediction ?? 0}
              </p>
              <p className="text-xs text-gray-500 mt-1">Risk assessments</p>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-sm text-gray-600 mb-1">Avg Confidence</p>
              <p className="text-2xl font-bold text-green-600">
                {stats ? `${stats.avgConfidence}%` : "0%"}
              </p>
              <p className="text-xs text-gray-500 mt-1">Combined Accuracy</p>
            </div>
          </div>

          {/* Daily Summary table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">
                Daily Summary
              </h3>
            </div>
            <div className="overflow-x-auto">
              {dailySummary.some((d) => d.total_logs > 0) ? (
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
                        Detections
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Dangers
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
                    {dailySummary
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
                            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
                              {row.detections}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                              {row.danger_predictions}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="w-20 bg-gray-200 rounded-full h-2 mr-2">
                                <div
                                  className="bg-green-600 h-2 rounded-full"
                                  style={{ width: `${row.avg_confidence}%` }}
                                />
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

      {/* ══════════════════════════════════════════════════════════════════════
          LOGS VIEW
      ══════════════════════════════════════════════════════════════════════ */}
      {history.length > 0 && viewMode === "logs" && (
        <>
          {/* Logs stats cards — 4 columns (maintenance removed) */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <p className="text-xs text-gray-600 mb-1">Total Entries</p>
              <p className="text-2xl font-bold text-gray-900">
                {totalCount.toLocaleString()}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                ML + Sensor records ({history.length.toLocaleString()})
              </p>
            </div>
            <div className="bg-red-50 rounded-lg shadow p-4">
              <p className="text-xs text-red-600 mb-1">Anomalies</p>
              <p className="text-2xl font-bold text-red-600">
                {stats?.anomalyCount ?? 0}
              </p>
              <p className="text-xs text-red-500 mt-1">
                {stats
                  ? `${stats.anomalyRate}% rate • ML + Sensor`
                  : "ML + Sensor"}
              </p>
            </div>
            <div className="bg-purple-50 rounded-lg shadow p-4">
              <p className="text-xs text-purple-600 mb-1">Object Detections</p>
              <p className="text-2xl font-bold text-purple-600">
                {stats
                  ? (stats.byType?.object_detection ?? 0) +
                    (stats.byType?.detection ?? 0)
                  : 0}
              </p>
              <p className="text-xs text-purple-500 mt-1">
                Object detections only
              </p>
            </div>
            <div className="bg-green-50 rounded-lg shadow p-4">
              <p className="text-xs text-green-600 mb-1">Avg Confidence</p>
              <p className="text-2xl font-bold text-green-600">
                {stats?.avgConfidence ?? 0}%
              </p>
              <p className="text-xs text-green-500 mt-1">
                Across all prediction types
              </p>
            </div>
          </div>

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
                <option value="detection">Object Detection</option>
                <option value="danger">Danger Prediction</option>
                <option value="environment">Environment</option>
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
                                  {type.replace(/_/g, " ")}
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
                                  />
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
