import React, { useState, useEffect, useRef } from "react";
import { cameraAPI } from "../../services/api";

const POLL_INTERVAL = 5000; // 5 seconds

const CameraTab = () => {
  const [snapshotUrl, setSnapshotUrl] = useState(null);
  const [updatedAt, setUpdatedAt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [frameCount, setFrameCount] = useState(0);
  const [isActive, setIsActive] = useState(false);
  const pollRef = useRef(null);

  useEffect(() => {
    fetchSnapshot(); // Initial fetch
    startPolling();
    return () => stopPolling();
  }, []);

  const startPolling = () => {
    stopPolling();
    pollRef.current = setInterval(fetchSnapshot, POLL_INTERVAL);
  };

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const fetchSnapshot = async () => {
    try {
      const response = await cameraAPI.getSnapshot();
      const data = response.data?.data;

      if (data?.snapshotUrl) {
        // Add cache-busting timestamp so browser always reloads
        const url = `${data.snapshotUrl}?t=${Date.now()}`;
        setSnapshotUrl(url);
        setUpdatedAt(data.updatedAt);
        setFrameCount((prev) => prev + 1);
        setIsActive(true);
        setError(null);
      } else {
        setIsActive(false);
      }
    } catch (err) {
      console.error("Snapshot fetch error:", err);
      setError("Could not reach backend");
    } finally {
      setLoading(false);
    }
  };

  const getTimeSince = (timestamp) => {
    if (!timestamp) return "Unknown";
    const diff = Math.floor((Date.now() - new Date(timestamp)) / 1000);
    if (diff < 5) return "Just now";
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return `${Math.floor(diff / 3600)}h ago`;
  };

  return (
    <div className="space-y-4 fade-in">
      <h2 className="text-2xl font-bold text-gray-900">Camera Preview</h2>

      {/* Status Bar */}
      <div className="flex items-center justify-between bg-white rounded-lg shadow px-4 py-3">
        <div className="flex items-center gap-2">
          <div
            className={`w-2.5 h-2.5 rounded-full ${isActive ? "bg-green-500 animate-pulse" : "bg-gray-400"}`}
          />
          <span className="text-sm font-medium text-gray-700">
            {isActive ? "Live" : "Waiting for device..."}
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span>Frame: {frameCount}</span>
          <span>Updates every 5s</span>
          {updatedAt && <span>Last: {getTimeSince(updatedAt)}</span>}
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

          {/* No snapshot */}
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

          {/* Snapshot image */}
          {snapshotUrl && (
            <>
              <img
                src={snapshotUrl}
                alt="Latest camera snapshot"
                className="w-full h-full object-cover"
                onError={() => {
                  setError("Failed to load image");
                  setIsActive(false);
                }}
              />

              {/* LIVE badge */}
              <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-red-600 text-white text-xs font-bold px-2.5 py-1 rounded-full shadow">
                <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                LIVE
              </div>

              {/* Frame info */}
              <div className="absolute bottom-3 right-3 bg-black/60 text-white text-xs px-2 py-1 rounded">
                ~5s delay · Frame: {frameCount}
              </div>
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
