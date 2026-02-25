import React, { useState, useEffect, useCallback } from "react";
import {
  Search,
  Filter,
  X,
  ChevronLeft,
  ChevronRight,
  ImageOff,
} from "lucide-react";
import { adminAPI } from "../../services/api";

const PAGE_SIZE = 25;

const DANGER_COLORS = {
  Critical: "bg-red-100 text-red-800 border border-red-200",
  High: "bg-orange-100 text-orange-800 border border-orange-200",
  Medium: "bg-amber-100 text-amber-800 border border-amber-200",
  Low: "bg-green-100 text-green-800 border border-green-200",
};

// ── Image preview modal ───────────────────────────────────────────────────────
const ImageModal = ({ detection, onClose }) => {
  if (!detection) return null;
  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl shadow-2xl max-w-2xl w-full overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200">
          <div>
            <h3 className="font-semibold text-gray-900">
              {detection.object_detected ?? "Unknown"} —{" "}
              {detection.danger_level ?? "N/A"} danger
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">
              {detection.detected_at
                ? new Date(detection.detected_at).toLocaleString()
                : "—"}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5">
          {detection.image_url ? (
            <img
              src={detection.image_url}
              alt="Detection snapshot"
              className="w-full rounded-lg object-contain max-h-96 bg-gray-100"
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-48 bg-gray-50 rounded-lg border border-gray-200">
              <ImageOff className="w-8 h-8 text-gray-400 mb-2" />
              <p className="text-sm text-gray-500">
                No image available for this detection
              </p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
            {[
              ["Device", detection.device_name ?? "—"],
              [
                "Distance",
                detection.distance_cm != null
                  ? `${detection.distance_cm} cm`
                  : "—",
              ],
              [
                "Confidence",
                detection.detection_confidence != null
                  ? `${(detection.detection_confidence * 100).toFixed(1)}%`
                  : "—",
              ],
              ["Source", detection.detection_source ?? "—"],
            ].map(([label, value]) => (
              <div key={label} className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-0.5">{label}</p>
                <p className="font-medium text-gray-900">{value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const AdminDetectionLogs = () => {
  const [detections, setDetections] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState("");
  const [dangerFilter, setDangerFilter] = useState("");
  const [selectedRow, setSelectedRow] = useState(null);

  const fetchDetections = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminAPI.getAllDetections({
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
        search: search || undefined,
        danger: dangerFilter || undefined,
      });
      setDetections(res.data?.detections ?? res.data?.data ?? []);
      setTotal(res.data?.total ?? 0);
    } catch (err) {
      setError("Failed to load detections.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [page, search, dangerFilter]);

  // Reset to page 0 when filters change
  useEffect(() => {
    setPage(0);
  }, [search, dangerFilter]);
  useEffect(() => {
    fetchDetections();
  }, [fetchDetections]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="space-y-5 fade-in">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Detection Logs</h2>
        <span className="text-sm text-gray-500">
          {total.toLocaleString()} total records
        </span>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search by object, device, source…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-purple-400 focus:border-transparent"
          />
          {search && (
            <button
              onClick={() => setSearch("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="relative">
          <Filter className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <select
            value={dangerFilter}
            onChange={(e) => setDangerFilter(e.target.value)}
            className="pl-9 pr-8 py-2 border border-gray-200 rounded-lg text-sm appearance-none focus:ring-2 focus:ring-purple-400 focus:border-transparent bg-white"
          >
            <option value="">All danger levels</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 text-sm">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                {[
                  "Timestamp",
                  "Device",
                  "Object",
                  "Distance",
                  "Danger",
                  "Confidence",
                  "Source",
                  "Image",
                ].map((h) => (
                  <th
                    key={h}
                    className="text-left px-4 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wide whitespace-nowrap"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="border-b border-gray-100">
                    {Array.from({ length: 8 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 bg-gray-100 animate-pulse rounded" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : detections.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-12 text-gray-500">
                    No detections found
                    {(search || dangerFilter) &&
                      " matching the current filters"}
                    .
                  </td>
                </tr>
              ) : (
                detections.map((d, i) => (
                  <tr
                    key={d.id ?? i}
                    onClick={() => setSelectedRow(d)}
                    className="border-b border-gray-100 hover:bg-purple-50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3 whitespace-nowrap text-gray-700">
                      {d.detected_at
                        ? new Date(d.detected_at).toLocaleString()
                        : "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-800 font-medium">
                      {d.device_name ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-800">
                      {d.object_detected ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-700">
                      {d.distance_cm != null ? `${d.distance_cm} cm` : "—"}
                    </td>
                    <td className="px-4 py-3">
                      {d.danger_level ? (
                        <span
                          className={`text-xs font-semibold px-2 py-0.5 rounded-full ${DANGER_COLORS[d.danger_level] ?? "bg-gray-100 text-gray-700"}`}
                        >
                          {d.danger_level}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-700">
                      {d.detection_confidence != null
                        ? `${(d.detection_confidence * 100).toFixed(1)}%`
                        : "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {d.detection_source ?? "—"}
                    </td>
                    <td className="px-4 py-3">
                      {d.image_url ? (
                        <img
                          src={d.image_url}
                          alt="thumb"
                          className="w-10 h-10 object-cover rounded border border-gray-200"
                        />
                      ) : (
                        <div className="w-10 h-10 bg-gray-100 rounded border border-gray-200 flex items-center justify-center">
                          <ImageOff className="w-4 h-4 text-gray-400" />
                        </div>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-gray-50">
            <p className="text-xs text-gray-600">
              Showing {page * PAGE_SIZE + 1}–
              {Math.min((page + 1) * PAGE_SIZE, total)} of{" "}
              {total.toLocaleString()}
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="p-1.5 rounded hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-xs text-gray-700">
                Page {page + 1} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="p-1.5 rounded hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Image modal */}
      {selectedRow && (
        <ImageModal
          detection={selectedRow}
          onClose={() => setSelectedRow(null)}
        />
      )}
    </div>
  );
};

export default AdminDetectionLogs;
