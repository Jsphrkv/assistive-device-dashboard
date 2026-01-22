import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const PeakTimesChart = ({ data }) => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Peak Detection Times
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="hour_range" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="detection_count" fill="#10b981" name="Detections" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PeakTimesChart;
