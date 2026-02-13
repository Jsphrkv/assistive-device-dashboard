import React, { useEffect } from "react";
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
import { TrendingUp } from "lucide-react";

const AlertsChart = ({ data, loading }) => {
  // ✅ Debug logging
  useEffect(() => {
    console.log("📊 AlertsChart received data:", data);
    console.log("📊 AlertsChart data length:", data?.length);
    console.log("📊 AlertsChart first item:", data?.[0]);
  }, [data]);

  const hasData = data && data.length > 0;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Alerts Per Day
      </h3>

      {loading ? (
        <div className="h-64 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : !hasData ? (
        <div className="h-64 flex items-center justify-center text-gray-400">
          <div className="text-center">
            <TrendingUp className="w-12 h-12 mx-auto mb-2 text-gray-300" />
            <p className="text-sm">No data available</p>
            <p className="text-xs mt-1">
              Alerts will appear as they are detected
            </p>
          </div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="alerts"
              stroke="#3B82F6"
              strokeWidth={2}
              name="Total Alerts"
              dot={{ fill: "#3B82F6", r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default AlertsChart;
