import React, { useState, useEffect } from "react";
import AlertsChart from "./AlertsChart";
import ObstaclesChart from "./ObstaclesChart";
import PeakTimesChart from "./PeakTimesChart";
import { statisticsAPI } from "../../services/api";
import MLStatistics from "../ml/MLStatistics";
import { BarChart3 } from "lucide-react";

const StatisticsTab = ({ deviceId }) => {
  const [dailyStats, setDailyStats] = useState([]);
  const [obstacleStats, setObstacleStats] = useState([]);
  const [hourlyStats, setHourlyStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hasData, setHasData] = useState(false);

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    setLoading(true);

    try {
      const [daily, obstacles, hourly] = await Promise.all([
        statisticsAPI.getDaily(7),
        statisticsAPI.getObstacles(),
        statisticsAPI.getHourly(),
      ]);

      const hasAnyData =
        (daily.data?.data && daily.data.data.length > 0) ||
        (obstacles.data?.data && obstacles.data.data.length > 0) ||
        (hourly.data?.data && hourly.data.data.length > 0);

      setDailyStats(daily.data?.data || []);
      setObstacleStats(obstacles.data?.data || []);
      setHourlyStats(hourly.data?.data || []);
      setHasData(hasAnyData);
    } catch (error) {
      console.error("Error fetching statistics:", error);
      setHasData(false);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="space-y-6 fade-in">
        <h2 className="text-2xl font-bold text-gray-900">
          Alert History & Statistics
        </h2>

        {!hasData && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <div className="flex items-start gap-3">
              <BarChart3 className="w-6 h-6 text-yellow-600 mt-1" />
              <div>
                <h3 className="text-lg font-semibold text-yellow-900 mb-2">
                  No Statistics Available
                </h3>
                <p className="text-yellow-800">
                  Statistics will appear here once your device starts sending
                  detection data.
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AlertsChart data={dailyStats} />
          <ObstaclesChart data={obstacleStats} />
        </div>

        <div className="grid grid-cols-1 gap-6">
          <PeakTimesChart data={hourlyStats} />
        </div>
      </div>

      <div className="mt-8">
        <MLStatistics deviceId={deviceId} />
      </div>
    </div>
  );
};

export default StatisticsTab;
