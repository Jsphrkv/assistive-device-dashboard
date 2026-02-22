import React from "react";
import { getDangerColor } from "../../utils/helpers";

// NOTE: This component is NOT currently used by DetectionLogsTab —
// that tab renders its own inline table. LogsTable is a simpler
// read-only table, likely intended for embedding elsewhere (e.g. Dashboard
// or a modal). Keeping it here in case it's used in other places.

const LogsTable = ({ logs }) => {
  if (!logs || logs.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No detection logs found
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Date & Time
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Obstacle Type
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Distance (cm)
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Danger Level
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Alert Triggered
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {logs.map((log) => (
            <tr key={log.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 text-sm text-gray-900">
                {/* FIX: Format raw ISO timestamp so it's human-readable */}
                {log.detected_at
                  ? new Date(log.detected_at).toLocaleString()
                  : "N/A"}
              </td>
              <td className="px-6 py-4 text-sm text-gray-900">
                {log.obstacle_type || "unknown"}
              </td>
              <td className="px-6 py-4 text-sm text-gray-900">
                {/* FIX: null guard — was rendering "null cm" or "undefined cm" */}
                {log.distance_cm != null ? `${log.distance_cm} cm` : "N/A"}
              </td>
              <td className="px-6 py-4">
                <span
                  className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getDangerColor(
                    log.danger_level,
                  )}`}
                >
                  {log.danger_level || "Unknown"}
                </span>
              </td>
              <td className="px-6 py-4 text-sm text-gray-900">
                {log.alert_type || "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default LogsTable;
