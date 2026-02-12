import React, { useState, useEffect } from "react";
import {
  FileText,
  Filter,
  Download,
  Search,
  AlertTriangle,
  Clock,
  RefreshCw,
  FileSpreadsheet,
  FileJson,
  Users,
  Car,
  Layers,
  MapPin,
} from "lucide-react";
import { detectionsAPI } from "../../services/api";
import { useMLHistory } from "../../hooks/ml/useMLHistory"; // Import the hook

// Object icons mapping
const OBJECT_ICONS = {
  person: "👤",
  vehicle: "🚗",
  stairs_down: "🪜⬇️",
  stairs_up: "🪜⬆️",
  pothole: "🕳️",
  curb: "🛑",
  wall: "🧱",
  door: "🚪",
  pole: "📫",
  furniture: "🪑",
  bicycle: "🚲",
  animal: "🐕",
  tree: "🌲",
  obstacle: "⚠️",
  moving_object: "🔄",
  unknown: "❓",
};

const DetectionLogsTab = () => {
  // ✅ Use the hook instead of manual state management
  const {
    history: detections,
    loading,
    error,
    refresh,
    addToHistory,
    fetchStats,
    stats: mlStats,
  } = useMLHistory({
    limit: 100,
    autoFetch: true,
    cacheDuration: 30000, // 30 seconds cache
  });

  const [filteredDetections, setFilteredDetections] = useState([]);
  const [filterObject, setFilterObject] = useState("all");
  const [filterCategory, setFilterCategory] = useState("all");
  const [filterDanger, setFilterDanger] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateRange, setDateRange] = useState("7days");

  // ✅ Fetch stats on mount
  useEffect(() => {
    fetchStats(7); // Fetch last 7 days stats
  }, [fetchStats]);

  // ✅ Apply filters whenever detections or filters change
  useEffect(() => {
    applyFilters();
  }, [
    detections,
    filterObject,
    filterCategory,
    filterDanger,
    searchQuery,
    dateRange,
  ]);

  const applyFilters = () => {
    let filtered = [...detections];

    // Object filter
    if (filterObject !== "all") {
      filtered = filtered.filter((d) => d.object_detected === filterObject);
    }

    // Category filter
    if (filterCategory !== "all") {
      filtered = filtered.filter((d) => d.object_category === filterCategory);
    }

    // Danger level filter
    if (filterDanger !== "all") {
      filtered = filtered.filter(
        (d) => d.danger_level?.toLowerCase() === filterDanger,
      );
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (d) =>
          d.object_detected?.toLowerCase().includes(query) ||
          d.obstacle_type?.toLowerCase().includes(query),
      );
    }

    // Date range filter
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

      filtered = filtered.filter((d) => new Date(d.detected_at) >= cutoff);
    }

    setFilteredDetections(filtered);
  };

  // ✅ Function to handle real-time detection logging
  const handleNewDetection = async (detection) => {
    try {
      // Add detection to history (this will also save to backend)
      await addToHistory({
        ...detection,
        detected_at: new Date().toISOString(),
      });
    } catch (error) {
      console.error("Failed to log detection:", error);
    }
  };

  // ✅ Use the hook's refresh function
  const handleRefresh = async () => {
    try {
      await refresh(); // Force refresh bypasses cache
    } catch (error) {
      console.error("Failed to refresh:", error);
    }
  };

  const exportDetections = async (format) => {
    try {
      let params = new URLSearchParams({ format });

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

        params.append("start_date", cutoff.toISOString());
      }

      if (filterObject !== "all") {
        params.append("object", filterObject);
      }

      const response = await detectionsAPI.export(params.toString());

      // Download file
      const blob = new Blob([response.data], {
        type:
          format === "pdf"
            ? "application/pdf"
            : format === "json"
              ? "application/json"
              : "text/csv",
      });

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `detections_${new Date().toISOString().split("T")[0]}.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Export failed:", error);
      alert("Export failed. Please try again.");
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      critical: "bg-red-100 text-red-800 border-red-300",
      navigation: "bg-orange-100 text-orange-800 border-orange-300",
      environmental: "bg-yellow-100 text-yellow-800 border-yellow-300",
      unknown: "bg-gray-100 text-gray-800 border-gray-300",
    };
    return colors[category] || colors.unknown;
  };

  const getDangerBadge = (level) => {
    const colors = {
      High: "bg-red-500 text-white",
      Medium: "bg-yellow-500 text-white",
      Low: "bg-blue-500 text-white",
    };
    return colors[level] || colors.Low;
  };

  // Calculate stats
  const stats = {
    total: filteredDetections.length,
    critical: filteredDetections.filter((d) => d.object_category === "critical")
      .length,
    navigation: filteredDetections.filter(
      (d) => d.object_category === "navigation",
    ).length,
    environmental: filteredDetections.filter(
      (d) => d.object_category === "environmental",
    ).length,
    high_danger: filteredDetections.filter((d) => d.danger_level === "High")
      .length,
  };

  // Get unique objects for filter
  const uniqueObjects = [
    ...new Set(detections.map((d) => d.object_detected)),
  ].filter(Boolean);

  // ✅ Show error state if there's an error
  if (error) {
    return (
      <div className="flex flex-col justify-center items-center h-64">
        <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
        <p className="text-red-600 font-medium">{error}</p>
        <button
          onClick={handleRefresh}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (loading && detections.length === 0) {
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
            Real-time log of all ML detections and predictions •{" "}
            {detections.length} total entries
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            <span className="text-sm">Refresh</span>
          </button>

          {/* Export dropdown */}
          <div className="relative group">
            <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
              <Download className="w-4 h-4" />
              <span className="text-sm">Export</span>
            </button>
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
              <button
                onClick={() => exportDetections("csv")}
                className="w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 rounded-t-lg"
              >
                <FileSpreadsheet className="w-4 h-4" />
                Export CSV
              </button>
              <button
                onClick={() => exportDetections("json")}
                className="w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2"
              >
                <FileJson className="w-4 h-4" />
                Export JSON
              </button>
              <button
                onClick={() => exportDetections("pdf")}
                className="w-full text-left px-4 py-2 hover:bg-gray-50 flex items-center gap-2 rounded-b-lg"
              >
                <FileText className="w-4 h-4" />
                Export PDF
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-xs text-gray-600 mb-1">Total Logs</p>
          <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
        </div>
        <div className="bg-red-50 rounded-lg shadow p-4">
          <p className="text-xs text-red-600 mb-1">Critical</p>
          <p className="text-2xl font-bold text-red-600">{stats.critical}</p>
        </div>
        <div className="bg-orange-50 rounded-lg shadow p-4">
          <p className="text-xs text-orange-600 mb-1">Navigation</p>
          <p className="text-2xl font-bold text-orange-600">
            {stats.navigation}
          </p>
        </div>
        <div className="bg-yellow-50 rounded-lg shadow p-4">
          <p className="text-xs text-yellow-600 mb-1">Environmental</p>
          <p className="text-2xl font-bold text-yellow-600">
            {stats.environmental}
          </p>
        </div>
        <div className="bg-purple-50 rounded-lg shadow p-4">
          <p className="text-xs text-purple-600 mb-1">High Danger</p>
          <p className="text-2xl font-bold text-purple-600">
            {stats.high_danger}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center mb-4">
          <Filter className="w-5 h-5 text-gray-600 mr-2" />
          <h3 className="text-sm font-semibold text-gray-900">Filters</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <select
            value={filterObject}
            onChange={(e) => setFilterObject(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Objects</option>
            {uniqueObjects.map((obj) => (
              <option key={obj} value={obj}>
                {OBJECT_ICONS[obj] || "❓"} {obj}
              </option>
            ))}
          </select>

          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Categories</option>
            <option value="critical">Critical</option>
            <option value="navigation">Navigation</option>
            <option value="environmental">Environmental</option>
            <option value="unknown">Unknown</option>
          </select>

          <select
            value={filterDanger}
            onChange={(e) => setFilterDanger(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Danger Levels</option>
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
                    Object
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Distance
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Danger
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Alert
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Confidence
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredDetections.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="px-6 py-12 text-center">
                      <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300" />
                      <p className="text-gray-500 font-medium">
                        No detections found
                      </p>
                      <p className="text-sm text-gray-400 mt-1">
                        {detections.length === 0
                          ? "Detections will appear as the device operates"
                          : "Try adjusting your filters"}
                      </p>
                    </td>
                  </tr>
                ) : (
                  filteredDetections.map((detection) => (
                    <tr key={detection.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div className="flex items-center">
                          <Clock className="w-4 h-4 text-gray-400 mr-2" />
                          {new Date(detection.detected_at).toLocaleString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">
                            {OBJECT_ICONS[detection.object_detected] || "❓"}
                          </span>
                          <div>
                            <p className="text-sm font-medium text-gray-900 capitalize">
                              {detection.object_detected || "unknown"}
                            </p>
                            <p className="text-xs text-gray-500">
                              {detection.obstacle_type}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-3 py-1 text-xs font-medium rounded-full border ${getCategoryColor(detection.object_category)}`}
                        >
                          {detection.object_category || "unknown"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {detection.distance_cm
                          ? `${detection.distance_cm.toFixed(1)} cm`
                          : "N/A"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded uppercase ${getDangerBadge(detection.danger_level)}`}
                        >
                          {detection.danger_level}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {detection.alert_type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div
                              className="bg-green-600 h-2 rounded-full"
                              style={{
                                width: `${detection.detection_confidence || 85}%`,
                              }}
                            ></div>
                          </div>
                          <span className="text-xs">
                            {(detection.detection_confidence || 85).toFixed(0)}%
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
      {filteredDetections.length > 0 && (
        <div className="text-center text-sm text-gray-600">
          Showing {filteredDetections.length} of {detections.length} total
          detections
        </div>
      )}
    </div>
  );
};

// ✅ Export the handleNewDetection function so it can be used externally
export { DetectionLogsTab };
export default DetectionLogsTab;
