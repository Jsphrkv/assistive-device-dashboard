import React, { useState, useEffect } from "react";
import { Activity, TrendingUp } from "lucide-react";
import { mlAPI } from "../../services/api";

const ActivityMonitor = ({ deviceId }) => {
  const [activityData, setActivityData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetchActivityData();

    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchActivityData();
    }, 30000);

    return () => clearInterval(interval);
  }, [deviceId]);

  // Update history when new activity data arrives
  useEffect(() => {
    if (activityData && activityData.activity) {
      setHistory((prev) => [
        { ...activityData, timestamp: new Date() },
        ...prev.slice(0, 9), // Keep last 10 items
      ]);
    }
  }, [activityData]);

  const fetchActivityData = async () => {
    try {
      // Assuming you have an endpoint to get activity predictions
      const response = await mlAPI.predictActivity(deviceId);
      setActivityData(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching activity data:", error);
      setActivityData(null);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="h-20 bg-gray-200 rounded"></div>
      </div>
    );
  }

  // Show empty state if no data
  if (!activityData) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center mb-4">
          <Activity className="w-6 h-6 text-gray-400 mr-2" />
          <h3 className="text-lg font-semibold text-gray-600">
            Activity Monitor
          </h3>
        </div>

        <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 p-6">
          <div className="text-center">
            <Activity className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-sm text-gray-500">
              No activity data available yet. Connect your device to start
              monitoring.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const getActivityEmoji = (activity) => {
    switch (activity) {
      case "resting":
        return "😴";
      case "walking":
        return "🚶";
      case "using_device":
        return "📱";
      default:
        return "❓";
    }
  };

  const getIntensityColor = (intensity) => {
    switch (intensity) {
      case "high":
        return "bg-red-100 text-red-800";
      case "moderate":
        return "bg-yellow-100 text-yellow-800";
      default:
        return "bg-green-100 text-green-800";
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center mb-4">
        <Activity className="w-6 h-6 text-blue-600 mr-2" />
        <h3 className="text-lg font-semibold text-gray-900">
          Activity Monitor
        </h3>
      </div>

      {/* Current Activity */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 mb-4">
        <div className="text-center">
          <div className="text-5xl mb-2">
            {getActivityEmoji(activityData.activity)}
          </div>
          <h4 className="text-2xl font-bold text-gray-900 mb-1 capitalize">
            {activityData.activity.replace("_", " ")}
          </h4>
          <p className="text-sm text-gray-600 mb-3">
            {activityData.description}
          </p>

          <div className="flex items-center justify-center space-x-4">
            <div
              className={`px-3 py-1 rounded-full text-xs font-semibold ${getIntensityColor(activityData.intensity)}`}
            >
              {activityData.intensity.toUpperCase()} Intensity
            </div>
            <div className="text-sm text-gray-600">
              {(activityData.confidence * 100).toFixed(0)}% confident
            </div>
          </div>
        </div>
      </div>

      {/* Activity Probabilities */}
      {activityData.all_probabilities && (
        <div className="mb-4">
          <h5 className="text-sm font-semibold text-gray-700 mb-2">
            Detection Confidence:
          </h5>
          <div className="space-y-2">
            {Object.entries(activityData.all_probabilities).map(
              ([activity, prob]) => (
                <div key={activity} className="flex items-center">
                  <span className="text-xs w-24 capitalize">
                    {activity.replace("_", " ")}
                  </span>
                  <div className="flex-1 bg-gray-200 rounded-full h-2 mx-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${prob * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-xs w-12 text-right">
                    {(prob * 100).toFixed(0)}%
                  </span>
                </div>
              ),
            )}
          </div>
        </div>
      )}

      {/* Recent History */}
      {history.length > 0 && (
        <div>
          <h5 className="text-sm font-semibold text-gray-700 mb-2">
            Recent Activity:
          </h5>
          <div className="space-y-1">
            {history.slice(0, 5).map((item, index) => (
              <div
                key={index}
                className="flex items-center justify-between text-xs text-gray-600"
              >
                <span className="capitalize">
                  {getActivityEmoji(item.activity)}{" "}
                  {item.activity.replace("_", " ")}
                </span>
                <span>{new Date(item.timestamp).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ActivityMonitor;
