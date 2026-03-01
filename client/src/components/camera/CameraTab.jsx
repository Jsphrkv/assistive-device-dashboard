import React, { useState, useEffect, useRef, useCallback } from "react";
import { RefreshCw } from "lucide-react";
// import { cameraAPI } from "../../services/api";

const POLL_INTERVAL = 5000; // 5 seconds
const TICK_INTERVAL = 1000; // 1 second — keeps "Last: Xs ago" display fresh

// FIX: If the snapshot's updatedAt is older than this, the device is
// considered offline even if the backend returns a valid URL.
// The backend always returns the last stored snapshot — even one from
// 27h ago — so we must check freshness ourselves rather than trusting
// a non-null URL as proof the device is currently on.
// 30s = 2× the poll interval, giving one missed cycle of grace.
const STALE_THRESHOLD_MS = 30_000;

const CameraTab = () => {
  const [snapshotUrl, setSnapshotUrl] = useState(null);
  const [updatedAt, setUpdatedAt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [frameCount, setFrameCount] = useState(0);
  const [isActive, setIsActive] = useState(false);
  const [, setTick] = useState(0); // forces re-render every second so "Xs ago" stays accurate

  const pollRef = useRef(null);
  const tickRef = useRef(null);
  const isMountedRef = useRef(true); // guards against setState on unmounted component

  const fetchSnapshot = useCallback(async () => {
    try {
      const response = await cameraAPI.getSnapshot();

      if (!isMountedRef.current) return;

      const data = response.data?.data;

      if (data?.snapshotUrl) {
        // FIX: Core stale-snapshot fix. The backend returns the last
        // stored snapshot URL regardless of device status. We calculate
        // the age of the snapshot and only mark the device as "Live"
        // if the image was uploaded within the last 30 seconds.
        // If stale (e.g. 27h old), we still show the last known frame
        // so the user can see what the camera last captured, but we
        // correctly show the device as offline — not "Live".
        const snapshotAge = data.updatedAt
          ? Date.now() - new Date(data.updatedAt).getTime()
          : Infinity;
        const isRecent = snapshotAge < STALE_THRESHOLD_MS;

        // Cache-busting timestamp so browser always reloads the image
        const url = `${data.snapshotUrl}?t=${Date.now()}`;
        setSnapshotUrl(url);
        setUpdatedAt(data.updatedAt);
        setError(null);

        if (isRecent) {
          setFrameCount((prev) => prev + 1);
          setIsActive(true);
        } else {
          // Stale snapshot — device is offline. Don't increment frameCount
          // since no new frame was actually received.
          setIsActive(false);
        }
      } else {
        setIsActive(false);
      }
    } catch (err) {
      console.error("Snapshot fetch error:", err);
      if (!isMountedRef.current) return;

      setIsActive(false);
      setError("Could not reach backend");
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, []);

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const startPolling = useCallback(() => {
    stopPolling();
    pollRef.current = setInterval(fetchSnapshot, POLL_INTERVAL);
  }, [fetchSnapshot]);

  const startTick = () => {
    if (tickRef.current) clearInterval(tickRef.current);
    tickRef.current = setInterval(() => {
      if (isMountedRef.current) setTick((t) => t + 1);
    }, TICK_INTERVAL);
  };

  const stopTick = () => {
    if (tickRef.current) {
      clearInterval(tickRef.current);
      tickRef.current = null;
    }
  };

  useEffect(() => {
    isMountedRef.current = true;
    fetchSnapshot();
    startPolling();
    startTick();

    return () => {
      isMountedRef.current = false;
      stopPolling();
      stopTick();
    };
  }, [fetchSnapshot, startPolling]);

  const handleManualRefresh = () => {
    setLoading(true);
    fetchSnapshot();
    startPolling();
  };

  const getTimeSince = (timestamp) => {
    if (!timestamp) return "Unknown";
    const diff = Math.floor((Date.now() - new Date(timestamp)) / 1000);
    if (diff < 5) return "Just now";
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return `${Math.floor(diff / 3600)}h ago`;
  };

  // Whether we have a snapshot but it's stale — used to show context in UI
  const isStale = snapshotUrl && !isActive && !error;

  return (
    <div className="space-y-4 fade-in">
      <h2 className="text-2xl font-bold text-gray-900">Camera Preview</h2>

      {/* Status Bar */}
      <div className="flex items-center justify-between bg-white rounded-lg shadow px-4 py-3">
        <div className="flex items-center gap-2">
          <div
            className={`w-2.5 h-2.5 rounded-full ${
              isActive
                ? "bg-green-500 animate-pulse"
                : isStale
                  ? "bg-yellow-400"
                  : "bg-gray-400"
            }`}
          />
          <span className="text-sm font-medium text-gray-700">
            {isActive
              ? "Live"
              : isStale
                ? "Device offline — showing last known frame"
                : "Waiting for device..."}
          </span>
        </div>

        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span>Frame: {frameCount}</span>
          <span>Updates every 5s</span>
          {updatedAt && <span>Last: {getTimeSince(updatedAt)}</span>}

          <button
            onClick={handleManualRefresh}
            disabled={loading}
            title="Refresh now"
            className="flex items-center gap-1 px-2 py-1 rounded hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`}
            />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Camera View */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="relative bg-gray-900" style={{ aspectRatio: "4/3" }}>
          {/* Loading */}
          {loading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-400">
              <div className="w-8 h-8 border-2 border-gray-400 border-t-transparent rounded-full animate-spin mb-3" />
              <p className="text-sm">Connecting to device...</p>
            </div>
          )}

          {/* No snapshot at all */}
          {!loading && !snapshotUrl && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-500">
              <svg
                className="w-16 h-16 mb-4 opacity-40"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              <p className="text-sm font-medium">No snapshot available</p>
              <p className="text-xs mt-1 text-gray-400">
                {error || "Waiting for device to send first frame..."}
              </p>
            </div>
          )}

          {/* Snapshot image — shown for both live and stale snapshots */}
          {snapshotUrl && (
            <>
              <img
                src={snapshotUrl}
                alt="Latest camera snapshot"
                className={`w-full h-full object-cover ${isStale ? "opacity-60" : ""}`}
                onError={() => {
                  if (!isMountedRef.current) return;
                  setError("Failed to load image");
                  setIsActive(false);
                }}
              />

              {/* Badge — LIVE when active, OFFLINE when stale */}
              {isActive && (
                <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-red-600 text-white text-xs font-bold px-2.5 py-1 rounded-full shadow">
                  <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                  LIVE
                </div>
              )}
              {isStale && (
                <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-yellow-500 text-white text-xs font-bold px-2.5 py-1 rounded-full shadow">
                  <div className="w-1.5 h-1.5 rounded-full bg-white" />
                  OFFLINE · Last frame {getTimeSince(updatedAt)}
                </div>
              )}

              {/* Frame info — only shown when live */}
              {isActive && (
                <div className="absolute bottom-3 right-3 bg-black/60 text-white text-xs px-2 py-1 rounded">
                  ~5s delay · Frame: {frameCount}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
          <p className="text-xs text-gray-500 text-center">
            Camera feed updates every 5 seconds · Snapshots stored in Supabase
            Storage
          </p>
        </div>
      </div>

      {/* Info card */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>ℹ️ How it works:</strong> Your device captures a snapshot
          every 5 seconds and uploads it here. The image automatically refreshes
          — no need to reload the page.
        </p>
      </div>
    </div>
  );
};

export default CameraTab;
