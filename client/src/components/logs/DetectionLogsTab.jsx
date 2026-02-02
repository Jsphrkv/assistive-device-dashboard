import React, { useState, useEffect } from "react";
import {
  FileText,
  Filter,
  Download,
  Search,
  AlertTriangle,
  CheckCircle,
  Activity,
  Wrench,
  Clock,
  RefreshCw,
  BarChart3,
} from "lucide-react";
import { useMLHistory } from "../../hooks/ml/useMLHistory";

const DetectionLogsTab = ({ deviceId }) => {
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [filterType, setFilterType] = useState("all");
  const [filterSeverity, setFilterSeverity] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateRange, setDateRange] = useState("all");

  // Get real ML history from the hook
  const { history, loading, refresh } = useMLHistory(
    deviceId || "default",
    500,
  );

  useEffect(() => {
    applyFilters();
  }, [history, filterType, filterSeverity, searchQuery, dateRange]);

  const applyFilters = () => {
    if (!history || history.length === 0) {
      setFilteredLogs([]);
      return;
    }

    // Convert history to log format
    let logs = history.map((item) => ({
      id: item.timestamp || Date.now(),
      timestamp: new Date(item.timestamp || Date.now()),
      type: detectLogType(item),
      severity: item.severity || (item.is_anomaly ? "medium" : "low"),
      status: item.is_anomaly ? "alert" : "normal",
      message: item.message || "Detection logged",
      confidence: item.confidence || item.anomaly_score || 0.85,
      details: item,
    }));

    // Apply filters
    if (filterType !== "all") {
      logs = logs.filter((log) => log.type === filterType);
    }

    if (filterSeverity !== "all") {
      logs = logs.filter((log) => log.severity === filterSeverity);
    }

    if (searchQuery) {
      logs = logs.filter((log) =>
        log.message.toLowerCase().includes(searchQuery.toLowerCase()),
      );
    }

    if (dateRange !== "all") {
      const now = new Date();
      const cutoff = new Date();

      switch (dateRange) {
        case "1hour":
          cutoff.setHours(now.getHours() - 1);
          break;
        case "24hours":
          cutoff.setHours(now.getHours() - 24);
          break;
        case "7days":
          cutoff.setDate(now.getDate() - 7);
          break;
        case "30days":
          cutoff.setDate(now.getDate() - 30);
          break;
      }

      logs = logs.filter((log) => log.timestamp >= cutoff);
    }

    // Sort by newest first
    logs.sort((a, b) => b.timestamp - a.timestamp);

    setFilteredLogs(logs);
  };

  const detectLogType = (item) => {
    const msg = item.message?.toLowerCase() || "";
    const source = item.source?.toLowerCase() || "";

    // Check source first for ML Statistics
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

  const exportLogs = () => {
    if (filteredLogs.length === 0) return;

    const csv = [
      ["Timestamp", "Type", "Severity", "Status", "Message", "Confidence"],
      ...filteredLogs.map((log) => [
        log.timestamp.toLocaleString(),
        log.type,
        log.severity,
        log.status,
        log.message,
        (log.confidence * 100).toFixed(1) + "%",
      ]),
    ]
      .map((row) => row.join(","))
      .join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `detection-logs-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case "anomaly":
        return <AlertTriangle className="w-4 h-4" />;
      case "activity":
        return <Activity className="w-4 h-4" />;
      case "maintenance":
        return <Wrench className="w-4 h-4" />;
      case "statistics":
        return <BarChart3 className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "alert":
        return "bg-red-100 text-red-800 border-red-300";
      case "warning":
        return "bg-yellow-100 text-yellow-800 border-yellow-300";
      case "normal":
        return "bg-green-100 text-green-800 border-green-300";
      default:
        return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  const getSeverityBadge = (severity) => {
    const colors = {
      high: "bg-red-500 text-white",
      medium: "bg-yellow-500 text-white",
      low: "bg-blue-500 text-white",
    };
    return colors[severity] || colors.low;
  };

  // Calculate statistics
  const stats = {
    total: filteredLogs.length,
    anomalies: filteredLogs.filter((l) => l.type === "anomaly").length,
    activities: filteredLogs.filter((l) => l.type === "activity").length,
    maintenance: filteredLogs.filter((l) => l.type === "maintenance").length,
    statistics: filteredLogs.filter((l) => l.type === "statistics").length,
    alerts: filteredLogs.filter((l) => l.status === "alert").length,
    warnings: filteredLogs.filter((l) => l.status === "warning").length,
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
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Detection Logs</h2>
          <p className="text-sm text-gray-600 mt-1">
            Real-time log of all ML detections and predictions
            {history.length > 0 && (
              <span className="ml-2 text-blue-600 font-semibold">
                • {history.length} total entries
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={refresh}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span className="text-sm">Refresh</span>
          </button>
          <button
            onClick={exportLogs}
            disabled={filteredLogs.length === 0}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="w-4 h-4" />
            <span className="text-sm">Export Logs</span>
          </button>
        </div>
      </div>

      {/* Info Banner - Only show if no logs */}
      {history.length === 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <FileText className="w-6 h-6 text-blue-600 mt-1" />
            <div>
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                No Detection Logs Yet
              </h3>
              <p className="text-blue-800">
                Logs will appear here automatically as the ML components
                (Anomaly Detection, Activity Monitor, Maintenance Prediction, ML
                Statistics) make detections. Check the Dashboard tab to see ML
                components in action.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-7 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-xs text-gray-600 mb-1">Total Logs</p>
          <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
        </div>
        <div className="bg-red-50 rounded-lg shadow p-4">
          <p className="text-xs text-red-600 mb-1">Anomalies</p>
          <p className="text-2xl font-bold text-red-600">{stats.anomalies}</p>
        </div>
        <div className="bg-blue-50 rounded-lg shadow p-4">
          <p className="text-xs text-blue-600 mb-1">Activities</p>
          <p className="text-2xl font-bold text-blue-600">{stats.activities}</p>
        </div>
        <div className="bg-purple-50 rounded-lg shadow p-4">
          <p className="text-xs text-purple-600 mb-1">Maintenance</p>
          <p className="text-2xl font-bold text-purple-600">
            {stats.maintenance}
          </p>
        </div>
        <div className="bg-teal-50 rounded-lg shadow p-4">
          <p className="text-xs text-teal-600 mb-1">Analytics</p>
          <p className="text-2xl font-bold text-teal-600">{stats.statistics}</p>
        </div>
        <div className="bg-orange-50 rounded-lg shadow p-4">
          <p className="text-xs text-orange-600 mb-1">Alerts</p>
          <p className="text-2xl font-bold text-orange-600">{stats.alerts}</p>
        </div>
        <div className="bg-yellow-50 rounded-lg shadow p-4">
          <p className="text-xs text-yellow-600 mb-1">Warnings</p>
          <p className="text-2xl font-bold text-yellow-600">{stats.warnings}</p>
        </div>
      </div>

      {/* Filters */}
      {history.length > 0 && (
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
              <option value="statistics">Analytics</option>
            </select>

            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Severities</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>

            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Time</option>
              <option value="1hour">Last Hour</option>
              <option value="24hours">Last 24 Hours</option>
              <option value="7days">Last 7 Days</option>
              <option value="30days">Last 30 Days</option>
            </select>
          </div>
        </div>
      )}

      {/* Logs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <div className="max-h-[600px] overflow-y-auto">
            <table className="w-full">
              <thead className="bg-gray-50 sticky top-0 z-10">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Message
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Confidence
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredLogs.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center">
                      <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                      <p className="text-gray-500 font-medium">No logs found</p>
                      <p className="text-sm text-gray-400 mt-1">
                        {history.length === 0
                          ? "Logs will appear as ML components make detections"
                          : "Try adjusting your filters"}
                      </p>
                    </td>
                  </tr>
                ) : (
                  filteredLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div className="flex items-center">
                          <Clock className="w-4 h-4 text-gray-400 mr-2" />
                          {log.timestamp.toLocaleString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <span
                            className={`mr-2 ${
                              log.type === "anomaly"
                                ? "text-red-600"
                                : log.type === "activity"
                                  ? "text-blue-600"
                                  : log.type === "maintenance"
                                    ? "text-purple-600"
                                    : "text-teal-600"
                            }`}
                          >
                            {getTypeIcon(log.type)}
                          </span>
                          <span className="text-sm font-medium text-gray-900 capitalize">
                            {log.type}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded uppercase ${getSeverityBadge(log.severity)}`}
                        >
                          {log.severity}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-3 py-1 text-xs font-medium rounded-full border ${getStatusColor(log.status)}`}
                        >
                          {log.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 max-w-md">
                        {log.message}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div
                              className="bg-green-600 h-2 rounded-full"
                              style={{ width: `${log.confidence * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-xs">
                            {(log.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Pagination Info */}
      {filteredLogs.length > 0 && (
        <div className="text-center text-sm text-gray-600">
          Showing {filteredLogs.length} of {history.length} total logs
        </div>
      )}
    </div>
  );
};

export default DetectionLogsTab;
