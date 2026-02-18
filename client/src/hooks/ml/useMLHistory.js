import { useState, useEffect, useCallback, useRef } from "react";
import { mlAPI } from "../../services/api";

// Cache outside component - shared across all hook instances
const cache = {
  data: null,
  timestamp: null,
  total: 0,
  statsByDays: {},
  statsTimestamp: null,
};

const CACHE_DURATION = 30000; // 30 seconds

export const useMLHistory = (options = {}) => {
  const {
    deviceId,
    limit = 50,
    offset = 0,
    type,
    source = "all", // ✅ NEW: 'predictions', 'detections', 'all'
    anomaliesOnly = false,
    startDate,
    endDate,
    autoFetch = true,
    cacheDuration = CACHE_DURATION,
  } = options;

  const [history, setHistory] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const isMounted = useRef(true);
  const [totalAnomalyCount, setTotalAnomalyCount] = useState(0);

  // Fetch history with caching
  const fetchHistory = useCallback(
    async (force = false) => {
      const now = Date.now();

      // Return cached data if fresh
      if (
        !force &&
        cache.data &&
        cache.timestamp &&
        now - cache.timestamp < cacheDuration
      ) {
        console.log("✅ Using cached ML history");
        setHistory(cache.data);
        setTotalCount(cache.total || cache.data.length);
        return cache.data;
      }

      setLoading(true);
      setError(null);

      try {
        const response = await mlAPI.getHistory({
          limit,
          offset,
          type,
          source, // ✅ NEW: Pass source parameter
          anomalies_only: anomaliesOnly,
          start_date: startDate,
          end_date: endDate,
        });

        const data = response.data.data || [];

        // Update cache
        cache.data = data;
        cache.total = response.data.total || data.length;
        cache.timestamp = now;

        if (isMounted.current) {
          setHistory(data);
          setTotalCount(response.data.total || data.length);
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
    [
      limit,
      offset,
      type,
      source,
      anomaliesOnly,
      startDate,
      endDate,
      cacheDuration,
    ],
  );

  // Fetch stats with caching
  const fetchStats = useCallback(
    async (days = 7, force = false) => {
      const now = Date.now();
      const cacheKey = String(days);

      // ✅ Now checks cache for the specific days value
      if (
        !force &&
        cache.statsByDays[cacheKey] &&
        cache.statsTimestamp[cacheKey] &&
        now - cache.statsTimestamp[cacheKey] < cacheDuration
      ) {
        setStats(cache.statsByDays[cacheKey]);
        return cache.statsByDays[cacheKey];
      }

      try {
        const response = await mlAPI.getStats(days);
        const statsData = response.data;

        cache.statsByDays[cacheKey] = statsData; // ✅ keyed by days
        cache.statsTimestamp[cacheKey] = now;

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

  const fetchTotalAnomalyCount = useCallback(async () => {
    try {
      const response = await mlAPI.getHistory({
        anomalies_only: true,
        limit: 1, // Minimal data transfer — we only need response.data.total
        offset: 0,
      });
      const count = response.data.total || 0;
      if (isMounted.current) setTotalAnomalyCount(count);
      return count;
    } catch (err) {
      console.error("Failed to fetch total anomaly count:", err);
      return 0;
    }
  }, []);

  // Auto-fetch on mount
  useEffect(() => {
    isMounted.current = true;
    if (autoFetch) {
      fetchHistory();
      fetchTotalAnomalyCount(); // ✅ independent, lightweight call
    }
    return () => {
      isMounted.current = false;
    };
  }, [autoFetch, fetchHistory, fetchTotalAnomalyCount]);

  // ✅ REMOVED: addToHistory - ML history is read-only analytics

  // Clear history and cache
  const clearHistory = useCallback(() => {
    setHistory([]);
    cache.total = 0;
    cache.data = null;
    cache.timestamp = null;
  }, []);

  // Get anomalies only
  const getAnomalies = useCallback(() => {
    return history.filter((item) => item.is_anomaly);
  }, [history]);

  // Filter by type
  const getByType = useCallback(
    (predictionType) => {
      return history.filter((item) => item.prediction_type === predictionType);
    },
    [history],
  );

  // Filter by source
  const getBySource = useCallback(
    (sourceType) => {
      return history.filter((item) => item.source === sourceType);
    },
    [history],
  );

  // Filter by date range
  const getByDateRange = useCallback(
    (start, end) => {
      return history.filter((item) => {
        const itemDate = new Date(item.timestamp);
        return itemDate >= start && itemDate <= end;
      });
    },
    [history],
  );

  // Refresh data (force fetch)
  const refresh = useCallback(async () => {
    return fetchHistory(true);
  }, [fetchHistory]);

  return {
    history,
    totalCount,
    stats,
    loading,
    error,
    fetchHistory,
    fetchStats,
    clearHistory,
    getAnomalies,
    getByType,
    getBySource,
    getByDateRange,
    refresh,
    totalAnomalyCount,
    fetchTotalAnomalyCount, // ✅ NEW: Expose total anomaly count
  };
};
