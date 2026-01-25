import { useState } from "react";

export const useMLStatistics = (deviceId, timeRange = "24h") => {
  const [statistics] = useState({
    totalPredictions: 0,
    anomalyCount: 0,
    anomalyRate: 0,
    avgAnomalyScore: 0,
    severityBreakdown: { high: 0, medium: 0, low: 0 },
  });
  const [loading] = useState(false);
  const [error] = useState(null);

  // API fetch commented out - using local calculations only

  const calculateLocalStats = (history) => {
    if (!history || history.length === 0) {
      return {
        totalPredictions: 0,
        anomalyCount: 0,
        anomalyRate: 0,
        avgAnomalyScore: 0,
        severityBreakdown: { high: 0, medium: 0, low: 0 },
      };
    }

    const anomalies = history.filter((item) => item.is_anomaly);
    const anomalyCount = anomalies.length;
    const totalPredictions = history.length;

    const avgAnomalyScore =
      history.reduce((sum, item) => sum + (item.anomaly_score || 0), 0) /
      totalPredictions;

    const severityBreakdown = anomalies.reduce(
      (acc, item) => {
        const severity = item.severity || "low";
        acc[severity] = (acc[severity] || 0) + 1;
        return acc;
      },
      { high: 0, medium: 0, low: 0 },
    );

    return {
      totalPredictions,
      anomalyCount,
      anomalyRate: (anomalyCount / totalPredictions) * 100,
      avgAnomalyScore: avgAnomalyScore * 100,
      severityBreakdown,
    };
  };

  return {
    statistics,
    loading,
    error,
    calculateLocalStats,
    refresh: () => {},
  };
};

export const useMLAnalytics = (deviceId, options = {}) => {
  const { historyLimit = 50 } = options;

  const [history, setHistory] = useState([]);
  const statsHook = useMLStatistics(deviceId);

  const addToHistory = (prediction) => {
    setHistory((prev) => [prediction, ...prev].slice(0, historyLimit));
  };

  const combinedStats = {
    ...statsHook.statistics,
    localStats: statsHook.calculateLocalStats(history),
  };

  return {
    history,
    statistics: combinedStats,
    loading: false,
    error: null,
    addToHistory,
    refresh: () => {},
  };
};
