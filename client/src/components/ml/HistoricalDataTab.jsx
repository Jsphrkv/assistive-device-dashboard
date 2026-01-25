import React, { useState, useEffect } from "react";
import { Calendar, Download, TrendingUp, BarChart3 } from "lucide-react";
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

const HistoricalDataTab = ({ deviceId }) => {
  const [historicalData, setHistoricalData] = useState([]);
  const [dateRange, setDateRange] = useState("7days");
  const [loading, setLoading] = useState(true);

  const { history } = useMLHistory(deviceId || "default", 200);

  useEffect(() => {
    loadHistoricalData();
  }, [dateRange, history]);

  const loadHistoricalData = () => {
    setLoading(true);
    // Generate mock historical data
    const days = dateRange === "7days" ? 7 : dateRange === "30days" ? 30 : 90;

    const data = Array.from({ length: days }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (days - i - 1));

      return {
        date: date.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
        }),
        anomalies: Math.floor(Math.random() * 15),
        maintenance_alerts: Math.floor(Math.random() * 5),
        activity_changes: Math.floor(Math.random() * 20) + 10,
        avg_confidence: 75 + Math.random() * 20,
      };
    });

    setHistoricalData(data);
    setLoading(false);
  };

  const exportData = () => {
    if (historicalData.length === 0) return;

    const csv = [
      [
        "Date",
        "Anomalies",
        "Maintenance Alerts",
        "Activity Changes",
        "Avg Confidence",
      ],
      ...historicalData.map((row) => [
        row.date,
        row.anomalies,
        row.maintenance_alerts,
        row.activity_changes,
        row.avg_confidence.toFixed(2),
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
  };

  const totalAnomalies = historicalData.reduce(
    (sum, d) => sum + d.anomalies,
    0,
  );
  const totalMaintenance = historicalData.reduce(
    (sum, d) => sum + d.maintenance_alerts,
    0,
  );
  const totalActivity = historicalData.reduce(
    (sum, d) => sum + d.activity_changes,
    0,
  );
  const avgConfidence =
    historicalData.length > 0
      ? historicalData.reduce((sum, d) => sum + d.avg_confidence, 0) /
        historicalData.length
      : 0;

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            Historical ML Data
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Track ML predictions over time
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* Date Range Filter */}
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

          {/* Export Button */}
          <button
            onClick={exportData}
            disabled={historicalData.length === 0}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="w-4 h-4" />
            <span className="text-sm">Export</span>
          </button>
        </div>
      </div>

      {/* ML Predictions Over Time */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          ML Predictions Timeline
        </h3>
        {historicalData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={historicalData}>
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
              />
              <Line
                type="monotone"
                dataKey="maintenance_alerts"
                stroke="#F59E0B"
                strokeWidth={2}
                name="Maintenance Alerts"
              />
              <Line
                type="monotone"
                dataKey="activity_changes"
                stroke="#3B82F6"
                strokeWidth={2}
                name="Activity Changes"
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-96 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <BarChart3 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p>No historical data available</p>
              <p className="text-sm mt-2">
                Data will appear as predictions are made
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-600 mb-1">Total Anomalies</p>
          <p className="text-2xl font-bold text-red-600">{totalAnomalies}</p>
          <p className="text-xs text-gray-500 mt-1">
            {dateRange === "7days"
              ? "Last 7 days"
              : dateRange === "30days"
                ? "Last 30 days"
                : "Last 90 days"}
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-600 mb-1">Maintenance Alerts</p>
          <p className="text-2xl font-bold text-orange-600">
            {totalMaintenance}
          </p>
          <p className="text-xs text-gray-500 mt-1">Total predictions</p>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-600 mb-1">Activity Changes</p>
          <p className="text-2xl font-bold text-blue-600">{totalActivity}</p>
          <p className="text-xs text-gray-500 mt-1">State transitions</p>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-600 mb-1">Avg Confidence</p>
          <p className="text-2xl font-bold text-green-600">
            {avgConfidence.toFixed(1)}%
          </p>
          <p className="text-xs text-gray-500 mt-1">Model accuracy</p>
        </div>
      </div>

      {/* Data Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Detailed Records
          </h3>
        </div>
        <div className="overflow-x-auto">
          {historicalData.length > 0 ? (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Anomalies
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Maintenance
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Activity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Confidence
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {historicalData.slice(0, 10).map((row, index) => (
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
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-800">
                        {row.maintenance_alerts}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                        {row.activity_changes}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {row.avg_confidence.toFixed(1)}%
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
    </div>
  );
};

export default HistoricalDataTab;
