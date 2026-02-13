import React, { useState, useEffect } from "react";
import { Activity, TrendingUp } from "lucide-react";
import { mlAPI } from "../../services/api";

const ActivityMonitor = ({ deviceId }) => {
  const [activityData, setActivityData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchActivityData();
    const interval = setInterval(fetchActivityData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [deviceId]);

  const fetchActivityData = async () => {
    try {
      setLoading(true);

      // ✅ Use getHistory with activity filter
      const response = await mlAPI.getHistory({
        type: "activity",
        limit: 1,
      });

      const activities = response.data?.data || [];

      if (activities.length > 0) {
        const latest = activities[0];
        setActivityData({
          activity: latest.result?.activity || "Unknown",
          confidence: (latest.confidence_score || 0) * 100,
          intensity: latest.result?.intensity || "low",
          timestamp: latest.timestamp,
        });
      } else {
        setActivityData(null);
      }
    } catch (error) {
      console.error("Error fetching activity data:", error);
      setActivityData(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !activityData) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-600" />
          Activity Monitor
        </h3>
        <button
          onClick={fetchActivityData}
          disabled={loading}
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          <TrendingUp className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {!activityData ? (
        <div className="text-center py-8">
          <Activity className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-gray-500 text-sm">
            No activity data collected yet
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <p className="text-sm text-gray-600 mb-1">Current Activity</p>
            <p className="text-2xl font-bold text-blue-600 capitalize">
              {activityData.activity}
            </p>
          </div>

          <div>
            <p className="text-sm text-gray-600 mb-2">Confidence</p>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${activityData.confidence}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              {activityData.confidence.toFixed(1)}%
            </p>
          </div>

          <div className="flex items-center justify-between pt-2 border-t">
            <span className="text-sm text-gray-600">Intensity</span>
            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold ${
                activityData.intensity === "high"
                  ? "bg-red-100 text-red-700"
                  : activityData.intensity === "medium"
                    ? "bg-yellow-100 text-yellow-700"
                    : "bg-green-100 text-green-700"
              }`}
            >
              {activityData.intensity}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ActivityMonitor;
