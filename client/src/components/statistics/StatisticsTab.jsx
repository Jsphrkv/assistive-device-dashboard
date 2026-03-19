import React, { useState, useEffect, useRef } from "react";
import { BarChart3, RefreshCw, AlertCircle } from "lucide-react";
import { statisticsAPI, mlAPI } from "../../services/api";
import AlertsChart from "./AlertsChart";
import ObstaclesChart from "./ObstaclesChart";
import PeakTimesChart from "./PeakTimesChart";
import AnomalyAlert from "../ml/AnomalyAlert";
import DangerMonitor from "../ml/DangerMonitor";
import EnvironmentMonitor from "../ml/EnvironmentMonitor";
import ObjectDetectionWidget from "../ml/ObjectDetectionWidget";

const StatisticsTab = ({ deviceId }) => {
  const [dailyStats, setDailyStats] = useState([]);
  const [obstacleStats, setObstacleStats] = useState([]);
  const [hourlyStats, setHourlyStats] = useState([]);
  const [mlSummary, setMlSummary] = useState(null);

  const [mlData, setMlData] = useState({
    dangerData: [],
    environmentData: [],
    anomalyData: null,
  });

  const [initialLoading, setInitialLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [hasData, setHasData] = useState(false);

  const isFirstLoad = useRef(true);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 30000);
    return () => clearInterval(interval);
  }, [deviceId]);

  // Single combined fetch — no detectionsAPI call here anymore.
  // ObjectDetectionWidget now reads ml_predictions directly.
  const fetchAll = async () => {
    if (isFirstLoad.current) {
      setInitialLoading(true);
    } else {
      setRefreshing(true);
    }
    setError(null);

    try {
      const [
        dailyRes,
        obstaclesRes,
        hourlyRes,
        summaryRes,
        dangerRes,
        environmentRes,
        anomalyRes,
      ] = await Promise.all([
        statisticsAPI.getDaily(7).catch(() => ({ data: { data: [] } })),
        statisticsAPI.getObstacles().catch(() => ({ data: { data: [] } })),
        statisticsAPI.getHourly().catch(() => ({ data: { data: [] } })),
        statisticsAPI.getSummary().catch(() => ({ data: null })),
        mlAPI
          .getHistory({ type: "danger_prediction", limit: 10 })
          .catch(() => ({ data: { data: [] } })),
        mlAPI
          .getHistory({ type: "environment_classification", limit: 10 })
          .catch(() => ({ data: { data: [] } })),
        mlAPI.getDetectionAnomalies().catch(() => ({ data: null })),
      ]);

      const dailyRaw = dailyRes.data?.data || [];
      const obstaclesRaw = obstaclesRes.data?.data || [];
      const hourlyRaw = hourlyRes.data?.data || [];

      setDailyStats(
        dailyRaw.map((item) => ({
          date: item.stat_date || item.date,
          alerts: item.total_alerts || item.alerts || 0,
        })),
      );
      setHourlyStats(
        hourlyRaw.map((item) => ({
          hour: item.hour_range || item.hour,
          detections: item.detection_count || item.detections || 0,
        })),
      );
      setObstacleStats(
        obstaclesRaw.map((item) => ({
          name:
            item.obstacle_type ||
            item.object_detected ||
            item.name ||
            "unknown",
          value: item.total_count || item.count || 0,
        })),
      );
      setMlSummary(summaryRes.data || null);
      setHasData(
        dailyRaw.length > 0 || obstaclesRaw.length > 0 || hourlyRaw.length > 0,
      );

      const filterByDevice = (items) => {
        if (!deviceId || deviceId === "device-001") return items;
        return items.filter((item) => item.device_id === deviceId);
      };

      setMlData({
        dangerData: filterByDevice(dangerRes.data?.data || []),
        environmentData: filterByDevice(environmentRes.data?.data || []),
        anomalyData: anomalyRes.data || null,
      });
    } catch (err) {
      console.error("Error fetching statistics:", err);
      if (isFirstLoad.current) {
        setError(err.message || "Failed to load statistics");
      }
    } finally {
      if (isFirstLoad.current) {
        setInitialLoading(false);
        isFirstLoad.current = false;
      } else {
        setRefreshing(false);
      }
    }
  };

  const handleRefresh = () => {
    isFirstLoad.current = false;
    fetchAll();
  };

  if (initialLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
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
                onClick={handleRefresh}
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

  const totalDetections = mlSummary?.totalPredictions ?? 0;
  const highDanger = mlSummary?.severityBreakdown?.high ?? 0;
  const mediumDanger = mlSummary?.severityBreakdown?.medium ?? 0;
  const lowDanger = mlSummary?.severityBreakdown?.low ?? 0;
  const anomalyRate = mlSummary?.anomalyRate ?? 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">
          Statistics & Analytics
        </h2>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          <RefreshCw
            className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`}
          />
          <span className="text-sm">
            {refreshing ? "Refreshing..." : "Refresh All"}
          </span>
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
                detection data.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      {mlSummary && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 mb-1">Total Detections</p>
            <p className="text-3xl font-bold text-gray-900">
              {totalDetections.toLocaleString()}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              All-time sensor records
            </p>
          </div>
          <div className="bg-red-50 rounded-lg shadow p-6">
            <p className="text-sm text-red-600 mb-1">High Danger</p>
            <p className="text-3xl font-bold text-red-600">
              {highDanger.toLocaleString()}
            </p>
            <p className="text-xs text-red-500 mt-1">
              Immediate attention needed
            </p>
          </div>
          <div className="bg-yellow-50 rounded-lg shadow p-6">
            <p className="text-sm text-yellow-600 mb-1">Medium Danger</p>
            <p className="text-3xl font-bold text-yellow-600">
              {mediumDanger.toLocaleString()}
            </p>
            <p className="text-xs text-yellow-500 mt-1">Caution recommended</p>
          </div>
          <div className="bg-blue-50 rounded-lg shadow p-6">
            <p className="text-sm text-blue-600 mb-1">Low Danger</p>
            <p className="text-3xl font-bold text-blue-600">
              {lowDanger.toLocaleString()}
            </p>
            <p className="text-xs text-blue-500 mt-1">Normal operation range</p>
          </div>
          <div className="bg-purple-50 rounded-lg shadow p-6">
            <p className="text-sm text-purple-600 mb-1">Anomaly Rate</p>
            <p className="text-3xl font-bold text-purple-600">
              {typeof anomalyRate === "number"
                ? `${anomalyRate.toFixed(2)}%`
                : `${anomalyRate}%`}
            </p>
            <p className="text-xs text-purple-500 mt-1">
              High + Critical detections
            </p>
          </div>
        </div>
      )}

      {/* Detection Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AlertsChart data={dailyStats} loading={false} />
        <ObstaclesChart data={obstacleStats} loading={false} />
      </div>
      <PeakTimesChart data={hourlyStats} loading={false} />

      {/* ── ML Statistics ─────────────────────────────────────────────────── */}
      <div className="mt-8 space-y-6">
        <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-600" />
          ML Statistics
        </h3>

        {/* Row 1: YOLO + Object Detection — self-fetches from ml_predictions */}
        <ObjectDetectionWidget deviceId={deviceId} />

        {/* Row 2: Anomaly Detection */}
        <AnomalyAlert
          deviceId={deviceId}
          data={mlData.anomalyData}
          loading={refreshing}
        />

        {/* Row 3: Danger + Environment */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <DangerMonitor
            deviceId={deviceId}
            dangerData={mlData.dangerData}
            loading={refreshing}
          />
          <EnvironmentMonitor
            deviceId={deviceId}
            environmentData={mlData.environmentData}
            loading={refreshing}
          />
        </div>
      </div>
    </div>
  );
};

export default StatisticsTab;
