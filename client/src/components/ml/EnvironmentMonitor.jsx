import React, { useState, useEffect } from "react";
import { MapPin, Sun, Layers, RefreshCw } from "lucide-react";
import { mlAPI } from "../../services/api";

const EnvironmentMonitor = ({
  deviceId,
  environmentData: propEnvironmentData,
  loading: propLoading,
}) => {
  const [environmentData, setEnvironmentData] = useState(null);
  const [loading, setLoading] = useState(true);

  const usingProps = propEnvironmentData !== undefined;

  useEffect(() => {
    if (usingProps) {
      processEnvironmentData(propEnvironmentData);
      setLoading(propLoading || false);
    } else {
      fetchEnvironmentData();
      const interval = setInterval(fetchEnvironmentData, 30000);
      return () => clearInterval(interval);
    }
  }, [deviceId, propEnvironmentData, propLoading, usingProps]);

  const processEnvironmentData = (data) => {
    if (!data || data.length === 0) {
      setEnvironmentData(null);
      return;
    }

    const latest = data[0];

    // API /api/ml-history wraps flat DB columns into a `result` object:
    // {
    //   confidence_score: number | null   ← top-level, 0-1 normalized by backend
    //   result: {
    //     environment_type, lighting_condition, complexity_level, message
    //   }
    // }
    const result = latest.result || {};

    // confidence_score is already 0-1 from _normalize_confidence() in backend
    const rawConf = latest.confidence_score ?? 0;
    const confidencePct = rawConf > 1 ? rawConf : rawConf * 100;

    setEnvironmentData({
      environmentType: result.environment_type || "unknown",
      lightingCondition: result.lighting_condition || "unknown",
      complexityLevel: result.complexity_level || "unknown",
      confidence: confidencePct,
      timestamp: latest.timestamp,
    });
  };

  const fetchEnvironmentData = async () => {
    try {
      setLoading(true);
      const response = await mlAPI.getHistory({
        type: "environment_classification",
        limit: 10,
      });
      const predictions = response.data?.data || [];
      const filtered =
        deviceId && deviceId !== "device-001"
          ? predictions.filter((p) => p.device_id === deviceId)
          : predictions;
      processEnvironmentData(filtered);
    } catch (error) {
      console.error("Error fetching environment data:", error);
      setEnvironmentData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    if (!usingProps) fetchEnvironmentData();
  };

  if (loading && !environmentData) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
        </div>
      </div>
    );
  }

  const environmentConfig = {
    indoor: { icon: "🏢", color: "bg-blue-100 text-blue-700", label: "Indoor" },
    outdoor: {
      icon: "🌳",
      color: "bg-green-100 text-green-700",
      label: "Outdoor",
    },
    crowded: {
      icon: "👥",
      color: "bg-orange-100 text-orange-700",
      label: "Crowded",
    },
    open_space: {
      icon: "🏞️",
      color: "bg-teal-100 text-teal-700",
      label: "Open Space",
    },
    narrow_corridor: {
      icon: "🚪",
      color: "bg-purple-100 text-purple-700",
      label: "Corridor",
    },
    unknown: {
      icon: "❓",
      color: "bg-gray-100 text-gray-700",
      label: "Unknown",
    },
  };
  const lightingConfig = {
    bright: { icon: "☀️", color: "text-yellow-600" },
    dim: { icon: "🌥️", color: "text-gray-600" },
    dark: { icon: "🌙", color: "text-indigo-600" },
    unknown: { icon: "💡", color: "text-gray-400" },
  };
  const complexityConfig = {
    simple: {
      color: "bg-green-100 text-green-700 border-green-300",
      label: "Simple",
    },
    moderate: {
      color: "bg-yellow-100 text-yellow-700 border-yellow-300",
      label: "Moderate",
    },
    complex: {
      color: "bg-red-100 text-red-700 border-red-300",
      label: "Complex",
    },
    unknown: {
      color: "bg-gray-100 text-gray-700 border-gray-300",
      label: "Unknown",
    },
  };

  const envCfg =
    environmentConfig[environmentData?.environmentType] ||
    environmentConfig.unknown;
  const lightCfg =
    lightingConfig[environmentData?.lightingCondition] ||
    lightingConfig.unknown;
  const cmpxCfg =
    complexityConfig[environmentData?.complexityLevel] ||
    complexityConfig.unknown;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <MapPin className="w-5 h-5 text-purple-600" />
          Environment Monitor
        </h3>
        {!usingProps && (
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="text-sm text-purple-600 hover:text-purple-700"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        )}
      </div>

      {!environmentData ? (
        <div className="text-center py-8">
          <MapPin className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p className="text-gray-500 text-sm">No environment data yet</p>
          <p className="text-gray-400 text-xs mt-1">
            Collecting sensor patterns...
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="text-center">
            <div className="text-6xl mb-2">{envCfg.icon}</div>
            <div
              className={`inline-block px-4 py-2 rounded-full font-semibold ${envCfg.color}`}
            >
              {envCfg.label}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Sun className="w-4 h-4 text-gray-600" />
                <p className="text-xs text-gray-600 font-medium">Lighting</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-2xl">{lightCfg.icon}</span>
                <span className={`font-semibold capitalize ${lightCfg.color}`}>
                  {environmentData.lightingCondition}
                </span>
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Layers className="w-4 h-4 text-gray-600" />
                <p className="text-xs text-gray-600 font-medium">Complexity</p>
              </div>
              <div
                className={`px-3 py-1 rounded-lg border font-semibold text-sm ${cmpxCfg.color}`}
              >
                {cmpxCfg.label}
              </div>
            </div>
          </div>

          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <p className="text-xs text-blue-600 font-medium mb-2">
              💡 Recommendations
            </p>
            <ul className="text-xs text-blue-700 space-y-1">
              {environmentData.environmentType === "crowded" && (
                <li>• Reduce speed and stay alert in crowded areas</li>
              )}
              {environmentData.environmentType === "narrow_corridor" && (
                <li>• Proceed carefully - limited maneuvering space</li>
              )}
              {environmentData.lightingCondition === "dark" && (
                <li>• Low visibility - use extra caution</li>
              )}
              {environmentData.complexityLevel === "complex" && (
                <li>• High obstacle density - navigate slowly</li>
              )}
              {environmentData.environmentType === "open_space" && (
                <li>• Open area - safe for normal navigation</li>
              )}
              {environmentData.environmentType !== "crowded" &&
                environmentData.environmentType !== "narrow_corridor" &&
                environmentData.environmentType !== "open_space" &&
                environmentData.lightingCondition !== "dark" &&
                environmentData.complexityLevel !== "complex" && (
                  <li>• Conditions are normal — proceed as usual</li>
                )}
            </ul>
          </div>

          {environmentData.confidence > 0 && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs text-gray-600">
                  Classification Confidence
                </p>
                <p className="text-xs text-gray-600">
                  {environmentData.confidence.toFixed(0)}%
                </p>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-purple-600 h-2 rounded-full transition-all"
                  style={{
                    width: `${Math.min(100, environmentData.confidence)}%`,
                  }}
                />
              </div>
            </div>
          )}

          <div className="pt-2 border-t text-xs text-gray-500 text-center">
            Updated {new Date(environmentData.timestamp).toLocaleTimeString()}
          </div>
        </div>
      )}
    </div>
  );
};

export default EnvironmentMonitor;
