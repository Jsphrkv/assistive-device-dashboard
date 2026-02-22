import React, { useEffect } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Package } from "lucide-react";

const COLORS = [
  "#3B82F6",
  "#10B981",
  "#F59E0B",
  "#EF4444",
  "#8B5CF6",
  "#EC4899",
  "#14B8A6",
  "#F97316",
  "#6B7280",
  "#A855F7",
  "#06B6D4",
  "#84CC16",
  "#D946EF",
  "#F43F5E",
  "#64748B",
  "#7C3AED",
];

const ObstaclesChart = ({ data, loading }) => {
  useEffect(() => {
    console.log("📊 ObstaclesChart received data:", data);
    console.log("📊 ObstaclesChart data length:", data?.length);
    console.log("📊 ObstaclesChart first item:", data?.[0]);
  }, [data]);

  const hasData = data && data.length > 0;

  // ✅ FIXED: Safe string handling with null guards
  const formattedData = hasData
    ? data.map((item) => {
        // Guard against null/undefined name
        const safeName = item.name || item.obstacle_type || "unknown";

        // Convert to string and safely split
        const cleanName = String(safeName)
          .split(">")[0] // Remove anything after >
          .split("%")[0] // Remove anything after %
          .trim(); // Remove whitespace

        return {
          ...item,
          name: cleanName || "unknown", // Final fallback
        };
      })
    : [];

  // Custom label renderer to show only percentage
  const renderCustomLabel = (entry) => {
    const total = formattedData.reduce((sum, item) => sum + item.value, 0);
    const percentage = Math.round((entry.value / total) * 100);
    return percentage > 5 ? `${percentage}%` : "";
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Most Common Obstacles
      </h3>

      {loading ? (
        <div className="h-64 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : !hasData ? (
        <div className="h-64 flex items-center justify-center text-gray-400">
          <div className="text-center">
            <Package className="w-12 h-12 mx-auto mb-2 text-gray-300" />
            <p className="text-sm">No obstacle data</p>
            <p className="text-xs mt-1">
              Obstacles will appear as they are detected
            </p>
          </div>
        </div>
      ) : (
        <div className="flex flex-col md:flex-row justify-center items-center gap-8 md:gap-4">
          {/* Legend on the left */}
          <div className="w-full md:w-1/3 md:max-w-[200px]">
            <div className="space-y-1.5 max-h-[300px] overflow-y-auto pr-2">
              {formattedData.map((item, index) => {
                const total = formattedData.reduce(
                  (sum, i) => sum + i.value,
                  0,
                );
                const percentage = Math.round((item.value / total) * 100);
                return (
                  <div
                    key={`legend-${index}`}
                    className="flex items-center gap-2 text-sm"
                  >
                    <span
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <span className="text-gray-700 truncate flex-1">
                      {item.name}
                    </span>
                    <span className="text-gray-500 text-xs whitespace-nowrap">
                      {item.value} ({percentage}%)
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Chart on the right */}
          <div className="w-full md:w-2/3 h-[300px] flex justify-center">
            <div className="w-full max-w-[300px] md:max-w-none">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={formattedData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={renderCustomLabel}
                    labelLine={false}
                  >
                    {formattedData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value, name) => {
                      const total = formattedData.reduce(
                        (sum, item) => sum + item.value,
                        0,
                      );
                      const percentage = Math.round((value / total) * 100);
                      return [`${value} (${percentage}%)`, name];
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ObstaclesChart;
