import { useState } from "react";

export const useMLHistory = (deviceId, limit = 50) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // API fetch commented out - using local state only for now
  // Uncomment when backend endpoints are ready

  const addToHistory = (prediction) => {
    setHistory((prev) => [prediction, ...prev].slice(0, limit));
  };

  const clearHistory = () => {
    setHistory([]);
  };

  const getAnomalies = () => {
    return history.filter((item) => item.is_anomaly);
  };

  const getByDateRange = (startDate, endDate) => {
    return history.filter((item) => {
      const itemDate = new Date(item.timestamp);
      return itemDate >= startDate && itemDate <= endDate;
    });
  };

  return {
    history,
    loading,
    error,
    addToHistory,
    clearHistory,
    getAnomalies,
    getByDateRange,
    refresh: () => {}, // Empty function for now
  };
};
