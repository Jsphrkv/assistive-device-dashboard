import React, { useState, useEffect, useCallback } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Camera, RefreshCw, Eye, TrendingUp } from "lucide-react";
import { mlAPI, detectionsAPI } from "../../services/api";

// ── constants ─────────────────────────────────────────────────────────────────

const RANGE_OPTIONS = [
  { label: "24h", value: "24h", hours: 24 },
  { label: "7d", value: "7d", hours: 168 },
  { label: "30d", value: "30d", hours: 720 },
];

const SOURCE_COLORS = {
  camera: "#6366f1",
  yolo: "#6366f1",
  ultrasonic: "#10b981",
  heuristic: "#f59e0b",
  unknown: "#94a3b8",
};

const OBJECT_COLORS = [
  "#6366f1",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
  "#f97316",
  "#84cc16",
];

// ── helpers ───────────────────────────────────────────────────────────────────

const cutoffISO = (hours) => {
  const d = new Date();
  d.setHours(d.getHours() - hours);
  return d.toISOString();
};

const fmtConfidence = (v) => (v != null ? `${(v * 100).toFixed(0)}%` : "—");

// ── component ─────────────────────────────────────────────────────────────────

const ObjectDetectionWidget = ({ deviceId }) => {
  const [range, setRange] = useState("7d");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const hours = RANGE_OPTIONS.find((r) => r.value === range)?.hours ?? 168;
      const cutoff = cutoffISO(hours);

      // Fetch detection_logs — this has detection_source, object_detected, confidence
      const logsRes = await detectionsAPI.getRecent();
      const allLogs = (logsRes.data?.detections || []).filter(
        (d) => new Date(d.detected_at) >= new Date(cutoff),
      );

      // Fetch ml_predictions for yolo_detection + object_detection types
      const [yoloRes, objRes] = await Promise.all([
        mlAPI
          .getHistory({ type: "yolo_detection", limit: 1000 })
          .catch(() => ({ data: { data: [] } })),
        mlAPI
          .getHistory({ type: "object_detection", limit: 1000 })
          .catch(() => ({ data: { data: [] } })),
      ]);

      const yoloPreds = (yoloRes.data?.data || []).filter(
        (d) => new Date(d.timestamp) >= new Date(cutoff),
      );
      const objPreds = (objRes.data?.data || []).filter(
        (d) => new Date(d.timestamp) >= new Date(cutoff),
      );

      // ── 1. Totals ────────────────────────────────────────────────────────
      const totalCamera = allLogs.filter(
        (d) => d.detection_source === "camera",
      ).length;
      const totalUltrasonic = allLogs.filter(
        (d) => d.detection_source !== "camera",
      ).length;
      const totalYolo = yoloPreds.length;
      const totalObj = objPreds.length;
      const totalAll = allLogs.length;

      // ── 2. Source breakdown (pie) ────────────────────────────────────────
      const sourceCounts = allLogs.reduce((acc, d) => {
        const src = d.detection_source || "unknown";
        acc[src] = (acc[src] || 0) + 1;
        return acc;
      }, {});
      const sourceData = Object.entries(sourceCounts).map(([name, value]) => ({
        name,
        value,
        color: SOURCE_COLORS[name] || SOURCE_COLORS.unknown,
      }));

      // ── 3. Top 5 objects (bar) ───────────────────────────────────────────
      const objCounts = allLogs.reduce((acc, d) => {
        const obj = d.object_detected || "unknown";
        acc[obj] = (acc[obj] || 0) + 1;
        return acc;
      }, {});
      const topObjects = Object.entries(objCounts)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 5)
        .map(([name, count]) => ({ name, count }));

      // ── 4. Confidence over time (line) ───────────────────────────────────
      // Bucket by day (7d/30d) or by 2-hour blocks (24h)
      const bucketMs = hours <= 24 ? 2 * 3600 * 1000 : 24 * 3600 * 1000;
      const buckets = {};

      allLogs.forEach((d) => {
        if (d.detection_confidence == null) return;
        const ts = new Date(d.detected_at).getTime();
        const key = Math.floor(ts / bucketMs) * bucketMs;
        if (!buckets[key]) buckets[key] = [];
        buckets[key].push(parseFloat(d.detection_confidence));
      });

      const confidenceLine = Object.entries(buckets)
        .sort(([a], [b]) => Number(a) - Number(b))
        .map(([key, vals]) => {
          const avg = vals.reduce((s, v) => s + v, 0) / vals.length;
          const dt = new Date(Number(key));
          const label =
            hours <= 24
              ? dt.toLocaleTimeString("en-PH", {
                  hour: "2-digit",
                  minute: "2-digit",
                  timeZone: "Asia/Manila",
                })
              : dt.toLocaleDateString("en-PH", {
                  month: "short",
                  day: "numeric",
                  timeZone: "Asia/Manila",
                });
          return {
            time: label,
            confidence: parseFloat((avg * 100).toFixed(1)),
          };
        });

      // ── 5. Avg confidence ────────────────────────────────────────────────
      const allConf = allLogs
        .map((d) => parseFloat(d.detection_confidence))
        .filter((v) => !isNaN(v) && v > 0);
      const avgConf = allConf.length
        ? allConf.reduce((s, v) => s + v, 0) / allConf.length
        : null;

      setData({
        totals: { totalAll, totalCamera, totalUltrasonic, totalYolo, totalObj },
        sourceData,
        topObjects,
        confidenceLine,
        avgConf,
      });
    } catch (err) {
      console.error("ObjectDetectionWidget fetch error:", err);
      setError("Could not load detection data");
    } finally {
      setLoading(false);
    }
  }, [range, deviceId]);

  useEffect(() => {
    fetchData();
    const id = setInterval(fetchData, 60000);
    return () => clearInterval(id);
  }, [fetchData]);

  // ── loading ────────────────────────────────────────────────────────────────
  if (loading && !data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-48">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600" />
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center py-12">
        <p className="text-red-500 text-sm">{error}</p>
        <button
          onClick={fetchData}
          className="mt-3 text-sm text-blue-600 underline"
        >
          Retry
        </button>
      </div>
    );
  }

  const { totals, sourceData, topObjects, confidenceLine, avgConf } = data;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div className="flex items-center gap-2">
          <Eye className="w-5 h-5 text-indigo-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Object Detection & YOLO Stats
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {/* range toggle */}
          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            {RANGE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setRange(opt.value)}
                className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                  range === opt.value
                    ? "bg-indigo-600 text-white"
                    : "bg-white text-gray-600 hover:bg-gray-50"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <button
            onClick={fetchData}
            disabled={loading}
            className="text-gray-400 hover:text-gray-600"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* summary stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <div className="bg-indigo-50 rounded-lg p-3 text-center">
          <Camera className="w-4 h-4 text-indigo-500 mx-auto mb-1" />
          <p className="text-2xl font-bold text-indigo-700">
            {totals.totalAll.toLocaleString()}
          </p>
          <p className="text-xs text-indigo-500 mt-0.5">Total Detections</p>
        </div>
        <div className="bg-purple-50 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-purple-700">
            {totals.totalCamera.toLocaleString()}
          </p>
          <p className="text-xs text-purple-500 mt-0.5">Camera (YOLO)</p>
        </div>
        <div className="bg-emerald-50 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-emerald-700">
            {totals.totalUltrasonic.toLocaleString()}
          </p>
          <p className="text-xs text-emerald-500 mt-0.5">Ultrasonic</p>
        </div>
        <div className="bg-blue-50 rounded-lg p-3 text-center">
          <TrendingUp className="w-4 h-4 text-blue-500 mx-auto mb-1" />
          <p className="text-2xl font-bold text-blue-700">
            {avgConf != null ? `${(avgConf * 100).toFixed(0)}%` : "—"}
          </p>
          <p className="text-xs text-blue-500 mt-0.5">Avg Confidence</p>
        </div>
      </div>

      {/* charts — 3 column grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Source breakdown — pie */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-3">
            Detection Source
          </p>
          {sourceData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie
                    data={sourceData}
                    cx="50%"
                    cy="50%"
                    outerRadius={70}
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                    labelLine={false}
                  >
                    {sourceData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => [`${v} detections`, ""]} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-wrap gap-2 mt-2 justify-center">
                {sourceData.map((s, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-1 text-xs text-gray-600"
                  >
                    <div
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ background: s.color }}
                    />
                    {s.name} ({s.value})
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
              No data in range
            </div>
          )}
        </div>

        {/* Top 5 objects — bar */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-3">
            Top Detected Objects
          </p>
          {topObjects.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart
                data={topObjects}
                layout="vertical"
                margin={{ left: 8, right: 16, top: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 11 }}
                  width={70}
                />
                <Tooltip formatter={(v) => [`${v} detections`, "Count"]} />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {topObjects.map((_, i) => (
                    <Cell
                      key={i}
                      fill={OBJECT_COLORS[i % OBJECT_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
              No data in range
            </div>
          )}
        </div>

        {/* Confidence over time — line */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-3">
            Confidence Over Time
          </p>
          {confidenceLine.length > 1 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart
                data={confidenceLine}
                margin={{ left: 0, right: 8, top: 4, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 10 }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip formatter={(v) => [`${v}%`, "Avg Confidence"]} />
                <Line
                  type="monotone"
                  dataKey="confidence"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
              Not enough data points yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ObjectDetectionWidget;
