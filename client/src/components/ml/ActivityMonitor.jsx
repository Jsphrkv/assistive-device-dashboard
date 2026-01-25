import React, { useState, useEffect } from "react";
import { Activity, User, TrendingUp } from "lucide-react";
import { mlAPI } from "../../services/api";
import { useMLAnalytics } from "../../hooks/ml/useMLStatistics";

const ActivityMonitor = () => {
  const [activityData, setActivityData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    recognizeActivity();
    // Update every 5 seconds
    const interval = setInterval(recognizeActivity, 5000);
    return () => clearInterval(interval);
  }, []);

  const recognizeActivity = async () => {
    try {
      const sensorData = {
        acc_x: (Math.random() - 0.5) * 4,
        acc_y: (Math.random() - 0.5) * 4,
        acc_z: 9.8 + (Math.random() - 0.5) * 2,
        gyro_x: (Math.random() - 0.5) * 40,
        gyro_y: (Math.random() - 0.5) * 40,
        gyro_z: (Math.random() - 0.5) * 30,
      };

      const response = await mlAPI.recognizeActivity(sensorData);
      const data = response.data;

      setActivityData(data);
      setHistory((prev) => [
        { ...data, timestamp: new Date() },
        ...prev.slice(0, 9),
      ]);
      setLoading(false);
    } catch (error) {
      console.error("Activity recognition error:", error);
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

  if (!activityData) return null;

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

      {/* Recent History */}
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
    </div>
  );
};

export default ActivityMonitor;
