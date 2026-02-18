import { useState, useEffect, useCallback, useRef } from "react";
import { mlAPI } from "../../services/api";

// ✅ FIX: Cache keyed by days so fetchStats(7) and fetchStats(90) never share a slot
const cache = {
  data: null,
  timestamp: null,
  total: 0,
  statsByDays: {}, // { "7": {...}, "30": {...}, "90": {...} }
  statsTimestamp: {}, // { "7": 1234567890, ... }
};

const CACHE_DURATION = 30000; // 30 seconds

export const useMLHistory = (options = {}) => {
  const {
    deviceId,
    limit = 50,
    offset = 0,
    type,
    source = "all",
    anomaliesOnly = false,
    startDate,
    endDate,
    autoFetch = true,
    cacheDuration = CACHE_DURATION,
  } = options;

  const [history, setHistory] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [stats, setStats] = useState(null);
  const [totalAnomalyCount, setTotalAnomalyCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const isMounted = useRef(true);

  // Fetch history with caching
  const fetchHistory = useCallback(
    async (force = false) => {
      const now = Date.now();

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
          source,
          anomalies_only: anomaliesOnly,
          start_date: startDate,
          end_date: endDate,
        });

        const data = response.data.data || [];

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

  // ✅ FIX: fetchStats now keys cache by days value
  //    Previously all days shared one cache slot, so fetchStats(90) would
  //    return the same cached result as fetchStats(7).
  const fetchStats = useCallback(
    async (days = 7, force = false) => {
      const now = Date.now();
      const cacheKey = String(days);

      if (
        !force &&
        cache.statsByDays[cacheKey] &&
        cache.statsTimestamp[cacheKey] &&
        now - cache.statsTimestamp[cacheKey] < cacheDuration
      ) {
        console.log(`✅ Using cached ML stats (${days} days)`);
        const cached = cache.statsByDays[cacheKey];
        if (isMounted.current) {
          setStats(cached);
          setTotalAnomalyCount(cached.anomalyCount || 0);
        }
        return cached;
      }

      try {
        const response = await mlAPI.getStats(days);
        const statsData = response.data;

        cache.statsByDays[cacheKey] = statsData;
        cache.statsTimestamp[cacheKey] = now;

        if (isMounted.current) {
          setStats(statsData);
          setTotalAnomalyCount(statsData.anomalyCount || 0);
        }

        return statsData;
      } catch (err) {
        console.error("Failed to fetch ML stats:", err);
        throw err;
      }
    },
    [cacheDuration],
  );

  // ✅ Lightweight fetch just for total anomaly count (all-time, unfiltered)
  const fetchTotalAnomalyCount = useCallback(async () => {
    try {
      const response = await mlAPI.getHistory({
        anomalies_only: true,
        limit: 1,
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
      fetchTotalAnomalyCount();
    }

    return () => {
      isMounted.current = false;
    };
  }, [autoFetch, fetchHistory, fetchTotalAnomalyCount]);

  const clearHistory = useCallback(() => {
    setHistory([]);
    cache.total = 0;
    cache.data = null;
    cache.timestamp = null;
  }, []);

  const getAnomalies = useCallback(() => {
    return history.filter((item) => item.is_anomaly);
  }, [history]);

  const getByType = useCallback(
    (predictionType) => {
      return history.filter((item) => item.prediction_type === predictionType);
    },
    [history],
  );

  const getBySource = useCallback(
    (sourceType) => {
      return history.filter((item) => item.source === sourceType);
    },
    [history],
  );

  const getByDateRange = useCallback(
    (start, end) => {
      return history.filter((item) => {
        const itemDate = new Date(item.timestamp);
        return itemDate >= start && itemDate <= end;
      });
    },
    [history],
  );

  const refresh = useCallback(async () => {
    return fetchHistory(true);
  }, [fetchHistory]);

  return {
    history,
    totalCount,
    stats,
    totalAnomalyCount,
    loading,
    error,
    fetchHistory,
    fetchStats,
    fetchTotalAnomalyCount,
    clearHistory,
    getAnomalies,
    getByType,
    getBySource,
    getByDateRange,
    refresh,
  };
};
