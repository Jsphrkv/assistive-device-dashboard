import React from "react";
import { getDangerColor } from "../../utils/helpers";

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
                {log.detected_at}
              </td>
              <td className="px-6 py-4 text-sm text-gray-900">
                {log.obstacle_type}
              </td>
              <td className="px-6 py-4 text-sm text-gray-900">
                {log.distance_cm} cm
              </td>
              <td className="px-6 py-4">
                <span
                  className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getDangerColor(
                    log.danger_level
                  )}`}
                >
                  {log.danger_level}
                </span>
              </td>
              <td className="px-6 py-4 text-sm text-gray-900">
                {log.alert_type}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default LogsTable;
