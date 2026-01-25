// src/components/logs/DetectionLogsTab.jsx
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
  Calendar,
  Clock,
  XCircle,
} from "lucide-react";
import { useMLHistory } from "../../hooks/ml/useMLHistory";

const DetectionLogsTab = ({ deviceId }) => {
  const [allLogs, setAllLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [filterType, setFilterType] = useState("all"); // all, anomaly, activity, maintenance
  const [filterSeverity, setFilterSeverity] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateRange, setDateRange] = useState("all");

  // Use ML history hook
  const { history, loading } = useMLHistory(deviceId || "default", 500);

  useEffect(() => {
    // Combine real history with mock logs
    loadDetectionLogs();
  }, [history]);

  useEffect(() => {
    // Apply filters whenever logs or filters change
    applyFilters();
  }, [allLogs, filterType, filterSeverity, searchQuery, dateRange]);

  const loadDetectionLogs = () => {
    // Start with real history data
    const realLogs = history.map((item) => ({
      id: item.timestamp,
      timestamp: new Date(item.timestamp),
      type: item.message?.toLowerCase().includes("maintenance")
        ? "maintenance"
        : item.message?.toLowerCase().includes("activity")
          ? "activity"
          : "anomaly",
      severity: item.severity || (item.is_anomaly ? "medium" : "low"),
      status: item.is_anomaly ? "alert" : "normal",
      message: item.message || "Detection logged",
      confidence: item.confidence || item.anomaly_score || Math.random(),
      details: item,
    }));

    // Generate additional mock logs for demonstration
    const mockLogs = generateMockLogs(50);

    // Combine and sort by timestamp (newest first)
    const combined = [...realLogs, ...mockLogs].sort(
      (a, b) => b.timestamp - a.timestamp,
    );

    setAllLogs(combined);
  };

  const generateMockLogs = (count) => {
    const types = ["anomaly", "activity", "maintenance"];
    const severities = ["low", "medium", "high"];
    const statuses = ["normal", "alert", "warning"];

    const messages = {
      anomaly: [
        "Unusual device temperature detected",
        "Battery drain rate anomaly",
        "Signal strength fluctuation",
        "Unexpected usage pattern",
        "Error rate spike detected",
      ],
      activity: [
        "Activity changed to walking",
        "Device in use - high intensity",
        "Resting state detected",
        "Activity transition: walking to resting",
        "Continuous usage detected",
      ],
      maintenance: [
        "Routine maintenance check passed",
        "Battery replacement recommended",
        "Device age threshold approaching",
        "Usage intensity high - monitor closely",
        "All systems operating normally",
      ],
    };

    return Array.from({ length: count }, (_, i) => {
      const type = types[Math.floor(Math.random() * types.length)];
      const severity =
        severities[Math.floor(Math.random() * severities.length)];
      const isAlert = Math.random() > 0.7;
      const status = isAlert
        ? "alert"
        : Math.random() > 0.5
          ? "warning"
          : "normal";

      const timestamp = new Date();
      timestamp.setMinutes(
        timestamp.getMinutes() - Math.floor(Math.random() * 10000),
      );

      return {
        id: `mock-${i}-${Date.now()}`,
        timestamp,
        type,
        severity,
        status,
        message:
          messages[type][Math.floor(Math.random() * messages[type].length)],
        confidence: 0.7 + Math.random() * 0.3,
        details: {
          deviceId: deviceId || "default",
          source: "mock-generator",
        },
      };
    });
  };

  const applyFilters = () => {
    let filtered = [...allLogs];

    // Filter by type
    if (filterType !== "all") {
      filtered = filtered.filter((log) => log.type === filterType);
    }

    // Filter by severity
    if (filterSeverity !== "all") {
      filtered = filtered.filter((log) => log.severity === filterSeverity);
    }

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter((log) =>
        log.message.toLowerCase().includes(searchQuery.toLowerCase()),
      );
    }

    // Filter by date range
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

      filtered = filtered.filter((log) => log.timestamp >= cutoff);
    }

    setFilteredLogs(filtered);
  };

  const exportLogs = () => {
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
    alerts: filteredLogs.filter((l) => l.status === "alert").length,
    warnings: filteredLogs.filter((l) => l.status === "warning").length,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Detection Logs</h2>
          <p className="text-sm text-gray-600 mt-1">
            Comprehensive log of all ML detections and predictions
          </p>
        </div>
        <button
          onClick={exportLogs}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Download className="w-4 h-4" />
          <span className="text-sm">Export Logs</span>
        </button>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
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
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center mb-4">
          <Filter className="w-5 h-5 text-gray-600 mr-2" />
          <h3 className="text-sm font-semibold text-gray-900">Filters</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
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

          {/* Type Filter */}
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Types</option>
            <option value="anomaly">Anomalies</option>
            <option value="activity">Activities</option>
            <option value="maintenance">Maintenance</option>
          </select>

          {/* Severity Filter */}
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

          {/* Date Range Filter */}
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
                    <td
                      colSpan="6"
                      className="px-6 py-8 text-center text-gray-500"
                    >
                      No logs found matching your filters
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
                                  : "text-purple-600"
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
          Showing {filteredLogs.length} of {allLogs.length} total logs
        </div>
      )}
    </div>
  );
};

export default DetectionLogsTab;
