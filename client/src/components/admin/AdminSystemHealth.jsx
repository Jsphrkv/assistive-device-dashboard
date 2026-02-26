import React, { useState, useEffect, useCallback } from "react";
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Server,
  Cpu,
  Wifi,
  HeartPulse,
} from "lucide-react";
import { adminAPI, deviceAPI } from "../../services/api";

const POLL_INTERVAL = 30_000; // 30s

// ── Small reusable status row ─────────────────────────────────────────────────
const StatusRow = ({ label, value, status, sub }) => {
  const icon =
    status === "ok" ? (
      <CheckCircle className="w-4 h-4 text-green-500" />
    ) : status === "error" ? (
      <XCircle className="w-4 h-4 text-red-500" />
    ) : (
      <AlertCircle className="w-4 h-4 text-amber-400" />
    );

  const badge =
    status === "ok"
      ? "bg-green-100 text-green-800"
      : status === "error"
        ? "bg-red-100   text-red-800"
        : "bg-amber-100 text-amber-800";

  return (
    <div className="flex items-center justify-between py-2.5 border-b border-gray-100 last:border-0">
      <div>
        <p className="text-sm font-medium text-gray-800">{label}</p>
        {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
      </div>
      <div className="flex items-center gap-2">
        <span
          className={`text-xs font-semibold px-2 py-0.5 rounded-full ${badge}`}
        >
          {value}
        </span>
        {icon}
      </div>
    </div>
  );
};

// ── Section card wrapper ──────────────────────────────────────────────────────
const Card = ({ title, icon: Icon, children, loading }) => (
  <div className="bg-white rounded-lg shadow p-5">
    <div className="flex items-center gap-2 mb-4">
      <Icon className="w-5 h-5 text-purple-600" />
      <h3 className="text-base font-semibold text-gray-900">{title}</h3>
      {loading && (
        <div className="ml-auto">
          <div className="w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
    {children}
  </div>
);

const AdminSystemHealth = () => {
  const [health, setHealth] = useState(null);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [error, setError] = useState(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthRes, devicesRes] = await Promise.allSettled([
        adminAPI.getHealth(),
        deviceAPI.getAll(),
      ]);

      if (healthRes.status === "fulfilled") {
        setHealth(healthRes.value.data);
      } else {
        // Build a degraded health object so UI still renders
        setHealth({
          hfSpace: { status: "error", latencyMs: null },
          renderBackend: { status: "error", latencyMs: null },
          mlModels: {
            yolo: { status: "unknown", source: "—" },
            danger: { status: "unknown", source: "—" },
            anomaly: { status: "unknown", source: "—" },
            object: { status: "unknown", source: "—" },
          },
        });
      }

      if (devicesRes.status === "fulfilled") {
        setDevices(devicesRes.value.data?.data || []);
      }

      setLastRefresh(new Date());
    } catch (err) {
      setError("Failed to load system health.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchAll]);

  // Derive active device count from last_seen freshness (same 2-min threshold
  // used in DeviceSystemTab — "active" DB status ≠ currently online)
  const ONLINE_THRESHOLD_MS = 2 * 60 * 1000;
  const onlineDevices = devices.filter(
    (d) =>
      d.last_seen &&
      Date.now() - new Date(d.last_seen).getTime() < ONLINE_THRESHOLD_MS,
  );

  const hf = health?.hfSpace;
  const rb = health?.renderBackend;
  const ml = health?.mlModels;

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">System Health</h2>
          {lastRefresh && (
            <p className="text-xs text-gray-500 mt-0.5">
              Last checked: {lastRefresh.toLocaleTimeString()} · auto-refreshes
              every 30s
            </p>
          )}
        </div>
        <button
          onClick={fetchAll}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 text-sm">
          {error}
        </div>
      )}

      {/* Summary stat bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          {
            label: "Active Devices",
            value: loading ? "—" : `${onlineDevices.length}/${devices.length}`,
            color: "purple",
          },
          {
            label: "HF Space",
            value: loading ? "—" : hf?.status === "ok" ? "Online" : "Offline",
            color: hf?.status === "ok" ? "green" : "red",
          },
          {
            label: "Render Backend",
            value: loading ? "—" : rb?.status === "ok" ? "Online" : "Offline",
            color: rb?.status === "ok" ? "green" : "red",
          },
          {
            label: "ML Models",
            value: loading
              ? "—"
              : ml
                ? `${Object.values(ml).filter((m) => m.status === "ok").length}/${Object.keys(ml).length}`
                : "—",
            color: "blue",
          },
        ].map(({ label, value, color }) => (
          <div
            key={label}
            className="bg-white rounded-lg shadow p-4 text-center"
          >
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">
              {label}
            </p>
            <p className={`text-2xl font-bold text-${color}-600`}>{value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Services */}
        <Card title="Services" icon={Wifi} loading={loading}>
          {hf && rb ? (
            <>
              <StatusRow
                label="Hugging Face Space (ML)"
                value={hf.status === "ok" ? "Online" : "Offline"}
                status={hf.status}
                sub={
                  hf.latencyMs != null
                    ? `${hf.latencyMs}ms response`
                    : undefined
                }
              />
              <StatusRow
                label="Render Backend (API)"
                value={rb.status === "ok" ? "Online" : "Offline"}
                status={rb.status}
                sub={
                  rb.latencyMs != null
                    ? `${rb.latencyMs}ms response`
                    : undefined
                }
              />
            </>
          ) : (
            <p className="text-sm text-gray-400 py-2">
              Loading service status…
            </p>
          )}
        </Card>

        {/* ML Models */}
        <Card title="ML Model Health" icon={Cpu} loading={loading}>
          {ml ? (
            <>
              <StatusRow
                label="YOLO Object Detection"
                value={
                  ml.yolo?.status === "ok"
                    ? "Loaded"
                    : (ml.yolo?.status ?? "Unknown")
                }
                status={ml.yolo?.status === "ok" ? "ok" : "error"}
                sub={`Source: ${ml.yolo?.source ?? "yolo_onnx"}`}
              />
              <StatusRow
                label="Danger Predictor"
                value={
                  ml.danger?.status === "ok"
                    ? "Loaded"
                    : (ml.danger?.status ?? "Unknown")
                }
                status={ml.danger?.status === "ok" ? "ok" : "error"}
                sub={`Source: ${ml.danger?.source ?? "ml_model"}`}
              />
              <StatusRow
                label="Anomaly Detector"
                value={
                  ml.anomaly?.status === "ok"
                    ? "Loaded"
                    : (ml.anomaly?.status ?? "Unknown")
                }
                status={ml.anomaly?.status === "ok" ? "ok" : "error"}
                sub={`Source: ${ml.anomaly?.source ?? "ml_model"}`}
              />
              <StatusRow
                label="Object Detector"
                value={
                  ml.object?.status === "ok"
                    ? "Loaded"
                    : (ml.object?.status ?? "Unknown")
                }
                status={ml.object?.status === "ok" ? "ok" : "error"}
                sub={`Source: ${ml.object?.source ?? "ml_model"}`}
              />
              <StatusRow
                label="Environment Classifier"
                value={
                  ml.environment?.status === "ok"
                    ? "Loaded"
                    : (ml.environment?.status ?? "Unknown")
                }
                status={ml.environment?.status === "ok" ? "ok" : "error"}
                sub={`Source: ${ml.environment?.source ?? "ml_model"}`}
              />
            </>
          ) : (
            <p className="text-sm text-gray-400 py-2">Loading model status…</p>
          )}
        </Card>

        {/* Registered Devices */}
        <Card title="Registered Devices" icon={Server} loading={loading}>
          {devices.length === 0 ? (
            <p className="text-sm text-gray-400 py-2">No devices registered.</p>
          ) : (
            devices.map((d) => {
              const isOnline =
                d.last_seen &&
                Date.now() - new Date(d.last_seen).getTime() <
                  ONLINE_THRESHOLD_MS;
              return (
                <StatusRow
                  key={d.id}
                  label={d.device_name}
                  value={isOnline ? "Online" : "Offline"}
                  status={isOnline ? "ok" : "error"}
                  sub={
                    d.last_seen
                      ? `Last seen: ${new Date(d.last_seen).toLocaleString()}`
                      : "Never connected"
                  }
                />
              );
            })
          )}
        </Card>

        {/* Overall health summary */}
        <Card title="Health Summary" icon={HeartPulse} loading={loading}>
          {health && ml ? (
            (() => {
              const allOk =
                hf?.status === "ok" &&
                rb?.status === "ok" &&
                Object.values(ml).every((m) => m.status === "ok");
              const someDown =
                hf?.status !== "ok" ||
                rb?.status !== "ok" ||
                Object.values(ml).some((m) => m.status !== "ok");

              return (
                <div
                  className={`rounded-lg p-4 text-center ${
                    allOk
                      ? "bg-green-50 border border-green-200"
                      : someDown
                        ? "bg-amber-50 border border-amber-200"
                        : "bg-red-50   border border-red-200"
                  }`}
                >
                  <p
                    className={`text-2xl font-bold mb-1 ${
                      allOk
                        ? "text-green-700"
                        : someDown
                          ? "text-amber-700"
                          : "text-red-700"
                    }`}
                  >
                    {allOk
                      ? "✅ All Systems Operational"
                      : someDown
                        ? "⚠️ Partial Degradation"
                        : "❌ System Issues"}
                  </p>
                  <p
                    className={`text-sm ${
                      allOk
                        ? "text-green-600"
                        : someDown
                          ? "text-amber-600"
                          : "text-red-600"
                    }`}
                  >
                    {allOk
                      ? "All services and models are healthy."
                      : "One or more components need attention."}
                  </p>
                </div>
              );
            })()
          ) : (
            <div className="animate-pulse h-20 bg-gray-100 rounded-lg" />
          )}
        </Card>
      </div>
    </div>
  );
};

export default AdminSystemHealth;
