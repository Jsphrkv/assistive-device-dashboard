import { useState, useEffect, useCallback, useRef } from "react";
import { detectionsAPI } from "../services/api";

// Cache outside component - shared across all hook instances
const cache = {
  data: null,
  timestamp: null,
};

const CACHE_DURATION = 30000; // 30 seconds

export const useDetectionLogs = (options = {}) => {
  const {
    limit = 100,
    autoFetch = true,
    cacheDuration = CACHE_DURATION,
  } = options;

  const [detections, setDetections] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const isMounted = useRef(true);

  // Fetch detections with caching
  const fetchDetections = useCallback(
    async (force = false) => {
      const now = Date.now();

      // Return cached data if fresh
      if (
        !force &&
        cache.data &&
        cache.timestamp &&
        now - cache.timestamp < cacheDuration
      ) {
        console.log("✅ Using cached detection logs");
        setDetections(cache.data);
        return cache.data;
      }

      setLoading(true);
      setError(null);

      try {
        // Fetch from detections API (includes ML data!)
        const response = await detectionsAPI.getRecent(limit);

        // Backend returns: { detections: [...] }
        const data = response.data.detections || [];

        // Update cache
        cache.data = data;
        cache.timestamp = now;

        if (isMounted.current) {
          setDetections(data);
        }

        return data;
      } catch (err) {
        console.error("Failed to fetch detection logs:", err);
        const errorMsg =
          err.response?.data?.error || "Failed to load detection logs";

        if (isMounted.current) {
          setError(errorMsg);
          setDetections([]);
        }

        throw err;
      } finally {
        if (isMounted.current) {
          setLoading(false);
        }
      }
    },
    [limit, cacheDuration],
  );

  // Auto-fetch on mount
  useEffect(() => {
    isMounted.current = true;

    if (autoFetch) {
      fetchDetections();
    }

    return () => {
      isMounted.current = false;
    };
  }, [autoFetch, fetchDetections]);

  // Add new detection (for real-time updates)
  const addDetection = useCallback((detection) => {
    setDetections((prev) => [detection, ...prev]);

    // Invalidate cache since we have new data
    cache.data = null;
    cache.timestamp = null;
  }, []);

  // Clear detections and cache
  const clearDetections = useCallback(() => {
    setDetections([]);
    cache.data = null;
    cache.timestamp = null;
  }, []);

  // Refresh data (force fetch)
  const refresh = useCallback(async () => {
    return fetchDetections(true);
  }, [fetchDetections]);

  // Get ML-detected items only
  const getMLDetections = useCallback(() => {
    return detections.filter((d) => d.detection_source === "camera");
  }, [detections]);

  // Get high-confidence detections
  const getHighConfidenceDetections = useCallback(
    (threshold = 80) => {
      return detections.filter(
        (d) => d.detection_confidence && d.detection_confidence >= threshold,
      );
    },
    [detections],
  );

  // Get detections by object type
  const getDetectionsByObject = useCallback(
    (objectType) => {
      return detections.filter((d) => d.object_detected === objectType);
    },
    [detections],
  );

  // Calculate ML statistics
  const getMLStats = useCallback(() => {
    const mlDetections = detections.filter(
      (d) => d.detection_source === "camera",
    );
    const avgConfidence =
      mlDetections.length > 0
        ? mlDetections.reduce(
            (sum, d) => sum + (d.detection_confidence || 0),
            0,
          ) / mlDetections.length
        : 0;

    return {
      total: mlDetections.length,
      avgConfidence: avgConfidence.toFixed(1),
      highConfidence: mlDetections.filter((d) => d.detection_confidence >= 80)
        .length,
      uniqueObjects: [
        ...new Set(mlDetections.map((d) => d.object_detected)),
      ].filter(Boolean).length,
    };
  }, [detections]);

  return {
    detections,
    loading,
    error,
    fetchDetections,
    addDetection,
    clearDetections,
    refresh,
    // ML-specific helpers
    getMLDetections,
    getHighConfidenceDetections,
    getDetectionsByObject,
    getMLStats,
  };
};
