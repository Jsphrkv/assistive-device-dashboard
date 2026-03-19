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
} from "recharts";
import { Camera, RefreshCw, Eye, TrendingUp, Cpu } from "lucide-react";
import { mlAPI } from "../../services/api";

// ── constants ─────────────────────────────────────────────────────────────────

const RANGE_OPTIONS = [
  { label: "24h", value: "24h", hours: 24 },
  { label: "7d", value: "7d", hours: 168 },
  { label: "30d", value: "30d", hours: 720 },
];

const SOURCE_COLORS = [
  "#6366f1",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
  "#f97316",
  "#84cc16",
];

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

const cutoffDate = (hours) => {
  const d = new Date();
  d.setHours(d.getHours() - hours);
  return d;
};

const PieLegend = ({ data }) => (
  <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3 justify-center">
    {data.map((entry, i) => (
      <div
        key={i}
        className="flex items-center gap-1.5 text-xs text-gray-600 min-w-0"
      >
        <div
          className="w-2.5 h-2.5 rounded-full flex-shrink-0"
          style={{ background: SOURCE_COLORS[i % SOURCE_COLORS.length] }}
        />
        <span className="truncate max-w-[110px]" title={entry.name}>
          {entry.name}
        </span>
        <span className="text-gray-400 flex-shrink-0">({entry.value})</span>
      </div>
    ))}
  </div>
);

// ── component ─────────────────────────────────────────────────────────────────

const ObjectDetectionWidget = ({ deviceId }) => {
  // Pulls exclusively from ml_predictions via existing /ml-history endpoints.
  // Detection Logs tab already shows raw sensor data — no duplication here.

  const [range, setRange] = useState("7d");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const hours = RANGE_OPTIONS.find((r) => r.value === range)?.hours ?? 168;
      const cutoff = cutoffDate(hours);

      // Fetch yolo_detection + object_detection from ml_predictions
      const [yoloRes, objRes] = await Promise.all([
        mlAPI
          .getHistory({ type: "yolo_detection", limit: 1000 })
          .catch(() => ({ data: { data: [] } })),
        mlAPI
          .getHistory({ type: "object_detection", limit: 1000 })
          .catch(() => ({ data: { data: [] } })),
      ]);

      const yoloPreds = (yoloRes.data?.data || []).filter(
        (d) => new Date(d.timestamp) >= cutoff,
      );
      const objPreds = (objRes.data?.data || []).filter(
        (d) => new Date(d.timestamp) >= cutoff,
      );

      const allPreds = [...yoloPreds, ...objPreds];

      // ── Totals ───────────────────────────────────────────────────────────
      const totalYolo = yoloPreds.length;
      const totalObj = objPreds.length;
      const totalAll = allPreds.length;

      // ── Model source breakdown (pie) ─────────────────────────────────────
      // Shows yolo_onnx vs ml_model vs fallback vs heuristic
      const sourceCounts = allPreds.reduce((acc, d) => {
        const src =
          d.result?.model_source ||
          (d.prediction_type === "yolo_detection" ? "yolo_onnx" : "ml_model");
        acc[src] = (acc[src] || 0) + 1;
        return acc;
      }, {});

      // Also group by prediction_type for clearer labeling
      const typeCounts = {
        "YOLO Camera": totalYolo,
        "Object ML": totalObj,
      };

      const sourceData = Object.entries(typeCounts)
        .filter(([, v]) => v > 0)
        .sort(([, a], [, b]) => b - a)
        .map(([name, value]) => ({ name, value }));

      // ── Top 5 detected objects ───────────────────────────────────────────
      const objCounts = allPreds.reduce((acc, d) => {
        const obj =
          d.result?.object_detected ||
          d.result?.object ||
          d.result?.obstacle_type ||
          "unknown";
        if (obj && obj !== "none") {
          acc[obj] = (acc[obj] || 0) + 1;
        }
        return acc;
      }, {});

      const topObjects = Object.entries(objCounts)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 5)
        .map(([name, count]) => ({ name, count }));

      // ── Confidence over time ─────────────────────────────────────────────
      const bucketMs = hours <= 24 ? 2 * 3600 * 1000 : 24 * 3600 * 1000;
      const buckets = {};

      allPreds.forEach((d) => {
        const conf = d.confidence_score;
        if (conf == null) return;
        const ts = new Date(d.timestamp).getTime();
        const key = Math.floor(ts / bucketMs) * bucketMs;
        if (!buckets[key]) buckets[key] = [];
        // confidence_score is 0-1 from backend
        buckets[key].push(parseFloat(conf));
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

      // ── Avg confidence ───────────────────────────────────────────────────
      const confVals = allPreds
        .map((d) => d.confidence_score)
        .filter((v) => v != null && v > 0)
        .map((v) => parseFloat(v));
      const avgConf = confVals.length
        ? confVals.reduce((s, v) => s + v, 0) / confVals.length
        : null;

      setData({
        totals: { totalAll, totalYolo, totalObj },
        sourceData,
        topObjects,
        confidenceLine,
        avgConf,
      });
    } catch (err) {
      console.error("ObjectDetectionWidget error:", err);
      setError("Could not load ML detection data");
    } finally {
      setLoading(false);
    }
  }, [range, deviceId]);

  useEffect(() => {
    fetchData();
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

  const { totals, sourceData, topObjects, confidenceLine, avgConf } = data || {
    totals: { totalAll: 0, totalYolo: 0, totalObj: 0 },
    sourceData: [],
    topObjects: [],
    confidenceLine: [],
    avgConf: null,
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div className="flex items-center gap-2">
          <Eye className="w-5 h-5 text-indigo-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Object Detection & YOLO Stats
          </h3>
          <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
            ml_predictions
          </span>
        </div>
        <div className="flex items-center gap-2">
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

      {/* summary cards — 4 columns */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <div className="bg-indigo-50 rounded-lg p-3 text-center">
          <Cpu className="w-4 h-4 text-indigo-500 mx-auto mb-1" />
          <p className="text-2xl font-bold text-indigo-700">
            {totals.totalAll.toLocaleString()}
          </p>
          <p className="text-xs text-indigo-500 mt-0.5">Total ML Runs</p>
        </div>
        <div className="bg-purple-50 rounded-lg p-3 text-center">
          <Camera className="w-4 h-4 text-purple-500 mx-auto mb-1" />
          <p className="text-2xl font-bold text-purple-700">
            {totals.totalYolo.toLocaleString()}
          </p>
          <p className="text-xs text-purple-500 mt-0.5">YOLO (Camera)</p>
        </div>
        <div className="bg-emerald-50 rounded-lg p-3 text-center">
          <Cpu className="w-4 h-4 text-emerald-500 mx-auto mb-1" />
          <p className="text-2xl font-bold text-emerald-700">
            {totals.totalObj.toLocaleString()}
          </p>
          <p className="text-xs text-emerald-500 mt-0.5">Object ML</p>
        </div>
        <div className="bg-blue-50 rounded-lg p-3 text-center">
          <TrendingUp className="w-4 h-4 text-blue-500 mx-auto mb-1" />
          <p className="text-2xl font-bold text-blue-700">
            {avgConf != null ? `${(avgConf * 100).toFixed(0)}%` : "—"}
          </p>
          <p className="text-xs text-blue-500 mt-0.5">Avg Confidence</p>
        </div>
      </div>

      {/* charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Prediction type breakdown — pie */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">
            ML Prediction Type
          </p>
          {sourceData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie
                    data={sourceData}
                    cx="50%"
                    cy="50%"
                    outerRadius={75}
                    dataKey="value"
                    label={false}
                    labelLine={false}
                  >
                    {sourceData.map((_, i) => (
                      <Cell
                        key={i}
                        fill={SOURCE_COLORS[i % SOURCE_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(v, name) => [`${v} predictions`, name]}
                  />
                </PieChart>
              </ResponsiveContainer>
              <PieLegend data={sourceData} />
            </>
          ) : (
            <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
              No data in range
            </div>
          )}
        </div>

        {/* Top 5 objects */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">
            Top Detected Objects
          </p>
          {topObjects.length > 0 ? (
            <ResponsiveContainer width="100%" height={210}>
              <BarChart
                data={topObjects}
                layout="vertical"
                margin={{ left: 4, right: 16, top: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 11 }}
                  width={80}
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

        {/* Confidence over time */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">
            Confidence Over Time
          </p>
          {confidenceLine.length > 1 ? (
            <ResponsiveContainer width="100%" height={210}>
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
