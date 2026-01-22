import React, { useState, useEffect } from "react";
import AlertsChart from "./AlertsChart";
import ObstaclesChart from "./ObstaclesChart";
import PeakTimesChart from "./PeakTimesChart";
import { statisticsAPI } from "../../services/api";

const StatisticsTab = () => {
  const [dailyStats, setDailyStats] = useState([]);
  const [obstacleStats, setObstacleStats] = useState([]);
  const [hourlyStats, setHourlyStats] = useState([]);
  const [loading, setLoading] = useState(true);

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

      if (daily.data) setDailyStats(daily.data.data);
      if (obstacles.data) setObstacleStats(obstacles.data.data);
      if (hourly.data) setHourlyStats(hourly.data.data);
    } catch (error) {
      console.error("Error fetching statistics:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in">
      <h2 className="text-2xl font-bold text-gray-900">
        Alert History & Statistics
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AlertsChart data={dailyStats} />
        <ObstaclesChart data={obstacleStats} />
      </div>

      <div className="grid grid-cols-1 gap-6">
        <PeakTimesChart data={hourlyStats} />
      </div>
    </div>
  );
};

export default StatisticsTab;
