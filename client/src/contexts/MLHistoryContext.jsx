import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import api from "../services/api";

const MLHistoryContext = createContext(null);

export const MLHistoryProvider = ({ children }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [deviceId, setDeviceId] = useState(null);

  // Fetch user's device on mount
  useEffect(() => {
    fetchUserDevice();
  }, []);

  const fetchUserDevice = async () => {
    try {
      const response = await api.get("/devices/");
      if (response.data?.data && response.data.data.length > 0) {
        setDeviceId(response.data.data[0].id);
      }
    } catch (err) {
      console.error("Error fetching user device:", err);
    }
  };

  // Fetch detection logs from backend
  const fetchHistory = useCallback(async () => {
    if (!deviceId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.get("/logs/detections", {
        params: {
          device_id: deviceId,
          limit: 500,
        },
      });

      if (response.data?.data) {
        setHistory(response.data.data);
      }
    } catch (err) {
      console.error("Error fetching ML history:", err);
      setError(err.response?.data?.error || "Failed to fetch history");
    } finally {
      setLoading(false);
    }
  }, [deviceId]);

  // Auto-fetch when deviceId is set
  useEffect(() => {
    if (deviceId) {
      fetchHistory();
    }
  }, [deviceId, fetchHistory]);

  // Add new detection to history
  const addToHistory = useCallback((detection) => {
    setHistory((prev) => [detection, ...prev].slice(0, 500));
  }, []);

  // Clear all history
  const clearHistory = useCallback(() => {
    setHistory([]);
  }, []);

  // Get filtered data
  const getAnomalies = useCallback(() => {
    return history.filter((item) => item.is_anomaly);
  }, [history]);

  const getByType = useCallback(
    (type) => {
      return history.filter((item) => item.log_type === type);
    },
    [history],
  );

  const getByDateRange = useCallback(
    (startDate, endDate) => {
      return history.filter((item) => {
        const itemDate = new Date(item.timestamp);
        return itemDate >= startDate && itemDate <= endDate;
      });
    },
    [history],
  );

  const value = {
    history,
    loading,
    error,
    deviceId,
    fetchHistory,
    addToHistory,
    clearHistory,
    getAnomalies,
    getByType,
    getByDateRange,
    refresh: fetchHistory,
  };

  return (
    <MLHistoryContext.Provider value={value}>
      {children}
    </MLHistoryContext.Provider>
  );
};

// Custom hook to use the context
export const useMLHistory = () => {
  const context = useContext(MLHistoryContext);
  if (!context) {
    throw new Error("useMLHistory must be used within MLHistoryProvider");
  }
  return context;
};

export default MLHistoryContext;
