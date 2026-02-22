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
    limit = 10000,
    autoFetch = true,
    cacheDuration = CACHE_DURATION,
  } = options;

  const [detections, setDetections] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const isMounted = useRef(true);

  const fetchDetections = useCallback(
    async (force = false) => {
      const now = Date.now();

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
        const response = await detectionsAPI.getRecent(limit);
        const data = response.data.detections || [];

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

  useEffect(() => {
    isMounted.current = true;

    if (autoFetch) {
      fetchDetections();
    }

    return () => {
      isMounted.current = false;
    };
  }, [autoFetch, fetchDetections]);

  const addDetection = useCallback((detection) => {
    setDetections((prev) => [detection, ...prev]);
    cache.data = null;
    cache.timestamp = null;
  }, []);

  const clearDetections = useCallback(() => {
    setDetections([]);
    cache.data = null;
    cache.timestamp = null;
  }, []);

  const refresh = useCallback(async () => {
    return fetchDetections(true);
  }, [fetchDetections]);

  // Returns only camera/ML-sourced detections from detection_logs
  // Note: ML predictions stored in ml_predictions table won't appear here —
  // they are fetched separately via mlAPI in the stats cards.
  const getMLDetections = useCallback(() => {
    return detections.filter((d) => d.detection_source === "camera");
  }, [detections]);

  // FIX: detection_confidence is stored as decimal (0.87), not percentage (87).
  // Threshold parameter should be 0–1. Default changed from 80 → 0.80.
  const getHighConfidenceDetections = useCallback(
    (threshold = 0.8) => {
      return detections.filter(
        (d) => d.detection_confidence && d.detection_confidence >= threshold,
      );
    },
    [detections],
  );

  const getDetectionsByObject = useCallback(
    (objectType) => {
      return detections.filter((d) => d.object_detected === objectType);
    },
    [detections],
  );

  // FIX: avgConfidence and highConfidence now correctly handle decimal confidence values.
  const getMLStats = useCallback(() => {
    const mlDetections = detections.filter(
      (d) => d.detection_source === "camera",
    );

    const avgConfidenceRaw =
      mlDetections.length > 0
        ? mlDetections.reduce(
            (sum, d) => sum + (d.detection_confidence || 0),
            0,
          ) / mlDetections.length
        : 0;

    // FIX: convert decimal to percentage for display
    const avgConfidencePct =
      avgConfidenceRaw > 1
        ? avgConfidenceRaw // already a percentage
        : avgConfidenceRaw * 100;

    // FIX: compare against decimal threshold (0.80), not 80
    const highConfidenceCount = mlDetections.filter(
      (d) => d.detection_confidence >= 0.8,
    ).length;

    return {
      total: mlDetections.length,
      avgConfidence: avgConfidencePct.toFixed(1),
      highConfidence: highConfidenceCount,
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
    getMLDetections,
    getHighConfidenceDetections,
    getDetectionsByObject,
    getMLStats,
  };
};
