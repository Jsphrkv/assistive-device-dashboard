import React, { useState, useEffect } from "react";
import { AlertTriangle, TrendingUp } from "lucide-react";
import { mlAPI } from "../../services/api";

const DangerMonitor = ({ deviceId }) => {
  const [dangerData, setDangerData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDangerData();
    const interval = setInterval(fetchDangerData, 10000); // Refresh every 10s (danger needs frequent updates)
    return () => clearInterval(interval);
  }, [deviceId]);

  const fetchDangerData = async () => {
    try {
      setLoading(true);

      // Get latest danger predictions
      const response = await mlAPI.getHistory({
        type: "danger_prediction",
        limit: 1,
      });

      const predictions = response.data?.data || [];

      if (predictions.length > 0) {
        const latest = predictions[0];
        setDangerData({
          dangerScore: latest.result?.danger_score || 0,
          recommendedAction: latest.result?.recommended_action || "SAFE",
          timeToCollision: latest.result?.time_to_collision || 999,
          confidence: (latest.result?.confidence || 0) * 100,
          timestamp: latest.timestamp,
        });
      } else {
        setDangerData(null);
      }
    } catch (error) {
      console.error("Error fetching danger data:", error);
      setDangerData(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !dangerData) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
        </div>
      </div>
    );
  }

  // Danger level colors and labels
  const getDangerLevel = (score) => {
    if (score >= 80)
      return {
        level: "CRITICAL",
        color: "red",
        bgColor: "bg-red-100",
        textColor: "text-red-700",
        borderColor: "border-red-300",
      };
    if (score >= 60)
      return {
        level: "HIGH",
        color: "orange",
        bgColor: "bg-orange-100",
        textColor: "text-orange-700",
        borderColor: "border-orange-300",
      };
    if (score >= 30)
      return {
        level: "MEDIUM",
        color: "yellow",
        bgColor: "bg-yellow-100",
        textColor: "text-yellow-700",
        borderColor: "border-yellow-300",
      };
    return {
      level: "LOW",
      color: "green",
      bgColor: "bg-green-100",
      textColor: "text-green-700",
      borderColor: "border-green-300",
    };
  };

  const actionColors = {
    STOP: "bg-red-100 text-red-700 border-red-300",
    SLOW_DOWN: "bg-orange-100 text-orange-700 border-orange-300",
    CAUTION: "bg-yellow-100 text-yellow-700 border-yellow-300",
    SAFE: "bg-green-100 text-green-700 border-green-300",
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-600" />
          Danger Monitor
        </h3>
        <button
          onClick={fetchDangerData}
          disabled={loading}
          className="text-sm text-red-600 hover:text-red-700"
        >
          <TrendingUp className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {!dangerData ? (
        <div className="text-center py-8">
          <AlertTriangle className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-gray-500 text-sm">No danger predictions yet</p>
          <p className="text-gray-400 text-xs mt-1">
            Waiting for obstacle detections...
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Danger Score Display */}
          <div className="text-center">
            <div className="relative inline-flex items-center justify-center w-32 h-32">
              {/* Background circle */}
              <svg className="transform -rotate-90 w-32 h-32">
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="transparent"
                  className="text-gray-200"
                />
                {/* Progress circle */}
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="currentColor"
                  strokeWidth="8"
                  fill="transparent"
                  strokeDasharray={`${2 * Math.PI * 56}`}
                  strokeDashoffset={`${2 * Math.PI * 56 * (1 - dangerData.dangerScore / 100)}`}
                  className={`${
                    dangerData.dangerScore >= 80
                      ? "text-red-600"
                      : dangerData.dangerScore >= 60
                        ? "text-orange-600"
                        : dangerData.dangerScore >= 30
                          ? "text-yellow-600"
                          : "text-green-600"
                  }`}
                  strokeLinecap="round"
                />
              </svg>
              {/* Score text */}
              <div className="absolute">
                <div className="text-3xl font-bold text-gray-900">
                  {dangerData.dangerScore.toFixed(0)}
                </div>
                <div className="text-xs text-gray-500">Danger Score</div>
              </div>
            </div>
          </div>

          {/* Danger Level Badge */}
          <div className="text-center">
            <span
              className={`inline-block px-4 py-2 rounded-full text-sm font-bold border-2 ${getDangerLevel(dangerData.dangerScore).bgColor} ${getDangerLevel(dangerData.dangerScore).textColor} ${getDangerLevel(dangerData.dangerScore).borderColor}`}
            >
              {getDangerLevel(dangerData.dangerScore).level} DANGER
            </span>
          </div>

          {/* Recommended Action */}
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-xs text-gray-600 mb-2">Recommended Action</p>
            <div
              className={`px-4 py-3 rounded-lg border-2 text-center font-bold ${actionColors[dangerData.recommendedAction]}`}
            >
              {dangerData.recommendedAction.replace("_", " ")}
            </div>
          </div>

          {/* Time to Collision */}
          {dangerData.timeToCollision < 10 && (
            <div className="bg-red-50 rounded-lg p-4 border-2 border-red-300">
              <p className="text-xs text-red-600 mb-1">Time to Collision</p>
              <p className="text-2xl font-bold text-red-700">
                {dangerData.timeToCollision.toFixed(1)}s
              </p>
            </div>
          )}

          {/* Confidence */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <p className="text-xs text-gray-600">Prediction Confidence</p>
              <p className="text-xs text-gray-600">
                {dangerData.confidence.toFixed(0)}%
              </p>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${dangerData.confidence}%` }}
              ></div>
            </div>
          </div>

          {/* Last Updated */}
          <div className="pt-2 border-t text-xs text-gray-500 text-center">
            Updated {new Date(dangerData.timestamp).toLocaleTimeString()}
          </div>
        </div>
      )}
    </div>
  );
};

export default DangerMonitor;
