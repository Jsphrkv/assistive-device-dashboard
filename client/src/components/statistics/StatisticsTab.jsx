import React, { useState, useEffect } from "react";
import { BarChart3, RefreshCw, AlertCircle } from "lucide-react";
import { statisticsAPI } from "../../services/api";
import AlertsChart from "./AlertsChart";
import ObstaclesChart from "./ObstaclesChart";
import PeakTimesChart from "./PeakTimesChart";
import MLStatistics from "../ml/MLStatistics";

const StatisticsTab = ({ deviceId }) => {
  const [dailyStats, setDailyStats] = useState([]);
  const [obstacleStats, setObstacleStats] = useState([]);
  const [hourlyStats, setHourlyStats] = useState([]);
  const [mlSummary, setMlSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasData, setHasData] = useState(false);

  useEffect(() => {
    fetchStatistics();

    // Auto-refresh every 60 seconds
    const interval = setInterval(fetchStatistics, 60000);
    return () => clearInterval(interval);
  }, [deviceId]);

  const fetchStatistics = async () => {
    setLoading(true);
    setError(null);

    try {
      const [dailyRes, obstaclesRes, hourlyRes, summaryRes] = await Promise.all(
        [
          statisticsAPI.getDaily(7).catch((err) => {
            console.error("Daily stats error:", err);
            return { data: { data: [] } };
          }),
          statisticsAPI.getObstacles().catch((err) => {
            console.error("Obstacles stats error:", err);
            return { data: { data: [] } };
          }),
          statisticsAPI.getHourly().catch((err) => {
            console.error("Hourly stats error:", err);
            return { data: { data: [] } };
          }),
          statisticsAPI.getSummary().catch((err) => {
            console.error("Summary stats error:", err);
            return { data: null };
          }),
        ],
      );

      const dailyRaw = dailyRes.data?.data || [];
      const obstaclesRaw = obstaclesRes.data?.data || [];
      const hourlyRaw = hourlyRes.data?.data || [];
      const summary = summaryRes.data || null;

      console.log("📊 Raw daily data from API:", dailyRaw);
      console.log("📊 Raw hourly data from API:", hourlyRaw);
      console.log("📊 Raw obstacles data from API:", obstaclesRaw);

      // Transform daily data
      const transformedDaily = dailyRaw.map((item) => ({
        date: item.stat_date || item.date,
        alerts: item.total_alerts || item.alerts || 0,
      }));

      // Transform hourly data
      const transformedHourly = hourlyRaw.map((item) => ({
        hour: item.hour_range || item.hour,
        detections: item.detection_count || item.detections || 0,
      }));

      // ✅ FIX: Use "value" instead of "count" for the pie chart
      const transformedObstacles = obstaclesRaw.map((item) => ({
        name:
          item.obstacle_type || item.object_detected || item.name || "unknown",
        value: item.total_count || item.count || 0, // ✅ Changed from "count" to "value"
      }));

      console.log("📊 Transformed daily data:", transformedDaily);
      console.log("📊 Transformed hourly data:", transformedHourly);
      console.log("📊 Transformed obstacles data:", transformedObstacles);

      const hasAnyData =
        transformedDaily.length > 0 ||
        transformedObstacles.length > 0 ||
        transformedHourly.length > 0;

      setDailyStats(transformedDaily);
      setObstacleStats(transformedObstacles);
      setHourlyStats(transformedHourly);
      setMlSummary(summary);
      setHasData(hasAnyData);

      console.log("✅ Statistics loaded:", {
        daily: transformedDaily.length,
        obstacles: transformedObstacles.length,
        hourly: transformedHourly.length,
        summary: summary ? "yes" : "no",
      });
    } catch (error) {
      console.error("Error fetching statistics:", error);
      setError(error.message || "Failed to load statistics");
      setHasData(false);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-red-600 mt-1" />
            <div>
              <h3 className="text-lg font-semibold text-red-900 mb-2">
                Error Loading Statistics
              </h3>
              <p className="text-red-800 mb-4">{error}</p>
              <button
                onClick={fetchStatistics}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">
          Statistics & Analytics
        </h2>
        <button
          onClick={fetchStatistics}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          <span className="text-sm">Refresh</span>
        </button>
      </div>

      {/* No Data Warning */}
      {!hasData && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <BarChart3 className="w-6 h-6 text-yellow-600 mt-1" />
            <div>
              <h3 className="text-lg font-semibold text-yellow-900 mb-2">
                No Statistics Available Yet
              </h3>
              <p className="text-yellow-800">
                Statistics will appear here once your device starts collecting
                detection data. Make sure your device is paired and active.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Summary Statistics Cards */}
      {mlSummary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 mb-1">Total Detections</p>
            <p className="text-3xl font-bold text-gray-900">
              {mlSummary.totalPredictions || 0}
            </p>
          </div>

          <div className="bg-red-50 rounded-lg shadow p-6">
            <p className="text-sm text-red-600 mb-1">High Priority</p>
            <p className="text-3xl font-bold text-red-600">
              {mlSummary.severityBreakdown?.high || 0}
            </p>
          </div>

          <div className="bg-yellow-50 rounded-lg shadow p-6">
            <p className="text-sm text-yellow-600 mb-1">Medium Priority</p>
            <p className="text-3xl font-bold text-yellow-600">
              {mlSummary.severityBreakdown?.medium || 0}
            </p>
          </div>

          <div className="bg-blue-50 rounded-lg shadow p-6">
            <p className="text-sm text-blue-600 mb-1">Anomaly Rate</p>
            <p className="text-3xl font-bold text-blue-600">
              {mlSummary.anomalyRate || 0}%
            </p>
          </div>
        </div>
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AlertsChart data={dailyStats} loading={loading} />
        <ObstaclesChart data={obstacleStats} loading={loading} />
      </div>

      {/* Peak Times Chart - Full Width */}
      <div className="grid grid-cols-1 gap-6">
        <PeakTimesChart data={hourlyStats} loading={loading} />
      </div>

      {/* ML Statistics Component */}
      <div className="mt-8">
        <MLStatistics deviceId={deviceId} />
      </div>
    </div>
  );
};

export default StatisticsTab;
