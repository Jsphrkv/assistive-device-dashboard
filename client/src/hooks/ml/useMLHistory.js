import { useState, useEffect, useCallback, useRef } from "react";
import { mlAPI } from "../services/api";

// ✅ Cache outside component - shared across all hook instances
const cache = {
  data: null,
  timestamp: null,
  stats: null,
  statsTimestamp: null,
};

const CACHE_DURATION = 30000; // 30 seconds

export const useMLHistory = (options = {}) => {
  const {
    deviceId,
    limit = 50,
    offset = 0,
    type,
    anomaliesOnly = false,
    startDate,
    endDate,
    autoFetch = true,
    cacheDuration = CACHE_DURATION,
  } = options;

  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const isMounted = useRef(true);

  // ✅ Fetch history with caching
  const fetchHistory = useCallback(
    async (force = false) => {
      const now = Date.now();

      // ✅ Return cached data if fresh
      if (
        !force &&
        cache.data &&
        cache.timestamp &&
        now - cache.timestamp < cacheDuration
      ) {
        console.log("✅ Using cached ML history");
        setHistory(cache.data);
        return cache.data;
      }

      setLoading(true);
      setError(null);

      try {
        const response = await mlAPI.getHistory({
          limit,
          offset,
          type,
          anomalies_only: anomaliesOnly,
          start_date: startDate,
          end_date: endDate,
        });

        const data = response.data.data || [];

        // ✅ Update cache
        cache.data = data;
        cache.timestamp = now;

        if (isMounted.current) {
          setHistory(data);
        }

        return data;
      } catch (err) {
        console.error("Failed to fetch ML history:", err);
        const errorMsg =
          err.response?.data?.error || "Failed to load ML history";

        if (isMounted.current) {
          setError(errorMsg);
          setHistory([]);
        }

        throw err;
      } finally {
        if (isMounted.current) {
          setLoading(false);
        }
      }
    },
    [limit, offset, type, anomaliesOnly, startDate, endDate, cacheDuration],
  );

  // ✅ Fetch stats with caching
  const fetchStats = useCallback(
    async (days = 7, force = false) => {
      const now = Date.now();

      // ✅ Return cached stats if fresh
      if (
        !force &&
        cache.stats &&
        cache.statsTimestamp &&
        now - cache.statsTimestamp < cacheDuration
      ) {
        console.log("✅ Using cached ML stats");
        setStats(cache.stats);
        return cache.stats;
      }

      try {
        const response = await mlAPI.getStats(days);
        const statsData = response.data;

        // ✅ Update cache
        cache.stats = statsData;
        cache.statsTimestamp = now;

        if (isMounted.current) {
          setStats(statsData);
        }

        return statsData;
      } catch (err) {
        console.error("Failed to fetch ML stats:", err);
        throw err;
      }
    },
    [cacheDuration],
  );

  // ✅ Auto-fetch on mount
  useEffect(() => {
    isMounted.current = true;

    if (autoFetch) {
      fetchHistory();
    }

    return () => {
      isMounted.current = false;
    };
  }, [autoFetch, fetchHistory]);

  // ✅ Add to history (for real-time updates)
  const addToHistory = useCallback(
    async (prediction) => {
      // Update local state
      setHistory((prev) => [...prev, prediction]);

      // ✅ Save to Supabase
      if (deviceId) {
        await api.post("/logs/detections", {
          device_id: deviceId,
          ...prediction,
        });
      }
    },
    [deviceId],
  );

  // ✅ Clear history and cache
  const clearHistory = useCallback(() => {
    setHistory([]);
    cache.data = null;
    cache.timestamp = null;
  }, []);

  // ✅ Get anomalies only
  const getAnomalies = useCallback(() => {
    return history.filter((item) => item.is_anomaly);
  }, [history]);

  // ✅ Filter by date range
  const getByDateRange = useCallback(
    (start, end) => {
      return history.filter((item) => {
        const itemDate = new Date(item.timestamp);
        return itemDate >= start && itemDate <= end;
      });
    },
    [history],
  );

  // ✅ Refresh data (force fetch)
  const refresh = useCallback(async () => {
    return fetchHistory(true);
  }, [fetchHistory]);

  return {
    history,
    stats,
    loading,
    error,
    fetchHistory,
    fetchStats,
    addToHistory,
    clearHistory,
    getAnomalies,
    getByDateRange,
    refresh,
  };
};
