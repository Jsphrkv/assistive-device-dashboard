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
  Brain,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { detectionsAPI, statisticsAPI, mlAPI } from "../../services/api";
import { useDetectionLogs } from "../../hooks/useDetectionLogs";

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

const ITEMS_PER_PAGE = 10;

const DetectionLogsTab = () => {
  const {
    detections,
    loading,
    error,
    refresh,
    addDetection,
    getMLDetections,
    getMLStats,
  } = useDetectionLogs({
    limit: 1000, // keep at 1000 — logs table only needs recent rows
    autoFetch: true,
    cacheDuration: 30000,
  });

  // ✅ DB-accurate stats (replaces local array counts for cards)
  const [dbStats, setDbStats] = useState({
    total: 0,
    critical: 0,
    navigation: 0,
    environmental: 0,
    high_danger: 0,
  });
  const [statsLoading, setStatsLoading] = useState(false);

  const [filteredDetections, setFilteredDetections] = useState([]);
  const [filterObject, setFilterObject] = useState("all");
  const [filterCategory, setFilterCategory] = useState("all");
  const [filterDanger, setFilterDanger] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateRange, setDateRange] = useState("7days");
  const [showMLOnly, setShowMLOnly] = useState(false);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);

  // ✅ Fetch DB-accurate stats on mount
  useEffect(() => {
    fetchDBStats();
  }, []);

  useEffect(() => {
    applyFilters();
    setCurrentPage(1);
  }, [
    detections,
    filterObject,
    filterCategory,
    filterDanger,
    searchQuery,
    dateRange,
    showMLOnly,
  ]);

  // ✅ Fetch all card numbers from the DB via statisticsAPI.getSummary()
  //    This uses COUNT queries server-side so numbers are always accurate
  //    regardless of how many records exist (no truncation issue).
  const fetchDBStats = async () => {
    setStatsLoading(true);
    try {
      const [summaryRes, mlRes] = await Promise.all([
        statisticsAPI.getSummary(),
        mlAPI.getStats(7),
      ]);
      const data = summaryRes.data;
      const mlData = mlRes.data;

      setDbStats({
        total: data?.totalPredictions || 0,
        critical: data?.categoryBreakdown?.critical || 0,
        navigation: data?.categoryBreakdown?.navigation || 0,
        environmental: data?.categoryBreakdown?.environmental || 0,
        high_danger: data?.severityBreakdown?.high || 0,
        ml_detections: mlData?.totalPredictions || 0,
        ml_confidence: mlData?.avgConfidence || 0,
      });
    } catch (error) {
      console.error("Error fetching DB stats:", error);
      setDbStats({
        total: detections.length,
        critical: detections.filter((d) => d.object_category === "critical")
          .length,
        navigation: detections.filter((d) => d.object_category === "navigation")
          .length,
        environmental: detections.filter(
          (d) => d.object_category === "environmental",
        ).length,
        high_danger: detections.filter((d) => d.danger_level === "High").length,
        ml_detections: 0,
        ml_confidence: 0,
      });
    } finally {
      setStatsLoading(false);
    }
  };

  // ✅ applyFilters still works on local detections array — correct for the table
  const applyFilters = () => {
    let filtered = [...detections];

    if (showMLOnly) {
      filtered = filtered.filter((d) => d.detection_source === "camera");
    }

    if (filterObject !== "all") {
      filtered = filtered.filter((d) => d.object_detected === filterObject);
    }

    if (filterCategory !== "all") {
      filtered = filtered.filter((d) => d.object_category === filterCategory);
    }

    if (filterDanger !== "all") {
      filtered = filtered.filter(
        (d) => d.danger_level?.toLowerCase() === filterDanger,
      );
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (d) =>
          d.object_detected?.toLowerCase().includes(query) ||
          d.obstacle_type?.toLowerCase().includes(query),
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
        default:
          break;
      }

      filtered = filtered.filter((d) => new Date(d.detected_at) >= cutoff);
    }

    setFilteredDetections(filtered);
  };

  const handleNewDetection = async (detection) => {
    try {
      addDetection({
        ...detection,
        detected_at: new Date().toISOString(),
      });
    } catch (error) {
      console.error("Failed to log detection:", error);
    }
  };

  const handleRefresh = async () => {
    try {
      await refresh();
      await fetchDBStats(); // ✅ also refresh DB-accurate stats
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
          default:
            break;
        }

        params.append("start_date", cutoff.toISOString());
      }

      if (filterObject !== "all") {
        params.append("object", filterObject);
      }

      const response = await detectionsAPI.export(params.toString());

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

  // Pagination calculations — based on filtered local array (correct for table)
  const totalPages = Math.ceil(filteredDetections.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const currentDetections = filteredDetections.slice(startIndex, endIndex);

  const goToPage = (page) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

  const mlStats = getMLStats();

  const uniqueObjects = [
    ...new Set(detections.map((d) => d.object_detected)),
  ].filter(Boolean);

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
            <span className="text-blue-600 font-semibold">
              {dbStats.total.toLocaleString()} total entries
            </span>
            {detections.length < dbStats.total && (
              <span className="text-gray-500">
                {" "}
                (showing {detections.length.toLocaleString()} most recent)
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            disabled={loading || statsLoading}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw
              className={`w-4 h-4 ${loading || statsLoading ? "animate-spin" : ""}`}
            />
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

      {/* ✅ Statistics Cards — all from DB (accurate regardless of row limit) */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-xs text-gray-600 mb-1">Total Logs</p>
          <p className="text-2xl font-bold text-gray-900">
            {dbStats.total.toLocaleString()}
          </p>
          {detections.length < dbStats.total && (
            <p className="text-xs text-gray-500 mt-1">
              Loaded: {detections.length.toLocaleString()}
            </p>
          )}
        </div>

        <div className="bg-red-50 rounded-lg shadow p-4">
          <p className="text-xs text-red-600 mb-1">Critical</p>
          <p className="text-2xl font-bold text-red-600">
            {dbStats.critical.toLocaleString()}
          </p>
        </div>

        <div className="bg-orange-50 rounded-lg shadow p-4">
          <p className="text-xs text-orange-600 mb-1">Navigation</p>
          <p className="text-2xl font-bold text-orange-600">
            {dbStats.navigation.toLocaleString()}
          </p>
        </div>

        <div className="bg-yellow-50 rounded-lg shadow p-4">
          <p className="text-xs text-yellow-600 mb-1">Environmental</p>
          <p className="text-2xl font-bold text-yellow-600">
            {dbStats.environmental.toLocaleString()}
          </p>
        </div>

        <div className="bg-purple-50 rounded-lg shadow p-4">
          <p className="text-xs text-purple-600 mb-1">High Danger</p>
          <p className="text-2xl font-bold text-purple-600">
            {dbStats.high_danger.toLocaleString()}
          </p>
        </div>

        <div className="bg-blue-50 rounded-lg shadow p-4">
          <div className="flex items-center gap-1 mb-1">
            <Brain className="w-3 h-3 text-blue-600" />
            <p className="text-xs text-blue-600">ML Detections</p>
          </div>
          {/* mlStats is from the local array — acceptable here as an approximation */}
          <p className="text-2xl font-bold text-blue-600">
            {dbStats.ml_detections}
          </p>
          <p className="text-xs text-blue-500 mt-1">
            Avg: {dbStats.ml_confidence}%
          </p>
        </div>
      </div>

      {/* ML Filter Toggle */}
      {mlStats.total > 0 && (
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowMLOnly(!showMLOnly)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              showMLOnly
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            <Brain className="w-4 h-4" />
            <span className="text-sm">
              {showMLOnly ? "Showing ML Only" : "Show ML Only"} ({mlStats.total}
              )
            </span>
          </button>
          {showMLOnly && (
            <button
              onClick={() => setShowMLOnly(false)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
            >
              Show All
            </button>
          )}
        </div>
      )}

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

      {/* Logs Table — reads from local detections array (1000 most recent) */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
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
              {currentDetections.length === 0 ? (
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
                currentDetections.map((detection) => (
                  <tr key={detection.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-gray-400" />
                        {new Date(detection.detected_at).toLocaleString()}
                        {detection.detection_source === "camera" && (
                          <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full flex items-center gap-1">
                            <Brain className="w-3 h-3" />
                            ML
                          </span>
                        )}
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
                          />
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

      {/* Pagination — based on filteredDetections (local array) */}
      {filteredDetections.length > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Showing {startIndex + 1} to{" "}
            {Math.min(endIndex, filteredDetections.length)} of{" "}
            {filteredDetections.length} loaded logs
          </p>

          <div className="flex items-center gap-2">
            <button
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            <span className="text-sm text-gray-700">
              Page {currentPage} of {totalPages}
            </span>

            <button
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DetectionLogsTab;
