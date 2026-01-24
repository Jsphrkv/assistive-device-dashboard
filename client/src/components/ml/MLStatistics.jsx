import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
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
import { TrendingUp, Activity, AlertTriangle } from "lucide-react";

const MLStatistics = () => {
  const [anomalyHistory, setAnomalyHistory] = useState([]);
  const [activityDistribution, setActivityDistribution] = useState([]);
  const [maintenanceTimeline, setMaintenanceTimeline] = useState([]);

  useEffect(() => {
    // Simulate loading historical data
    generateMockData();

    const interval = setInterval(() => {
      updateRealTimeData();
    }, 10000); // Update every 10 seconds

    return () => clearInterval(interval);
  }, []);

  const generateMockData = () => {
    // Anomaly history (last 7 days)
    const anomalyData = Array.from({ length: 7 }, (_, i) => ({
      date: new Date(
        Date.now() - (6 - i) * 24 * 60 * 60 * 1000,
      ).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      anomalies: Math.floor(Math.random() * 10),
      severity: Math.random() * 100,
    }));
    setAnomalyHistory(anomalyData);

    // Activity distribution
    const activityData = [
      { name: "Resting", value: 45, color: "#10B981" },
      { name: "Walking", value: 30, color: "#3B82F6" },
      { name: "Using Device", value: 25, color: "#8B5CF6" },
    ];
    setActivityDistribution(activityData);

    // Maintenance predictions (next 6 months)
    const maintenanceData = Array.from({ length: 6 }, (_, i) => ({
      month: new Date(
        Date.now() + i * 30 * 24 * 60 * 60 * 1000,
      ).toLocaleDateString("en-US", { month: "short" }),
      probability: Math.max(20, Math.min(95, 30 + i * 12 + Math.random() * 10)),
      devices: Math.floor(Math.random() * 5) + 1,
    }));
    setMaintenanceTimeline(maintenanceData);
  };

  const updateRealTimeData = () => {
    // Add new data point to anomaly history
    setAnomalyHistory((prev) => {
      const newData = [
        ...prev.slice(1),
        {
          date: new Date().toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
          }),
          anomalies: Math.floor(Math.random() * 10),
          severity: Math.random() * 100,
        },
      ];
      return newData;
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">ML Analytics</h2>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <TrendingUp className="w-5 h-5 text-blue-600" />
          <span>Real-time ML Insights</span>
        </div>
      </div>

      {/* Anomaly Detection Trend */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center mb-4">
          <AlertTriangle className="w-5 h-5 text-orange-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">
            Anomaly Detection Trend
          </h3>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={anomalyHistory}>
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
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Activity Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <Activity className="w-5 h-5 text-blue-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">
              Activity Distribution
            </h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={activityDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) =>
                  `${name} ${(percent * 100).toFixed(0)}%`
                }
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {activityDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 space-y-2">
            {activityDistribution.map((activity, index) => (
              <div
                key={index}
                className="flex items-center justify-between text-sm"
              >
                <div className="flex items-center">
                  <div
                    className="w-3 h-3 rounded-full mr-2"
                    style={{ backgroundColor: activity.color }}
                  ></div>
                  <span className="text-gray-700">{activity.name}</span>
                </div>
                <span className="font-semibold text-gray-900">
                  {activity.value}%
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Maintenance Predictions */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-4">
            <TrendingUp className="w-5 h-5 text-purple-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">
              Maintenance Predictions
            </h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={maintenanceTimeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar
                dataKey="probability"
                fill="#8B5CF6"
                name="Maintenance Probability (%)"
                radius={[8, 8, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-4 bg-purple-50 rounded-lg p-3">
            <p className="text-sm text-purple-800">
              <span className="font-semibold">Prediction:</span> Next
              maintenance likely needed in{" "}
              {maintenanceTimeline[0]?.month || "soon"}
            </p>
          </div>
        </div>
      </div>

      {/* ML Model Performance */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          ML Model Performance
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
            <p className="text-sm text-blue-600 font-medium mb-1">
              Anomaly Detection
            </p>
            <p className="text-3xl font-bold text-blue-900">89.3%</p>
            <p className="text-xs text-blue-600 mt-1">Accuracy</p>
          </div>
          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
            <p className="text-sm text-green-600 font-medium mb-1">
              Activity Recognition
            </p>
            <p className="text-3xl font-bold text-green-900">92.7%</p>
            <p className="text-xs text-green-600 mt-1">Accuracy</p>
          </div>
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
            <p className="text-sm text-purple-600 font-medium mb-1">
              Maintenance Prediction
            </p>
            <p className="text-3xl font-bold text-purple-900">88.0%</p>
            <p className="text-xs text-purple-600 mt-1">Accuracy</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MLStatistics;
