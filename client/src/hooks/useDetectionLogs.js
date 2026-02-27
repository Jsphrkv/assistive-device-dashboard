import { useState, useEffect, useCallback, useRef } from "react";
import { detectionsAPI } from "../services/api";

// Cache outside component - shared across all hook instances
const cache = {
  data: null,
  timestamp: null,
};

const CACHE_DURATION = 30000; // 30 seconds

export const useDetectionLogs = (options = {}) => {
  const { autoFetch = true, cacheDuration = CACHE_DURATION } = options;
  // Note: `limit` is intentionally removed — the backend controls pagination
  // and returns all sensor/camera detection_logs rows (up to 5000) in bulk.

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
        // No limit param — backend paginates internally (5 pages × 1000 = 5000 max)
        const response = await detectionsAPI.getRecent();
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
    [cacheDuration],
  );

  useEffect(() => {
    isMounted.current = true;
    if (autoFetch) fetchDetections();
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

  // Returns camera-sourced detections only (detection_source === "camera")
  // Note: ML model predictions live in the separate ml_predictions table
  // and are fetched via mlAPI — they do NOT appear in this hook.
  const getCameraDetections = useCallback(() => {
    return detections.filter((d) => d.detection_source === "camera");
  }, [detections]);

  // detection_confidence is stored as a decimal (e.g. 0.87), threshold is 0–1
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

  // Stats scoped to camera-sourced detections only
  const getCameraStats = useCallback(() => {
    const cameraDetections = detections.filter(
      (d) => d.detection_source === "camera",
    );

    const avgConfidenceRaw =
      cameraDetections.length > 0
        ? cameraDetections.reduce(
            (sum, d) => sum + (d.detection_confidence || 0),
            0,
          ) / cameraDetections.length
        : 0;

    // Confidence stored as decimal (0.87) — convert to percentage for display
    const avgConfidencePct =
      avgConfidenceRaw > 1 ? avgConfidenceRaw : avgConfidenceRaw * 100;

    // Compare against decimal threshold (0.80)
    const highConfidenceCount = cameraDetections.filter(
      (d) => d.detection_confidence >= 0.8,
    ).length;

    return {
      total: cameraDetections.length,
      avgConfidence: avgConfidencePct.toFixed(1),
      highConfidence: highConfidenceCount,
      uniqueObjects: [
        ...new Set(cameraDetections.map((d) => d.object_detected)),
      ].filter(Boolean).length,
    };
  }, [detections]);

  // Keep getMLStats as an alias for backward compatibility
  const getMLStats = getCameraStats;

  return {
    detections,
    loading,
    error,
    fetchDetections,
    addDetection,
    clearDetections,
    refresh,
    getCameraDetections,
    getHighConfidenceDetections,
    getDetectionsByObject,
    getCameraStats,
    getMLStats, // backward-compat alias
  };
};
