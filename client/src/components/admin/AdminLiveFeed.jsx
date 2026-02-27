import React, { useState, useEffect, useRef, useCallback } from "react";
import { Radio, Pause, Play, Trash2 } from "lucide-react";
import { adminAPI } from "../../services/api";

const POLL_INTERVAL = 3_000;
const MAX_FEED_ITEMS = 100;

const DANGER_ROW = {
  Critical: "bg-red-50   border-l-4 border-red-500",
  High: "bg-orange-50 border-l-4 border-orange-400",
  Medium: "bg-amber-50  border-l-4 border-amber-400",
  Low: "bg-green-50  border-l-4 border-green-400",
};

const DANGER_BADGE = {
  Critical: "bg-red-100    text-red-800    border border-red-200",
  High: "bg-orange-100 text-orange-800 border border-orange-200",
  Medium: "bg-amber-100  text-amber-800  border border-amber-200",
  Low: "bg-green-100  text-green-800  border border-green-200",
};

// ✅ FIX: Normalize confidence regardless of storage format
const normalizeConfidence = (v) => {
  if (v == null) return null;
  if (v > 1) return v / 100; // stored as e.g. 87.5 → normalize to 0.875
  return v;
};

const DangerPulse = ({ level }) => {
  if (level !== "Critical" && level !== "High") return null;
  return (
    <span className="relative flex h-2.5 w-2.5 flex-shrink-0">
      <span
        className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
          level === "Critical" ? "bg-red-500" : "bg-orange-400"
        }`}
      />
      <span
        className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
          level === "Critical" ? "bg-red-500" : "bg-orange-400"
        }`}
      />
    </span>
  );
};

const FeedRow = ({ item, isNew }) => {
  const rowBg =
    DANGER_ROW[item.danger_level] ?? "bg-white border-l-4 border-gray-200";
  const badge = DANGER_BADGE[item.danger_level];

  // ✅ FIX: normalize before displaying
  const confNorm = normalizeConfidence(item.detection_confidence);

  return (
    <div
      className={`${rowBg} rounded-r-lg px-4 py-3 flex items-center gap-3 transition-all duration-500 ${
        isNew ? "opacity-0 animate-[fadeIn_0.3s_ease-out_forwards]" : ""
      }`}
    >
      <DangerPulse level={item.danger_level} />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-semibold text-gray-900 truncate">
            {item.object_detected ?? "Unknown"}
          </span>
          {item.danger_level && (
            <span
              className={`text-xs font-semibold px-2 py-0.5 rounded-full ${badge}`}
            >
              {item.danger_level}
            </span>
          )}
          {item.detection_source && (
            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
              {item.detection_source}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 mt-0.5 text-xs text-gray-500">
          {item.device_name && <span>{item.device_name}</span>}
          {item.distance_cm != null && <span>{item.distance_cm} cm</span>}
          {/* ✅ FIX: use normalized value */}
          {confNorm != null && <span>{(confNorm * 100).toFixed(0)}% conf</span>}
        </div>
      </div>

      <div className="text-xs text-gray-400 whitespace-nowrap flex-shrink-0">
        {item.detected_at
          ? new Date(item.detected_at).toLocaleTimeString()
          : "—"}
      </div>
    </div>
  );
};

const AdminLiveFeed = () => {
  const [feed, setFeed] = useState([]);
  const [paused, setPaused] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newIds, setNewIds] = useState(new Set());
  const [stats, setStats] = useState({ total: 0, critical: 0, high: 0 });

  const knownIds = useRef(new Set());
  const intervalRef = useRef(null);

  const fetchFeed = useCallback(async () => {
    if (paused) return;
    try {
      const res = await adminAPI.getLiveFeed(30);
      const items = res.data?.detections ?? res.data?.data ?? [];

      const incoming = items.filter(
        (item) => item.id && !knownIds.current.has(item.id),
      );

      if (incoming.length > 0) {
        const incomingIds = new Set(incoming.map((i) => i.id));
        incoming.forEach((i) => knownIds.current.add(i.id));
        setFeed((prev) => [...incoming, ...prev].slice(0, MAX_FEED_ITEMS));
        setNewIds(incomingIds);
        setTimeout(() => setNewIds(new Set()), 800);
      }

      if (knownIds.current.size === 0) {
        items.forEach((i) => {
          if (i.id) knownIds.current.add(i.id);
        });
        setFeed(items.slice(0, MAX_FEED_ITEMS));
      }

      setError(null);
    } catch (err) {
      setError("Feed unavailable — retrying…");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [paused]);

  useEffect(() => {
    setStats({
      total: feed.length,
      critical: feed.filter((f) => f.danger_level === "Critical").length,
      high: feed.filter((f) => f.danger_level === "High").length,
    });
  }, [feed]);

  useEffect(() => {
    fetchFeed();
  }, []); // eslint-disable-line

  useEffect(() => {
    if (!paused) {
      intervalRef.current = setInterval(fetchFeed, POLL_INTERVAL);
    } else {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [paused, fetchFeed]);

  const clearFeed = () => {
    setFeed([]);
    knownIds.current.clear();
  };

  return (
    <div className="space-y-5 fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold text-gray-900">
            Live Detection Feed
          </h2>
          {!paused && (
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500" />
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPaused((p) => !p)}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-lg transition-colors ${
              paused
                ? "bg-green-600 text-white hover:bg-green-700"
                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            {paused ? (
              <>
                <Play className="w-4 h-4" /> Resume
              </>
            ) : (
              <>
                <Pause className="w-4 h-4" /> Pause
              </>
            )}
          </button>
          <button
            onClick={clearFeed}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Clear
          </button>
        </div>
      </div>

      {/* Status bar */}
      <div className="flex items-center gap-4 text-sm">
        <span className="text-gray-500">
          {paused
            ? "⏸ Paused — new detections won't appear until resumed"
            : `Polling every ${POLL_INTERVAL / 1000}s`}
        </span>
      </div>

      {/* Summary stat pills */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "In Feed", value: stats.total, color: "purple" },
          { label: "Critical", value: stats.critical, color: "red" },
          { label: "High", value: stats.high, color: "orange" },
        ].map(({ label, value, color }) => (
          <div
            key={label}
            className="bg-white rounded-lg shadow p-3 text-center"
          >
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">
              {label}
            </p>
            <p className={`text-xl font-bold text-${color}-600`}>{value}</p>
          </div>
        ))}
      </div>

      {error && (
        <div className="bg-amber-50 border border-amber-200 text-amber-800 rounded-lg p-3 text-sm">
          {error}
        </div>
      )}

      {/* Feed list */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <Radio className="w-4 h-4 text-purple-600" />
            Live Feed
          </div>
          <span className="text-xs text-gray-500">
            {feed.length} items (max {MAX_FEED_ITEMS})
          </span>
        </div>

        <div className="divide-y divide-gray-100 max-h-[60vh] overflow-y-auto">
          {loading ? (
            Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="h-14 animate-pulse bg-gray-50 border-l-4 border-gray-200 px-4 py-3"
              >
                <div className="h-4 bg-gray-200 rounded w-48 mb-2" />
                <div className="h-3 bg-gray-100 rounded w-32" />
              </div>
            ))
          ) : feed.length === 0 ? (
            <div className="py-16 text-center">
              <Radio className="w-8 h-8 text-gray-300 mx-auto mb-3" />
              <p className="text-sm text-gray-500">
                Waiting for detections…
                <br />
                <span className="text-xs text-gray-400">
                  New events from all devices will appear here in real time.
                </span>
              </p>
            </div>
          ) : (
            feed.map((item, i) => (
              <FeedRow
                key={item.id ?? i}
                item={item}
                isNew={item.id && newIds.has(item.id)}
              />
            ))
          )}
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-4px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
};

export default AdminLiveFeed;
