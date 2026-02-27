import React, { useState, useEffect, useCallback } from "react";
import { RefreshCw, TrendingUp } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from "recharts";
import { adminAPI } from "../../services/api";

const DAYS_OPTIONS = [7, 14, 30];

// Colour palettes
const PIE_COLORS = [
  "#7c3aed",
  "#2563eb",
  "#16a34a",
  "#dc2626",
  "#ea580c",
  "#0891b2",
  "#ca8a04",
];
const DANGER_COLORS = {
  Critical: "#dc2626",
  High: "#ea580c",
  Medium: "#f59e0b",
  Low: "#16a34a",
};

const Section = ({ title, children }) => (
  <div className="bg-white rounded-lg shadow p-5">
    <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">
      {title}
    </h3>
    {children}
  </div>
);

// Custom recharts tooltip
const ChartTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2 text-xs">
      {label && <p className="text-gray-600 mb-1 font-medium">{label}</p>}
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>
          {p.name}: <span className="font-semibold">{p.value}</span>
        </p>
      ))}
    </div>
  );
};

const AdminMLAnalytics = () => {
  const [days, setDays] = useState(7);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminAPI.getMLAnalytics(days);
      setData(res.data);
    } catch (err) {
      setError("Failed to load ML analytics.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  // ── Build chart datasets from API response ────────────────────────────────
  // Expected shape from /admin/analytics:
  // {
  //   hourlyDetections: [{ hour: "2026-02-25 14:00", count: 12 }, ...],
  //   objectDistribution: [{ object_type: "person", count: 45 }, ...],
  //   dangerFrequency: [{ danger_level: "High", count: 20 }, ...],
  //   modelSourceRatio: { ml_model: 80, fallback: 20 },
  //   totalDetections: 300,
  //   avgConfidence: 0.74,
  // }

  const hourly = data?.hourlyDetections ?? [];
  const objects = data?.objectDistribution ?? [];
  const danger = data?.dangerFrequency ?? [];
  const sourceRatio = data?.modelSourceRatio ?? {};

  const sourceData = Object.entries(sourceRatio).map(([name, value]) => ({
    name,
    value,
  }));

  const fallbackPct =
    sourceRatio.fallback != null &&
    sourceRatio.ml_model + sourceRatio.fallback > 0
      ? Math.round(
          (sourceRatio.fallback /
            (sourceRatio.ml_model + sourceRatio.fallback)) *
            100,
        )
      : null;

  const Skeleton = () => (
    <div className="h-48 bg-gray-100 animate-pulse rounded-lg" />
  );

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">ML Analytics</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            Detection trends and model performance
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Days selector */}
          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            {DAYS_OPTIONS.map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1.5 text-sm font-medium transition-colors ${
                  days === d
                    ? "bg-purple-600 text-white"
                    : "bg-white text-gray-600 hover:bg-gray-50"
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
          <button
            onClick={fetch}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 text-sm">
          {error}
        </div>
      )}

      {/* Summary stat pills */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          {
            label: "Total ML Predictions",
            value: data?.totalPredictions?.toLocaleString() ?? "—",
          },
          {
            label: "Avg Confidence",
            value:
              data?.avgConfidence != null
                ? `${(data.avgConfidence * 100).toFixed(1)}%`
                : "—",
          },
          {
            label: "Model Coverage",
            value: fallbackPct != null ? `${100 - fallbackPct}% ML` : "—",
          },
          {
            label: "Fallback Rate",
            value: fallbackPct != null ? `${fallbackPct}%` : "—",
          },
        ].map(({ label, value }) => (
          <div
            key={label}
            className="bg-white rounded-lg shadow p-4 text-center"
          >
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
              {label}
            </p>
            <p className="text-2xl font-bold text-purple-700">
              {loading ? "—" : value}
            </p>
          </div>
        ))}
      </div>

      {/* Line chart — detections per hour */}
      <Section title={`Detections per Hour — Last ${days} days`}>
        {loading ? (
          <Skeleton />
        ) : hourly.length === 0 ? (
          <p className="text-sm text-gray-400 py-10 text-center">
            No hourly data for this period.
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart
              data={hourly}
              margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="hour"
                tick={{ fontSize: 10, fill: "#9ca3af" }}
                tickFormatter={(v) => {
                  const d = new Date(v);
                  return isNaN(d)
                    ? v
                    : `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:00`;
                }}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 10, fill: "#9ca3af" }}
                allowDecimals={false}
              />
              <Tooltip content={<ChartTooltip />} />
              <Line
                type="monotone"
                dataKey="count"
                name="Detections"
                stroke="#7c3aed"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </Section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Pie — object type distribution */}
        <Section title="Object Type Distribution">
          {loading ? (
            <Skeleton />
          ) : objects.length === 0 ? (
            <p className="text-sm text-gray-400 py-10 text-center">No data.</p>
          ) : (
            <div className="flex items-center gap-4">
              <ResponsiveContainer width="55%" height={180}>
                <PieChart>
                  <Pie
                    data={objects}
                    dataKey="count"
                    nameKey="object_type"
                    cx="50%"
                    cy="50%"
                    outerRadius={70}
                    innerRadius={35}
                  >
                    {objects.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<ChartTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              <ul className="flex-1 space-y-1.5 text-xs">
                {objects.slice(0, 7).map((o, i) => (
                  <li key={o.object_type} className="flex items-center gap-2">
                    <span
                      className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{
                        backgroundColor: PIE_COLORS[i % PIE_COLORS.length],
                      }}
                    />
                    <span className="text-gray-700 truncate">
                      {o.object_type}
                    </span>
                    <span className="ml-auto font-semibold text-gray-900">
                      {o.count}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Section>

        {/* Bar — danger level frequency */}
        <Section title="Danger Level Frequency">
          {loading ? (
            <Skeleton />
          ) : danger.length === 0 ? (
            <p className="text-sm text-gray-400 py-10 text-center">No data.</p>
          ) : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart
                data={danger}
                margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="danger_level"
                  tick={{ fontSize: 11, fill: "#6b7280" }}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: "#9ca3af" }}
                  allowDecimals={false}
                />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="count" name="Count" radius={[4, 4, 0, 0]}>
                  {danger.map((d) => (
                    <Cell
                      key={d.danger_level}
                      fill={DANGER_COLORS[d.danger_level] ?? "#6b7280"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Section>
      </div>

      {/* Model source ratio */}
      <Section title="Model Source Ratio — ML Model vs Rule-based Fallback">
        {loading ? (
          <Skeleton />
        ) : sourceData.length === 0 ? (
          <p className="text-sm text-gray-400 py-4 text-center">
            No source data available.
          </p>
        ) : (
          <div className="space-y-3">
            {sourceData.map((s, i) => {
              const total = sourceData.reduce((sum, x) => sum + x.value, 0);
              const pct = total > 0 ? Math.round((s.value / total) * 100) : 0;
              const isML = s.name === "ml_model";
              return (
                <div key={s.name}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium text-gray-700">
                      {isML
                        ? "ML Model (real inference)"
                        : "Rule-based Fallback"}
                    </span>
                    <span
                      className={`font-semibold ${isML ? "text-purple-700" : "text-amber-600"}`}
                    >
                      {pct}% ({s.value.toLocaleString()})
                    </span>
                  </div>
                  <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isML ? "bg-purple-500" : "bg-amber-400"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
            {fallbackPct != null && fallbackPct > 30 && (
              <div className="mt-3 bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-2 text-sm text-amber-800">
                <TrendingUp className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <p>
                  <strong>{fallbackPct}%</strong> of detections are using the
                  rule-based fallback. Check your ML model health — models may
                  not be loading correctly.
                </p>
              </div>
            )}
          </div>
        )}
      </Section>
    </div>
  );
};

export default AdminMLAnalytics;
