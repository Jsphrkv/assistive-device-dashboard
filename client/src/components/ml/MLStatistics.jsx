import React, { useState, useEffect, useMemo } from "react";
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  TrendingUp,
  Activity,
  AlertTriangle,
  RefreshCw,
  BarChart3,
} from "lucide-react";
import { useMLHistory } from "../../hooks/ml/useMLHistory";

const MLStatistics = ({ deviceId }) => {
  const { history, loading, refresh } = useMLHistory(
    deviceId || "default",
    500,
  );
  const [lastAnalysisTime, setLastAnalysisTime] = useState(null);

  // Process real data into chart formats
  const stats = useMemo(() => {
    if (!history || history.length === 0) {
      return {
        anomalyHistory: [],
        activityDistribution: [],
        modelPerformance: {
          anomalyAccuracy: 0,
          activityAccuracy: 0,
        },
      };
    }

    // 1. Anomaly History - Group by date (last 7 days)
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - (6 - i));
      d.setHours(0, 0, 0, 0);
      return d;
    });

    const anomalyHistory = last7Days.map((date) => {
      const nextDay = new Date(date);
      nextDay.setDate(nextDay.getDate() + 1);

      const dayLogs = history.filter((item) => {
        const itemDate = new Date(item.timestamp);
        return (
          itemDate >= date && itemDate < nextDay && item.is_anomaly === true
        );
      });

      const avgSeverity =
        dayLogs.length > 0
          ? dayLogs.reduce((sum, item) => {
              let severity = 30;
              if (
                item.result?.severity === "high" ||
                item.result?.danger_level === "High"
              ) {
                severity = 100;
              } else if (
                item.result?.severity === "medium" ||
                item.result?.danger_level === "Medium"
              ) {
                severity = 60;
              }
              return sum + severity;
            }, 0) / dayLogs.length
          : 0;

      return {
        date: date.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
        }),
        anomalies: dayLogs.length,
        severity: avgSeverity,
      };
    });

    // 2. Activity Distribution
    const activityCounts = history.reduce(
      (acc, item) => {
        if (item.prediction_type === "activity") {
          const activity = item.result?.activity?.toLowerCase() || "";
          if (activity.includes("resting") || activity === "sitting") {
            acc.resting++;
          } else if (activity.includes("walking")) {
            acc.walking++;
          } else if (activity.includes("using") || activity === "standing") {
            acc.using++;
          }
        }
        return acc;
      },
      { resting: 0, walking: 0, using: 0 },
    );

    const total =
      activityCounts.resting + activityCounts.walking + activityCounts.using;
    const activityDistribution =
      total > 0
        ? [
            {
              name: "Resting",
              value: Math.round((activityCounts.resting / total) * 100),
              color: "#10B981",
            },
            {
              name: "Walking",
              value: Math.round((activityCounts.walking / total) * 100),
              color: "#3B82F6",
            },
            {
              name: "Using Device",
              value: Math.round((activityCounts.using / total) * 100),
              color: "#8B5CF6",
            },
          ]
        : [];

    // 3. Model Performance - Calculate from confidence scores
    const anomalyLogs = history.filter((item) => item.is_anomaly === true);
    const activityLogs = history.filter(
      (item) => item.prediction_type === "activity",
    );

    const avgConfidence = (logs) => {
      if (logs.length === 0) return 0;
      const sum = logs.reduce(
        (acc, item) => acc + (item.confidence_score || 0.85),
        0,
      );
      return (sum / logs.length) * 100;
    };

    const modelPerformance = {
      anomalyAccuracy: avgConfidence(anomalyLogs),
      activityAccuracy: avgConfidence(activityLogs),
    };

    return {
      anomalyHistory,
      activityDistribution,
      modelPerformance,
    };
  }, [history]);

  // Log statistical analysis when data changes significantly
  useEffect(() => {
    if (history.length === 0) return;

    const now = Date.now();
    if (lastAnalysisTime && now - lastAnalysisTime < 5 * 60 * 1000) {
      return;
    }

    const anomalyCount = history.filter(
      (item) => item.is_anomaly === true,
    ).length;
    const activityCount = history.filter(
      (item) => item.prediction_type === "activity",
    ).length;

    console.log(
      `📊 Statistics Analysis: ${anomalyCount} anomalies, ${activityCount} activities`,
    );

    setLastAnalysisTime(now);
  }, [history.length, lastAnalysisTime]);

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
          <h2 className="text-2xl font-bold text-gray-900">ML Analytics</h2>
          <p className="text-sm text-gray-600 mt-1">
            Real-time insights from ML detection history
            {history.length > 0 && (
              <span className="ml-2 text-blue-600 font-semibold">
                • {history.length} data points analyzed
              </span>
            )}
          </p>
        </div>
        <button
          onClick={refresh}
          className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          <span className="text-sm">Refresh</span>
        </button>
      </div>

      {/* Empty State */}
      {history.length === 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-start gap-3">
            <BarChart3 className="w-6 h-6 text-blue-600 mt-1" />
            <div>
              <h3 className="text-lg font-semibold text-blue-900 mb-2">
                No Analytics Data Yet
              </h3>
              <p className="text-blue-800">
                Statistics and charts will appear here automatically as ML
                components collect data. Visit the Dashboard tab to see ML
                components in action, then return here for insights.
              </p>
            </div>
          </div>
        </div>
      )}

      {history.length > 0 && (
        <>
          {/* Anomaly Detection Trend */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center mb-4">
              <AlertTriangle className="w-5 h-5 text-orange-600 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">
                Anomaly Detection Trend (Last 7 Days)
              </h3>
            </div>
            {stats.anomalyHistory.some((d) => d.anomalies > 0) ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={stats.anomalyHistory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="anomalies"
                    stroke="#F59E0B"
                    strokeWidth={2}
                    name="Anomalies Detected"
                    dot={{ fill: "#F59E0B", r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="severity"
                    stroke="#EF4444"
                    strokeWidth={2}
                    name="Average Severity"
                    dot={{ fill: "#EF4444", r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <AlertTriangle className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No anomaly detections in the last 7 days</p>
              </div>
            )}
          </div>

          {/* Activity Distribution */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center mb-4">
              <Activity className="w-5 h-5 text-blue-600 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">
                Activity Distribution
              </h3>
            </div>
            {stats.activityDistribution.length > 0 ? (
              <div className="flex flex-col lg:flex-row items-center gap-8">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={stats.activityDistribution}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) =>
                        `${name} ${(percent * 100).toFixed(0)}%`
                      }
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {stats.activityDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex flex-col gap-3 min-w-[160px]">
                  {stats.activityDistribution.map((activity, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between text-sm gap-4"
                    >
                      <div className="flex items-center">
                        <div
                          className="w-3 h-3 rounded-full mr-2 flex-shrink-0"
                          style={{ backgroundColor: activity.color }}
                        />
                        <span className="text-gray-700">{activity.name}</span>
                      </div>
                      <span className="font-semibold text-gray-900">
                        {activity.value}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Activity className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No activity data collected yet</p>
              </div>
            )}
          </div>

          {/* ML Model Performance — 2 columns */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              ML Model Performance (Average Confidence)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
                <p className="text-sm text-blue-600 font-medium mb-1">
                  Anomaly Detection
                </p>
                <p className="text-3xl font-bold text-blue-900">
                  {stats.modelPerformance.anomalyAccuracy.toFixed(1)}%
                </p>
                <p className="text-xs text-blue-600 mt-1">Avg Confidence</p>
              </div>
              <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
                <p className="text-sm text-green-600 font-medium mb-1">
                  Activity Recognition
                </p>
                <p className="text-3xl font-bold text-green-900">
                  {stats.modelPerformance.activityAccuracy.toFixed(1)}%
                </p>
                <p className="text-xs text-green-600 mt-1">Avg Confidence</p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default MLStatistics;
