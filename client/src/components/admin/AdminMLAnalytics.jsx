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
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from "recharts";
import { adminAPI } from "../../services/api";

const DAYS_OPTIONS = [7, 14, 30];

const PIE_COLORS = [
  "#7c3aed",
  "#2563eb",
  "#16a34a",
  "#dc2626",
  "#ea580c",
  "#0891b2",
  "#ca8a04",
  "#9333ea",
  "#0d9488",
];
const DANGER_COLORS = {
  Critical: "#dc2626",
  High: "#ea580c",
  Medium: "#f59e0b",
  Low: "#16a34a",
  Unknown: "#6b7280",
};
const TYPE_COLORS = [
  "#7c3aed",
  "#2563eb",
  "#0891b2",
  "#16a34a",
  "#ea580c",
  "#ca8a04",
  "#9333ea",
];

const Section = ({ title, subtitle, children }) => (
  <div className="bg-white rounded-lg shadow p-5">
    <div className="mb-4">
      <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
        {title}
      </h3>
      {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
    </div>
    {children}
  </div>
);

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

const Skeleton = () => (
  <div className="h-48 bg-gray-100 animate-pulse rounded-lg" />
);

const AdminMLAnalytics = () => {
  const [days, setDays] = useState(7);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
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
    fetchData();
  }, [fetchData]);

  const hourly = data?.hourlyDetections ?? [];
  const objects = data?.objectDistribution ?? [];
  const danger = data?.dangerFrequency ?? [];
  const predTypes = data?.predictionTypeBreakdown ?? [];
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

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">ML Analytics</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            ML model prediction trends and performance —{" "}
            <span className="font-medium text-purple-600">
              sourced entirely from ml_predictions
            </span>
          </p>
        </div>
        <div className="flex items-center gap-3">
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
            onClick={fetchData}
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

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          {
            label: "Total ML Predictions",
            value: data?.totalPredictions?.toLocaleString() ?? "—",
            sub: `Last ${days} days`,
          },
          {
            label: "Avg Detection Confidence",
            value:
              data?.avgConfidence != null && data.avgConfidence > 0
                ? `${(data.avgConfidence * 100).toFixed(1)}%`
                : "—",
            sub: "ml_predictions.detection_confidence",
          },
          {
            label: "Model Coverage",
            value: fallbackPct != null ? `${100 - fallbackPct}% ML` : "—",
            sub: "Real inference rate",
          },
          {
            label: "Fallback Rate",
            value: fallbackPct != null ? `${fallbackPct}%` : "—",
            sub: "Rule-based fallback",
          },
        ].map(({ label, value, sub }) => (
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
            {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
          </div>
        ))}
      </div>

      {/* Line chart — predictions per hour */}
      <Section
        title={`ML Predictions per Hour — Last ${days} Days`}
        subtitle="Hourly count of ML inference runs (ml_predictions.created_at)"
      >
        {loading ? (
          <Skeleton />
        ) : hourly.length === 0 ? (
          <p className="text-sm text-gray-400 py-10 text-center">
            No prediction data for this period.
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
                name="ML Predictions"
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
        {/* Pie — predicted object distribution */}
        <Section
          title="Predicted Object Distribution"
          subtitle="Objects identified by the ML model (ml_predictions.object_detected)"
        >
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

        {/* Bar — predicted danger level frequency */}
        <Section
          title="Predicted Danger Level Frequency"
          subtitle="Danger levels assigned by ML model (ml_predictions.danger_level)"
        >
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
                <Bar dataKey="count" name="Predictions" radius={[4, 4, 0, 0]}>
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

      {/* Prediction type breakdown */}
      <Section
        title="Prediction Type Breakdown"
        subtitle="Distribution of prediction categories run by the ML pipeline (ml_predictions.prediction_type)"
      >
        {loading ? (
          <Skeleton />
        ) : predTypes.length === 0 ? (
          <p className="text-sm text-gray-400 py-4 text-center">
            No prediction type data available.
          </p>
        ) : (
          <div className="flex items-center gap-6">
            <ResponsiveContainer width="35%" height={180}>
              <PieChart>
                <Pie
                  data={predTypes}
                  dataKey="count"
                  nameKey="prediction_type"
                  cx="50%"
                  cy="50%"
                  outerRadius={70}
                  innerRadius={35}
                >
                  {predTypes.map((_, i) => (
                    <Cell key={i} fill={TYPE_COLORS[i % TYPE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <ul className="flex-1 space-y-2 text-xs">
              {predTypes.map((t, i) => {
                const total = predTypes.reduce((s, x) => s + x.count, 0);
                const pct = total > 0 ? Math.round((t.count / total) * 100) : 0;
                return (
                  <li
                    key={t.prediction_type}
                    className="flex items-center gap-2"
                  >
                    <span
                      className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{
                        backgroundColor: TYPE_COLORS[i % TYPE_COLORS.length],
                      }}
                    />
                    <span className="text-gray-700 capitalize truncate">
                      {t.prediction_type}
                    </span>
                    <span className="ml-auto font-semibold text-gray-900">
                      {t.count.toLocaleString()}
                    </span>
                    <span className="text-gray-400 w-8 text-right">{pct}%</span>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </Section>

      {/* Model source ratio */}
      <Section
        title="Model Source Ratio — ML Model vs Rule-based Fallback"
        subtitle="Whether predictions used real ML inference or rule-based fallback (ml_predictions.model_source)"
      >
        {loading ? (
          <Skeleton />
        ) : sourceData.length === 0 ? (
          <p className="text-sm text-gray-400 py-4 text-center">
            No source data available.
          </p>
        ) : (
          <div className="space-y-3">
            {sourceData.map((s) => {
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
                      className={`h-full rounded-full transition-all duration-500 ${isML ? "bg-purple-500" : "bg-amber-400"}`}
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
                  <strong>{fallbackPct}%</strong> of predictions used the
                  rule-based fallback. Check ML model health — models may not be
                  loading correctly on the HF Space.
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
